---
name: launch-announcement
description: The reference library behind a product launch — what each place that actually sends users wants (Reddit, Hacker News, Product Hunt, Uneed and 107 launch directories), the per-platform copy templates, and who said what. To plan and run a launch, use gtm-shiplist, which reads this library. Use for a platform's rules, timing or format, a launch copy template (Product Hunt, Show HN, Reddit, directory listing), the directory list, "where should I launch" or "write my Product Hunt post".
---

# launch-announcement

The first users don't come from your own audience. They come from platforms where
nobody knows who you are and it doesn't matter.

This skill is the reference: what each platform wants and the copy templates. To
plan and run a launch, use `gtm-shiplist`; it and the other `gtm-*` skills named here
are in [benyki/gtm-engine](https://github.com/benyki/gtm-engine). The agent writes; the user submits. Nothing is posted
automatically — every platform on this list bans accounts for automated submission,
and a banned account on launch day costs more than the launch was worth.

**How (not just what):**

| Step | Reference |
|---|---|
| Which platform, what it wants, what goes wrong | `references/platforms.md` |
| Reddit — subreddits, rules, the self-promo trap | `references/reddit.md` |
| The long tail: 107 directories, a ranked worklist, and 27 more from a 50-list | `references/directories.md` |
| Copy templates: Product Hunt, Show HN, Reddit post, directory listing | `templates/` |
| Who said what, and how much to trust it | `references/sources.md` |
| Authors to credit and follow | `CREDITS.md` |

---

## The correction that comes first

If the user's plan is "launch on my X account," stop and say this:

> Launching your startup on a new Twitter account will flop.
> — [@marclou](https://x.com/marclou/status/1933506642051805518)

A new account has no distribution. Ranking on Product Hunt or hitting the front
page of Hacker News does not care how many followers you have. So the order is:

1. **Launch** where follower count is irrelevant — HN, Reddit, Product Hunt, Uneed, TinyLaunch, TAAFT
2. **Then** post the result to X/LinkedIn — "we hit #1 on Uneed" is content; "check out my app" is not
3. **Then** use the audience that built for the *next* launch

Winning is how you get the audience, not the other way round. This also means a
launch is not a one-shot: the same product can be relaunched every few weeks with
a different angle (`gtm-shiplist` writes the relaunch date down; the source is in `references/sources.md`).

---

## The run

To plan and run a launch, use `gtm-shiplist`.

---

## Rules

- **Never auto-submit.** Every platform here treats scripted submission as spam. The user pastes, always
- **Never ask for upvotes.** Product Hunt de-ranks it and Hacker News bans for it. This is not a grey area
- **One subreddit on day one.** Cross-posting the same text to eight subreddits is the fastest way to a sitewide Reddit ban — see `references/reddit.md`
- **Never submit to a platform you haven't read the rules page of that week.** These sites change their submission terms constantly and half the advice online is stale
- **Don't fake the launch.** No sockpuppet accounts, no bought upvotes, no "we're a team of 12" when it's one person. It gets found and the post becomes the story
- **A launch is not a growth strategy.** It's a spike. What happens on day 4 is the actual product question — hand back to `gtm-seo`, `gtm-social` or `gtm-outreach` for that

## Going further

- `gtm-shiplist` — plan and run the launch day, then close it with the numbers and a relaunch date
- `gtm-social` — turn the result ("#1 on Uneed") into the posts that build the audience
- `gtm-seo` — the AlternativeTo / OpenAlternative listings in `references/directories.md` are evergreen search surface, not launch-day traffic

---

## Credits

This skill is a synthesis of other people's launches, not original research. The
rankings, the directory lists and the ordering principle come from:

| Author | Contributed |
|---|---|
| [@Neerajscript](https://x.com/Neerajscript) | [The subreddit seed list](https://x.com/Neerajscript/status/2005520668000145645) |
| [@eliana_jordan](https://x.com/eliana_jordan) | [Six platforms rated by what actually happened](https://x.com/eliana_jordan/status/1944348597648244850) — the `[E]` notes |
| [@hridoyreh](https://x.com/hridoyreh) | [All 107 directories](https://x.com/hridoyreh/status/2036816122096533589) |
| [@Hartdrawss](https://x.com/Hartdrawss) | [The weighted worklist](https://x.com/Hartdrawss/status/2020430122562531608) the tier structure is built on |
| [@marclou](https://x.com/marclou) | [The ordering principle](https://x.com/marclou/status/1933506642051805518), and TAAFT |
| [@hthieblot](https://x.com/hthieblot) | [Relaunch cadence](https://x.com/hthieblot/status/1937561367604846802) — a launch is repeatable |

Plus sharp details from people in their replies —
[@chrissyinspace](https://x.com/chrissyinspace) on the TinyLaunch backlink trap,
[@MarkZofMarkZ](https://x.com/MarkZofMarkZ),
[@jmqcooper](https://x.com/jmqcooper),
[@rcwhiteley](https://x.com/rcwhiteley),
[@anshrathodfr](https://x.com/anshrathodfr),
[@askOkara](https://x.com/askOkara).

Full attribution and what each one contributed where: **`CREDITS.md`**.

When you quote a platform verdict to a user — "Uneed brought real leads",
"TinyLaunch's backlink never came" — **name whose launch it was**. It's one
person's experience, and saying so is both fair to them and more honest about how
much the user should bet on it.
