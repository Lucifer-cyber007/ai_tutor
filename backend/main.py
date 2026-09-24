"""
AI Tutor backend (FastAPI).

Stateless: the browser sends the learner profile and recent chat history with every request.
Run locally from the project root:
    uvicorn main:app --reload --app-dir backend
"""
import logging
import time
import unicodedata
from collections import defaultdict, deque
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ValidationError, field_validator

from groq_client import TutorAIError, chat_completion, json_completion
from math_check import compare_numeric, verify_question
from prompts import (
    EVALUATE_USER_TEMPLATE,
    LEVELS,
    SUMMARY_USER_TEMPLATE,
    TOPICS,
    build_chat_prompt,
    build_evaluate_prompt,
    build_practice_prompt,
    build_summary_prompt,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")  # local only; on Cloud Run the env vars are set directly

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ai_tutor")

# ---- Limits ----
MAX_MESSAGE_CHARS = 1000        # one learner message
MAX_HISTORY_TURNS = 20          # past messages sent back by the browser
MAX_HISTORY_CHARS = 4000        # one past message (tutor replies can be long)
MAX_ANSWER_CHARS = 200          # one practice/quiz answer
MAX_QUESTIONS = 5               # questions per /practice request
EXTRA_QUESTIONS = 2             # ask the AI for a few extra, in case some fail the maths check
RATE_LIMIT_REQUESTS = 20        # per IP ...
RATE_LIMIT_WINDOW_SECONDS = 60  # ... per minute

app = FastAPI(title="AI Tutor", docs_url=None, redoc_url=None, openapi_url=None)


# ---- Request models (input validation) ----
def _not_blank(value: str, message: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(message)
    return value


class Profile(BaseModel):
    name: str = Field(max_length=40)
    level: Literal[tuple(LEVELS)]
    topic: Literal[tuple(TOPICS)]

    @field_validator("name")
    @classmethod
    def name_is_letters(cls, value: str) -> str:
        value = _not_blank(value, "Please enter your name.")
        # Letters in any language, plus space . ' -   (also keeps prompt injection out of the name)
        if not all(unicodedata.category(ch)[0] in "LM" or ch in " .'-" for ch in value):
            raise ValueError("Please use only letters in your name.")
        return value


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_HISTORY_CHARS)


class ChatRequest(BaseModel):
    profile: Profile
    mode: Literal["learn", "doubt"] = "learn"
    message: str = Field(max_length=MAX_MESSAGE_CHARS)
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        return _not_blank(value, "Please type a message first.")


class PracticeRequest(BaseModel):
    profile: Profile
    count: int = Field(default=3, ge=1, le=MAX_QUESTIONS)


class EvaluateRequest(BaseModel):
    profile: Profile
    question: str = Field(min_length=1, max_length=600)
    correct_answer: str = Field(min_length=1, max_length=MAX_ANSWER_CHARS)
    learner_answer: str = Field(max_length=MAX_ANSWER_CHARS)
    skill: str = Field(default="", max_length=100)
    attempt: Literal[1, 2] = 1  # 2 = final try (show the full answer)

    @field_validator("learner_answer")
    @classmethod
    def answer_not_blank(cls, value: str) -> str:
        return _not_blank(value, "Please type your answer first.")


class QuizScore(BaseModel):
    score: int = Field(ge=0, le=MAX_QUESTIONS)
    total: int = Field(ge=1, le=MAX_QUESTIONS)


class SummaryRequest(BaseModel):
    profile: Profile
    attempted: int = Field(ge=0, le=1000)
    correct: int = Field(ge=0, le=1000)
    quiz_scores: list[QuizScore] = Field(default_factory=list, max_length=50)
    strong_areas: list[str] = Field(default_factory=list, max_length=10)
    weak_areas: list[str] = Field(default_factory=list, max_length=10)
    chat_messages: int = Field(default=0, ge=0, le=1000)

    @field_validator("strong_areas", "weak_areas")
    @classmethod
    def short_names(cls, names: list[str]) -> list[str]:
        return [name.strip()[:100] for name in names if name.strip()]

    @field_validator("correct")
    @classmethod
    def correct_not_more_than_attempted(cls, value: int, info) -> int:
        if value > info.data.get("attempted", value):
            raise ValueError("Correct answers can't be more than questions answered.")
        return value


# ---- Shapes we expect from the AI (JSON mode) ----
class GeneratedQuestion(BaseModel):
    question: str = Field(min_length=1)
    skill: str = ""
    kind: Literal["equation", "expression"]
    math: str
    answer: str
    solution: str = ""


class EvaluateResult(BaseModel):
    correct: bool
    explanation: str = ""
    correct_answer: str = ""
    hint: str = ""
    encouragement: str = ""
    weak_topic: str = ""


class NextLesson(BaseModel):
    title: str = Field(min_length=1)
    level: Literal[tuple(LEVELS)]
    reason: str = ""


class SummaryResult(BaseModel):
    summary: str = Field(min_length=1)
    next_lesson: NextLesson
    tips: list[str] = Field(default_factory=list)
    encouragement: str = ""


# ---- Rate limiting (simple, in memory, per IP) ----
_requests_by_ip: dict[str, deque] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    # Behind Firebase Hosting / Cloud Run the real client IP is the first X-Forwarded-For entry.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/") and path != "/api/health":
        now = time.monotonic()
        hits = _requests_by_ip[_client_ip(request)]
        while hits and now - hits[0] > RATE_LIMIT_WINDOW_SECONDS:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"error": "You are sending messages too fast. Please wait a minute and try again."},
            )
        hits.append(now)
    return await call_next(request)


