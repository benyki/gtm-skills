# Clarity metrics to SEO and UX analysis

Use Microsoft Clarity as behavioral evidence, not as a direct ranking oracle.
The goal is to infer where user experience supports or undermines SEO outcomes.

## Core lenses

### 1. Highest-traffic pages

Inspect:
- total sessions
- users
- page views
- landing-page share
- device split
- source split

Ask:
- Which pages attract the most demand?
- Which of those pages are likely SEO landing pages?
- Which pages deserve protection, refreshes, internal linking, or conversion tuning?

Actions:
- protect high-performing pages during redesigns
- refresh outdated content on durable traffic winners
- strengthen internal links from high-traffic informational pages to commercial pages

### 2. Engagement leaders

Inspect:
- average time on page or session depth proxies
- scroll depth
- repeat engagement
- low quick-back behavior

Ask:
- Which pages genuinely hold attention?
- Which topics or templates keep users engaged?
- Can those patterns be replicated on similar pages?

Actions:
- clone successful content structure into adjacent topics
- add stronger conversion paths on highly engaged pages
- use engaged pages as internal linking hubs

### 3. High traffic, weak experience

Inspect:
- high visits with low time spent
- high quick backs
- shallow scroll depth
- rage clicks or dead clicks
- JavaScript errors

Ask:
- Is search intent mismatched?
- Is the content too slow, too weak, or too confusing?
- Is there a broken or misleading UI element?

Actions:
- improve title-to-content message match
- rewrite the first screen for clarity and relevance
- reduce layout clutter and improve CTA prominence
- fix broken interactions immediately

### 4. Referrer and source quality

Inspect:
- top referrers
- source/medium style patterns if exposed in the data
- landing pages by source
- engagement quality by source

Ask:
- Which sources send engaged traffic?
- Which sources bounce quickly?
- Which source-page pairings create the best opportunity?

Actions:
- invest more in sources that send long-engagement users
- align landing pages to source expectations
- build content clusters around source-winning topics

### 5. Friction signals

Inspect:
- dead clicks
- rage clicks
- excessive quick backs
- error-heavy sessions
- device-specific friction

Ask:
- Where do users try to do something that is not possible?
- Which pages visually suggest clickable UI that does nothing?
- Are problems concentrated on mobile?

Actions:
- fix false affordances
- improve mobile tap targets
- remove obstructive popups and sticky elements
- debug broken JS and form flows

## Trend analysis windows

Always compare periods when data volume allows.

### Day-over-day
Use for:
- content launches
- release regressions
- sudden traffic quality changes
- campaign spillover into SEO landing pages

### Week-over-week
Use for:
- stable behavioral trend detection
- identifying sustained gains or losses
- spotting recurring weekday patterns

### 28-day versus prior 28-day
Use for:
- stronger baseline analysis
- broader content and sitewide changes
- seasonal smoothing

## Suggested dimensions

Pull and compare metrics by these dimensions when available:
- page URL or path
- referrer/source
- device
- browser
- country/region
- OS
- landing page

## Good report language

Prefer:
- “This page likely underperforms because behavior suggests…”
- “This source sends low-quality traffic relative to others…”
- “Users appear to expect this element to be clickable…”

Avoid:
- “This page ranks worse because…” unless ranking data exists elsewhere
- “Google penalized…” unless externally verified

## Prioritization framework

Rank fixes using:
- impact: traffic affected x severity of friction x business value
- effort: copy change, design tweak, engineering fix, or deep rebuild

Simple priority buckets:
- High impact / low effort
- High impact / medium effort
- Monitor
- Ignore for now
