# Credits

`prospect-finder` was written by adapting ideas from several open-source sales
and GTM skill libraries, then generalising them: away from specific vendors,
away from email-only outreach, and toward a single job — *produce a list where
every row carries a reason to write to that person*.

The text here is original. What was borrowed is **structure and judgement** —
the distinctions, the checks, and the numbers that only come from running real
campaigns. Thanks to the authors of all of these; their repos are worth reading
in full, and cover a great deal this skill deliberately doesn't.

---

## [growthenginenowoslawski/coldoutboundskills](https://github.com/growthenginenowoslawski/coldoutboundskills) — MIT

Open-source Claude Code skills for cold email and outbound, built from patterns
across 1,000+ real B2B campaigns.

Adapted here:

- **The person-first vs company-first distinction** — that "find everyone with
  title X" and "find the owner of each of these 500 domains" are different
  searches needing different sources. From
  [`skills/blitz-list-builder`](https://github.com/growthenginenowoslawski/coldoutboundskills/tree/main/skills/blitz-list-builder),
  generalised away from any specific vendor
  (`SKILL.md` §2, `references/sources.md`)
- **Hit-rate expectations by segment** — the contact-found benchmarks that let a
  thin result be diagnosed instead of assumed. Same skill, restated as ranges
  (`SKILL.md` → *What "good" looks like*)
- **Qualify a sample before scaling**, and the observation that unfiltered
  engagement-based lists run 30–50% off-ICP. From
  [`skills/competitor-engagers`](https://github.com/growthenginenowoslawski/coldoutboundskills/tree/main/skills/competitor-engagers)
  (`SKILL.md` §5)
- **The compliance checklist shape** — the practical "what a compliant cold email
  needs" list, and the not-legal-advice framing. From
  [`skills/cold-email-starter-kit/references/11-legal-compliance.md`](https://github.com/growthenginenowoslawski/coldoutboundskills/tree/main/skills/cold-email-starter-kit/references)
  (`references/compliance.md`)

## [gtmagents/gtm-agents](https://github.com/gtmagents/gtm-agents) — Apache-2.0

A large collection of GTM agents and skills for Claude Code, covering sales,
outbound, prospecting and RevOps.

Adapted here:

- **The research mindset** — "not their role and company size so I can fill the
  template, but what is happening in their world right now" — which is the
  premise this whole skill is built on
- **"Define your perfect signal" before searching**, as a fill-in-the-blank
  sentence that becomes the filter (`SKILL.md` §1)
- **The signal-freshness table** — how long each kind of signal stays usable
  (`references/signals.md`)
- **The "so what?" test** for rejecting facts that aren't signals
  (`references/signals.md`)
- **Tiered research with a per-person time budget**, restated around what's
  observable rather than around specific tools (`references/signals.md`)

All four from
[`plugins/copywriting/skills/cold-email-personalization/assets/research-playbook.md`](https://github.com/gtmagents/gtm-agents/tree/main/plugins/copywriting/skills/cold-email-personalization/assets).

---

## Also read while designing this

Not directly adapted, but useful context on how others scope the problem:

- [gtm-skills/gtm](https://github.com/gtm-skills/gtm) — MIT. A GTM toolkit
  (browser extension + MCP server) rather than a skill library; a good example of
  the tool-integrated approach this skill deliberately avoids
- [louisblythe/Sales-Skills](https://github.com/louisblythe/Sales-Skills) —
  discovery, qualification and sales-process skills. **No license file at the
  time of writing**, so nothing was taken from it
- [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills)
  — MIT. Marketing rather than prospecting, but the reference for how a
  skill library of this kind is organised

## What this skill deliberately does not do

The repos above go much further — sequencing, deliverability, inbox warmup,
campaign grading, CRM sync, sending platforms. `prospect-finder` stops at the
list on purpose: writing and sending belong to whatever outreach workflow
consumes it, and the list is the part that decides whether any of that is worth
doing.

If you need the rest, install one of the libraries above rather than growing
this one.
