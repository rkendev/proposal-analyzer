"""
FastAPI application — implemented in Phase 7.
Endpoints: POST /analyze, POST /generate, GET /stream/{job_id}, GET /health
See docs/specs/deployment-spec.md for CORS and rate limiting requirements.
"""
import asyncio
import json
from typing import Any, Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings
from exceptions import OrchestratorError
from orchestrator.graph import run_orchestrator
from schemas.state import ValidatorState


class AnalyzeRequest(BaseModel):
    job_posting: str = Field(min_length=50)
    proposal_draft: str = Field(min_length=50)
    mode: Literal["analyze"]


class GenerateRequest(BaseModel):
    job_posting: str = Field(min_length=50)
    mode: Literal["generate"]


class JobCreateResponse(BaseModel):
    job_id: str


class JobContext(BaseModel):
    state: ValidatorState
    queue: asyncio.Queue
    status: Literal["running", "complete", "error"] = "running"
    final_report_json: str | None = None
    task: asyncio.Task | None = None

    model_config = {"arbitrary_types_allowed": True}


app = FastAPI(title="Freelance Proposal Analyzer API")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.allowed_origin],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "Accept"],
)

jobs: dict[str, JobContext] = {}


@app.exception_handler(RequestValidationError)
async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


async def _run_job(job_id: str) -> None:
    job = jobs[job_id]
    try:
        report = await run_orchestrator(job.state, event_queue=job.queue)
        job.final_report_json = report.model_dump_json()
        job.status = "complete"
    except OrchestratorError as exc:
        job.status = "error"
        await job.queue.put({"event": "error", "message": str(exc)})
    except Exception as exc:
        job.status = "error"
        await job.queue.put({"event": "error", "message": str(exc)})


def _create_job_context(state: ValidatorState) -> str:
    job_id = str(uuid4())
    event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
    state_with_id = state.model_copy(update={"job_id": job_id})
    context = JobContext(state=state_with_id, queue=event_queue)
    jobs[job_id] = context
    context.task = asyncio.create_task(_run_job(job_id))
    return job_id


@app.post("/analyze", response_model=JobCreateResponse)
@limiter.limit("10/minute")
async def analyze(request: Request, payload: AnalyzeRequest) -> JobCreateResponse:
    state = ValidatorState(
        mode="analyze",
        job_posting=payload.job_posting,
        proposal_draft_text=payload.proposal_draft,
    )
    job_id = _create_job_context(state)
    return JobCreateResponse(job_id=job_id)


@app.post("/generate", response_model=JobCreateResponse)
@limiter.limit("10/minute")
async def generate(request: Request, payload: GenerateRequest) -> JobCreateResponse:
    state = ValidatorState(
        mode="generate",
        job_posting=payload.job_posting,
        proposal_draft_text=None,
    )
    job_id = _create_job_context(state)
    return JobCreateResponse(job_id=job_id)


@app.get("/stream/{job_id}")
async def stream(job_id: str) -> StreamingResponse:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator() -> Any:
        queue = jobs[job_id].queue
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
            except TimeoutError:
                yield ": keep-alive\n\n"
                continue

            yield f"data: {json.dumps(event)}\n\n"
            if event.get("event") in {"complete", "error"}:
                break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.api_version}
