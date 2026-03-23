"""
Win_strategy agent — implemented in Phase 5.
See docs/specs/project-spec.md for responsibilities and output schema.
"""
from pydantic import ValidationError

import litellm

from config import settings
from exceptions import AgentCallError, SchemaValidationError
from schemas.state import ValidatorState
from schemas.win_strategy import WinStrategy

_AGENT_NAME = "win_strategy"

_WIN_STRATEGY_JSON_KEYS = (
    "win_probability",
    "win_probability_score",
    "competing_profiles",
    "differentiation_angle",
    "top_improvements",
    "deal_breakers",
    "one_line_positioning",
)


def _system_prompt() -> str:
    forbidden = (
        "FORBIDDEN VOCABULARY — never use these exact terms in prose inside string "
        "values (write natural descriptions without naming schema fields):\n"
        "win_probability, win_probability_score, competing_profiles, "
        "differentiation_angle, top_improvements, deal_breakers, "
        "one_line_positioning, priority, action, expected_impact"
    )
    keys_list = ", ".join(_WIN_STRATEGY_JSON_KEYS)
    json_rules = (
        "You must respond with a single valid JSON object only. "
        "No markdown, no code fences, no prose before or after. "
        f"The JSON object must contain exactly these keys: {keys_list}. "
        "Use snake_case keys exactly as listed. "
        "win_probability must be one of: low, medium, high. "
        "win_probability_score must be an integer 0-10 inclusive. "
        "competing_profiles must be an array of 1-3 concise strings. "
        "differentiation_angle must be a non-empty single strongest angle. "
        "top_improvements must contain exactly 3 objects with keys: "
        "priority, action, expected_impact. "
        "Priorities must be exactly 1, 2, and 3. "
        "In analyze mode: top_improvements are prioritized improvements. "
        "In generate mode: top_improvements are top strengths framed as "
        "improvements with clear impact. "
        "deal_breakers must be an array of strings (empty array if none). "
        "one_line_positioning must be a single non-empty line."
    )
    return f"{forbidden}\n\n{json_rules}"


def _extract_message_content(response: object) -> str | None:
    choices = getattr(response, "choices", None)
    if not choices:
        return None
    first = choices[0]
    message = getattr(first, "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if content is None:
        return None
    if isinstance(content, str):
        return content
    return str(content)


def _sanitize_json_text(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```json"):
        text = text[len("```json") :].strip()
    elif text.startswith("```"):
        text = text[len("```") :].strip()
    if text.endswith("```"):
        text = text[: -len("```")].strip()
    return text


def win_strategy_agent(state: ValidatorState) -> dict:
    """
    Produce structured WinStrategy from upstream outputs via STRONG_MODEL.
    Returns {"win_strategy": WinStrategy}.
    """
    if state.job_analysis is None:
        raise AgentCallError(_AGENT_NAME, "job_analysis not available")
    if state.rate_analysis is None:
        raise AgentCallError(_AGENT_NAME, "rate_analysis not available")

    critique_json = (
        state.proposal_critique.model_dump_json()
        if state.proposal_critique is not None
        else "N/A"
    )
    draft_json = (
        state.proposal_draft.model_dump_json() if state.proposal_draft is not None else "N/A"
    )

    messages = [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": (
                "Generate a win strategy JSON object from this context.\n\n"
                f"Mode: {state.mode}\n"
                f"JobAnalysis JSON: {state.job_analysis.model_dump_json()}\n"
                f"RateAnalysis JSON: {state.rate_analysis.model_dump_json()}\n"
                f"ProposalCritique JSON (analyze mode context): {critique_json}\n"
                f"ProposalDraft JSON (generate mode context): {draft_json}\n\n"
                "Requirements: assess win probability and score, provide 1-3 likely "
                "competing profiles, identify the single strongest differentiation "
                "angle, include exactly 3 prioritized top_improvements, identify "
                "deal_breakers, and produce a one-line positioning statement."
            ),
        },
    ]

    try:
        response = litellm.completion(
            model=settings.strong_model_name,
            messages=messages,
            api_key=settings.anthropic_api_key,
        )
    except Exception as e:
        raise AgentCallError(_AGENT_NAME, str(e)) from e

    raw = _extract_message_content(response)
    if raw is None or not raw.strip():
        raise AgentCallError(_AGENT_NAME, "empty LLM response")
    cleaned = _sanitize_json_text(raw)
    if not cleaned:
        raise AgentCallError(_AGENT_NAME, "empty LLM response")

    try:
        win_strategy = WinStrategy.model_validate_json(cleaned)
    except ValidationError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e
    except ValueError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e

    return {"win_strategy": win_strategy}
