# Science & neuroscience RSS feeds — where to find a study

Sources for step 1 ("Find & verify the insight"). Two tiers: **write-ups** (great for
scroll-stopping findings with a clear number and a human angle — start here) and
**primary journals** (authoritative; use to verify or to go deeper). Always trace the
claim back to the primary study before putting a number on screen.

Fetch the latest across these with the helper:
```bash
python3 ~/.agents/skills/local-video-app-study/scripts/fetch_feeds.py --limit 8 --since-days 21
python3 ~/.agents/skills/local-video-app-study/scripts/fetch_feeds.py --only neuro --limit 12   # neuro-only
python3 ~/.agents/skills/local-video-app-study/scripts/fetch_feeds.py --list                     # just list feeds
```
Feeds occasionally rate-limit or block; if one 403s, fall back to `WebSearch`/`WebFetch`.

## Tier 1 — write-ups & magazines (best hunting ground)
| source | tag | RSS |
|--------|-----|-----|
| Neuroscience News | neuro | https://neurosciencenews.com/feed/ |
| ScienceDaily — Mind & Brain | neuro | https://www.sciencedaily.com/rss/mind_brain.xml |
| ScienceDaily — Neuroscience | neuro | https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml |
| PsyPost | neuro | https://www.psypost.org/feed/ |
| The Transmitter (Simons Foundation) | neuro | https://www.thetransmitter.org/feed/ |
| StudyFinds | science | https://studyfinds.org/feed/ |
| New Scientist | science | https://www.newscientist.com/feed/home/ |
| Quanta Magazine | science | https://api.quantamagazine.org/feed/ |
| Scientific American — Mind | science | https://www.scientificamerican.com/platform/syndication/rss/ |
| Knowable Magazine | science | https://knowablemagazine.org/rss |
| ScienceDaily — Top Science | science | https://www.sciencedaily.com/rss/top/science.xml |

## Tier 2 — primary journals & institutions (verify / go deeper)
| source | tag | RSS |
|--------|-----|-----|
| Nature (current issue) | science | https://www.nature.com/nature.rss |
| Nature Neuroscience | neuro | https://www.nature.com/neuro.rss |
| Nature Human Behaviour | neuro | https://www.nature.com/nathumbehav.rss |
| Science (AAAS) — news | science | https://www.science.org/rss/news_current.xml |
| Cell Press — Neuron | neuro | https://www.cell.com/neuron/inpress.rss |
| PNAS — current | science | https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=pnas |
| eLife — neuroscience | neuro | https://elifesciences.org/subjects/neuroscience.rss |
| MIT News — neuroscience | neuro | https://news.mit.edu/rss/topic/neuroscience |
| EurekAlert — Neuroscience | neuro | https://www.eurekalert.org/rss/neuroscience.xml |
| Phys.org — Neuroscience | neuro | https://phys.org/rss-feed/biology-news/neuroscience/ |

## How to pick (for THIS format)
A good study-video candidate has:
1. **A number that stops the scroll** — a clean percentage, an "N×", a "1 in N".
2. **A comparison or a striking human detail** — something for the bars/detail beats.
3. **A natural "ask yourself" angle** — the finding implies a question about the
   viewer's own mind/body/behavior.
4. **Recency** — favor the last ~3 weeks so it reads as news.
5. **Reputable + verifiable** — you can reach the primary paper (journal + year).

Skip: pure methods/replication-only papers with no vivid number, anything requiring
medical/financial advice to explain, and press releases that overclaim beyond the data.

## Etiquette
Space out requests; the fetcher sets a normal User-Agent and times out politely. Don't
hammer a single feed. Cache what you pull into the run's `source.md`.
