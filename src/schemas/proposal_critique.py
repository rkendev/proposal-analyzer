"""
Proposal Analyst agent output (analyze mode) — ProposalCritique.
See docs/specs/api-contract.md.
"""

from pydantic import BaseModel, ConfigDict, Field

from schemas.common import Weakness


class ProposalCritique(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(
        ge=0,
        le=10,
        description=(
            "Overall proposal quality. int 0-10 inclusive. Unit: score. "
            "Example: 4."
        ),
    )
    critical_weaknesses: list[Weakness] = Field(
        default_factory=list,
        description=(
            "Prioritized weaknesses. Empty list if none. Unit: Weakness objects."
        ),
    )
    missing_elements: list[str] = Field(
        default_factory=list,
        description=(
            "Required sections or proof missing from the draft. Empty list if none. "
            "Example: ['Past work samples', 'Timeline with milestones']."
        ),
    )
    tone_score: int = Field(
        ge=0,
        le=10,
        description=(
            "How well tone matches client and role. int 0-10 inclusive. Unit: score. "
            "Example: 5."
        ),
    )
    tone_issues: list[str] = Field(
        default_factory=list,
        description=(
            "Specific tone problems. Empty list if none. "
            "Example: ['Too informal for stated enterprise context']."
        ),
    )
    opening_hook_score: int = Field(
        ge=0,
        le=10,
        description=(
            "Strength of the opening hook. int 0-10 inclusive. Unit: score. "
            "Example: 3."
        ),
    )
    cta_strength_score: int = Field(
        ge=0,
        le=10,
        description=(
            "Strength of call-to-action / close. int 0-10 inclusive. Unit: score. "
            "Example: 4."
        ),
    )
    personalization_score: int = Field(
        ge=0,
        le=10,
        description=(
            "Evidence of personalization to this client/job. int 0-10 inclusive. "
            "Unit: score. Example: 2."
        ),
    )
    rewritten_opening: str = Field(
        min_length=1,
        description=(
            "Improved first paragraph. Non-empty string (markdown/plain text). "
            "Example: 'I have shipped three competitor price monitors for…'"
        ),
    )
