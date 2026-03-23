"""
Proposal_analyst agent — implemented in Phase 4.
See docs/specs/project-spec.md for responsibilities and output schema.
"""
from pydantic import ValidationError

import litellm

from config import settings
from exceptions import AgentCallError, SchemaValidationError
from schemas.proposal_critique import ProposalCritique
from schemas.proposal_draft import ProposalDraft
from schemas.state import ValidatorState

_AGENT_NAME = "proposal_analyst"

_PROPOSAL_CRITIQUE_JSON_KEYS = (
    "overall_score",
    "critical_weaknesses",
    "missing_elements",
    "tone_score",
    "tone_issues",
    "opening_hook_score",
    "cta_strength_score",
    "personalization_score",
    "rewritten_opening",
)

_PROPOSAL_DRAFT_JSON_KEYS = (
    "proposal_text",
    "word_count",
    "key_differentiators",
    "rate_argument_included",
)


def _system_prompt_analyze() -> str:
    forbidden = (
        "FORBIDDEN VOCABULARY — never use these exact terms in prose inside string "
        "values (write natural descriptions without naming schema fields):\n"
        "overall_score, critical_weaknesses, missing_elements, tone_score, "
        "tone_issues, opening_hook_score, cta_strength_score, personalization_score, "
        "rewritten_opening, weakness, impact, fix_suggestion"
    )
    keys_list = ", ".join(_PROPOSAL_CRITIQUE_JSON_KEYS)
    json_rules = (
        "You must respond with a single valid JSON object only. "
        "No markdown, no code fences, no prose before or after. "
        f"The JSON object must contain exactly these keys: {keys_list}. "
        "Use snake_case keys exactly as listed. "
        "overall_score, tone_score, opening_hook_score, cta_strength_score, and "
        "personalization_score must be integers 0-10 inclusive. "
        "critical_weaknesses must be an array of objects using keys weakness, impact, "
        "fix_suggestion only. impact must be one of: low, medium, high. "
        "missing_elements and tone_issues must be arrays of strings (empty arrays if none). "
        "rewritten_opening must be a non-empty improved first paragraph."
    )
    return f"{forbidden}\n\n{json_rules}"


def _system_prompt_generate() -> str:
    forbidden = (
        "FORBIDDEN VOCABULARY — never use these exact terms in prose inside string "
        "values (write natural descriptions without naming schema fields):\n"
        "proposal_text, word_count, key_differentiators, rate_argument_included"
    )
    keys_list = ", ".join(_PROPOSAL_DRAFT_JSON_KEYS)
    json_rules = (
        "You must respond with a single valid JSON object only. "
        "No markdown, no code fences, no prose before or after. "
        f"The JSON object must contain exactly these keys: {keys_list}. "
        "Use snake_case keys exactly as listed. "
        "proposal_text must be a complete freelancer proposal in markdown and non-empty. "
        "key_differentiators must be an array with 1-5 concise strings. "
        "rate_argument_included must be true when the proposal includes a clear rate/value "
        "argument grounded in the provided rate context. "
        "word_count must be a positive integer aligned with proposal_text."
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


def proposal_analyst_agent(state: ValidatorState) -> dict:
    """
    Produce ProposalCritique in analyze mode or ProposalDraft in generate mode
    via STRONG_MODEL.
    """
    if state.job_analysis is None:
        raise AgentCallError(_AGENT_NAME, "job_analysis not available")
    if state.rate_analysis is None:
        raise AgentCallError(_AGENT_NAME, "rate_analysis not available")

    if state.mode == "analyze":
        prompt = _system_prompt_analyze()
        proposal_text = state.proposal_draft_text if state.proposal_draft_text else "N/A"
        user_content = (
            "Generate a proposal critique JSON object from this context.\n\n"
            f"Mode: {state.mode}\n"
            f"JobAnalysis JSON: {state.job_analysis.model_dump_json()}\n"
            f"RateAnalysis JSON: {state.rate_analysis.model_dump_json()}\n"
            f"Proposal draft text: {proposal_text}\n\n"
            "Analyze mode requirements: score the proposal (0-10 fields), identify "
            "critical weaknesses with impact and fixes, list missing elements, identify "
            "tone issues, and rewrite the opening paragraph."
        )
    else:
        prompt = _system_prompt_generate()
        user_content = (
            "Generate a proposal draft JSON object from this context.\n\n"
            f"Mode: {state.mode}\n"
            f"JobAnalysis JSON: {state.job_analysis.model_dump_json()}\n"
            f"RateAnalysis JSON: {state.rate_analysis.model_dump_json()}\n\n"
            "Generate mode requirements: write a complete proposal in markdown, use "
            "1-5 key differentiators, and include a rate/value argument grounded in "
            "the provided rate analysis."
        )

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
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
        if state.mode == "analyze":
            critique = ProposalCritique.model_validate_json(cleaned)
            return {"proposal_critique": critique}
        draft = ProposalDraft.model_validate_json(cleaned)
        return {"proposal_draft": draft}
    except ValidationError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e
    except ValueError as e:
        raise SchemaValidationError(_AGENT_NAME, str(e)) from e
