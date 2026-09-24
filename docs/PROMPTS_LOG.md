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
