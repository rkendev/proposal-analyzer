"""
Pydantic v2 schemas for Freelance Proposal Analyzer.
"""

from schemas.common import Improvement, RedFlag, Weakness
from schemas.job_analysis import JobAnalysis
from schemas.proposal_critique import ProposalCritique
from schemas.proposal_draft import ProposalDraft
from schemas.proposal_report import ProposalReport
from schemas.rate_analysis import RateAnalysis
from schemas.state import ValidatorState
from schemas.win_strategy import WinStrategy

__all__ = [
    "Improvement",
    "JobAnalysis",
    "ProposalCritique",
    "ProposalDraft",
    "ProposalReport",
    "RateAnalysis",
    "RedFlag",
    "ValidatorState",
    "Weakness",
    "WinStrategy",
]
