"""Unit tests for Job Intelligence agent — mocked LiteLLM."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.job_intelligence import job_intelligence_agent
from exceptions import AgentCallError, SchemaValidationError
from schemas.job_analysis import JobAnalysis
from schemas.state import ValidatorState


def _minimal_state() -> ValidatorState:
    return ValidatorState(
        mode="analyze",
        job_posting=(
            "Need a Python developer to build a web scraper for an e-commerce site. "
            "Budget around $500. Skills: Python, BeautifulSoup. Two-week timeline."
        ),
    )


def _valid_job_analysis_dict() -> dict:
    return {
        "client_type_signals": ["Budget stated upfront", "Tight timeline"],
        "scope_clarity": "ambiguous",
        "scope_clarity_score": 6,
        "required_skills": ["Python", "BeautifulSoup"],
        "budget_signal": "stated",
        "estimated_budget": "$500",
        "red_flags": [
            {"flag": "Short deadline for unclear scope", "severity": "medium"},
        ],
        "project_complexity": "simple",
        "ideal_candidate_summary": (
            "A Python developer who can ship a reliable scraper within two weeks."
        ),
    }


def _mock_completion_response(content: str | None) -> MagicMock:
    resp = MagicMock()
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp.choices = [choice]
    return resp


@patch("agents.job_intelligence.litellm.completion")
def test_happy_path_returns_job_analysis_dict(mock_completion):
    payload = _valid_job_analysis_dict()
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = job_intelligence_agent(_minimal_state())

    assert set(result.keys()) == {"job_analysis"}
    assert isinstance(result["job_analysis"], JobAnalysis)
    ja = result["job_analysis"]
    assert ja.scope_clarity_score == 6
    assert ja.budget_signal == "stated"
    assert len(ja.red_flags) == 1
    assert ja.red_flags[0].severity == "medium"
    mock_completion.assert_called_once()
    call_kw = mock_completion.call_args.kwargs
    assert "response_format" not in call_kw
    assert call_kw["model"] is not None


@patch("agents.job_intelligence.litellm.completion")
def test_agent_call_error_on_litellm_exception(mock_completion):
    mock_completion.side_effect = RuntimeError("API unavailable")

    with pytest.raises(AgentCallError) as exc_info:
        job_intelligence_agent(_minimal_state())

    assert exc_info.value.agent_name == "job_intelligence"
    assert "API unavailable" in str(exc_info.value)


@patch("agents.job_intelligence.litellm.completion")
def test_schema_validation_error_on_malformed_json(mock_completion):
    mock_completion.return_value = _mock_completion_response("{not valid json")

    with pytest.raises(SchemaValidationError) as exc_info:
        job_intelligence_agent(_minimal_state())

    assert exc_info.value.agent_name == "job_intelligence"


@patch("agents.job_intelligence.litellm.completion")
def test_agent_call_error_on_empty_response(mock_completion):
    mock_completion.return_value = _mock_completion_response("")

    with pytest.raises(AgentCallError) as exc_info:
        job_intelligence_agent(_minimal_state())

    assert exc_info.value.agent_name == "job_intelligence"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.job_intelligence.litellm.completion")
def test_agent_call_error_on_whitespace_only_response(mock_completion):
    mock_completion.return_value = _mock_completion_response("   \n\t  ")

    with pytest.raises(AgentCallError) as exc_info:
        job_intelligence_agent(_minimal_state())

    assert exc_info.value.agent_name == "job_intelligence"


@patch("agents.job_intelligence.litellm.completion")
def test_agent_call_error_on_none_content(mock_completion):
    mock_completion.return_value = _mock_completion_response(None)

    with pytest.raises(AgentCallError) as exc_info:
        job_intelligence_agent(_minimal_state())

    assert exc_info.value.agent_name == "job_intelligence"


@patch("agents.job_intelligence.litellm.completion")
def test_agent_call_error_on_missing_choices(mock_completion):
    mock_completion.return_value = MagicMock(choices=[])

    with pytest.raises(AgentCallError) as exc_info:
        job_intelligence_agent(_minimal_state())

    assert exc_info.value.agent_name == "job_intelligence"
