"""Unit tests for Proposal Analyst agent — mocked LiteLLM."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.proposal_analyst import proposal_analyst_agent
from config import settings
from exceptions import AgentCallError, SchemaValidationError
from schemas.job_analysis import JobAnalysis
from schemas.proposal_critique import ProposalCritique
from schemas.proposal_draft import ProposalDraft
from schemas.rate_analysis import RateAnalysis
from schemas.state import ValidatorState


def _sample_job_analysis() -> JobAnalysis:
    return JobAnalysis(
        client_type_signals=["Budget stated upfront", "Tight timeline urgency"],
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


def _sample_rate_analysis() -> RateAnalysis:
    return RateAnalysis(
        recommended_rate_min=450.0,
        recommended_rate_max=700.0,
        rate_currency="USD",
        rate_type="fixed",
        rate_justification=(
            "Comparable fixed-scope scraper projects often fall in this range."
        ),
        current_rate_assessment="underpriced",
        assessment_explanation="Given scope and timeline, this rate is low.",
        negotiation_leverage="Tight timeline and milestones justify value pricing.",
        rate_red_flags=[],
    )


def _minimal_state_analyze() -> ValidatorState:
    return ValidatorState(
        mode="analyze",
        job_posting=(
            "Need a Python developer to build a web scraper for e-commerce prices. "
            "Budget is around $500 and deadline is two weeks."
        ),
        proposal_draft_text=(
            "Hi, I can do this quickly. I have Python experience. "
            "My rate is $400 fixed."
        ),
        job_analysis=_sample_job_analysis(),
        rate_analysis=_sample_rate_analysis(),
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
        rate_analysis=_sample_rate_analysis(),
    )


def _valid_proposal_critique_dict() -> dict:
    return {
        "overall_score": 4,
        "critical_weaknesses": [
            {
                "weakness": "Opening is generic and not tailored to client needs.",
                "impact": "high",
                "fix_suggestion": "Lead with a client-specific outcome and relevant proof.",
            }
        ],
        "missing_elements": ["Portfolio link", "Milestone breakdown"],
        "tone_score": 5,
        "tone_issues": ["Reads as template-like"],
        "opening_hook_score": 3,
        "cta_strength_score": 4,
        "personalization_score": 2,
        "rewritten_opening": (
            "I have delivered competitor price tracking scrapers for e-commerce teams, "
            "and I would apply that playbook to your catalog with clear milestones."
        ),
    }


def _valid_proposal_draft_dict() -> dict:
    return {
        "proposal_text": (
            "## Summary\n\nI can deliver a reliable competitor-price scraper in two "
            "weeks with staged milestones and validation checks.\n\n"
            "## Rate\n\nBased on your scope, a fixed engagement in the recommended "
            "range is appropriate."
        ),
        "word_count": 44,
        "key_differentiators": [
            "E-commerce scraping experience",
            "Milestone-driven delivery",
            "Quality checks and logging",
        ],
        "rate_argument_included": True,
    }


def _mock_completion_response(content: str | None) -> MagicMock:
    resp = MagicMock()
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp.choices = [choice]
    return resp


@patch("agents.proposal_analyst.litellm.completion")
def test_happy_path_analyze_mode_returns_proposal_critique(mock_completion):
    payload = _valid_proposal_critique_dict()
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = proposal_analyst_agent(_minimal_state_analyze())

    assert set(result.keys()) == {"proposal_critique"}
    assert "proposal_draft" not in result
    assert isinstance(result["proposal_critique"], ProposalCritique)
    assert result["proposal_critique"].overall_score == 4
    call_kw = mock_completion.call_args.kwargs
    assert call_kw["model"] == settings.strong_model_name
    assert "response_format" not in call_kw


@patch("agents.proposal_analyst.litellm.completion")
def test_happy_path_generate_mode_returns_proposal_draft(mock_completion):
    payload = _valid_proposal_draft_dict()
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = proposal_analyst_agent(_minimal_state_generate())

    assert set(result.keys()) == {"proposal_draft"}
    assert "proposal_critique" not in result
    assert isinstance(result["proposal_draft"], ProposalDraft)
    assert result["proposal_draft"].rate_argument_included is True
    call_kw = mock_completion.call_args.kwargs
    assert call_kw["model"] == settings.strong_model_name
    assert "response_format" not in call_kw


@patch("agents.proposal_analyst.litellm.completion")
def test_agent_call_error_on_litellm_exception(mock_completion):
    mock_completion.side_effect = RuntimeError("API unavailable")

    with pytest.raises(AgentCallError) as exc_info:
        proposal_analyst_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "proposal_analyst"
    assert "API unavailable" in str(exc_info.value)


@patch("agents.proposal_analyst.litellm.completion")
def test_schema_validation_error_on_malformed_json(mock_completion):
    mock_completion.return_value = _mock_completion_response("{not valid json")

    with pytest.raises(SchemaValidationError) as exc_info:
        proposal_analyst_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "proposal_analyst"


@patch("agents.proposal_analyst.litellm.completion")
def test_agent_call_error_on_empty_response(mock_completion):
    mock_completion.return_value = _mock_completion_response("")

    with pytest.raises(AgentCallError) as exc_info:
        proposal_analyst_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "proposal_analyst"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.proposal_analyst.litellm.completion")
def test_agent_call_error_on_none_content(mock_completion):
    mock_completion.return_value = _mock_completion_response(None)

    with pytest.raises(AgentCallError) as exc_info:
        proposal_analyst_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "proposal_analyst"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.proposal_analyst.litellm.completion")
def test_markdown_fence_stripping_works_before_parse(mock_completion):
    payload = _valid_proposal_draft_dict()
    fenced = f"```json\n{json.dumps(payload)}\n```"
    mock_completion.return_value = _mock_completion_response(fenced)

    result = proposal_analyst_agent(_minimal_state_generate())

    assert isinstance(result["proposal_draft"], ProposalDraft)
    assert result["proposal_draft"].word_count > 0


def test_agent_call_error_when_job_analysis_missing():
    state = _minimal_state_analyze().model_copy(update={"job_analysis": None})

    with pytest.raises(AgentCallError) as exc_info:
        proposal_analyst_agent(state)

    assert exc_info.value.agent_name == "proposal_analyst"
    assert "job_analysis not available" in str(exc_info.value)


def test_agent_call_error_when_rate_analysis_missing():
    state = _minimal_state_analyze().model_copy(update={"rate_analysis": None})

    with pytest.raises(AgentCallError) as exc_info:
        proposal_analyst_agent(state)

    assert exc_info.value.agent_name == "proposal_analyst"
    assert "rate_analysis not available" in str(exc_info.value)
