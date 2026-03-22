"""
Golden test fixtures for Freelance Proposal Analyzer.
Used across unit, integration, and acceptance tests.
All agents are tested against these realistic scenarios.
"""

import pytest


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


@pytest.fixture
def sample_analyze_request():
    """Realistic analyze mode request with a weak proposal."""
    return {
        "job_posting": WEAK_PROPOSAL_JOB_POSTING,
        "proposal_draft": WEAK_PROPOSAL_DRAFT,
        "mode": "analyze"
    }


@pytest.fixture
def sample_generate_request():
    """Realistic generate mode request — strong job posting."""
    return {
        "job_posting": STRONG_JOB_POSTING,
        "mode": "generate"
    }


@pytest.fixture
def minimal_job_posting():
    """Minimal valid job posting for edge case testing."""
    return "Need a developer to build a basic todo app. Budget TBD." * 2


# ── Placeholder agent output fixtures (populated in Phase 1) ─────────────────
# These will be filled in once schemas are implemented.

@pytest.fixture
def sample_job_analysis():
    """Valid JobAnalysis instance for downstream agent testing."""
    # TODO: Return JobAnalysis instance in Phase 1
    return {}


@pytest.fixture
def sample_rate_analysis():
    """Valid RateAnalysis instance for downstream agent testing."""
    # TODO: Return RateAnalysis instance in Phase 1
    return {}
