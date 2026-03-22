"""
Job Intelligence agent output — JobAnalysis.
See docs/specs/api-contract.md (job_analysis nested object).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from schemas.common import RedFlag


class JobAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_type_signals: list[str] = Field(
        default_factory=list,
        description=(
            "Observations about client type and buying style. List of strings; "
            "empty list if none. Unit: short phrases. Example: "
            "['First-time buyer', 'Budget-stated upfront']."
        ),
    )
    scope_clarity: Literal["clear", "ambiguous", "vague"] = Field(
        description=(
            "How clearly the job scope is defined. One of: clear, ambiguous, vague. "
            "Example: ambiguous."
        ),
    )
    scope_clarity_score: int = Field(
        ge=0,
        le=10,
        description=(
            "How clear the scope is. int 0-10 inclusive. Unit: score. "
            "10=crystal clear. Example: 6."
        ),
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description=(
            "Extracted required skills. Empty list if none stated. "
            "Unit: skill names as strings. Example: ['Python', 'BeautifulSoup']."
        ),
    )
    budget_signal: Literal["stated", "hinted", "absent"] = Field(
        description=(
            "Whether budget information appears. One of: stated, hinted, absent. "
            "Example: stated."
        ),
    )
    estimated_budget: str = Field(
        min_length=1,
        description=(
            "Human-readable budget estimate or unknown. Non-empty string. "
            "Unit: USD range text or 'unknown'. Example: '$500' or 'unknown'."
        ),
    )
    red_flags: list[RedFlag] = Field(
        default_factory=list,
        description=(
            "Structured red flags from the posting. Empty list if none. "
            "Unit: RedFlag objects."
        ),
    )
    project_complexity: Literal["simple", "moderate", "complex"] = Field(
        description=(
            "Estimated project complexity. One of: simple, moderate, complex. "
            "Example: simple."
        ),
    )
    ideal_candidate_summary: str = Field(
        min_length=1,
        description=(
            "One to two sentences describing the ideal hire. Non-empty string. "
            "Example: 'Strong Python scraper with e-commerce pricing experience.'"
        ),
    )
