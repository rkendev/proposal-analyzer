# CLAUDE.md — Freelance Proposal Analyzer

Cross-tool documentation. Read by Claude Code, Cursor, and any
AI coding assistant before touching this project.

---

## Project Summary

Multi-agent AI system for freelancers.
Two modes: Analyze (critique an existing proposal) and Generate
(write a proposal from a job posting).

Stack: Python 3.11, FastAPI, LangGraph, LiteLLM, Pydantic v2
Deploy: Railway (API) + Lovable (UI)
Repo: github.com/rkendev/proposal-analyzer

---

## TIER 1 — Never Violate (ask before breaking these)

1. Every agent output is a Pydantic v2 model. No raw strings
   reach the orchestrator. No exceptions.

2. Every agent prompt MUST include a FORBIDDEN VOCABULARY block
   that lists all Pydantic field names from its output schema.
   The LLM must never use these names in prose output.
   This prevents schema field leakage into user-facing text.
   (Critical lesson from Project 1.)

3. All numeric scores are int, range 0–10 inclusive.
   Document the range in both the schema AND the api-contract.md.
   Unit ambiguity (0-10 vs 0-100) is a production bug.
   (Critical lesson from Project 1.)

4. All list fields default to empty list []. Never None.

5. .gitignore and .dockerignore are committed before any other
   file. The .env file is never committed under any circumstance.

6. Dockerfile uses COPY src/ only. Never COPY . .
   This prevents .env from being copied into the Docker image.
   (Critical lesson from Project 1 Phase 7.)

7. Dockerfile CMD uses sh -c form for PORT variable expansion.
   Exec form does not expand shell variables — Railway breaks.
   (Critical lesson from Project 1 Phase 7.)

8. New chat thread in Cursor for every phase. No exceptions.
   Long threads cause context drift and expensive cache re-reads.

9. pytest must pass before every git commit. No exceptions.

---

## TIER 2 — Strong Preference

- CHEAP_MODEL for extraction tasks (Job Intelligence, Rate
  Intelligence). STRONG_MODEL for reasoning tasks (Proposal
  Analyst, Win Strategy). Verify routing in Phase 2.

- One Lovable prompt per change. Never batch UI fixes.
  Lovable batches multiple changes poorly.

- Plan Mode (Shift+Tab) before every new phase in Cursor.
  Reference @docs/specs/project-spec.md in every plan prompt.

- Add .cursorignore to exclude .venv, logs, and data files
  from Cursor indexing to reduce cost.

- Rate Intelligence Agent: evaluate in Phase 3 whether a
  web_search tool call is needed to ground rate estimates
  in current market data. Document the decision in
  docs/specs/agent-decisions.md.

---

## Phase Map

| Phase | Deliverable                              | Gate           |
|-------|------------------------------------------|----------------|
| 0     | All spec docs, Docker, git, rules        | Manual review  |
| 1     | Pydantic schemas + exceptions + tests    | pytest green   |
| 2     | Job Intelligence Agent + tests           | pytest green   |
| 3     | Rate Intelligence Agent + tests          | pytest green   |
| 4     | Proposal Analyst Agent (both modes)      | pytest green   |
| 5     | Win Strategy Agent + tests               | pytest green   |
| 6     | LangGraph orchestrator + integration     | pytest green   |
| 7     | FastAPI + SSE streaming + Railway        | live /health   |
| 8     | Lovable frontend                         | acceptance list|

---

## Directory Structure

```
proposal-analyzer/
├── src/
│   ├── agents/         # One file per agent
│   ├── api/            # FastAPI app + routes
│   ├── orchestrator/   # LangGraph graph
│   ├── schemas/        # Pydantic v2 models
│   ├── config.py       # Settings via pydantic-settings
│   └── exceptions.py   # Custom exception hierarchy
├── tests/
│   ├── unit/           # Mocked LLM calls
│   ├── integration/    # API contract tests
│   └── acceptance/     # Real LLM calls, behavioral tests
├── docs/specs/
│   ├── project-spec.md
│   ├── deployment-spec.md
│   └── api-contract.md
├── .cursor/rules/      # Cursor-specific rules
├── .github/workflows/  # CI pipeline
├── CLAUDE.md           # This file
├── LOVABLE.md          # Frontend tool protocol
├── Dockerfile
├── .dockerignore
├── .gitignore
├── .env.example
└── requirements.txt
```
