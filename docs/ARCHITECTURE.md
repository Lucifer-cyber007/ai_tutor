# Architecture

Live: https://supple-defender-503708-t7.web.app (Firebase Hosting) -> Cloud Run `ai-tutor-api` (asia-south1)

## Flow

```
 Student (browser)
      |
      v
 Firebase Hosting  -- serves index.html, style.css, app.js
      |   "/api/**" is rewritten to Cloud Run (same domain, so no CORS)
      v
 Cloud Run: FastAPI backend (Docker)
      |   - checks the input (length, allowed values)
      |   - rate limit per IP
      |   - adds the tutor system prompt (backend/prompts.py)
      |   - GROQ_API_KEY comes from Google Secret Manager
      v
 Groq model (GROQ_MODEL, default openai/gpt-oss-120b)
      |
      v
 Maths check (sympy, backend/math_check.py)
      |   - re-solves every generated question; wrong ones are dropped
      |   - marks numeric learner answers by computer
      v
 Response  -> chat reply / quiz questions / answer feedback (JSON)
      |
      v
 Browser keeps progress for the session -> summary + next lesson recommendation
```
