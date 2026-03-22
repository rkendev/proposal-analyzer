"""
Golden test fixtures for Freelance Proposal Analyzer.
Used across unit, integration, and acceptance tests.
All agents are tested against these realistic scenarios.
"""

import pytest

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


# ── Golden request fixtures ───────────────────────────────────────────────────

WEAK_PROPOSAL_JOB_POSTING = """
I need a Python developer to build a web scraper for my e-commerce site.
The scraper should extract product prices from competitor websites.
Budget is around $500. Need it done in 2 weeks.
Skills: Python, BeautifulSoup, requests
"""

WEAK_PROPOSAL_DRAFT = """
Hi, I am a Python developer. I can do this project.
I have experience with web scraping. I will use Python and BeautifulSoup.
I can start immediately. My rate is $400 for the project.
Let me know if you want to proceed.
"""

STRONG_JOB_POSTING = """
Senior Python developer needed for a 3-month engagement to build a
data pipeline that processes 500k daily transactions from our payment
system into a PostgreSQL analytics database. Must have experience with
async Python, SQLAlchemy, and handling financial data at scale.
Budget: $8,000-12,000 USD fixed price. Looking for someone with
proven experience in fintech or payments.
Required skills: Python 3.10+, asyncio, SQLAlchemy, PostgreSQL,
pytest, Docker
"""


def three_top_improvements() -> list[Improvement]:
    """Exactly three Improvement rows for WinStrategy (api-contract)."""
    return [
        Improvement(
            priority=1,
            action="Tie opening to the client's product and data volume.",
            expected_impact="Stronger relevance in the first sentences.",
        ),
        Improvement(
            priority=2,
            action="Add milestones that de-risk the two-week deadline.",
            expected_impact="Clear delivery plan reduces client anxiety.",
        ),
        Improvement(
            priority=3,
            action="Align stated price with a brief value justification.",
            expected_impact="Rate reads as intentional, not arbitrary.",
        ),
    ]


@pytest.fixture
def sample_analyze_request():
    """Realistic analyze mode request with a weak proposal."""
    return {
        "job_posting": WEAK_PROPOSAL_JOB_POSTING,
        "proposal_draft": WEAK_PROPOSAL_DRAFT,
        "mode": "analyze",
    }


@pytest.fixture
def sample_generate_request():
    """Realistic generate mode request — strong job posting."""
    return {
        "job_posting": STRONG_JOB_POSTING,
        "mode": "generate",
    }


@pytest.fixture
def minimal_job_posting():
    """Minimal valid job posting for edge case testing."""
    return "Need a developer to build a basic todo app. Budget TBD." * 2


# ── Agent output fixtures ─────────────────────────────────────────────────────


@pytest.fixture
def sample_job_analysis():
    """Valid JobAnalysis instance for downstream agent testing."""
    return JobAnalysis(
        client_type_signals=[
            "Budget stated upfront",
            "Two-week deadline pressure",
        ],
        scope_clarity="ambiguous",
        scope_clarity_score=6,
        required_skills=["Python", "BeautifulSoup", "requests"],
        budget_signal="stated",
        estimated_budget="$500",
        red_flags=[
            RedFlag(flag="Timeline may be tight for discovery plus build", severity="medium"),
        ],
        project_complexity="simple",
        ideal_candidate_summary=(
            "A Python developer who can deliver a reliable price scraper within two weeks."
        ),
    )


@pytest.fixture
def sample_rate_analysis():
    """Valid RateAnalysis instance for downstream agent testing."""
    return RateAnalysis(
        recommended_rate_min=400.0,
        recommended_rate_max=750.0,
        rate_currency="USD",
        rate_type="fixed",
        rate_justification=(
            "Small fixed-scope scraper engagements in this band are common; "
            "client budget anchors near $500."
        ),
        current_rate_assessment="underpriced",
        assessment_explanation=(
            "A $400 fixed bid is below the recommended range for comparable scope."
        ),
        negotiation_leverage=(
            "Offer phased delivery: working scraper by day 10, hardening by day 14."
        ),
        rate_red_flags=[],
    )


@pytest.fixture
def sample_win_strategy():
    """Valid WinStrategy with exactly three top_improvements."""
    return WinStrategy(
        win_probability="medium",
        win_probability_score=5,
        competing_profiles=["Generalist scraper devs", "Offshore low-cost shops"],
        differentiation_angle="Emphasize reliability and clear milestone delivery.",
        top_improvements=three_top_improvements(),
        deal_breakers=["No demonstration of similar e-commerce scraping"],
        one_line_positioning="Focused Python scraper engineer for competitor price monitoring.",
    )


@pytest.fixture
def sample_proposal_critique():
    """Valid ProposalCritique for analyze-mode tests."""
    return ProposalCritique(
        overall_score=4,
        critical_weaknesses=[
            Weakness(
                weakness="Generic opening with no client-specific detail.",
                impact="high",
                fix_suggestion="Open with one sentence about their catalog or pricing goals.",
            ),
        ],
        missing_elements=["Portfolio link", "Milestone breakdown"],
        tone_score=5,
        tone_issues=["Reads as template-like"],
        opening_hook_score=3,
        cta_strength_score=4,
        personalization_score=2,
        rewritten_opening=(
            "I have built competitor price monitors for e-commerce catalogs; "
            "here is how I would approach yours in two weeks with clear milestones."
        ),
    )


@pytest.fixture
def sample_proposal_draft():
    """Valid ProposalDraft for generate-mode tests."""
    return ProposalDraft(
        proposal_text=(
            "## Summary\n\nI will deliver a robust scraper with logging and sample output "
            "within your timeline.\n\n## Approach\n\nPython, BeautifulSoup, scheduled runs.\n"
        ),
        word_count=42,
        key_differentiators=["E-commerce scraping experience", "Clear milestones"],
        rate_argument_included=True,
    )


@pytest.fixture
def sample_proposal_report_analyze(sample_job_analysis, sample_rate_analysis, sample_win_strategy, sample_proposal_critique):
    """Full ProposalReport for analyze mode."""
    return ProposalReport(
        mode="analyze",
        job_id="00000000-0000-4000-8000-000000000001",
        job_analysis=sample_job_analysis,
        rate_analysis=sample_rate_analysis,
        proposal_critique=sample_proposal_critique,
        proposal_draft=None,
        win_strategy=sample_win_strategy,
        overall_win_readiness_score=6,
    )


@pytest.fixture
def sample_proposal_report_generate(sample_job_analysis, sample_rate_analysis, sample_win_strategy, sample_proposal_draft):
    """Full ProposalReport for generate mode."""
    return ProposalReport(
        mode="generate",
        job_id="00000000-0000-4000-8000-000000000002",
        job_analysis=sample_job_analysis,
        rate_analysis=sample_rate_analysis,
        proposal_critique=None,
        proposal_draft=sample_proposal_draft,
        win_strategy=sample_win_strategy,
        overall_win_readiness_score=None,
    )
