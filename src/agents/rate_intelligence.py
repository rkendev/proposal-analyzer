"""
Rate_intelligence agent — implemented in Phase 3.
See docs/specs/project-spec.md for responsibilities and output schema.
"""
from pydantic import ValidationError

import litellm

from config import settings
from exceptions import AgentCallError, SchemaValidationError
from schemas.rate_analysis import RateAnalysis
from schemas.state import ValidatorState

_AGENT_NAME = "rate_intelligence"

_RATE_ANALYSIS_JSON_KEYS = (
    "recommended_rate_min",
    "recommended_rate_max",
    "rate_currency",
    "rate_type",
    "rate_justification",
    "current_rate_assessment",
    "assessment_explanation",
    "negotiation_leverage",
    "rate_red_flags",
)


def _system_prompt() -> str:
    forbidden = (
        "FORBIDDEN VOCABULARY — never use these exact terms in prose inside string "
        "values (write natural descriptions without naming schema fields):\n"
        "recommended_rate_min, recommended_rate_max, rate_currency, rate_type, "
        "rate_justification, current_rate_assessment, assessment_explanation, "
        "negotiation_leverage, rate_red_flags"
    )
    keys_list = ", ".join(_RATE_ANALYSIS_JSON_KEYS)
    json_rules = (
        "You must respond with a single valid JSON object only. "
        "No markdown, no code fences, no prose before or after. "
        f"The JSON object must contain exactly these keys: {keys_list}. "
        "Use snake_case keys exactly as listed. "
        "recommended_rate_min and recommended_rate_max must be positive numbers, and "
        "recommended_rate_max must be greater than recommended_rate_min. "
        "rate_currency must be USD. "
        "rate_type must be one of: hourly, fixed. "
        "current_rate_assessment must be one of: underpriced, fair, overpriced, not_applicable. "
        "If mode is generate, current_rate_assessment must be not_applicable. "
        "assessment_explanation and negotiation_leverage must be non-empty strings. "
        "rate_red_flags must be an array of strings (empty array if none)."
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


def rate_intelligence_agent(state: ValidatorState) -> dict:
    """
    Produce structured RateAnalysis from prior JobAnalysis context via CHEAP_MODEL.
    Returns {"rate_analysis": RateAnalysis}.
    """
    if state.job_analysis is None:
        raise SchemaValidationError(_AGENT_NAME, "state.job_analysis is required")

    proposal_text = state.proposal_draft_text if state.proposal_draft_text else "N/A"
    messages = [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": (
                "Generate a rate analysis JSON object from this context.\n\n"
                f"Mode: {state.mode}\n"
                f"JobAnalysis JSON: {state.job_analysis.model_dump_json()}\n"
                f"Proposal draft text: {proposal_text}\n\n"
                "Important mode rule: if mode is generate, set current_rate_assessment "
                "to not_applicable."
            ),
        },
    ]

    try:
        response = litellm.completion(
            model=settings.cheap_model_name,
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
        rate_analysis = RateAnalysis.model_validate_json(cleaned)
    except ValidationError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e
    except ValueError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e

    return {"rate_analysis": rate_analysis}
