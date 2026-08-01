#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import sys
from urllib import error, parse, request

BASE_URL = "https://www.clarity.ms/export-data/api/v1/project-live-insights"


def pick_project_id(cli_value: str | None) -> str | None:
    if cli_value:
        return cli_value
    for key in (
        "CLARITY_PROJECT_ID",
        "MICROSOFT_CLARITY_PROJECT_ID",
        "CLARITY_SITE_ID",
    ):
        value = os.getenv(key)
        if value:
            return value
    return None


def build_url(project_id: str, start_date: str, end_date: str, dimensions: list[str], metrics: list[str], limit: int) -> str:
    query = {
        "numOfRows": str(limit),
        "projectId": project_id,
        "startDate": start_date,
        "endDate": end_date,
    }
    if dimensions:
        query["dimensions"] = ",".join(dimensions)
    if metrics:
        query["measures"] = ",".join(metrics)
    return f"{BASE_URL}?{parse.urlencode(query)}"


def fetch_json(url: str, api_key: str) -> dict:
    req = request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    with request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch Microsoft Clarity live insights export data. Note: export metrics are not guaranteed to match Clarity dashboard cards exactly."
    )
    parser.add_argument("--project-id", help="Clarity project id. Falls back to env vars.")
    parser.add_argument("--start-date", required=True, help="Start date, typically YYYY-MM-DD")
    parser.add_argument("--end-date", required=True, help="End date, typically YYYY-MM-DD")
    parser.add_argument(
        "--dimension",
        action="append",
        dest="dimensions",
        default=[],
        help="Dimension to request, repeatable",
    )
    parser.add_argument(
        "--metric",
        action="append",
        dest="metrics",
        default=[],
        help="Measure/metric to request, repeatable",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument(
        "--show-disclaimer",
        action="store_true",
        help="Print a short note that export metrics may not equal dashboard cards exactly.",
    )
    args = parser.parse_args()

    api_key = os.getenv("CLARITY_API_KEY")
    if not api_key:
        print("Missing CLARITY_API_KEY in environment", file=sys.stderr)
        return 2

    project_id = pick_project_id(args.project_id)
    if not project_id:
        print(
            "Missing project id. Pass --project-id or set CLARITY_PROJECT_ID / MICROSOFT_CLARITY_PROJECT_ID / CLARITY_SITE_ID",
            file=sys.stderr,
        )
        return 2

    url = build_url(
        project_id=project_id,
        start_date=args.start_date,
        end_date=args.end_date,
        dimensions=args.dimensions,
        metrics=args.metrics,
        limit=args.limit,
    )

    try:
        data = fetch_json(url, api_key)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"HTTP {exc.code}: {body}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    if args.show_disclaimer:
        print(
            "NOTE: This response comes from the Clarity export API (project-live-insights). "
            "Some metrics may only be approximate equivalents of dashboard cards, especially bot-filtered or live-user UI summaries.",
            file=sys.stderr,
        )

    if args.pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
