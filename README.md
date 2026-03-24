# Freelance Proposal Analyzer

> AI-powered multi-agent system that tells you if your freelance proposal will win — before you send it.

🔗 **[Live Demo](https://proposal-ace-23.lovable.app)** | 📖 **[Medium Article](#)** (coming soon) | 💻 **[GitHub](https://github.com/rkendev/proposal-analyzer)**

---

## What It Does

Submit a job posting and your draft proposal. Four specialized AI agents analyze it in sequence and return a structured report with a win probability score, prioritized improvements, and a rewritten opening paragraph.

Or skip the proposal entirely — the system generates a complete, optimized proposal from the job posting alone.

**Analyze mode** — critiques an existing proposal:
- **Job Intelligence Agent** — Decodes client signals, scope clarity, budget hints, and red flags
- **Rate Intelligence Agent** — Recommends a defensible rate range with market justification
- **Proposal Analyst Agent** — Scores weaknesses, tone, hook, CTA, and personalization. Rewrites your opening.
- **Win Strategy Agent** — Assesses win probability, profiles competing bidders, identifies deal-breakers

**Generate mode** — writes a proposal from scratch:
- Same four agents run in sequence, each building on upstream context
- Output is a complete, markdown-formatted proposal grounded in job analysis and rate intelligence

---

## Architecture

```
Lovable UI (React/TypeScript)
        │
        │  POST /analyze or /generate  →  {job_id}  (immediate)
        │  GET  /stream/{job_id}        →  SSE stream
        ▼
FastAPI + Server-Sent Events
        │
        ▼
LangGraph Orchestrator (mode-aware)
        │
        ├──▶ [1] Job Intelligence Agent
        │         └──▶ JobAnalysis (Pydantic v2)
        │              Model: CHEAP_MODEL
        │
        ├──▶ [2] Rate Intelligence Agent  ◀── JobAnalysis
        │         └──▶ RateAnalysis (Pydantic v2)
        │              Model: CHEAP_MODEL
        │
        ├──▶ [3] Proposal Analyst Agent   ◀── JobAnalysis + RateAnalysis
        │         └──▶ ProposalCritique (analyze mode)
        │              ProposalDraft     (generate mode)
        │              Model: STRONG_MODEL
        │
        └──▶ [4] Win Strategy Agent       ◀── all upstream outputs
                  └──▶ WinStrategy (Pydantic v2)
                       ProposalReport (top-level output)
                       Model: STRONG_MODEL
```

---

## Tech Stack

| Layer          | Technology                                   |
|----------------|----------------------------------------------|
| Frontend       | React, TypeScript, Tailwind CSS (Lovable)    |
| Backend        | Python 3.11, FastAPI                         |
| Orchestration  | LangGraph                                    |
| LLM            | LiteLLM (model-agnostic)                     |
| Schema         | Pydantic v2                                  |
| Streaming      | FastAPI Server-Sent Events (SSE)             |
| Deployment     | Railway (API), Lovable (UI)                  |
| Testing        | pytest — 66 tests (unit + integration)       |
| CI             | GitHub Actions                               |

---

## Key Engineering Decisions

**Schema-enforced agent outputs** — Every agent returns a strictly typed Pydantic v2 model. No raw LLM text reaches the orchestrator. Scores are validated as integers 0–10, rates as floats with `max > min` enforcement, and list fields default to `[]`, never `None`. This eliminates an entire class of hallucination leakage between agents.

**Forbidden vocabulary in every agent prompt** — Each agent prompt contains an explicit block listing all Pydantic field names from its output schema. The LLM is instructed never to use these names in prose output. This prevents internal identifiers like `scope_clarity_score` or `rate_justification` from appearing verbatim in user-facing text — a failure mode discovered in a prior project and eliminated by design here.

**SSE streaming for long-running analysis** — Analysis takes 60–120 seconds. Rather than a black-box wait, the API emits four `agent_complete` progress events (25/50/75/100%) and a final `complete` event carrying the full `ProposalReport` as a JSON string. The Lovable frontend updates the loading UI in real time as each agent finishes.

**Cheap vs. strong model routing** — Extraction tasks (Job Intelligence, Rate Intelligence) use a cheaper, faster model. Reasoning tasks (Proposal Analyst, Win Strategy) use the strong model. Model routing is centralized in `src/config.py` via LiteLLM, making it swappable without touching agent code.

**Mode-aware orchestrator** — The same LangGraph graph handles both analyze and generate modes. Agent 3 (Proposal Analyst) branches on `state.mode` and returns either `ProposalCritique` or `ProposalDraft`. The final `ProposalReport` assembly sets the mode-specific fields accordingly.

**Upstream state validation** — Agents 3 and 4 validate that required upstream outputs (`job_analysis`, `rate_analysis`) are present in state before calling the LLM. Missing upstream outputs raise `AgentCallError` immediately rather than generating garbage output downstream.

---

## Running Locally

This repo contains the backend API only. The frontend is deployed at **[proposal-ace-23.lovable.app](https://proposal-ace-23.lovable.app)**. To explore the backend locally, use FastAPI's built-in Swagger UI at `http://localhost:8001/docs` — no frontend required.

```bash
git clone https://github.com/rkendev/proposal-analyzer
cd proposal-analyzer
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add your ANTHROPIC_API_KEY
uvicorn src.api.main:app --reload --port 8001
```

Open `http://localhost:8001/docs` to submit test proposals interactively.

```bash
python -m pytest tests/unit tests/integration -v  # 66 tests
```

---

## Project Structure

```
src/
├── agents/
│   ├── job_intelligence.py     # Client signals, scope, budget, red flags
│   ├── rate_intelligence.py    # Rate range, justification, market leverage
│   ├── proposal_analyst.py     # Critique (analyze) or draft (generate)
│   └── win_strategy.py         # Win probability, deal-breakers, improvements
├── orchestrator/
│   └── graph.py                # LangGraph graph + SSE event emission
├── schemas/
│   ├── common.py               # RedFlag, Weakness, Improvement
│   ├── job_analysis.py         # JobAnalysis (Pydantic v2)
│   ├── rate_analysis.py        # RateAnalysis (Pydantic v2)
│   ├── proposal_critique.py    # ProposalCritique (analyze mode)
│   ├── proposal_draft.py       # ProposalDraft (generate mode)
│   ├── win_strategy.py         # WinStrategy (Pydantic v2)
│   ├── proposal_report.py      # ProposalReport (top-level API response)
│   └── state.py                # ValidatorState (LangGraph state)
├── api/
│   └── main.py                 # FastAPI — /analyze, /generate, /stream, /health
├── config.py                   # Settings via pydantic-settings
└── exceptions.py               # AgentCallError, SchemaValidationError, OrchestratorError
tests/
├── unit/                       # Mocked LLM — schema, agent, and error tests
├── integration/                # API contract and orchestrator pipeline tests
└── acceptance/                 # Real LLM behavioral tests (run pre-deploy)
docs/specs/
├── project-spec.md             # Agent responsibilities and phase plan
├── deployment-spec.md          # Docker, CORS, SSE, Railway config
├── api-contract.md             # Field names, types, ranges, display rules
└── agent-decisions.md          # Architectural decisions per agent
```

---

## API Endpoints

| Method | Endpoint            | Description                              |
|--------|---------------------|------------------------------------------|
| POST   | `/analyze`          | Submit job + proposal → returns job_id   |
| POST   | `/generate`         | Submit job posting → returns job_id      |
| GET    | `/stream/{job_id}`  | SSE stream → ProposalReport on complete  |
| GET    | `/health`           | Health check — used by Railway + Lovable |
| GET    | `/docs`             | FastAPI Swagger UI                       |

Rate limiting: 10 requests/minute/IP on POST endpoints.

---

## Build Log

Built in 8 phases using Cursor (Agent mode via Remote SSH) and Lovable:

- Phase 0 — Spec, deployment config, Docker, Cursor rules, scaffold
- Phase 1 — Pydantic v2 schemas, exception hierarchy, 16 unit tests
- Phase 2 — Job Intelligence Agent, 23 unit tests
- Phase 3 — Rate Intelligence Agent, 32 unit tests
- Phase 4 — Proposal Analyst Agent (analyze + generate modes), 41 unit tests
- Phase 5 — Win Strategy Agent, 52 unit tests
- Phase 6 — LangGraph orchestrator, SSE streaming, 57 tests
- Phase 7 — FastAPI layer, Railway deployment, 66 tests
- Phase 8 — Lovable frontend, end-to-end integration