# ---- Clean error responses (never raw stack traces) ----
@app.exception_handler(RequestValidationError)
async def handle_validation_error(request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(part) for part in first.get("loc", []) if part != "body")
    error_type = first.get("type", "")

    if error_type == "json_invalid":
        message = "The request was not valid JSON."
    elif field == "message" and error_type == "string_too_long":
        message = f"Your message is too long. Please keep it under {MAX_MESSAGE_CHARS} characters."
    elif field == "learner_answer" and error_type == "string_too_long":
        message = f"Your answer is too long. Please keep it under {MAX_ANSWER_CHARS} characters."
    elif field == "profile.name" and error_type == "string_too_long":
        message = "Your name is too long. Please use at most 40 characters."
    elif error_type == "value_error":  # our own friendly messages from the validators
        message = str(first.get("msg", "")).removeprefix("Value error, ")
    elif field == "history" and error_type == "too_long":
        message = "The chat history is too long. Please refresh the page to start again."
    else:
        message = f"Invalid request ({field or 'body'}): {first.get('msg', 'bad input')}"
    return JSONResponse(status_code=400, content={"error": message})


@app.exception_handler(TutorAIError)
async def handle_ai_error(request: Request, exc: TutorAIError):
    return JSONResponse(status_code=503, content={"error": str(exc)})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    log.exception("Unexpected error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"error": "Something went wrong on our side. Please try again."})


# ---- Endpoints ----
@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(req: ChatRequest):
    p = req.profile
    messages = [{"role": "system", "content": build_chat_prompt(p.name, p.level, p.topic, req.mode)}]
    messages += [turn.model_dump() for turn in req.history]
    messages.append({"role": "user", "content": req.message})
    return {"reply": chat_completion(messages)}


@app.post("/api/practice")
def practice(req: PracticeRequest):
    p = req.profile
    messages = [
        {"role": "system", "content": build_practice_prompt(p.level, p.topic, req.count + EXTRA_QUESTIONS)},
        {"role": "user", "content": "Write the questions now."},
    ]

    def keep_verified(data: dict) -> list[dict]:
        items = data.get("questions")
        if not isinstance(items, list):
            raise ValueError('JSON has no "questions" list')
        verified = []
        for item in items:
            try:
                q = GeneratedQuestion.model_validate(item)
                answer = verify_question(q.kind, q.math, q.answer)
                if p.topic == "word_problems":
                    answer = answer.split("=")[-1].strip()  # learner never saw the letter, so show "5" not "s = 5"
            except (ValidationError, ValueError) as exc:
                log.warning("Dropped a generated question: %s | %s", exc, item)
                continue
            verified.append({"question": q.question, "skill": q.skill, "answer": answer, "solution": q.solution})
            if len(verified) == req.count:
                return verified
        raise ValueError(f"only {len(verified)} of {req.count} questions passed the maths check")

    return {"questions": json_completion(messages, keep_verified, temperature=0.8, max_tokens=5000, reasoning="medium")}


@app.post("/api/evaluate")
def evaluate(req: EvaluateRequest):
    p = req.profile
    # Numeric answers are marked by the computer, not the AI.
    checked = compare_numeric(req.correct_answer, req.learner_answer)
    computer_check = "not available" if checked is None else ("CORRECT" if checked else "INCORRECT")

    messages = [
        {"role": "system", "content": build_evaluate_prompt(p.name, p.level)},
        {"role": "user", "content": EVALUATE_USER_TEMPLATE.format(
            question=req.question,
            skill=req.skill or "not given",
            correct_answer=req.correct_answer,
            learner_answer=req.learner_answer,
            attempt=req.attempt,
            computer_check=computer_check,
        )},
    ]
    result = json_completion(messages, EvaluateResult.model_validate, temperature=0.2, max_tokens=2000)

    if checked is not None:
        result.correct = checked
    result.correct_answer = req.correct_answer
    if result.correct:
        result.weak_topic = ""
    elif not result.weak_topic:
        result.weak_topic = req.skill
    return result
