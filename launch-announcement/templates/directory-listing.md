# Directory listing — the reusable asset pack

Write this once, in one sitting, then paste it into all ~90 tail directories.
Every one of them asks for some subset of these fields.

Store the filled version at `runs/<run_id>/output/directory-pack.md` so the next
launch starts from it.

---

## Fields

| Field | Limit | Value |
|---|---|---|
| Name | — | `<product name>` |
| Tagline | 60 chars | `<same as Product Hunt — reuse it>` |
| Short description | 160 chars | `<one sentence: what it does, for whom>` |
| Long description | ~500 chars | `<3–4 sentences: problem, what it does, who it's for, price>` |
| Categories | 3–5 | `<the ones buyers browse>` |
| Tags / keywords | 5–10 | `<what someone would search>` |
| Pricing | — | `<Free / Freemium / $X per month / One-time $X>` |
| Website | — | `<url with a UTM per directory — see below>` |
| Logo | — | Square PNG, transparent, 512×512 |
| Screenshot | — | 1280×800, product in use, real data |
| Contact email | — | `<one you'll actually read — approvals arrive here>` |
| Founder / maker | — | `<name + X or LinkedIn>` |

---

## Long description

```
<Problem, one sentence, concrete.>
<Product name> <does the thing>, so you <outcome>.
Built for <specific audience>. <Price.>
```

No "leverage", no "empower", no "seamlessly". Directories are read by people
scanning twenty tiles — say the thing.

---

## Track every submission

| Directory | Date | Status | Backlink claimed | Referrals |
|---|---|---|---|---|
| | | pending / live / rejected | y/n/na | |

Two reasons this table exists:

1. **Review queues run for weeks.** Without a log you resubmit and get flagged
2. **Some directories require you to claim your backlink** — it isn't automatic. That's what happened to `[E]` on TinyLaunch (`references/sources.md`). If the backlink is why you submitted, follow up

## UTM

Tag each listing so referral traffic is attributable:

```
?utm_source=<directory>&utm_medium=directory&utm_campaign=launch
```

After two weeks, read the numbers and put them in the run log. If the whole tail
sent 11 visits, that's the answer for next time — and `engine-loop` should have it
rather than recommending the same batch again.

## Don't

- Don't pay for a generic directory listing on a first launch
- Don't submit to an AI directory if it isn't an AI product — dead link, nobody clicks
- Don't do this on launch day. Week 2 (see `references/directories.md`)
