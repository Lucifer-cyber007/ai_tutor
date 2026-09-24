# AI Tutor - Personalized Learning Assistant

A simple AI tutor for **Class 8 Algebra** (variables, expressions, linear equations, word problems).

**Live app:** https://supple-defender-503708-t7.web.app. See `docs/DEPLOY.md` for how it is deployed.

- Backend: Python + FastAPI (`backend/`), uses the Groq API
- Frontend: plain HTML/CSS/JS (`frontend/`)
- Docs for submission: `docs/`

## Run locally (Windows PowerShell)

```powershell
# 1. One-time setup
python -m venv .venv
.\.venv\Scripts\pip install -r backend\requirements.txt
copy .env.example .env      # then open .env and paste your Groq key

# 2. Start the server
.\.venv\Scripts\python -m uvicorn main:app --reload --app-dir backend --port 8000
```

Open http://localhost:8000 in your browser.
