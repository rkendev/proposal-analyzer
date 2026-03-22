"""
LangGraph orchestrator state — ValidatorState.
Holds request inputs, per-agent outputs, and the final report.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas.job_analysis import JobAnalysis
from schemas.proposal_critique import ProposalCritique
from schemas.proposal_draft import ProposalDraft
from schemas.proposal_report import ProposalReport
from schemas.rate_analysis import RateAnalysis
from schemas.win_strategy import WinStrategy


class ValidatorState(BaseModel):
    """Graph state passed between agents. extra=forbid catches typos early."""

    model_config = ConfigDict(extra="forbid")

    mode: Literal["analyze", "generate"] = Field(
        description="Pipeline mode: analyze (job + draft) or generate (job only)."
    )
    job_posting: str = Field(
        min_length=1,
        description="Raw job posting text from the client. Non-empty string.",
    )
    proposal_draft_text: str | None = Field(
        default=None,
        description=(
            "User's proposal draft for analyze mode (maps from request field "
            "proposal_draft). Null in generate mode. Distinct from proposal_draft "
            "which is the generated ProposalDraft model."
        ),
    )
    job_id: str | None = Field(
        default=None,
        description="UUID or id for SSE stream correlation. Null before dispatch.",
    )
    job_analysis: JobAnalysis | None = Field(
        default=None,
        description="Output of Job Intelligence agent.",
    )
    rate_analysis: RateAnalysis | None = Field(
        default=None,
        description="Output of Rate Intelligence agent.",
    )
    proposal_critique: ProposalCritique | None = Field(
        default=None,
        description="Output of Proposal Analyst in analyze mode.",
    )
    proposal_draft: ProposalDraft | None = Field(
        default=None,
        description="Output of Proposal Analyst in generate mode (model, not raw text).",
    )
    win_strategy: WinStrategy | None = Field(
        default=None,
        description="Output of Win Strategy agent.",
    )
    final_report: ProposalReport | None = Field(
        default=None,
        description="Assembled ProposalReport returned to the client.",
    )
