---
name: clarity-api-seo
description: Use Microsoft Clarity Data Export API to turn website behavioral analytics into actionable SEO and UX recommendations. Trigger when the user wants Clarity-based analysis for a site or project, including most visited pages, trend evolution by day or week, traffic sources, engaged pages, dead clicks, rage clicks, quick backs, JavaScript errors, scroll depth, device/country splits, or prioritized fixes that can improve search performance, landing page quality, and conversion paths.
---

# Clarity API SEO

Use this skill to pull Microsoft Clarity export analytics and convert them into a concise, useful website improvement report.

## Outcome

Produce actionable findings, not raw metric dumps. Prioritize pages and patterns that can improve:

Important: this skill uses the **Clarity export API**, not the dashboard UI directly. Export metrics are useful, but they are **not guaranteed to be 1:1 with dashboard cards** such as live users, new vs returning users, or bot-excluded daily summary tiles.
- organic performance and landing-page quality
- engagement and time on page
- UX friction that hurts conversion or retention
- technical issues that suggest broken experiences
- source quality and content opportunities

## Secrets and environment rules

Never read `.env`, `.env.local`, or any env file with real values.
Read `.env.example` only to confirm variable names when needed.
At execution time, load the project env into the shell and reference the key by name only:

```bash
set -a; . .env; set +a
```

Assume the Clarity API key variable is:

```bash
CLARITY_API_KEY
```

If the project also stores a Clarity project id or site id, inspect `.env.example` for likely names such as `CLARITY_PROJECT_ID`, `MICROSOFT_CLARITY_PROJECT_ID`, or similar. If no project identifier exists, ask the user for it.

## Workflow

1. Read `references/metrics-and-analysis.md` before building the report logic.
2. Read `references/truth-table.md` before claiming equivalence with dashboard metrics.
3. Use `scripts/clarity_export.py` to call the Clarity API.
4. Pull at least two comparison windows when possible:
   - recent 7 days
   - prior 7 days
   - recent 28 days
   - prior 28 days
5. Save raw JSON exports locally when useful for auditing.
6. Produce a ranked summary with:
   - biggest wins
   - biggest problems
   - page-level opportunities
   - source/channel insights
   - trend changes versus prior period
   - recommended next fixes

## Minimum analysis checklist

Cover these whenever the API data supports them:
- most visited pages
- pages with strongest engagement or longest time spent
- pages with weak engagement despite high traffic
- entry pages and landing pages worth improving for SEO intent
- traffic source quality and top referring patterns
- dead clicks, rage clicks, excessive quick backs, and error-heavy pages
- mobile versus desktop differences
- country or region differences when meaningful
- changes over day and week windows
- anomalies or sudden drops/spikes

## Reporting rules

Write a compact report with these sections:
1. Executive summary
2. Traffic and engagement trends
3. Top pages to protect and expand
4. Pages to fix first
5. Source/referrer insights
6. Technical and UX friction
7. Next actions ranked by impact and effort

Always translate metrics into recommendations.

Also explicitly label whether a reported number is:
- export API direct
- approximate dashboard equivalent
- unavailable from current export endpoint

Example:
- “Page /pricing has high traffic and high quick backs” → tighten message match, improve speed, and test clearer CTA hierarchy.
- “Blog posts from source X drive long engagement” → create adjacent content and improve internal links to money pages.
- “Dead clicks cluster on mobile nav” → fix tap targets or misleading visual affordances.

## Scripts

- `scripts/clarity_export.py`
  - Fetches Clarity aggregate metrics for configurable dimensions and date windows.
  - Supports JSON output for downstream analysis.

## References

- `references/metrics-and-analysis.md`
  - Maps Clarity metrics to SEO, UX, and CRO decisions.
- `references/api-notes.md`
  - Notes about expected API usage, assumptions, and extension points.
- `references/truth-table.md`
  - Maps dashboard ideas to export API equivalents and confidence levels.
- `references/weekly-commands.md`
  - Small weekly command cookbook for the most useful recurring pulls.

## Implementation notes

Prefer a few broad API pulls over many tiny requests.
Compare each finding against a baseline period when possible.
Call out confidence limits when a conclusion is based on partial Clarity coverage rather than direct SEO ranking data.
Do not claim ranking changes unless supported by external search-console style evidence.
Do not present export API totals as exact dashboard card values unless you independently verified parity for that metric.
