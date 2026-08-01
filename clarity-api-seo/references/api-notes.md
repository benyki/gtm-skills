# API notes

Source docs:
- https://learn.microsoft.com/en-us/clarity/setup-and-installation/clarity-data-export-api

## Intended use

Use the export API to retrieve aggregated analytics across configurable date windows and dimensions, then summarize that data into SEO and UX opportunities.

This endpoint should be treated as an **aggregate export surface**, not as a guaranteed replica of the Clarity dashboard UI cards.

## Assumptions

Because Clarity API capabilities may evolve, keep the implementation tolerant:
- accept explicit start and end dates
- accept project id from argument or env var
- accept metric and dimension selections from CLI flags
- return raw JSON unchanged by default
- allow a thin analysis layer to be built on top later

## Environment

Expected env var for auth:
- `CLARITY_API_KEY`

Optional project identifier env vars to check in `.env.example`:
- `CLARITY_PROJECT_ID`
- `MICROSOFT_CLARITY_PROJECT_ID`
- `CLARITY_SITE_ID`

## Practical strategy

Prefer a small set of high-value pulls:
1. top pages for recent 7 days
2. top pages for prior 7 days
3. top sources for recent 7 days
4. top friction signals by page for recent 7 days
5. top pages for recent 28 days
6. top pages for prior 28 days

## Dashboard parity warning

Do not assume these dashboard ideas are directly reconstructible from the current export endpoint alone:
- live users
- new vs returning users cards
- user intent card
- top user card
- exact bot-excluded daily dashboard numbers

Some export metrics are close approximations, but parity must be validated metric by metric.

See also:
- `truth-table.md`
- `weekly-commands.md`

## Future extensions

Potential follow-up improvements:
- generate markdown report automatically from raw JSON
- support batch project analysis
- enrich with Google Search Console or Lighthouse data
- save CSV summaries for spreadsheet workflows
