# Challenges & Bugs

## C1 - Confusing error for invalid JSON (Phase 1)
- **What didn't work:** Sending a request body that is not JSON returned
  `Invalid request (0): JSON decode error`, which is unclear.
- **Error:** FastAPI's validation error has type `json_invalid` and location `("body", 0)`,
  so our generic message showed the meaningless field name "0".
- **How we debugged it:** Ran a curl test that sends plain text `hello` to `/api/chat` and read the response.
- **What we changed:** Added a special case in `handle_validation_error` (backend/main.py) for
  `json_invalid` -> `The request was not valid JSON.` Re-tested: pass.
