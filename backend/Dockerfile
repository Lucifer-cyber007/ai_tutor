# AI Tutor backend for Google Cloud Run.
# Only the backend folder is sent to the build, so .env and key files are never included.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./

# Run as a normal user, not root.
RUN useradd --create-home appuser
USER appuser

# Cloud Run tells the app which port to use in $PORT.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]
