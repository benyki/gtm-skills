# Sources — where the people actually are

Ordered by what to try first, not by sophistication. Every method here works
with a browser and patience; the paid ones only buy speed.

## 0. The list they already have

Before searching anything: their inbox, their existing customers, churned users,
waitlist, people who replied to a post, connections, past colleagues, anyone who
signed up and never activated. Highest reply rate in outreach, and reliably the
first thing everyone skips.

## 1. Person-first — you have a description

| Where | Good for | How |
|---|---|---|
| **Professional networks** | roles, seniority, company size, geography | People search with filters; note that the observable usually comes from their *activity*, not the profile |
| **Communities** — subreddits, Discords, Slack groups, forums | people defined by a behaviour rather than a title | Read the threads. The person asking the question you answer is the lead, and the question is the observable |
| **Creator platforms** — TikTok, YouTube, Instagram, Substack | creator and influencer outreach | Search the niche's terms, sort by recent; check the bio/link for the contact route |
| **Developer platforms** — GitHub, Stack Overflow, package registries | technical buyers and builders | Contributors to adjacent projects; issues that describe your problem |
| **Job boards** | companies whose priorities just changed | The role they're hiring for *is* the signal |
| **Event and conference lists** | industry-specific reach | Speaker and attendee pages, past years included |

## 2. Company-first — you have accounts

| Where | Good for |
|---|---|
| **Directories and marketplaces** — app stores, agency lists, integration directories, review sites | "companies of type X" |
| **Local business data** — maps and listings | geography-bound SMB targeting |
| **Funding and news feeds** | companies whose situation just changed |
| **Competitor customers** — logo walls, case studies, review sites, integration pages | the highest-intent list available, and usually free |

Then find the right person at each account: the platform search from §1,
constrained to that company. Titles vary wildly by company size — at a
ten-person company the buyer is the founder; at a thousand-person company the
founder is unreachable and irrelevant.

## 3. Scaling it

In order:

1. **By hand** — the first 20–50, always. It's where the filter gets built
2. **Browser automation** — the same searches, repeated. `agent-browser` or an
   equivalent. Free, and it works on anything a person can see
3. **Scraping APIs / actors** — when hand-collection is the bottleneck and the
   filter is proven. `apify-ultimate-scraper` and similar
4. **Paid contact databases** — filter-by-attribute at volume, with contact
   routes included. Worth it when the ICP is defined by firmographics rather than
   behaviour, and only once you know the filter converts

**Never start at 3 or 4.** A paid database with an unproven filter produces
thousands of rows that all fail the "so what?" test, and it charges for the
privilege.

## Choosing between person-first and company-first

| Situation | Shape |
|---|---|
| "Find everyone with title X in industry Y" | person-first |
| "I have 500 domains, find the owner of each" | company-first |
| "Add a second contact at companies I already target" | company-first |
| "Widest net in a vertical" | person-first |
| "These specific named accounts" | company-first |

Most campaigns use person-first to build, then company-first to deepen.
*(Distinction adapted from the cold-outbound list-building skills — see
`../CREDITS.md`.)*

## Contact routes, in order of usefulness

1. A **verified work email** — best, when the platform or database gives one
2. A **platform DM or reply** — normal for creators and community members, and
   often better-performing than email in those niches
3. A **contact form or link-in-bio** — slow, but it's a real route
4. A **guessed email pattern** — last resort. Guessing burns sender reputation
   when it bounces; if you can't verify it, prefer route 2

Record which one you have in `contact_type`. A workflow that assumes email and
receives handles will silently drop half the list.

## Recording the source

Every row keeps the search or list it came from, and every row keeps its
`profile_url`. Two reasons: the next agent verifies the observable instead of
re-researching it, and after a few weeks you can compare reply rate **by source**
— which usually tells you more than any copy test.
