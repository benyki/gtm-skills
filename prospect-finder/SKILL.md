---
name: prospect-finder
description: Find N real people matching a description — on any platform, with or without paid tools — each carrying one specific, recent observable you can open a message with, deduplicated against a CRM you already have. Platform-agnostic and vendor-neutral: LinkedIn, TikTok, GitHub, Reddit, job boards, directories, Google Maps, or a paid database if one is already available. Use when someone says "find me leads", "build a prospect list", "find creators for outreach", "who should I contact", "scrape a list of companies", or hands over an ICP and asks who fits.
---

# prospect-finder

Builds the list. Not the email, not the sequence — the list, and the one thing
per person that makes an email worth sending.

**The list decides more than the copy does.** A good message to the wrong 200
people loses to an average message to the right 20, and no amount of A/B testing
rescues a bad list; it just measures it precisely. So this skill spends its
effort on *who* and on *why each person is worth writing to*, and stops there.

Credits and what was adapted from whom: `CREDITS.md`.

| Step | Reference |
|---|---|
| Finding a signal per person | `references/signals.md` |
| Where to search, per platform | `references/sources.md` |
| Consent, opt-out, data rules | `references/compliance.md` |

## The output contract

One CSV, one row per person, and every row carries an **observable**:

```csv
name,company,role,contact,contact_type,profile_url,source,observable,observed_at
```

| Column | Rule |
|---|---|
| `contact` / `contact_type` | email, LinkedIn URL, platform handle — whatever route you actually have |
| `profile_url` | where you found them, so the next agent can verify instead of re-researching |
| `source` | the search or list this came from. Later you compare reply rate **by source**, which usually moves the number more than copy does |
| `observable` | one specific, recent, real thing about them. **A row without one is not a lead** |
| `observed_at` | when that thing happened, not when you found it — signals go stale (`references/signals.md`) |

If the caller has a CRM, that's the target shape instead — map into it and keep
these fields as columns. Never invent a column-free "notes" blob.

## The run

### 1. Get the description sharp enough to search

You cannot search for "founders" or "businesses". Push until the answer names a
person you could picture:

- **Who** — role or the behaviour that stands in for a role
- **Where** — platform, geography, industry, company size
- **What they did recently** — the thing that makes them worth contacting *now*
- **How many** — and by when

Then write the campaign's target signal as one sentence, before searching:

> *"The ideal prospect shows evidence of __________, because it means they're
> dealing with __________ right now."*

That sentence is the filter. Everything below is just executing it. *(This
framing is adapted from gtm-agents' research playbook — see `CREDITS.md`.)*

### 2. Pick the search shape

Two shapes, and they need different sources:

| You have | Shape | Search |
|---|---|---|
| A description of **people** ("heads of growth at Series A SaaS") | **person-first** | platform people-search, a database, a community's member list |
| A list of **companies or accounts** ("these 300 domains", "these 50 competitors' customers") | **company-first** | find the right person at each one |

Both are valid; most real campaigns start person-first and use company-first to
add a second contact at the same accounts. *(Distinction adapted from the
cold-outbound skills — `CREDITS.md`.)* Sources for each: `references/sources.md`.

### 3. Hand-build ten before you build two hundred

Take **ten** and research each for a minute. Then count how many yielded a real
observable:

| Yield | What it means |
|---|---|
| 8–10 | the filter works — scale this source |
| 4–7 | the filter is close; tighten one dimension and re-test |
| 0–3 | **the source or the description is wrong.** More volume just produces more filler |

This is the cheapest hour in the whole workflow, and skipping it is how people
end up with 500 rows and no way to open any of them. It also teaches you which
titles are decoys and which company sizes never answer — knowledge no scraper
gives you.

### 4. Scale the source that passed

Only now reach for tooling, and only as much as the volume needs:
`references/sources.md` covers the free path (browser + platform search), the
scraping path, and the paid-database path, in that order. Nothing here requires
a paid tool; every method degrades gracefully to "a person searching carefully".

Cap what you collect: name, company, one contact route, one observable, the
source URL. A row with forty enrichment fields is a row nobody reads.

### 5. Qualify the batch before spending anything on it

Lists built from engagement, follows, or broad platform search run **30–50%
off-ICP** — peers, candidates, students, competitors, fans. Before enriching,
emailing or importing:

- Sample 50 rows and check each against the description from step 1
- If more than a fifth fail, fix the filter and re-pull rather than hand-cleaning
- Only then enrich or import the whole set

*(This check, and the 30–50% figure, come from the competitor-engagers skill —
`CREDITS.md`.)*

### 6. Dedupe against what already exists

Before the list is handed anywhere:

- **Dedupe internally** on contact, then profile URL, then name + company
- **Dedupe against the CRM.** Anyone already contacted is removed — not
  re-contacted, not "refreshed". This is the one silent, expensive mistake this
  skill can make, and nobody notices until the recipient does
- **Anyone marked closed / unsubscribed / not-interested stays out permanently**,
  including on a fresh import months later

### 7. Hand over with the honest numbers

Report: how many were found, how many survived qualification, how many had an
observable, which source each came from, and what you'd change about the filter.
A list handed over without its hit rate is a list nobody can improve.

## What "good" looks like

Expect roughly these contact-found rates, so a thin result is diagnosed rather
than assumed:

| Segment | Person found | Contact route found |
|---|---|---|
| Small local businesses | 70–80% | 40–60% |
| Small/mid tech companies | 80–90% | 50–70% |
| Large companies | 90%+ | high — but picking the *right* person matters more than finding one |
| Solo operators, micro-businesses, creators | 30–50% | often no public route at all |

*(Benchmarks adapted from the cold-outbound list-building skills — `CREDITS.md`.)*

For creators and solo operators specifically, the contact route is often a DM or
a link-in-bio form rather than an email. That's a normal outcome, not a failed
search — record the route you actually have in `contact_type`.

## Rules

- **A row without an observable is not a lead.** Drop it or leave the person out.
  Filler personalisation is worse than none: it reads as automated *and* lazy
- **Never invent a fact about a person.** If the research is thin, say so. A
  made-up detail in a cold message is unrecoverable
- **Never re-contact someone already in the CRM.** Check before every handover
- **Respect the platform and the person** — public profile data is one thing, a
  login-walled page or a private group is another, and the account risk lands on
  the user. `references/compliance.md`
- **Honour opt-outs permanently**, across every future list and campaign
- **This skill never sends anything.** It produces a list; a human decides what
  happens to it

## Credits

Adapted, with thanks, from several open-source sales skill libraries — see
[`CREDITS.md`](CREDITS.md) for what came from where.
