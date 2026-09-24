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
