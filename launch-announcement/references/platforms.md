# Platforms — what each one wants, and what goes wrong

Two things before the table.

**Verify the rules before every submission.** These sites change submission terms,
queue lengths and pricing constantly, and most launch advice online is two years
stale. Open the platform's own rules/FAQ page the week you submit. Where this file
states a specific mechanic, treat it as "last known" and confirm it.

**Marked claims.** Lines tagged `[E]` come from
[@eliana_jordan's post-mortem](https://x.com/eliana_jordan/status/1944348597648244850)
of one real launch — one data point, one product, not a law. Lines tagged `[H]`
come from [@Hartdrawss's weighted list](https://x.com/Hartdrawss/status/2020430122562531608),
where each platform carries a priority number (3 = every launch, 1 = batch it).
Everything unmarked is general practice — apply judgment.

---

## Tiers

| Tier | Platforms | What you're buying |
|---|---|---|
| **1 — pick one as Day 0** | Product Hunt, Hacker News, Reddit | Real traffic, real signups, real risk of public failure |
| **2 — Day 1–3** | Uneed, Fazier, DevHunt, Indie Hackers, TAAFT, Peerlist, BetaList | Smaller spikes, warmer audiences, low effort |
| **3 — Week 2+, batched** | The other ~90 in `directories.md` | Backlinks and long-tail SEO. Not traffic |

Never run two tier-1 launches on the same day. Product Hunt wants your whole
morning in the comments; Hacker News wants you refreshing for the first 30 minutes.
Doing both means doing neither.

---

## Tier 1

### Product Hunt

`[H]` weight **3** — submitted for every client MVP.
`[E]` "good user spike but hard to climb, ended #19."

The default answer, and the most competitive. A top-5 finish is a meaningful spike;
#19 is a badge and some backlinks.

- The PH day runs **midnight to midnight Pacific**. Scheduling for 12:01 AM PT gives your post the full 24 hours to accumulate votes. Launching at noon PT means competing against posts with a twelve-hour head start
- **Tuesday–Thursday** are the crowded days and also the high-traffic days. Monday and Friday are easier to rank on and send fewer people. Weekends are quiet on both counts
- **Tagline: ~60 characters.** This is the whole pitch. Benefit, not category. "Ship your side project to 100 directories" beats "A modern launch automation platform"
- **The gallery does the selling.** First image is a caption-on-screenshot that states the benefit; the rest show the product actually working. A video helps and is not required
- **Post the maker comment immediately**, before any votes arrive — what it does, why you built it, what's deliberately missing, and the price. This comment is what people read before deciding to vote
- **Answer every comment for the full 24 hours.** Engagement is the part you control
- **Never ask for upvotes** — not in a DM, not in a newsletter, not in a Slack. PH detects vote clustering and will de-rank or remove the post. Asking people to "check it out" is fine; asking for the vote is not
- Hunters matter much less than they did; self-launching is normal now

### Hacker News

`[H]` weight **1**, but that reflects submission effort, not upside — HN's ceiling is the highest of anything on this list and its variance is brutal.

- Title format: **`Show HN: <what it is>`**. Read the official Show HN rules page before posting; it is short and it is enforced
- It has to be something people can **actually try right now**. A landing page with a waitlist is not a Show HN and will be flagged
- **Strip every piece of marketing language.** No "revolutionary", no "seamless", no emoji. HN reacts to hype the way an immune system reacts to an infection. Plain description of the thing
- **Weekday mornings, US Eastern.** Weekends are low traffic and low competition — sometimes the right trade for a small project
- Put the detail in **your own first comment**: what you built it with, what's hard about it, what it can't do yet, what it costs
- The first **20–30 minutes** decide it. If it doesn't move off /newest it's over — and that's normal, most Show HNs die there
- **Never organise upvotes.** Voting rings get accounts and domains banned, and HN is good at spotting them
- Prepare for the comments to be blunt. Answering a harsh technical critique well converts better than the post did

### Reddit

`[H]` weight **1**. Highest ceiling per hour of work on this whole list, and the easiest place to get permanently banned.

Full playbook, subreddit list and per-sub rules: **`reddit.md`**. The short version:

- **One subreddit on day one.** Not eight
- Read the sidebar rules and the last week of posts before writing a word
- Most of these subs remove promotional posts on sight. The ones that don't have a designated thread — use it
- Write the post so it stands alone if the link were removed

---

## Tier 2

### Uneed

`[H]` weight **3**. `[E]` "got me to #1 and brought real leads. My favorite."

The strongest signal in the sources: the only platform in that post-mortem credited
with **leads**, not just a traffic spike.

- Smaller pool than Product Hunt, so ranking is realistic for a first launch
- Runs daily and weekly leaderboards; there's a free queue and a paid option to pick your date. For a first launch the free queue is fine — the point is the ranking, not the day
- Reuse the Product Hunt tagline and gallery. It's the same format and this is the highest-return 20 minutes of the whole launch

### Fazier

`[H]` weight **1**. `[E]` "#1 weekly, #3 monthly. People liked it. I didn't like the platform."

Worth submitting, tempered expectations. Good rankings were achievable; the
platform experience was the complaint, not the outcome. Submit, don't invest time.

### TinyLaunch

`[H]` weight **1**. `[E]` "#2 but backlinks they promised? Never came."

**Specific trap:** in the replies to that post, another user pointed out the backlink
isn't automatic — you have to contact them to claim it. Eliana's reply: *"if I don't
message you I don't get the backlink? I didn't see it, thought it was automatic."*
If you submit here and the backlink is the reason, **follow up and claim it**.

### Peerlist

`[H]` weight **1**. `[E]` "no buzz. Felt like shouting into the void."

Developer-profile network with a project spotlight. Worth a submission because it's
free and takes minutes, but don't build the day around it. Better as a place your
profile lives than as a launch channel.

### tinystartups

`[H]` weight **1**. `[E]` "UI from hell. Didn't know if I was logged in or out."

Batch it with tier 3. Budget frustration, not time.

### Indie Hackers

`[H]` weight **2**.

**Not a launch platform** — there's no ranking to win. It's a community, and it
treats "here's my product" posts accordingly.

- Post a **milestone or a lesson**, with the product as context: "what I learned building X for 6 months", "our first $500", "why our first launch flopped"
- Numbers are the currency. Revenue, users, churn — real ones. Vague posts get ignored
- Answer every comment. The audience here is other founders, which means low conversion to users and high conversion to advice worth having

### DEV (dev.to)

**Not a launch platform**, same as Indie Hackers: no ranking, no launch day. It's a
developer blogging community, and a launch there is an article.

- Write the build story (the hard part, the stack, a snippet) and tag it `#showdev`. A post that is only "we launched X" gets nothing
- Cross-post from our own blog with `canonical_url` set to the original, so the search credit stays with us
- Dev tools and anything with an interesting technical story fit. Consumer apps with no technical angle mostly don't

### DevHunt

`[H]` weight **1**.

Weekly, dev-tools-only, run by developers. If the product is a dev tool this is a
better fit than most of tier 2. If it isn't, skip it — the audience will tell you.

### There's An AI For That (TAAFT)

Named directly in [@marclou's list](https://x.com/marclou/status/1933506642051805518).

The one AI directory with traffic that matters. Only relevant for AI products. Free
submission with a long review queue and paid tiers to skip it — check current
pricing before assuming either. The listing keeps sending traffic long after launch
week, which makes it more like SEO than like a launch.

### BetaList

`[H]` weight **1**.

**Pre-launch only.** Wrong platform for a shipped product, right one for a waitlist.
The free queue is measured in weeks; paid is faster. Submit early or don't bother.

### Stacker News

Appears in both `[H]` and the 107-list. Bitcoin-adjacent developer community where
posts earn sats. Sharp technical audience, small. Worth it if the product touches
payments, privacy or self-hosting; noise otherwise.

---

## Tier 3 and the lifetime-deal tier

The remaining ~90 sites are in `directories.md` with instructions for batching them.

**One warning about the deal sites** — AppSumo, LTD Hunt, Dealify, DealMirror,
SaaS Mantra, PrimeClub, SaaSZilla, StackSocial and the rest of that cluster in the
107-list are a **different motion, not a launch**. They sell lifetime access at a
deep discount to an audience that buys on price.

- Real money arrives fast, which is why people do it
- You inherit permanent support obligations from users who paid once
- Refund rates are high and the audience is unforgiving
- It anchors your price low, publicly, and that's very hard to undo

Fine as a deliberate cash decision. A bad accident on launch day. Don't put these
in the same plan as Product Hunt without saying out loud that it's a different bet.

---

## Alternatives directories are SEO, not launch

AlternativeTo, OpenAlternative, SaaSHub `[H]` weight **2**, LibHunt, Serchen,
Tekpon, Appscribed.

These rank for **"<competitor> alternative"** — a query with buying intent that
never stops being searched. Listing here does approximately nothing on launch day
and keeps working for years. Treat as `gtm-seo` work: name the competitor you're
an alternative to, say honestly what they do better, and let the comparison do the
selling.
