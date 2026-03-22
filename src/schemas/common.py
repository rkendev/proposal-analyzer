"""
Shared Pydantic models used across agent outputs and ProposalReport.
See docs/specs/api-contract.md for field definitions, types, and ranges.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RedFlag(BaseModel):
    model_config = ConfigDict(extra="forbid")

    flag: str = Field(
        min_length=1,
        description=(
            "Short label for the risk or concern. Non-empty string. "
            "Example: 'Budget may be below market for scope.'"
        ),
    )
    severity: Literal["low", "medium", "high"] = Field(
        description=(
            "Severity of the flag. One of: low, medium, high. "
            "Example: high for deal-breaker signals."
        ),
    )


class Weakness(BaseModel):
    model_config = ConfigDict(extra="forbid")

    weakness: str = Field(
        min_length=1,
        description=(
            "Description of the weakness in the proposal. Non-empty string. "
            "Example: 'Opening does not reference client product.'"
        ),
    )
    impact: Literal["low", "medium", "high"] = Field(
        description=(
            "Business impact if unaddressed. One of: low, medium, high. "
            "Example: high for likely rejection."
        ),
    )
    fix_suggestion: str = Field(
        min_length=1,
        description=(
            "Concrete fix the freelancer can apply. Non-empty string. "
            "Example: 'Lead with one sentence tying your work to their SKU catalog.'"
        ),
    )


class Improvement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    priority: int = Field(
        ge=1,
        le=3,
        description=(
            "Sort order for the improvement. int 1-3 inclusive (not 0-10). "
            "1=highest priority. Example: 1."
        ),
    )
    action: str = Field(
        min_length=1,
        description=(
            "Specific action to take. Non-empty string. "
            "Example: 'Add a one-line ROI hook in the opening.'"
        ),
    )
    expected_impact: str = Field(
        min_length=1,
        description=(
            "Expected outcome of the action. Non-empty string. "
            "Example: 'Stronger relevance signal in first 10 seconds of reading.'"
        ),
    )
