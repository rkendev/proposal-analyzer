"""
Proposal Analyst agent output (generate mode) — ProposalDraft.
See docs/specs/api-contract.md.
"""

from pydantic import BaseModel, ConfigDict, Field


class ProposalDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    proposal_text: str = Field(
        min_length=1,
        description=(
            "Full generated proposal body. Non-empty string. Unit: markdown text. "
            "Example: '## Summary\\n\\nI will deliver…'."
        ),
    )
    word_count: int = Field(
        gt=0,
        description=(
            "Approximate word count of proposal_text. int greater than 0. "
            "Unit: words. Example: 320."
        ),
    )
    key_differentiators: list[str] = Field(
        default_factory=list,
        description=(
            "Differentiators emphasized in the proposal. Empty list if none. "
            "Example: ['Payment systems background', 'Async Python at scale']."
        ),
    )
    rate_argument_included: bool = Field(
        description=(
            "Whether the draft includes an explicit rate or value argument. "
            "Unit: boolean. Example: true."
        ),
    )
