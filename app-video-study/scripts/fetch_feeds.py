#!/usr/bin/env python3
"""fetch_feeds.py — pull recent items from the curated science/neuroscience RSS feeds.

Dependency-free (Python 3 stdlib). Prints the most recent items across the feeds in
references/rss-feeds.md so you can pick a study for a science-brand video.

    python3 fetch_feeds.py --limit 8 --since-days 21      # recent items, all feeds
    python3 fetch_feeds.py --only neuro --limit 12        # only neuroscience-tagged feeds
    python3 fetch_feeds.py --list                         # just list the feeds
    python3 fetch_feeds.py --json                         # machine-readable output

Feeds sometimes rate-limit/403; those are skipped with a note. Fall back to
WebSearch/WebFetch when a feed is unavailable.
"""
import argparse, datetime, gzip, io, json, re, sys, urllib.request
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

FEEDS = [
    # (name, tag, url)   tag in {neuro, science}
    ("Neuroscience News", "neuro", "https://neurosciencenews.com/feed/"),
    ("ScienceDaily — Mind & Brain", "neuro", "https://www.sciencedaily.com/rss/mind_brain.xml"),
    ("ScienceDaily — Neuroscience", "neuro", "https://www.sciencedaily.com/rss/mind_brain/neuroscience.xml"),
    ("PsyPost", "neuro", "https://www.psypost.org/feed/"),
    ("The Transmitter", "neuro", "https://www.thetransmitter.org/feed/"),
    ("StudyFinds", "science", "https://studyfinds.org/feed/"),
    ("New Scientist", "science", "https://www.newscientist.com/feed/home/"),
    ("Quanta Magazine", "science", "https://api.quantamagazine.org/feed/"),
    ("Scientific American", "science", "https://www.scientificamerican.com/platform/syndication/rss/"),
    ("Knowable Magazine", "science", "https://knowablemagazine.org/rss"),
    ("ScienceDaily — Top Science", "science", "https://www.sciencedaily.com/rss/top/science.xml"),
    ("Nature", "science", "https://www.nature.com/nature.rss"),
    ("Nature Neuroscience", "neuro", "https://www.nature.com/neuro.rss"),
    ("Nature Human Behaviour", "neuro", "https://www.nature.com/nathumbehav.rss"),
    ("Science (AAAS) news", "science", "https://www.science.org/rss/news_current.xml"),
    ("Cell Press — Neuron", "neuro", "https://www.cell.com/neuron/inpress.rss"),
    ("eLife — neuroscience", "neuro", "https://elifesciences.org/rss/subject/neuroscience.xml"),
    ("MIT News — neuroscience", "neuro", "https://news.mit.edu/rss/topic/neuroscience"),
    ("The Guardian — Neuroscience", "neuro", "https://www.theguardian.com/science/neuroscience/rss"),
    ("Phys.org — Neuroscience", "neuro", "https://phys.org/rss-feed/biology-news/neuroscience/"),
]

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 local-video-app-study/1.0"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    if data[:2] == b"\x1f\x8b":
        data = gzip.GzipFile(fileobj=io.BytesIO(data)).read()
    return data


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = re.sub(r"&[a-z]+;", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_date(s):
    if not s:
        return None
    try:
        return parsedate_to_datetime(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            return datetime.datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def parse_items(xml_bytes):
    """Return [{title, link, date(datetime|None), summary}] for RSS or Atom."""
    root = ET.fromstring(xml_bytes)
    tag = lambda e: e.tag.split("}")[-1]
    items = []
    # RSS: channel/item ; Atom: feed/entry
    nodes = [e for e in root.iter() if tag(e) in ("item", "entry")]
    for it in nodes:
        d = {"title": "", "link": "", "date": None, "summary": ""}
        for ch in it:
            t = tag(ch)
            if t == "title":
                d["title"] = strip_html("".join(ch.itertext()))
            elif t == "link":
                href = ch.get("href")
                d["link"] = href or (ch.text or "").strip() or d["link"]
            elif t in ("pubDate", "published", "updated", "date"):
                d["date"] = d["date"] or parse_date((ch.text or "").strip())
            elif t in ("description", "summary", "content"):
                if not d["summary"]:
                    d["summary"] = strip_html("".join(ch.itertext()))[:280]
        if d["title"]:
            items.append(d)
    return items


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["neuro", "science"], help="restrict to one tag")
    ap.add_argument("--limit", type=int, default=8, help="items to show per feed")
    ap.add_argument("--since-days", type=int, default=0, help="only items newer than N days (0 = no filter)")
    ap.add_argument("--list", action="store_true", help="just list the feeds and exit")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    feeds = [f for f in FEEDS if not args.only or f[1] == args.only]

    if args.list:
        for name, tag, url in feeds:
            print(f"[{tag:7}] {name:28} {url}")
        return

    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff = now - datetime.timedelta(days=args.since_days) if args.since_days else None
    out = []
    for name, tag, url in feeds:
        try:
            items = parse_items(fetch(url))
        except Exception as e:
            print(f"## {name} [{tag}] — SKIPPED ({type(e).__name__}: {e})", file=sys.stderr)
            continue
        def keyf(d):
            dt = d["date"]
            if dt and dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt or datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)
        items.sort(key=keyf, reverse=True)
        picked = []
        for d in items:
            dt = keyf(d)
            if cutoff and dt < cutoff:
                continue
            picked.append(d)
            if len(picked) >= args.limit:
                break
        for d in picked:
            out.append({"source": name, "tag": tag, "title": d["title"],
                        "date": d["date"].strftime("%Y-%m-%d") if d["date"] else "?",
                        "link": d["link"], "summary": d["summary"]})

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    cur = None
    for r in out:
        if r["source"] != cur:
            cur = r["source"]
            print(f"\n## {cur}  [{r['tag']}]")
        print(f"- ({r['date']}) {r['title']}")
        print(f"  {r['link']}")
        if r["summary"]:
            print(f"  {r['summary'][:200]}")
    print(f"\n[{len(out)} items across {len(feeds)} feeds]", file=sys.stderr)


if __name__ == "__main__":
    main()
