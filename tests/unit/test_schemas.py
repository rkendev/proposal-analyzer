"""Unit tests for Pydantic schema structure, ranges, and defaults."""

import pytest
from pydantic import ValidationError

from schemas import (
    Improvement,
    JobAnalysis,
    ProposalCritique,
    ProposalDraft,
    ProposalReport,
    RateAnalysis,
    RedFlag,
    Weakness,
    WinStrategy,
)
from schemas.state import ValidatorState


def test_red_flag_round_trip():
    rf = RedFlag(flag="Risk text here", severity="high")
    d = rf.model_dump()
    assert d == {"flag": "Risk text here", "severity": "high"}
    assert RedFlag.model_validate(d) == rf


def test_weakness_invalid_empty_field():
    with pytest.raises(ValidationError):
        Weakness(weakness="", impact="low", fix_suggestion="Fix")


def test_improvement_priority_range():
    Improvement(priority=1, action="A", expected_impact="B")
    Improvement(priority=3, action="A", expected_impact="B")
    with pytest.raises(ValidationError):
        Improvement(priority=0, action="A", expected_impact="B")
    with pytest.raises(ValidationError):
        Improvement(priority=4, action="A", expected_impact="B")


def test_job_analysis_list_defaults():
    ja = JobAnalysis(
        scope_clarity="clear",
        scope_clarity_score=8,
        budget_signal="absent",
        estimated_budget="unknown",
        project_complexity="simple",
        ideal_candidate_summary="Someone solid.",
    )
    assert ja.client_type_signals == []
    assert ja.required_skills == []
    assert ja.red_flags == []


def test_job_analysis_score_range():
    with pytest.raises(ValidationError):
        JobAnalysis(
            scope_clarity="clear",
            scope_clarity_score=11,
            budget_signal="absent",
            estimated_budget="unknown",
            project_complexity="simple",
            ideal_candidate_summary="X",
        )


def test_rate_analysis_ordering():
    with pytest.raises(ValidationError):
        RateAnalysis(
            recommended_rate_min=100.0,
            recommended_rate_max=50.0,
            rate_currency="USD",
            rate_type="hourly",
            rate_justification="J",
            current_rate_assessment="not_applicable",
            assessment_explanation="N/A",
            negotiation_leverage="N/A",
        )


def test_rate_analysis_positive_rates():
    with pytest.raises(ValidationError):
        RateAnalysis(
            recommended_rate_min=0.0,
            recommended_rate_max=10.0,
            rate_currency="USD",
            rate_type="hourly",
            rate_justification="J",
            current_rate_assessment="not_applicable",
            assessment_explanation="N/A",
            negotiation_leverage="N/A",
        )


def test_proposal_critique_scores():
    pc = ProposalCritique(
        overall_score=0,
        tone_score=10,
        opening_hook_score=5,
        cta_strength_score=5,
        personalization_score=5,
        rewritten_opening="Hello.",
    )
    assert pc.missing_elements == []
    with pytest.raises(ValidationError):
        ProposalCritique(
            overall_score=11,
            tone_score=0,
            opening_hook_score=0,
            cta_strength_score=0,
            personalization_score=0,
            rewritten_opening="X",
        )


def test_proposal_draft_word_count():
    with pytest.raises(ValidationError):
        ProposalDraft(
            proposal_text="Hello",
            word_count=0,
            rate_argument_included=False,
        )


def test_win_strategy_exactly_three_improvements():
    imp = Improvement(priority=1, action="a", expected_impact="b")
    with pytest.raises(ValidationError):
        WinStrategy(
            win_probability="low",
            win_probability_score=1,
            differentiation_angle="x",
            top_improvements=[imp],
            one_line_positioning="y",
        )


def test_proposal_report_analyze_shape(sample_proposal_report_analyze):
    r = sample_proposal_report_analyze
    assert r.mode == "analyze"
    assert r.proposal_critique is not None
    assert r.proposal_draft is None
    assert r.overall_win_readiness_score is not None
    assert 0 <= r.overall_win_readiness_score <= 10


def test_proposal_report_generate_shape(sample_proposal_report_generate):
    r = sample_proposal_report_generate
    assert r.mode == "generate"
    assert r.proposal_critique is None
    assert r.proposal_draft is not None
    assert r.overall_win_readiness_score is None


def test_proposal_report_dump_keys(sample_proposal_report_analyze):
    d = sample_proposal_report_analyze.model_dump()
    assert set(d.keys()) == {
        "mode",
        "job_id",
        "job_analysis",
        "rate_analysis",
        "proposal_critique",
        "proposal_draft",
        "win_strategy",
        "overall_win_readiness_score",
    }


def test_validator_state_proposal_draft_naming():
    """Input draft text vs generated ProposalDraft model must not collide."""
    st = ValidatorState(
        mode="analyze",
        job_posting="x" * 60,
        proposal_draft_text="y" * 60,
    )
    assert st.proposal_draft is None
    assert st.proposal_draft_text is not None


def test_overall_win_readiness_optional_score_none_valid():
    r = ProposalReport(
        mode="generate",
        job_id="jid",
        job_analysis=JobAnalysis(
            scope_clarity="clear",
            scope_clarity_score=5,
            budget_signal="stated",
            estimated_budget="$1",
            project_complexity="simple",
            ideal_candidate_summary="Summary here.",
        ),
        rate_analysis=RateAnalysis(
            recommended_rate_min=1.0,
            recommended_rate_max=2.0,
            rate_currency="USD",
            rate_type="fixed",
            rate_justification="J",
            current_rate_assessment="fair",
            assessment_explanation="E",
            negotiation_leverage="L",
        ),
        proposal_critique=None,
        proposal_draft=None,
        win_strategy=WinStrategy(
            win_probability="high",
            win_probability_score=8,
            differentiation_angle="A",
            top_improvements=[
                Improvement(priority=1, action="a1", expected_impact="e1"),
                Improvement(priority=2, action="a2", expected_impact="e2"),
                Improvement(priority=3, action="a3", expected_impact="e3"),
            ],
            one_line_positioning="One line.",
        ),
        overall_win_readiness_score=None,
    )
    assert r.overall_win_readiness_score is None


def test_overall_win_readiness_score_range_when_set():
    with pytest.raises(ValidationError):
        ProposalReport(
            mode="analyze",
            job_id="jid",
            job_analysis=JobAnalysis(
                scope_clarity="clear",
                scope_clarity_score=5,
                budget_signal="stated",
                estimated_budget="$1",
                project_complexity="simple",
                ideal_candidate_summary="Summary here.",
            ),
            rate_analysis=RateAnalysis(
                recommended_rate_min=1.0,
                recommended_rate_max=2.0,
                rate_currency="USD",
                rate_type="fixed",
                rate_justification="J",
                current_rate_assessment="fair",
                assessment_explanation="E",
                negotiation_leverage="L",
            ),
            proposal_critique=ProposalCritique(
                overall_score=5,
                tone_score=5,
                opening_hook_score=5,
                cta_strength_score=5,
                personalization_score=5,
                rewritten_opening="Open.",
            ),
            proposal_draft=None,
            win_strategy=WinStrategy(
                win_probability="medium",
                win_probability_score=5,
                differentiation_angle="A",
                top_improvements=[
                    Improvement(priority=1, action="a1", expected_impact="e1"),
                    Improvement(priority=2, action="a2", expected_impact="e2"),
                    Improvement(priority=3, action="a3", expected_impact="e3"),
                ],
                one_line_positioning="One line.",
            ),
            overall_win_readiness_score=11,
        )
