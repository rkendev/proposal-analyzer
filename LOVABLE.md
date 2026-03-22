# LOVABLE.md — Frontend Tool Protocol

This file exists because of Phase 8 failures in Project 1.
Read it before opening Lovable. Every rule here was learned
from a real production failure.

---

## The Two Things That Will Burn Credits If You Forget Them

**1. Preview ≠ Published.**
When Lovable rebuilds, it updates the Lovable internal preview
URL only. The public `.lovable.app` URL does NOT update until
you click the Publish button explicitly.
After every fix: click Publish → hard refresh → verify bundle
hash changed in DevTools Network tab.
If the bundle hash (e.g. index-AmCjBLme.js) has not changed,
nothing was deployed. Do not proceed.

**2. Lovable search only scans src/.**
It does not scan .env, vite.config.ts, project-level config,
or Lovable environment variable dashboard.
Never trust "no changes needed" when DevTools contradicts it.
Diagnose using DevTools and GitHub. Fix using Lovable chat.

---

## Before the First Lovable Prompt

1. Read docs/specs/api-contract.md completely.
2. Set VITE_API_BASE_URL in Lovable project settings (not code)
   to your Railway URL before writing a single component.
   Value: https://your-railway-url.up.railway.app
3. Reference it in code as import.meta.env.VITE_API_BASE_URL
   with NO fallback to a hardcoded IP or localhost.

---

## One Change Per Prompt — Non-Negotiable

Lovable batches poorly. Every prompt = exactly one change.
Never: "Fix the score display AND add the progress bar."
Always: two separate prompts.

---

## Debugging Protocol (in order, stop when fixed)

1. DevTools Network tab → reproduce the issue → read the error
2. Check JS bundle filename — did it change since last fix?
3. If wrong URL: search GitHub repo directly (not Lovable chat)
4. If CORS error: check FastAPI CORS middleware + ALLOWED_ORIGIN
5. Write one precise Lovable prompt: file + line + expected fix
6. After Lovable responds: click Publish
7. Hard refresh with Ctrl+Shift+R
8. Verify bundle hash changed
9. Verify request in Network tab goes to correct URL

---

## SSE Integration Pattern

After POST /analyze or POST /generate returns a job_id,
immediately open a Server-Sent Events connection:

```typescript
const es = new EventSource(
  `${import.meta.env.VITE_API_BASE_URL}/stream/${jobId}`
);

es.addEventListener("agent_complete", (e) => {
  const { agent, progress } = JSON.parse(e.data);
  setProgress(progress);      // 0, 25, 50, 75, 100
  setCurrentAgent(agent);     // show in loading UI
});

es.addEventListener("complete", (e) => {
  const report = JSON.parse(e.data);
  setReport(report);
  setMode("results");
  es.close();
});

es.addEventListener("error", () => {
  setError("Analysis failed. Please try again.");
  es.close();
});
```

Progress agent labels for UI display:
  job_intelligence  → "Analyzing job posting..."
  rate_intelligence → "Estimating market rates..."
  proposal_analyst  → "Evaluating your proposal..."
  win_strategy      → "Building win strategy..."

---

## Display Rules (from api-contract.md)

- All scores: X/10 format. Never as percentage.
- win_probability_score 0-3: red. 4-6: amber. 7-10: green.
- severity "high": red badge. "medium": amber. "low": grey.
- proposal_draft.proposal_text: always render with react-markdown.
  Install it explicitly: prompt "Install react-markdown and
  wrap all multi-line text fields with <ReactMarkdown>"
- overall_win_readiness_score: show in analyze mode only.
  Hide entirely in generate mode.
- recommended_rate_min/max: "$X,XXX – $X,XXX USD (hourly|fixed)"
- top_improvements: always show all 3, numbered 1-2-3.
- deal_breakers: show with ⚠️ icon per item.

---

## Phase 8 Acceptance Checklist

Phase 8 is NOT done until every item is manually verified
in the deployed published URL (not the Lovable preview):

[ ] VITE_API_BASE_URL set to Railway URL (not localhost)
[ ] POST /analyze returns job_id within 500ms (DevTools)
[ ] SSE stream emits progress events for each agent (DevTools)
[ ] Progress bar updates in real time during analysis
[ ] POST /generate returns job_id within 500ms (DevTools)
[ ] Full ProposalReport renders without raw schema field names
[ ] All scores display as X/10 (not %)
[ ] proposal_text renders as formatted markdown (not raw)
[ ] Rate displays as "$X,XXX – $X,XXX USD (type)"
[ ] deal_breakers show with ⚠️ icon
[ ] overall_win_readiness_score hidden in generate mode
[ ] Error state renders for 422 and 500 responses
[ ] Loading state shows cycling agent messages
[ ] /health ping fires on page load (check Network tab)
[ ] Ctrl+Shift+R shows new bundle hash vs previous build

---

## Known Lovable Limitations

- Session context degrades after ~15 prompts. Start a new
  Lovable session after every 10-12 prompts.
- Lovable TypeScript types are sometimes wrong. Verify
  rendered output against api-contract.md, not Lovable claims.
- react-markdown is not pre-installed. Prompt explicitly:
  "Install react-markdown and use it to render [field]"
- EventSource (SSE) requires explicit polyfill check for
  older browsers. Lovable may not add this automatically.
