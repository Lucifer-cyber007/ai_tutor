# Deploying AI Tutor

- **Backend:** Cloud Run service `ai-tutor-api` in `asia-south1` (Mumbai), built from `backend/Dockerfile`.
- **Frontend:** Firebase Hosting serves `frontend/`, and `firebase.json` sends `/api/**` to the Cloud Run service (same domain, so no CORS).
- **Groq key:** stored in Secret Manager (`groq-api-key`) and given to Cloud Run as the `GROQ_API_KEY` env var. It is never in the image or in git.

Project: `supple-defender-503708-t7` (deployed by the owner account vedhasingh1815@gmail.com)

## Live now
| What | URL |
|---|---|
| **App (share this)** | https://supple-defender-503708-t7.web.app |
| Backend (Cloud Run, direct) | https://ai-tutor-api-539430519324.asia-south1.run.app/api/health |

## Step 0 - one-time: log in as the project owner, billing, Firebase
```bash
gcloud auth login vedhasingh1815@gmail.com      # opens the browser
```
Google only lets a person (not a service account) link billing and add Firebase.

1. **Link billing** (Cloud Run needs it; this app normally stays inside the free tier):
   https://console.cloud.google.com/billing/linkedaccount?project=supple-defender-503708-t7
2. **Add Firebase to the project:** https://console.firebase.google.com -> "Create a project" ->
   "Add Firebase to Google Cloud project" -> choose `supple-defender-503708-t7` -> accept the terms
   (Google Analytics is not needed).
