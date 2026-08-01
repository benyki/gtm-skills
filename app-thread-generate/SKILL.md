---
name: app-thread-generate
description: Generate NEW word-etymology "backstory" threads for the brand and append them to the backlog at ~/code/<project>/world/threads/inputs/thread-inputs.json. Researches and verifies a word's true etymology, writes it as a 4-tweet thread using one of the canonical opener templates, computes the "<X> million daily users" figure from corpus frequency, and validates + appends the entry. Use when the user says "generate word threads", "write N new word threads", "add etymology threads to the backlog", "top up the thread backlog", or names words to turn into threads. Pairs with app-thread-backstory, which POSTS what this skill writes.
---

# app-thread-generate

Writes new word-backstory threads into the backlog. This is the **generation** half of the
pipeline; `app-thread-backstory` is the **posting** half. One produces backlog entries, the
other ships them to Bluesky / X.

## When to use

- "Generate 5 new word threads"
- "Top up the thread backlog"
- "Turn these words into threads: panic, robot, sabotage"
- Any request to *create* (not post) etymology threads

## Where things live

- **Backlog (append target):** `~/code/<project>/world/threads/inputs/thread-inputs.json`
- **Config (templates, schema, voice, candidate pool):** `~/code/<project>/world/threads/inputs/config.md`
- **Frequency estimator:** `~/code/<project>/world/threads/inputs/estimate-users.py`
- **This skill's scripts:** `~/.agents/skills/app-thread-generate/scripts/`
- **Verified-etymology notes / disqualified words:** `../app-thread-backstory/references/etymology-sources.md`

## Workflow (per word)

### 1. Choose words not already covered

```bash
node ~/.agents/skills/app-thread-generate/scripts/list-candidates.mjs 10
```
Prints candidate words **not** already in the backlog (deduped). The user may also name words —
the append step rejects anything already present, so dedupe is automatic.

### 2. Verify the etymology — NON-NEGOTIABLE

Per project memory, **never trust "surprising word origin" listicles.** Confirm against a real
source before writing:

- Online Etymology Dictionary (etymonline.com) — primary
- Wiktionary etymology section / OED if available

Use `WebFetch`/`WebSearch`. A catchy-but-false folk etymology (e.g. *sincere* = "without wax",
*posh* = "port out starboard home") is **disqualified** unless the thread's whole point is to debunk
it. If you can't find a solid source, drop the word and pick another. Jot the source in
[etymology-sources.md](../app-thread-backstory/references/etymology-sources.md), flagging any
spot where the popular telling overstates (so the copy stays honest).

### 3. Pick the opener template

By how the origin *feels* (full text in [config.md](file://~/code/<project>/world/threads/inputs/config.md)):

| template | use when | shows `<X>`? |
|---|---|---|
| `default-1` | safe default | yes |
| `default-2` | safe default | yes |
| `surprising` | the origin is surprising | no |
| `weird` | weird / mysterious / a great origin story → **story-across-centuries** body | no |

### 4. Compute the daily-users figure

```bash
# venv with wordfreq installed (pip install wordfreq)
python3 ~/code/<project>/world/threads/inputs/estimate-users.py <word>
```
Use the printed `est_users_M`. Apply the documented overrides only when warranted (event-spike words
→ pre-spike baseline). The number only *appears* on `default-1`/`default-2` hooks; on `surprising`/
`weird` it's metadata.

### 5. Write the thread

- **opener** = the chosen template, fully rendered (insert the word and, for default-*, the figure).
- **2–3 longer body posts** — fewer, meatier tweets, each ≤ 280 chars. Target **4 tweets total**
  (opener → 2 body → reply). Land the last body post on the payoff line.
- **cta_reply** = the standard YourApp CTA (copy an existing entry's `cta_reply` verbatim).
- Voice: curious, plain, a little wonder; no hype, no emoji storms; mark cited forms with `*italics*`.

### 6. Validate + append

Write the entry to a temp JSON file, then:

```bash
node ~/.agents/skills/app-thread-generate/scripts/append-thread.mjs --check --file /tmp/entry.json  # dry validate
node ~/.agents/skills/app-thread-generate/scripts/append-thread.mjs --file /tmp/entry.json           # append
```

The script enforces: required fields, valid template, **unique word/label**, every post ≤ 280 chars,
and the 4–5-tweet shape. It rejects on any violation — fix and retry.

### 7. (optional) Post it

Hand off to `app-thread-backstory` to post the new `todo` entries (Bluesky is scriptable/headless;
X needs the interactive browser).

## Entry shape

```jsonc
{
  "label": "panic",            // unique slug
  "word": "panic",
  "template": "weird",
  "daily_users_millions": 150, // from estimate-users.py
  "opener": "The backstory behind the word \"panic\" is fascinating. Let me tell you how we ended up using it:",
  "posts": ["… longer beat 1 …", "… longer beat 2, ending on the payoff …"],
  "cta_reply": "If you love where words come from, you'll love YourApp — … your-site.example",
  "lang": "en"
}
```
(`status` is set automatically by the append script to `{ x: "todo", bluesky: "todo", threads: "todo" }`
— per-platform, each flipped to `done` only when that platform's post lands.)

## Rules

- **Verify before you write.** No unsourced or debunked etymologies. ([verify-foreign-phrases])
- **Fewer, longer posts.** 2–3 body tweets, not a string of short ones. ~4 tweets total.
- **No em dashes (`—`)** anywhere in the copy. Restructure with a comma, colon, period, or
  parentheses. The append script rejects any entry containing one.
- **One link only**, in the reply. Never in body posts.
- **Dedupe is enforced** by the append script — don't fight it; pick another word.
- **Generation ≠ posting.** This skill never posts. It only writes `todo` entries.

## Files

- [SKILL.md](SKILL.md) — this file
- [scripts/list-candidates.mjs](scripts/list-candidates.mjs) — candidate words minus what's covered
- [scripts/append-thread.mjs](scripts/append-thread.mjs) — validate (`--check`) + append an entry
