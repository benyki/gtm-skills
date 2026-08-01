---
name: launch-announcement
description: Plans and writes a product launch across the places that actually send users — Reddit, Hacker News, Product Hunt, Uneed and the long tail of launch directories — with per-platform copy, a submission order, and a run logged back to gtm-engine. Use when the user says "launch my product", "where should I launch", "write my Product Hunt post", "Show HN", "submit to directories", "launch announcement", or has just shipped something and has no users yet.
---

# launch-announcement

The first users don't come from your own audience. They come from platforms where
nobody knows who you are and it doesn't matter.

This skill turns "I shipped something" into a dated submission plan plus the actual
copy for each destination. It writes; the user submits. Nothing is posted
automatically — every platform on this list bans accounts for automated submission,
and a banned account on launch day costs more than the launch was worth.

**How (not just what):**

| Step | Reference |
|---|---|
| Which platform, what it wants, what goes wrong | `references/platforms.md` |
| Reddit — subreddits, rules, the self-promo trap | `references/reddit.md` |
| The long tail: 107 directories + a ranked worklist | `references/directories.md` |
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
a different angle (see `engine-loop`, and the related source in `references/sources.md`).

---

## The run

### 1. Read the product

From the gtm-engine workspace when there is one:

- `shared/brand.md` — who it's for, the voice, banned words and claims
- `shared/channels.json` — where they already post
- the repo itself — README, landing copy, pricing

If there's no workspace, ask for three things and don't start without them: **what
it does in one sentence**, **who it's for**, and **what the user does in the first
60 seconds**. Every piece of launch copy below is derived from those three.

### 2. Decide the shape of the launch

Ask which one this is — it changes the platform set entirely:

| Shape | Goes to |
|---|---|
| Pre-launch / waitlist | BetaList, r/SideProject, Peerlist — not Product Hunt |
| Public v1, dev tool | Hacker News, DevHunt, Reddit, Product Hunt |
| Public v1, AI product | TAAFT, Uneed, Product Hunt, the AI directories |
| Public v1, consumer app | Product Hunt, Reddit, Uneed, TikTok/Reels via `engine-video` |
| Paid tool wanting cash today | Uneed, AppSumo and the lifetime-deal tier — read the warning in `references/platforms.md` |

### 3. Build the submission calendar

Never submit everywhere on the same day. One flagship, then the tail:

- **Day 0 (Tue–Thu)** — the one platform you're optimising for. Everything else waits
- **Day 0 + 2h** — Reddit, one subreddit only, written for that subreddit
- **Day 1–3** — the tier-2 platforms with real audiences (Uneed, Fazier, DevHunt, Indie Hackers)
- **Week 2+** — the directory tail, batched. These are backlinks, not traffic

Pick Day 0 from `references/platforms.md` — Product Hunt and Hacker News have
specific hours that matter and they conflict with each other.

### 4. Write the copy

One file per destination, in the user's voice, following that platform's format.
Templates are in `templates/`. The rules that apply everywhere:

- **Every platform gets its own copy.** The same paragraph pasted into HN, Reddit and Product Hunt fails on at least two of them. HN wants no marketing language at all; Reddit wants a story with the link buried; Product Hunt wants a benefit in 60 characters
- **Lead with what it does, not why you built it.** The founder story goes in the first comment, not the post
- **Name the price.** "Free tier + $9/mo" beats "affordable pricing" everywhere
- **Say what it doesn't do.** On HN and Reddit this reads as honesty and buys you the benefit of the doubt in the comments

Run the draft through `no-ai-slop-writting` before showing it. Launch copy is the
single most obvious place AI phrasing gets spotted, and on Reddit and HN getting
spotted is fatal.

### 5. Prepare the comment replies

More launches die in the comments than in the post. Before Day 0, write:

- The maker's first comment for each platform (what you built, why, what's next)
- Answers to the three hardest questions — usually *why not just use X*, *what's your moat*, and *is this just a wrapper*
- The pricing answer, in one sentence, with no hedging

### 6. Log it

```bash
python3 ~/.agents/skills/engine-loop/scripts/runlog.py new --workflow social --channel launch \
  --experiment exp-launch --arm default --template product-hunt.md
```

Write each piece of copy to `runs/<run_id>/output/`, one file per platform. After
submitting:

```bash
python3 ~/.agents/skills/engine-loop/scripts/runlog.py publish --run <run_id> --url https://...
```

Record the **rank and the referral traffic**, not the upvotes. A #1 that sent 40
visitors is worse than a #9 that sent 400, and only the second one should shape the
next launch. Set `metric_delay_hours` to 48 on the `launch` channel in
`shared/channels.json` — directory traffic peaks and dies inside two days.

---

## Rules

- **Never auto-submit.** Every platform here treats scripted submission as spam. The user pastes, always
- **Never ask for upvotes.** Product Hunt de-ranks it and Hacker News bans for it. This is not a grey area
- **One subreddit on day one.** Cross-posting the same text to eight subreddits is the fastest way to a sitewide Reddit ban — see `references/reddit.md`
- **Never submit to a platform you haven't read the rules page of that week.** These sites change their submission terms constantly and half the advice online is stale
- **Don't fake the launch.** No sockpuppet accounts, no bought upvotes, no "we're a team of 12" when it's one person. It gets found and the post becomes the story
- **A launch is not a growth strategy.** It's a spike. What happens on day 4 is the actual product question — hand back to `engine-seo`, `engine-social` or `engine-outreach` for that

## Going further

- `engine-loop` — score this launch against the next one instead of guessing
- `engine-social` — turn the result ("#1 on Uneed") into the posts that build the audience
- `engine-seo` — the AlternativeTo / OpenAlternative listings in `references/directories.md` are evergreen search surface, not launch-day traffic

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
