"""Unit tests for Win Strategy agent — mocked LiteLLM."""

import json
from unittest.mock import MagicMock, patch

import pytest

from agents.win_strategy import win_strategy_agent
from config import settings
from exceptions import AgentCallError, SchemaValidationError
from schemas.job_analysis import JobAnalysis
from schemas.proposal_critique import ProposalCritique
from schemas.proposal_draft import ProposalDraft
from schemas.rate_analysis import RateAnalysis
from schemas.state import ValidatorState
from schemas.win_strategy import WinStrategy


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


def _sample_proposal_critique() -> ProposalCritique:
    return ProposalCritique(
        overall_score=4,
        critical_weaknesses=[
            {
                "weakness": "Opening is generic and not tailored to client needs.",
                "impact": "high",
                "fix_suggestion": (
                    "Lead with a client-specific outcome and relevant proof."
                ),
            }
        ],
        missing_elements=["Portfolio link", "Milestone breakdown"],
        tone_score=5,
        tone_issues=["Reads as template-like"],
        opening_hook_score=3,
        cta_strength_score=4,
        personalization_score=2,
        rewritten_opening=(
            "I have delivered competitor price tracking scrapers for e-commerce teams."
        ),
    )


def _sample_proposal_draft() -> ProposalDraft:
    return ProposalDraft(
        proposal_text=(
            "## Summary\n\nI can deliver a reliable competitor-price scraper in two "
            "weeks with staged milestones and validation checks."
        ),
        word_count=31,
        key_differentiators=[
            "E-commerce scraping experience",
            "Milestone-driven delivery",
            "Quality checks and logging",
        ],
        rate_argument_included=True,
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
        rate_analysis=_sample_rate_analysis(),
        proposal_critique=_sample_proposal_critique(),
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
        proposal_draft=_sample_proposal_draft(),
    )


def _valid_win_strategy_dict() -> dict:
    return {
        "win_probability": "medium",
        "win_probability_score": 6,
        "competing_profiles": [
            "Generalist scraper freelancers",
            "Low-cost offshore agencies",
        ],
        "differentiation_angle": "Emphasize reliable delivery with clear milestones.",
        "top_improvements": [
            {
                "priority": 1,
                "action": "Lead with direct relevance to the client's specific outcome.",
                "expected_impact": "Higher trust in first 10 seconds of review.",
            },
            {
                "priority": 2,
                "action": "Add a concise milestone timeline with deliverables.",
                "expected_impact": "Reduces delivery-risk concerns.",
            },
            {
                "priority": 3,
                "action": "Support price with value framing and scope boundaries.",
                "expected_impact": "Rate appears intentional and defensible.",
            },
        ],
        "deal_breakers": ["No evidence of similar e-commerce scraping work."],
        "one_line_positioning": (
            "Python scraper specialist focused on reliable, milestone-driven delivery."
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


@patch("agents.win_strategy.litellm.completion")
def test_happy_path_analyze_mode_returns_win_strategy(mock_completion):
    payload = _valid_win_strategy_dict()
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = win_strategy_agent(_minimal_state_analyze())

    assert set(result.keys()) == {"win_strategy"}
    assert isinstance(result["win_strategy"], WinStrategy)
    assert result["win_strategy"].win_probability == "medium"
    call_kw = mock_completion.call_args.kwargs
    assert call_kw["model"] == settings.strong_model_name
    assert "response_format" not in call_kw


@patch("agents.win_strategy.litellm.completion")
def test_happy_path_generate_mode_returns_win_strategy(mock_completion):
    payload = _valid_win_strategy_dict()
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    result = win_strategy_agent(_minimal_state_generate())

    assert set(result.keys()) == {"win_strategy"}
    assert isinstance(result["win_strategy"], WinStrategy)
    assert result["win_strategy"].win_probability_score == 6
    call_kw = mock_completion.call_args.kwargs
    assert call_kw["model"] == settings.strong_model_name
    assert "response_format" not in call_kw


def test_agent_call_error_when_job_analysis_missing():
    state = _minimal_state_analyze().model_copy(update={"job_analysis": None})

    with pytest.raises(AgentCallError) as exc_info:
        win_strategy_agent(state)

    assert exc_info.value.agent_name == "win_strategy"
    assert "job_analysis not available" in str(exc_info.value)


def test_agent_call_error_when_rate_analysis_missing():
    state = _minimal_state_analyze().model_copy(update={"rate_analysis": None})

    with pytest.raises(AgentCallError) as exc_info:
        win_strategy_agent(state)

    assert exc_info.value.agent_name == "win_strategy"
    assert "rate_analysis not available" in str(exc_info.value)


@patch("agents.win_strategy.litellm.completion")
def test_agent_call_error_on_litellm_exception(mock_completion):
    mock_completion.side_effect = RuntimeError("API unavailable")

    with pytest.raises(AgentCallError) as exc_info:
        win_strategy_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "win_strategy"
    assert "API unavailable" in str(exc_info.value)


@patch("agents.win_strategy.litellm.completion")
def test_schema_validation_error_on_malformed_json(mock_completion):
    mock_completion.return_value = _mock_completion_response("{not valid json")

    with pytest.raises(SchemaValidationError) as exc_info:
        win_strategy_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "win_strategy"


@patch("agents.win_strategy.litellm.completion")
def test_agent_call_error_on_empty_response(mock_completion):
    mock_completion.return_value = _mock_completion_response("")

    with pytest.raises(AgentCallError) as exc_info:
        win_strategy_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "win_strategy"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.win_strategy.litellm.completion")
def test_agent_call_error_on_none_content(mock_completion):
    mock_completion.return_value = _mock_completion_response(None)

    with pytest.raises(AgentCallError) as exc_info:
        win_strategy_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "win_strategy"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.win_strategy.litellm.completion")
def test_agent_call_error_on_missing_choices(mock_completion):
    mock_completion.return_value = MagicMock(choices=[])

    with pytest.raises(AgentCallError) as exc_info:
        win_strategy_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "win_strategy"
    assert "empty" in str(exc_info.value).lower()


@patch("agents.win_strategy.litellm.completion")
def test_schema_validation_error_when_top_improvements_wrong_count(mock_completion):
    payload = _valid_win_strategy_dict()
    payload["top_improvements"] = payload["top_improvements"][:2]
    mock_completion.return_value = _mock_completion_response(json.dumps(payload))

    with pytest.raises(SchemaValidationError) as exc_info:
        win_strategy_agent(_minimal_state_analyze())

    assert exc_info.value.agent_name == "win_strategy"


@patch("agents.win_strategy.litellm.completion")
def test_markdown_fence_stripping_works_before_parse(mock_completion):
    payload = _valid_win_strategy_dict()
    fenced = f"```json\n{json.dumps(payload)}\n```"
    mock_completion.return_value = _mock_completion_response(fenced)

    result = win_strategy_agent(_minimal_state_generate())

    assert isinstance(result["win_strategy"], WinStrategy)
    assert len(result["win_strategy"].top_improvements) == 3
