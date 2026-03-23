"""Unit tests for Rate Intelligence agent — mocked LiteLLM."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.rate_intelligence import rate_intelligence_agent
from exceptions import AgentCallError, SchemaValidationError
from schemas.job_analysis import JobAnalysis
from schemas.rate_analysis import RateAnalysis
from schemas.state import ValidatorState


def _sample_job_analysis() -> JobAnalysis:
    return JobAnalysis(
        client_type_signals=["Budget stated upfront", "Fast timeline urgency"],
        scope_clarity="ambiguous",
        scope_clarity_score=6,
        required_skills=["Python", "BeautifulSoup", "requests"],
        budget_signal="stated",
        estimated_budget="$500",
        red_flags=[{"flag": "Timeline may be tight", "severity": "medium"}],
        project_complexity="simple",
        ideal_candidate_summary=(
            "A Python freelancer who can ship a reliable scraper quickly."
        ),
    )


def _minimal_state_analyze() -> ValidatorState:
    return ValidatorState(
        mode="analyze",
        job_posting=(
            "Need a Python developer to build a web scraper for e-commerce prices. "
            "Budget is around $500 and deadline is two weeks."
        ),
        proposal_draft_text=(
            "I can deliver this scraper in 2 weeks for $400 fixed and provide "
            "basic logging."
        ),
        job_analysis=_sample_job_analysis(),
    )


def _minimal_state_generate() -> ValidatorState:
    return ValidatorState(
        mode="generate",
        job_posting=(
            "Need a Python developer to build a web scraper for e-commerce prices. "
            "Budget is around $500 and deadline is two weeks."
        ),
        proposal_draft_text=None,
        job_analysis=_sample_job_analysis(),
    )


def _valid_rate_analysis_dict(assessment: str = "underpriced") -> dict:
    return {
        "recommended_rate_min": 450.0,
        "recommended_rate_max": 700.0,
        "rate_currency": "USD",
        "rate_type": "fixed",
        "rate_justification": (
            "Comparable fixed-scope scraper projects often fall in this range."
        ),
        "current_rate_assessment": assessment,
        "assessment_explanation": "Based on scope and timeline, this fit is reasonable.",
        "negotiation_leverage": (
            "Tight timeline and deliverable milestones support value-based pricing."
        ),
        "rate_red_flags": [],
    }


def _mock_completion_response(content: str | None) -> MagicMock:
    resp = MagicMock()
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp.choices = [choice]
    return resp


@patch("agents.rate_intelligence.litellm.completion")
def test_happy_path_analyze_mode_returns_rate_analysis_dict(mock_completion):
    payload = _valid_rate_analysis_dict("underpriced")
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = rate_intelligence_agent(_minimal_state_analyze())

    assert set(result.keys()) == {"rate_analysis"}
    assert isinstance(result["rate_analysis"], RateAnalysis)
    ra = result["rate_analysis"]
    assert ra.current_rate_assessment == "underpriced"
    assert ra.recommended_rate_max > ra.recommended_rate_min
    mock_completion.assert_called_once()
    call_kw = mock_completion.call_args.kwargs
    assert "response_format" not in call_kw
    assert call_kw["model"] is not None


@patch("agents.rate_intelligence.litellm.completion")
def test_happy_path_generate_mode_sets_not_applicable(mock_completion):
    payload = _valid_rate_analysis_dict("not_applicable")
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = rate_intelligence_agent(_minimal_state_generate())

    assert set(result.keys()) == {"rate_analysis"}
    assert isinstance(result["rate_analysis"], RateAnalysis)
    assert result["rate_analysis"].current_rate_assessment == "not_applicable"


@patch("agents.rate_intelligence.litellm.completion")
def test_parsing_strips_markdown_fences(mock_completion):
    payload = _valid_rate_analysis_dict("fair")
    fenced = f"```json\n{json.dumps(payload)}\n```"
    mock_completion.return_value = _mock_completion_response(fenced)

    result = rate_intelligence_agent(_minimal_state_analyze())

    assert isinstance(result["rate_analysis"], RateAnalysis)
    assert result["rate_analysis"].current_rate_assessment == "fair"


@patch("agents.rate_intelligence.litellm.completion")
def test_agent_call_error_on_litellm_exception(mock_completion):
    mock_completion.side_effect = RuntimeError("API unavailable")

    with pytest.raises(AgentCallError) as exc_info:
        rate_intelligence_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "rate_intelligence"
    assert "API unavailable" in str(exc_info.value)


@patch("agents.rate_intelligence.litellm.completion")
def test_schema_validation_error_on_malformed_json(mock_completion):
    mock_completion.return_value = _mock_completion_response("{not valid json")

    with pytest.raises(SchemaValidationError) as exc_info:
        rate_intelligence_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "rate_intelligence"


@patch("agents.rate_intelligence.litellm.completion")
def test_agent_call_error_on_empty_response(mock_completion):
    mock_completion.return_value = _mock_completion_response("")

    with pytest.raises(AgentCallError) as exc_info:
        rate_intelligence_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "rate_intelligence"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.rate_intelligence.litellm.completion")
def test_agent_call_error_on_none_content(mock_completion):
    mock_completion.return_value = _mock_completion_response(None)

    with pytest.raises(AgentCallError) as exc_info:
        rate_intelligence_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "rate_intelligence"


@patch("agents.rate_intelligence.litellm.completion")
def test_agent_call_error_on_missing_choices(mock_completion):
    mock_completion.return_value = MagicMock(choices=[])

    with pytest.raises(AgentCallError) as exc_info:
        rate_intelligence_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "rate_intelligence"


@patch("agents.rate_intelligence.litellm.completion")
def test_schema_validation_error_when_rate_max_not_greater_than_min(mock_completion):
    payload = _valid_rate_analysis_dict("fair")
    payload["recommended_rate_min"] = 700.0
    payload["recommended_rate_max"] = 700.0
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    with pytest.raises(SchemaValidationError) as exc_info:
        rate_intelligence_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "rate_intelligence"
