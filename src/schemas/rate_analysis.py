"""
Rate Intelligence agent output — RateAnalysis.
See docs/specs/api-contract.md (rate_analysis nested object).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RateAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recommended_rate_min: float = Field(
        gt=0,
        description=(
            "Lower bound of recommended rate. float USD per hour or per fixed "
            "engagement (see rate_type). Unit: USD. Range: greater than 0. "
            "Example: 45.0."
        ),
    )
    recommended_rate_max: float = Field(
        gt=0,
        description=(
            "Upper bound of recommended rate. float USD; must be greater than "
            "recommended_rate_min. Unit: USD. Range: greater than 0. "
            "Example: 65.0."
        ),
    )
    rate_currency: Literal["USD"] = Field(
        description=(
            "Currency for rates. Always USD at v1. Literal 'USD' only. "
            "Example: USD."
        ),
    )
    rate_type: Literal["hourly", "fixed"] = Field(
        description=(
            "Whether rates are hourly or fixed-price. One of: hourly, fixed. "
            "Example: fixed."
        ),
    )
    rate_justification: str = Field(
        min_length=1,
        description=(
            "Prose explaining the rate recommendation for use in a proposal. "
            "Non-empty string. Example: 'Scope aligns with a small fixed build; "
            "market for similar scrapers is typically $400–$800.'"
        ),
    )
    current_rate_assessment: Literal[
        "underpriced", "fair", "overpriced", "not_applicable"
    ] = Field(
        description=(
            "Assessment of the freelancer's stated rate vs market (analyze mode). "
            "One of: underpriced, fair, overpriced, not_applicable. "
            "Example: underpriced."
        ),
    )
    assessment_explanation: str = Field(
        min_length=1,
        description=(
            "Why the current rate was assessed that way. Non-empty string. "
            "Use 'N/A' if not applicable. Example: 'Stated $400 fixed is below "
            "typical comparable scope.'"
        ),
    )
    negotiation_leverage: str = Field(
        min_length=1,
        description=(
            "Talking points for negotiation. Non-empty string. "
            "Example: 'Client posted a tight deadline; value speed and milestones.'"
        ),
    )
    rate_red_flags: list[str] = Field(
        default_factory=list,
        description=(
            "Rate-related risks or inconsistencies. Empty list if none. "
            "Unit: short string items. Example: ['Budget line may not cover QA']."
        ),
    )

    @model_validator(mode="after")
    def max_must_exceed_min(self) -> "RateAnalysis":
        if self.recommended_rate_max <= self.recommended_rate_min:
            raise ValueError(
                "recommended_rate_max must be greater than recommended_rate_min"
            )
        return self
