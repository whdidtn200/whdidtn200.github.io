#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--event", default="schedule")
    parser.add_argument("--local-date", required=True)
    parser.add_argument("--timezone", default="Asia/Seoul")
    return parser.parse_args()


def parse_github_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def main() -> int:
    args = parse_args()
    timezone = ZoneInfo(args.timezone)
    url = (
        "https://api.github.com/repos/"
        f"{args.repo}/actions/workflows/{args.workflow}/runs?event={args.event}&per_page=5"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "malt-daily-publish-monitor",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1

    runs = payload.get("workflow_runs") or []
    match = None
    for run in runs:
        started_at = parse_github_datetime(run.get("run_started_at") or run.get("created_at"))
        if started_at is None:
            continue
        if started_at.astimezone(timezone).date().isoformat() == args.local_date:
            match = run
            break

    result = {
        "ok": True,
        "repo": args.repo,
        "workflow": args.workflow,
        "event": args.event,
        "local_date": args.local_date,
        "timezone": args.timezone,
        "run_found": bool(match),
    }

    if match:
        result["run"] = {
            "id": match.get("id"),
            "name": match.get("name"),
            "html_url": match.get("html_url"),
            "status": match.get("status"),
            "conclusion": match.get("conclusion"),
            "run_started_at": match.get("run_started_at"),
            "created_at": match.get("created_at"),
            "head_sha": match.get("head_sha"),
            "display_title": match.get("display_title"),
        }

    print(json.dumps(result, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
