# Deployment Spec — Freelance Proposal Analyzer

## Platform

- API: Railway
- Frontend: Lovable
- CI: GitHub Actions

## Environment Variables

All production secrets live in Railway dashboard ONLY.
Never in .env committed to repo.
Never in Dockerfile (no ENV instructions with secrets).
.env is for local development only and is in .gitignore.

Required Railway variables:
  CHEAP_MODEL_NAME    e.g. anthropic/claude-haiku-4-5-20251001
  STRONG_MODEL_NAME   e.g. anthropic/claude-sonnet-4-5-20250929
  ANTHROPIC_API_KEY   from console.anthropic.com
  ALLOWED_ORIGIN      https://your-app.lovable.app

## CORS Policy

Never use allow_origins=["*"] — this is a portfolio red flag.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Accept"],
)
```

ALLOWED_ORIGIN is injected from Railway environment.

## Docker Rules (learned from Project 1 Phase 7)

RULE 1: Use COPY src/ only. Never COPY . .
  - COPY . . copies .env into the image
  - This overrides Railway environment variables
  - The container runs with local credentials, not Railway credentials

RULE 2: Use sh -c form in CMD for variable expansion.
  - Exec form: CMD ["uvicorn", ..., "--port", "${PORT}"] — BROKEN
  - Shell form: CMD sh -c "uvicorn ... --port ${PORT:-8001}" — CORRECT
  - Railway injects PORT as an environment variable

RULE 3: .dockerignore must exist before first Railway deploy.
  - Minimum contents: .env, .env.*, .venv, tests/, docs/

## Pre-Deploy Checklist (run before every Railway push)

[ ] git ls-files | grep "\.env$" → must return 0 results
[ ] .dockerignore exists: cat .dockerignore | grep "^\.env$"
[ ] ALLOWED_ORIGIN set in Railway dashboard
[ ] ANTHROPIC_API_KEY set in Railway dashboard
[ ] After deploy: GET /health returns {"status": "ok"}
[ ] After deploy: POST /analyze returns {job_id: str} < 500ms
[ ] After deploy: GET /stream/{job_id} emits SSE events

## Streaming Architecture

SSE is non-negotiable for this project. The analysis takes
60-120 seconds. A black-box wait kills the demo.
(Lesson from Project 1 — streaming was not built, it was listed
as "what I would do differently". It is required here.)

Flow:
  POST /analyze or /generate  → returns {job_id} immediately
  GET /stream/{job_id}        → SSE stream opens
  4 agent_complete events     → progress 25, 50, 75, 100
  1 complete event            → full ProposalReport JSON
  1 error event (on failure)  → error message string

## Cold Start Mitigation

Railway hobby plan has cold starts (10-30 seconds).
GET /health must be called on page load to pre-warm the
instance before user submits.

## Rate Limiting

10 requests/minute/IP on POST /analyze and POST /generate.
Use slowapi (already in requirements.txt).

## Endpoints

POST /analyze      → {job_id: str}
POST /generate     → {job_id: str}
GET  /stream/{id}  → SSE stream → ProposalReport on complete
GET  /health       → {"status": "ok", "version": "1.0.0"}
GET  /docs         → FastAPI Swagger UI (do not disable)
