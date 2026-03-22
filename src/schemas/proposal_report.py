"""
Top-level API response — ProposalReport.
See docs/specs/api-contract.md.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas.job_analysis import JobAnalysis
from schemas.proposal_critique import ProposalCritique
from schemas.proposal_draft import ProposalDraft
from schemas.rate_analysis import RateAnalysis
from schemas.win_strategy import WinStrategy


class ProposalReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["analyze", "generate"] = Field(
        description=(
            "Which pipeline produced this report. One of: analyze, generate. "
            "Example: analyze."
        ),
    )
    job_id: str = Field(
        min_length=1,
        description=(
            "Server-generated job identifier for streaming and correlation. "
            "Non-empty string. Example: '550e8400-e29b-41d4-a716-446655440000'."
        ),
    )
    job_analysis: JobAnalysis = Field(
        description="Structured output from Job Intelligence. Unit: JobAnalysis model."
    )
    rate_analysis: RateAnalysis = Field(
        description="Structured output from Rate Intelligence. Unit: RateAnalysis model."
    )
    proposal_critique: ProposalCritique | None = Field(
        default=None,
        description=(
            "Proposal Analyst output in analyze mode only; null in generate mode. "
            "Unit: ProposalCritique model or null."
        ),
    )
    proposal_draft: ProposalDraft | None = Field(
        default=None,
        description=(
            "Proposal Analyst output in generate mode only; null in analyze mode. "
            "Unit: ProposalDraft model or null."
        ),
    )
    win_strategy: WinStrategy = Field(
        description="Structured output from Win Strategy. Unit: WinStrategy model."
    )
    overall_win_readiness_score: int | None = Field(
        default=None,
        ge=0,
        le=10,
        description=(
            "Aggregate readiness score for analyze mode only; null in generate mode. "
            "int 0-10 inclusive when present. Unit: score. Example: 6."
        ),
    )
