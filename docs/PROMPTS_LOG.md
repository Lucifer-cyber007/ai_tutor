# Prompts Log

Model: `openai/gpt-oss-120b` on Groq (set by `GROQ_MODEL`). The exact final prompts are at the
end of this file, copied from `backend/prompts.py`.

## 1. Building the app

### P1 - Master prompt (project setup + Phase 1)
> Build a small, reliable AI Tutor web app for Class 8 Algebra (linear equations, variables,
> algebraic expressions, word problems) for students aged 13-15. Stack: Groq API, Python +
> FastAPI on Cloud Run, plain HTML/CSS/JS on Firebase Hosting with a /api rewrite. Key never in
> frontend or git; validate input; rate limit per IP. Stateless backend. Work one phase at a
> time. Do Phase 1 only: a basic chatbot with title, chat window, text box, send button,
> loading indicator and error message.

**Result:** FastAPI backend (`/api/health`, `/api/chat`), plain-JS chat page, input
validation, per-IP rate limit (20 requests/minute), clean error messages.

### P2 - "next" (Phase 2: personalization + modes)
> Start screen: name, level (Beginner/Intermediate/Advanced), topic. Modes: Learn, Practice,
> Quiz (optional: Ask a Doubt). Practice: generate questions, learner answers, AI evaluates.
> Quiz: 5 questions, score at the end. Use Groq JSON mode for /practice and /evaluate; if the
> JSON is invalid, retry once, then a friendly error. The correct answer of generated questions
> must be verified before it is used.

**Result:** start screen + 4 tabs; `/api/practice` and `/api/evaluate` with JSON mode and one
retry; `backend/math_check.py` re-solves every generated question with sympy and drops wrong
ones; numeric learner answers are marked by the computer, not the AI.

### P3 - "Here is the Groq API key [removed from this log], use it and then move to the next phase"
**Result:** key saved only in `.env` (git-ignored). Real-AI testing found that the default model
was not available to this key (CHALLENGES C4) and several prompt problems (C5-C7), which were
fixed before Phase 3.

### P4 - Phase 3: progress tracking + session report
> Track in session: questions attempted, correct count, strong areas, weak areas.
> "Finish Session" button -> shows the performance summary and the recommended next lesson.

**Result:** progress line under the tabs, "Finish session" button, `/api/summary` (JSON mode,
retry once). The numbers on the report are calculated by the browser, not the AI.
