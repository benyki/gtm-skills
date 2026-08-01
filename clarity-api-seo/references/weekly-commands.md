# Weekly Clarity API command cookbook

Use these commands for a practical weekly review from the export API.

Assumption: env is already loaded and contains `CLARITY_API_KEY` plus `CLARITY_PROJECT_ID`.

```bash
set -a; . .env.local; set +a
```

Replace dates as needed.

## 1. Weekly overview

Best for:
- sessions trend proxy
- bot count proxy
- pages/session proxy
- engagement and friction summary

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-10 \
  --end-date 2026-04-16 \
  --metric Traffic \
  --metric ScrollDepth \
  --metric EngagementTime \
  --metric DeadClickCount \
  --metric RageClickCount \
  --metric QuickbackClick \
  --metric ScriptErrorCount \
  --pretty
```

## 2. Top pages this week

Best for:
- highest-demand pages
- pages to protect, refresh, or improve

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-10 \
  --end-date 2026-04-16 \
  --metric PopularPages \
  --limit 25 \
  --pretty
```

## 3. Top page titles this week

Useful for:
- sanity checking page naming
- spotting unexpected page-level traffic winners

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-10 \
  --end-date 2026-04-16 \
  --metric PageTitle \
  --limit 25 \
  --pretty
```

## 4. Referrers this week

Best for:
- search/referral source quality
- checking whether Bing, Yahoo, direct, etc. are sending traffic

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-10 \
  --end-date 2026-04-16 \
  --metric ReferrerUrl \
  --limit 25 \
  --pretty
```

## 5. Device and browser split

Best for:
- deciding whether mobile should dominate design fixes
- checking browser-specific issues

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-10 \
  --end-date 2026-04-16 \
  --metric Device \
  --metric Browser \
  --metric OS \
  --pretty
```

## 6. Country split

Best for:
- understanding geo concentration
- spotting unexpected markets

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-10 \
  --end-date 2026-04-16 \
  --metric Country \
  --limit 25 \
  --pretty
```

## 7. Prior week comparison

Run the same overview command for the prior week:

```bash
python3 scripts/clarity_export.py \
  --start-date 2026-04-03 \
  --end-date 2026-04-09 \
  --metric Traffic \
  --metric ScrollDepth \
  --metric EngagementTime \
  --metric DeadClickCount \
  --metric RageClickCount \
  --metric QuickbackClick \
  --metric ScriptErrorCount \
  --pretty
```

Then compare manually or in a small analysis script.

## Most obvious weekly data to pull

If you only do 4 calls each week, use these:

1. **Weekly overview**
2. **Top pages**
3. **Referrers**
4. **Device/browser split**

That gives you the clearest signal with the fewest API pulls.
