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

## Key design choices
- **Stateless backend:** the backend remembers nothing between requests. The browser
  sends the recent chat history (last 20 messages) with each request.
- **No database:** learner progress lives in the browser for the session only.
- **Progress numbers are exact:** the browser counts questions, correct answers and strong/weak
  skills (75%+ = strong, under 50% = weak). `/api/summary` only writes the words and picks the next lesson.
- **Secret key only on the server:** the frontend never sees the Groq key.
- **Local development:** FastAPI also serves the `frontend/` folder at `http://localhost:8000`,
  so the page and `/api` share one address, just like Firebase + Cloud Run in production.
