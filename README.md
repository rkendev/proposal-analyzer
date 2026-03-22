# Freelance Proposal Analyzer

> AI-powered multi-agent system that critiques or generates freelance proposals — built for freelancers who want to win more bids.

🔗 **[Live Demo](#)** (coming soon) | 📖 **[Medium Article](#)** (coming soon)

---

## What It Does

Submit a job posting and your draft proposal. Four specialized AI agents analyze it and return a structured report:

- **Job Intelligence Agent** — Decodes client signals, scope clarity, budget hints, and red flags
- **Rate Intelligence Agent** — Recommends a defensible rate range with market justification
- **Proposal Analyst Agent** — Scores your proposal, identifies critical weaknesses, rewrites your opening
- **Win Strategy Agent** — Assesses win probability, profiles competing bidders, identifies deal-breakers

Or skip the proposal and let the system generate one from scratch.

---

## Architecture

```
Lovable UI (React/TypeScript)
        │
        ▼
FastAPI + SSE Streaming
        │
        ▼
LangGraph Orchestrator
        ├──▶ Job Intelligence Agent   → JobAnalysis (Pydantic v2)
        ├──▶ Rate Intelligence Agent  → RateAnalysis (Pydantic v2)
        ├──▶ Proposal Analyst Agent   → ProposalCritique | ProposalDraft
        └──▶ Win Strategy Agent       → WinStrategy (Pydantic v2)
```

---

## Tech Stack

| Layer         | Technology                              |
|---------------|-----------------------------------------|
| Frontend      | React, TypeScript, Tailwind (Lovable)   |
| Backend       | Python 3.11, FastAPI                    |
| Orchestration | LangGraph                               |
| LLM           | LiteLLM (model-agnostic)               |
| Schemas       | Pydantic v2                             |
| Streaming     | FastAPI Server-Sent Events (SSE)        |
| Deployment    | Railway (API), Lovable (UI)             |
| Testing       | pytest — unit, integration, acceptance  |
| CI            | GitHub Actions                          |

---

## Local Setup

```bash
git clone https://github.com/rkendev/proposal-analyzer
cd proposal-analyzer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
uvicorn src.api.main:app --reload --port 8001
```

API docs available at http://localhost:8001/docs

---

## Build Log

Built in 8 phases using Cursor (Agent mode via Remote SSH) and Lovable:

- Phase 0 — Spec, deployment config, scaffold
- Phase 1 — Pydantic v2 schemas + exception hierarchy
- Phase 2 — Job Intelligence Agent
- Phase 3 — Rate Intelligence Agent
- Phase 4 — Proposal Analyst Agent (analyze + generate modes)
- Phase 5 — Win Strategy Agent
- Phase 6 — LangGraph orchestrator + SSE streaming
- Phase 7 — FastAPI layer, Railway deployment
- Phase 8 — Lovable frontend
