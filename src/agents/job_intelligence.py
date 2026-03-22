"""
Job Intelligence agent — Phase 2.
See docs/specs/project-spec.md for responsibilities and output schema.
"""

from pydantic import ValidationError

import litellm

from config import settings
from exceptions import AgentCallError, SchemaValidationError
from schemas.job_analysis import JobAnalysis
from schemas.state import ValidatorState

_AGENT_NAME = "job_intelligence"

# Top-level JSON keys (JobAnalysis). Nested red_flags items use: flag, severity
_JOB_ANALYSIS_JSON_KEYS = (
    "client_type_signals",
    "scope_clarity",
    "scope_clarity_score",
    "required_skills",
    "budget_signal",
    "estimated_budget",
    "red_flags",
    "project_complexity",
    "ideal_candidate_summary",
)


def _system_prompt() -> str:
    forbidden = (
        "FORBIDDEN VOCABULARY — never use these exact terms in prose inside string "
        "values (write natural descriptions without naming schema fields):\n"
        "client_type_signals, scope_clarity, scope_clarity_score, required_skills, "
        "budget_signal, estimated_budget, red_flags, project_complexity, "
        "ideal_candidate_summary, flag, severity"
    )
    keys_list = ", ".join(_JOB_ANALYSIS_JSON_KEYS)
    json_rules = (
        "You must respond with a single valid JSON object only. "
        "No markdown, no code fences, no prose before or after. "
        f"The JSON object must contain exactly these keys: {keys_list}. "
        "The red_flags value must be an array of objects; each object must have "
        "keys flag and severity only. "
        "Use snake_case keys exactly as listed. "
        "client_type_signals: 1–5 short observations about client type and buying style "
        "(or empty array if none). "
        "scope_clarity must be one of: clear, ambiguous, vague. "
        "scope_clarity_score: integer 0–10. "
        "required_skills: skill names as strings (empty array if none stated). "
        "budget_signal: one of stated, hinted, absent. "
        "estimated_budget: non-empty string, e.g. a USD range or 'unknown'. "
        "project_complexity: one of simple, moderate, complex. "
        "ideal_candidate_summary: one or two non-empty sentences. "
        "severity for each red flag: low, medium, or high."
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


def job_intelligence_agent(state: ValidatorState) -> dict:
    """
    Extract structured JobAnalysis from the job posting via CHEAP_MODEL.
    Returns {"job_analysis": JobAnalysis}.
    """
    messages = [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": (
                "Analyze the following job posting and produce the JSON object.\n\n"
                f"{state.job_posting}"
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

    try:
        job_analysis = JobAnalysis.model_validate_json(raw.strip())
    except ValidationError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e
    except ValueError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e

    return {"job_analysis": job_analysis}
