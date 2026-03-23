# Agent Design Decisions

Record architectural decisions for each agent here.
Fill this in during the relevant phase — before implementation.

## Agent 2 — Rate Intelligence Agent (Phase 3)

Decision required: Does this agent need a web_search tool call
to ground rate estimates in current market data?

Options:
  A) LLM training knowledge only — fast, no tool calls,
     but data goes stale and varies by training cutoff
  B) web_search tool call — grounds estimates in current
     Upwork/freelance market data, but adds latency and cost

Arguments for A: Rate ranges are relatively stable, training
  data includes substantial freelance market information,
  simpler architecture, no tool call failure modes.

Arguments for B: Rates change significantly by technology
  stack, location, and market conditions. A rate recommendation
  grounded in a live data source is more defensible and
  provides a stronger portfolio signal (AgenticRAG pattern).

Decision: Option A — use LLM training knowledge only (no web_search tool call) for Phase 3.
Rationale: Keeps latency and cost low for v1 while avoiding external tool-call failure modes; rate guidance is sufficient for this phase.
