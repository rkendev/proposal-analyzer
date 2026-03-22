# API Contract — Freelance Proposal Analyzer

Single source of truth for the backend-frontend boundary.
Both Pydantic schemas (Python) and TypeScript interfaces
(Lovable) are derived from this document.

Any change to a field name, type, range, or unit requires:
  1. Update this document first
  2. Update the Pydantic schema
  3. Update the TypeScript interface in Lovable
Never change one without the others.

---

## Request Bodies

### AnalyzeRequest
```
job_posting:     string   required, min 50 chars
proposal_draft:  string   required, min 50 chars
mode:            "analyze"
```

### GenerateRequest
```
job_posting:     string   required, min 50 chars
mode:            "generate"
```

---

## Response: ProposalReport

FIELD UNIT RULES (no ambiguity permitted):
  - All scores:   int,   0 to 10 inclusive
  - All rates:    float, USD, > 0
  - All lists:    array, never null — empty array if nothing
  - All strings:  non-empty string — "N/A" if not applicable
  - All booleans: true or false, never null

```typescript
interface ProposalReport {
  mode:   "analyze" | "generate"
  job_id: string

  job_analysis: {
    client_type_signals:     string[]   // 1-5 observations
    scope_clarity:           "clear" | "ambiguous" | "vague"
    scope_clarity_score:     number     // int, 0-10
    required_skills:         string[]   // extracted skill names
    budget_signal:           "stated" | "hinted" | "absent"
    estimated_budget:        string     // "$2,000-5,000" or "unknown"
    red_flags:               RedFlag[]
    project_complexity:      "simple" | "moderate" | "complex"
    ideal_candidate_summary: string     // 1-2 sentences
  }

  rate_analysis: {
    recommended_rate_min:      number   // float, USD, > 0
    recommended_rate_max:      number   // float, > recommended_rate_min
    rate_currency:             "USD"    // always USD at v1
    rate_type:                 "hourly" | "fixed"
    rate_justification:        string   // prose, for use in proposal
    current_rate_assessment:   "underpriced" | "fair" | "overpriced"
                               | "not_applicable"
    assessment_explanation:    string
    negotiation_leverage:      string
    rate_red_flags:            string[]
  }

  // ANALYZE MODE ONLY — null in generate mode
  proposal_critique: ProposalCritique | null

  // GENERATE MODE ONLY — null in analyze mode
  proposal_draft: ProposalDraft | null

  win_strategy: {
    win_probability:       "low" | "medium" | "high"
    win_probability_score: number     // int, 0-10
    competing_profiles:    string[]   // 1-3 items
    differentiation_angle: string
    top_improvements:      Improvement[]  // exactly 3 items
    deal_breakers:         string[]
    one_line_positioning:  string
  }

  // ANALYZE MODE ONLY — null in generate mode
  overall_win_readiness_score: number | null  // int, 0-10
}

interface RedFlag {
  flag:     string
  severity: "low" | "medium" | "high"
}

interface ProposalCritique {
  overall_score:         number     // int, 0-10
  critical_weaknesses:   Weakness[]
  missing_elements:      string[]
  tone_score:            number     // int, 0-10
  tone_issues:           string[]
  opening_hook_score:    number     // int, 0-10
  cta_strength_score:    number     // int, 0-10
  personalization_score: number     // int, 0-10
  rewritten_opening:     string     // improved first paragraph
}

interface ProposalDraft {
  proposal_text:          string    // full proposal, markdown format
  word_count:             number    // int, > 0
  key_differentiators:    string[]  // 1-5 items
  rate_argument_included: boolean
}

interface Weakness {
  weakness:       string
  impact:         "low" | "medium" | "high"
  fix_suggestion: string
}

interface Improvement {
  priority:        number   // int, 1, 2, or 3
  action:          string
  expected_impact: string
}
```

---

## Display Rules (Lovable must follow exactly)

| Field                       | Display Format                              |
|-----------------------------|---------------------------------------------|
| Any score (int 0-10)        | "X/10" — NEVER as percentage                |
| win_probability_score 0-3   | Red badge                                   |
| win_probability_score 4-6   | Amber badge                                 |
| win_probability_score 7-10  | Green badge                                 |
| severity "high"             | Red badge                                   |
| severity "medium"           | Amber badge                                 |
| severity "low"              | Grey badge                                  |
| proposal_text               | Render with react-markdown, never raw text  |
| rate_min / rate_max         | "$X,XXX – $X,XXX USD (hourly)" or "(fixed)" |
| top_improvements            | Show all 3, numbered 1-2-3, sorted by priority |
| deal_breakers               | Each item prefixed with ⚠️ icon             |
| overall_win_readiness_score | Show in analyze mode ONLY. Hide in generate |
| proposal_critique           | Show in analyze mode ONLY. null in generate |
| proposal_draft              | Show in generate mode ONLY. null in analyze |
