# Clarity API truth table

This table maps common Clarity dashboard ideas to the export API fields used by `project-live-insights`.

Important: the export API is useful, but it is **not a guaranteed 1:1 replica of the Clarity dashboard cards**. Treat dashboard reconciliation as a separate task.

## Legend

- **Exact**: export API field appears to match the dashboard concept closely enough to report directly
- **Approximate**: export API likely measures a related concept, but not necessarily the same filtering, denominator, or UI calculation
- **Unavailable**: not reliably available from the current export endpoint / current script alone

## Truth table

| Dashboard metric / card | Export API field equivalent | Status | Notes |
|---|---|---:|---|
| Sessions | `Traffic.totalSessionCount` | Approximate | May not match dashboard cards exactly, especially when bot exclusion or card-specific filters are involved. |
| Bot sessions excluded | `Traffic.totalBotSessionCount` | Approximate | Related, but not proven to match dashboard exclusion logic exactly. |
| Unique users | `Traffic.distinctUserCount` | Approximate | Useful directional metric, but do not assume exact parity with dashboard “Users overview”. |
| Pages per session | `Traffic.pagesPerSessionPercentage` | Approximate | Likely close, but name and calculation semantics are API-specific. |
| Scroll depth | `ScrollDepth.averageScrollDepth` | Exact-ish | Good direct metric for reporting, but still label as export API output. |
| Active time spent | `EngagementTime.activeTime` | Approximate | Good for trend use. Dashboard may present it with different formatting or scope. |
| Total time spent | `EngagementTime.totalTime` | Approximate | Same caution as above. |
| Rage clicks | `RageClickCount.*` | Exact-ish | Good friction signal from export API. |
| Dead clicks | `DeadClickCount.*` | Exact-ish | Good friction signal from export API. |
| Excessive scrolling | `ExcessiveScroll.*` | Exact-ish | Good friction signal from export API. |
| Quick backs | `QuickbackClick.*` | Exact-ish | Good friction signal from export API. |
| Script errors | `ScriptErrorCount.*` | Exact-ish | Good technical friction signal from export API. |
| Error clicks | `ErrorClickCount.*` | Exact-ish | Good export metric when available. |
| Browser split | `Browser` | Exact-ish | Good for segmentation/trend analysis. |
| Device split | `Device` | Exact-ish | Good for segmentation/trend analysis. |
| OS split | `OS` | Exact-ish | Good for segmentation/trend analysis. |
| Country split | `Country` | Exact-ish | Good for segmentation/trend analysis. |
| Page title leaders | `PageTitle` | Exact-ish | Good for quick inspection, but page URL is usually better. |
| Top pages | `PopularPages` | Exact-ish | One of the most useful export fields. |
| Referrers | `ReferrerUrl` | Exact-ish | Useful for source quality checks. |
| Landing pages | Not clearly exposed in current script | Unavailable | May require different dimensions/endpoint support beyond current usage. |
| New users sessions | Not clearly exposed in current script | Unavailable | Dashboard concept not mapped in current export usage. |
| Returning users sessions | Not clearly exposed in current script | Unavailable | Dashboard concept not mapped in current export usage. |
| Live users | Not available from this export endpoint | Unavailable | This is a dashboard/live product concept, not a historical export metric here. |
| User intent | Not available from this export endpoint | Unavailable | No current export mapping in the skill/script. |
| Top user / user replay style cards | Not available from this export endpoint | Unavailable | Outside current aggregate export scope. |

## Safe reporting rule

When using the export API, prefer language like:
- "Export API reports..."
- "API aggregate suggests..."
- "Approximate equivalent of the dashboard metric..."

Avoid language like:
- "This exactly matches the dashboard"
- "Clarity says yesterday was X" unless you independently confirmed parity.
