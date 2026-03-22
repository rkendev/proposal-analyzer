# Freelance Proposal Analyzer — Project Spec

## What It Does

Two-mode multi-agent system for freelancers:

**Analyze Mode** — paste job posting + draft proposal.
Returns structured critique with win-readiness score and
prioritized fixes.

**Generate Mode** — paste job posting only.
Returns a complete optimized proposal with strategic reasoning.

## Stack

| Layer        | Technology                         |
|--------------|------------------------------------|
| Frontend     | React, TypeScript, Tailwind (Lovable) |
| Backend      | Python 3.11+, FastAPI              |
| Orchestration| LangGraph                          |
| LLM          | LiteLLM (model-agnostic)           |
| Schemas      | Pydantic v2                        |
| Streaming    | FastAPI SSE (Server-Sent Events)   |
| Deployment   | Railway (API), Lovable (UI)        |
| Testing      | pytest                             |
| CI           | GitHub Actions                     |

## Architecture

```
Lovable UI (React/TypeScript)
        │  POST /analyze or POST /generate → {job_id}
        │  GET  /stream/{job_id}           → SSE stream
        ▼
FastAPI Layer (rate limiting, CORS, error handling)
        │
        ▼
LangGraph Orchestrator (mode-aware routing)
        │
        ├──▶ [1] Job Intelligence Agent
        │         └──▶ JobAnalysis (Pydantic v2)
        │              Model: CHEAP_MODEL
        │
        ├──▶ [2] Rate Intelligence Agent  ← receives JobAnalysis
        │         └──▶ RateAnalysis (Pydantic v2)
        │              Model: CHEAP_MODEL
        │              Note: evaluate web_search tool in Phase 3
        │
        ├──▶ [3] Proposal Analyst Agent   ← receives JobAnalysis + RateAnalysis
        │         └──▶ ProposalCritique (analyze mode)
        │              ProposalDraft     (generate mode)
        │              Model: STRONG_MODEL
        │
        └──▶ [4] Win Strategy Agent       ← receives all upstream outputs
                  └──▶ WinStrategy (Pydantic v2)
                       ProposalReport (top-level output)
                       Model: STRONG_MODEL
```

## Agent Responsibilities

### Agent 1 — Job Intelligence Agent
Model: CHEAP_MODEL
Inputs: job_posting (str)
Output: JobAnalysis

- Client type signals (first-time vs experienced, budget-conscious vs quality)
- Scope clarity score and classification
- Required skills as clean list
- Budget signal and estimate (even when unstated)
- Red flags with severity
- Project complexity classification
- Ideal candidate summary

### Agent 2 — Rate Intelligence Agent
Model: CHEAP_MODEL
Inputs: JobAnalysis
Output: RateAnalysis

- Recommended rate range (min/max, currency, hourly or fixed)
- Assessment of current rate if analyze mode
- Rate justification argument for proposal use
- Negotiation leverage points
- Rate red flags

Design decision (Phase 3): Evaluate whether web_search tool
is needed to ground rate estimates in current market data.
Document decision in docs/specs/agent-decisions.md.

### Agent 3 — Proposal Analyst Agent
Model: STRONG_MODEL
Inputs: JobAnalysis + RateAnalysis
Output: ProposalCritique (analyze) or ProposalDraft (generate)

Analyze mode:
- Overall score (0-10)
- Critical weaknesses with severity and fix
- Missing elements
- Opening hook, CTA, personalization scores
- Rewritten opening paragraph

Generate mode:
- Complete proposal text (markdown)
- Key differentiators used
- Rate argument included flag

### Agent 4 — Win Strategy Agent
Model: STRONG_MODEL
Inputs: all upstream outputs
Output: WinStrategy

- Win probability (low/medium/high) with score
- Competing bidder profiles
- Differentiation angle
- Top 3 prioritized improvements (analyze) or strengths (generate)
- Deal-breakers
- One-line positioning statement

## Phase Plan

| Phase | Deliverable                                  | Gate           |
|-------|----------------------------------------------|----------------|
| 0     | Scaffold — all spec/config/rule files        | Manual review  |
| 1     | All Pydantic schemas + exceptions + conftest | pytest green   |
| 2     | Job Intelligence Agent + unit tests          | pytest green   |
| 3     | Rate Intelligence Agent + unit tests         | pytest green   |
| 4     | Proposal Analyst Agent (both modes) + tests  | pytest green   |
| 5     | Win Strategy Agent + unit tests              | pytest green   |
| 6     | LangGraph orchestrator + integration tests   | pytest green   |
| 7     | FastAPI + SSE + deployment config + Railway  | live /health   |
| 8     | Lovable frontend                             | acceptance list|

## Cursor Rules Files

.cursor/rules/agents.mdc     — agent design and prompt standards
.cursor/rules/schemas.mdc    — Pydantic v2 schema standards
.cursor/rules/testing.mdc    — test patterns and coverage
.cursor/rules/streaming.mdc  — SSE implementation standards
.cursor/rules/api.mdc        — FastAPI design standards
