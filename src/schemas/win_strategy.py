"""
Win Strategy agent output — WinStrategy.
See docs/specs/api-contract.md (win_strategy nested object).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from schemas.common import Improvement


class WinStrategy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    win_probability: Literal["low", "medium", "high"] = Field(
        description=(
            "Qualitative win likelihood band. One of: low, medium, high. "
            "Example: medium."
        ),
    )
    win_probability_score: int = Field(
        ge=0,
        le=10,
        description=(
            "Quantified win likelihood. int 0-10 inclusive. Unit: score. "
            "Example: 5."
        ),
    )
    competing_profiles: list[str] = Field(
        default_factory=list,
        description=(
            "Likely competitor archetypes (1-3 in typical UI). Empty list if unknown. "
            "Unit: short profile strings. Example: ['Offshore generalist dev shops']."
        ),
    )
    differentiation_angle: str = Field(
        min_length=1,
        description=(
            "Primary angle to stand out. Non-empty string. "
            "Example: 'Emphasize compliance logging experience for fintech buyers.'"
        ),
    )
    top_improvements: list[Improvement] = Field(
        description=(
            "Exactly three prioritized improvements (analyze) or strengths framed "
            "as improvements (generate). Unit: Improvement objects with priority "
            "int 1-3. Must contain exactly 3 items."
        ),
    )
    deal_breakers: list[str] = Field(
        default_factory=list,
        description=(
            "Issues that could lose the job. Empty list if none. "
            "Example: ['No relevant portfolio link']."
        ),
    )
    one_line_positioning: str = Field(
        min_length=1,
        description=(
            "Single-line positioning statement. Non-empty string. "
            "Example: 'Senior Python data engineer for high-volume payment pipelines.'"
        ),
    )

    @field_validator("top_improvements")
    @classmethod
    def exactly_three_improvements(cls, v: list[Improvement]) -> list[Improvement]:
        if len(v) != 3:
            raise ValueError("top_improvements must contain exactly 3 items")
        return v
