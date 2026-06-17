#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--local-date", required=True)
    parser.add_argument("--timezone", required=True)
    parser.add_argument("--backup-result", required=True)
    parser.add_argument("--backup-summary", default="")
    parser.add_argument("--github-status-file")
    return parser.parse_args()


def load_github_status(path_value: str | None) -> dict:
    if not path_value:
        return {}
    path = Path(path_value)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_status_json"}


def backup_label(result: str) -> str:
    return {
        "success": "정상 완료",
        "recovered": "복구 완료",
        "failure": "실패",
        "unknown": "확인 필요",
    }.get(result, result)


def github_label(status: dict) -> str:
    if not status:
        return "GitHub 메인 상태를 아직 확인하지 못했습니다."
    if not status.get("ok", True):
        return "GitHub 메인 상태 조회 실패"
    if not status.get("run_found"):
        return "오늘 GitHub 메인 scheduled run 기록 없음"
    run = status.get("run") or {}
    conclusion = run.get("conclusion") or run.get("status") or "unknown"
    return f"GitHub 메인 run: {conclusion}"


def render_html(payload: dict) -> str:
    github_status = payload.get("github") or {}
    run = github_status.get("run") or {}
    github_line = github_label(github_status)
    workflow_url = run.get("html_url", "")
    workflow_meta = ""
    if workflow_url:
        workflow_meta = (
            f'<p><a href="{workflow_url}">GitHub workflow run 보기</a></p>'
        )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Automation Status | MALT Tech Blog</title>
  <meta name="description" content="MALT Tech Blog 자동 발행 상태 페이지" />
  <meta name="robots" content="noindex,follow" />
  <link rel="stylesheet" href="./assets/hud.css" />
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div class="brand">AUTOMATION · MALT HUD</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <a class="badge" href="./index.html">HOME</a>
        <a class="badge" href="./AI-OPS.html">AI OPS</a>
      </div>
    </div>
    <section class="card" style="margin-top:14px;">
      <div class="h">Automation Status</div>
      <p>이 페이지는 MALT Tech Blog 자동 발행 시스템의 최근 상태를 공개적으로 기록합니다.</p>
      <ul>
        <li><strong>최근 갱신 시각</strong>: {payload["updated_at_local"]}</li>
        <li><strong>로컬 기준일</strong>: {payload["local_date"]} ({payload["timezone"]})</li>
        <li><strong>맥미니 백업 배치</strong>: {backup_label(payload["backup"]["result"])}</li>
        <li><strong>GitHub 메인 배치</strong>: {github_line}</li>
      </ul>
      <p>{payload["backup"].get("summary", "")}</p>
      {workflow_meta}
      <p class="tiny">이 상태 페이지는 macmini backup workflow가 자동 갱신합니다.</p>
    </section>
  </div>
</body>
</html>
"""


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root)
    tz = ZoneInfo(args.timezone)
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(tz)
    github_status = load_github_status(args.github_status_file)

    payload = {
        "updated_at_utc": now_utc.isoformat(),
        "updated_at_local": now_local.isoformat(),
        "local_date": args.local_date,
        "timezone": args.timezone,
        "github": github_status,
        "backup": {
            "result": args.backup_result,
            "summary": args.backup_summary,
        },
    }

    (repo_root / "automation-status.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (repo_root / "AUTOMATION.html").write_text(render_html(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
