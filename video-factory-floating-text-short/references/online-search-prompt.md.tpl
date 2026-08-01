# Recurring content search prompt — {{THEME}}

Generated: {{DATE}}. Designed to be invoked by `$schedule` or `$loop`.

## Goal

Produce **N new on-theme content items** that fit the three-line floating-text template and append them to `payload.json` as `status: "pending"` entries.

## Inputs (fill these in)

- Theme: `{{THEME}}`
- Target audience: `<FILL>`
- Search keywords (comma-separated): `<FILL>`
- Series coherence notes (what makes items belong to the same series, what to avoid): `<FILL>`
- Line 1 template: `<FILL>`
- Line 2 template: `<FILL>`
- Line 3 template: `<FILL>`
- Working folder: `<FILL — e.g. ~/runs/{{THEME}}>`
- Batch size N: `5`

## 🔎 Strong default — live web verification

The default behavior of this prompt is to back every payload row with a **live web-research pass for that specific item**. The model's training data is stale and silently wrong about spelling, accents, dates, and attributions — one wrong character is a public mistake.

**Recommended mechanism:** spawn a subagent (`$Agent` with `subagent_type: "general-purpose"`, or `$Explore` for lighter lookups) briefed to verify every line of every row against **≥ 2 independent reputable sources** via `$WebSearch` + `$WebFetch`. The subagent returns a fully-verified batch which the orchestrator appends to `payload.json`.

**If the user opts out** (low-stakes themes, prototyping, drafts), that's a valid choice — record it in `video-template.md` so it's not re-litigated. If you're unsure whether verification is wanted, ask once via `AskUserQuestion` and remember the answer for the rest of the session. Don't unilaterally bypass and don't unilaterally enforce.

### Subagent invocation template

```
Agent({
  description: "Verify <N> on-theme rows for {{THEME}}",
  subagent_type: "general-purpose",
  prompt: "You are extending the {{THEME}} short-video series. Produce <N>
    new payload rows. Per row you MUST:
    1. Use WebSearch to find ≥ 2 independent reputable sources (cite URLs).
    2. Use WebFetch to read each source — never rely on snippets alone.
    3. Confirm exact spelling, accents, capitalization, and meaning.
    4. If sources disagree or you cannot find 2 → drop the candidate.
    5. Return a JSON array of fully-verified rows matching payload.json schema.
    Do NOT use prior knowledge as a substitute for a live source. Report any
    row you dropped and why. Under 800 words of prose; the JSON is the deliverable."
})
```

## Prompt body (give this to the subagent)

You are extending the `{{THEME}}` short-video series. Your job: research the web for fresh, **specific** content matching the search keywords above, and turn each finding into a single payload row.

Use, in this order — **web tools always come first, never as a fallback**:

1. `$WebSearch` + `$WebFetch` — **primary tools.** Required for spelling, accent, definition, attribution, and fact verification on every row. Cite ≥ 2 independent reputable sources per row (e.g. Larousse + Le Robert for French; Merriam-Webster + OED for English; Britannica + a primary source for facts).
2. `$apify-trend-analysis` — surface what is currently trending around the keywords. Skip evergreen junk if a fresher angle exists.
3. `$apify-content-analytics` and `$apify-competitor-intelligence` — see what the best creators in this space already published. **Avoid duplicates** by reading existing entries in `<working-folder>/payload.json` first.
4. `$mcp__plugin_context7_context7__query-docs` — only if the theme is a software library / API.

For each new content item:

- Slugify the title → `<series-slug>-part-<NNN>-<title-slug>` (zero-pad N to 3 digits; N = next available counter).
- Fit line 1 with the recurring hook (insert counter).
- Fit line 2 as the subject title — must obey the alphabet char limit (Latin: 28).
- Fit line 3 as a single sentence detail. If it does not wrap to ≤ 2 visual lines at the char limit, **rewrite it shorter, don't ship overflow**.
- Pick a `background_video` from `<working-folder>/clips/90s/` — round-robin or random; do not reuse the same clip twice in a row.
- Set `music: null` unless the user has approved a track in `<working-folder>/music/`.
- Set `filters: []` unless this specific entry needs a `$video-filter` look.
- Append the row to `<working-folder>/payload.json` with `status: "pending"`.

**Coherence guard:** every new item must read as part of the same series as existing ones. If a candidate would feel off-brand to the target audience, drop it and find another.

## After the prompt runs

The render step (`scripts/render-from-payload.py` in `$video-factory-floating-text-short`) will pick up the new `pending` entries and produce the actual MP4s.

## Scheduling

Wire this prompt as a cron with `$schedule` (e.g. daily 09:00) or run it on demand with `$loop`. Each invocation should be idempotent — re-running it should never produce duplicate rows.
