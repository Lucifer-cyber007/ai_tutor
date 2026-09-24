# Test Report

Tested locally. Real-AI tests use `openai/gpt-oss-120b`. "Pending" = still needs a manual browser test.
Tests marked "(fake AI)" replace Groq with fixed replies, so we can test our own code
(retries, maths check, marking) without using the API.

## Phase 1 - Basic chatbot

| No. | User Action | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| 1 | Open `GET /api/health` | `{"status":"ok"}` | `{"status":"ok"}` | Pass |
| 2 | Open `http://localhost:8000/` | Page loads | 200, page "AI Tutor - Class 8 Algebra" | Pass |
| 3 | Empty input (only spaces) | Friendly "type a message" error, no AI call | 400 `Please type a message first.` (frontend also blocks it) | Pass |
| 4 | Very long input (1001 characters) | Rejected with clear message | 400 `Your message is too long. Please keep it under 1000 characters.` | Pass |
| 5 | Groq API failure (wrong API key) | Friendly error, no stack trace; real cause in server log | 503 `The tutor is not set up correctly. Please try again later.` Log: `401 Unauthorized ... check GROQ_API_KEY` | Pass |
| 6 | Tampered history with role `system` | Rejected | 400 `Input should be 'user' or 'assistant'` | Pass |
| 7 | Request body is not JSON | Clean error | 400 `The request was not valid JSON.` | Pass |
| 8 | 22 requests in a few seconds from one IP | First 20 allowed, then blocked | Requests 21-22 got 429 `You are sending messages too fast...` | Pass |
| 9 | Open `/docs` (auto API docs) | Hidden in production | 404 | Pass |
