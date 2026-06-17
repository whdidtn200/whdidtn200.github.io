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

    backup_result = backup_label(payload["backup"]["result"])
    backup_class = {
        "정상 완료": "ok",
        "복구 완료": "ok",
        "실패": "bad",
        "확인 필요": "warn",
    }.get(backup_result, "warn")

    if not github_status:
        github_result = "상태 확인 안 됨"
        github_class = "warn"
    elif not github_status.get("ok", True):
        github_result = "조회 실패"
        github_class = "bad"
    elif not github_status.get("run_found"):
        github_result = "오늘 run 없음"
        github_class = "warn"
    else:
        conclusion = (run.get("conclusion") or run.get("status") or "unknown").lower()
        github_result = conclusion
        github_class = "ok" if conclusion == "success" else "warn"

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Automation Status | MALT Tech Blog</title>
  <meta name="description" content="MALT Tech Blog 자동 발행 상태 페이지" />
  <meta name="robots" content="noindex,follow" />
  <link rel="stylesheet" href="./assets/hud.css" />
  <style>
    .hero {{
      margin-top:14px;
      padding:18px;
    }}
    .hero h1 {{
      margin:6px 0 10px;
      font-size:32px;
      line-height:1.15;
    }}
    .hero p {{
      margin:0;
      color:var(--muted);
      line-height:1.7;
    }}
    .status-grid {{
      display:grid;
      grid-template-columns:repeat(3, minmax(0, 1fr));
      gap:14px;
      margin-top:14px;
    }}
    .status-card {{
      background:var(--panel);
      border:1px solid var(--line);
      border-radius:14px;
      padding:16px;
      box-shadow:0 8px 22px rgba(24,54,84,.05);
    }}
    .status-card .label {{
      font-size:12px;
      text-transform:uppercase;
      letter-spacing:.08em;
      color:var(--muted);
      margin-bottom:8px;
    }}
    .status-card .value {{
      font-size:28px;
      font-weight:800;
      line-height:1.1;
      margin-bottom:8px;
    }}
    .status-card.ok .value {{ color:#167c5f; }}
    .status-card.warn .value {{ color:#9a6700; }}
    .status-card.bad .value {{ color:#b3261e; }}
    .status-card p {{
      margin:0;
      color:var(--muted);
      line-height:1.6;
      font-size:14px;
    }}
    .detail {{
      margin-top:14px;
    }}
    .detail ul {{
      margin:0;
      padding-left:18px;
    }}
    @media (max-width: 860px) {{
      .status-grid {{
        grid-template-columns:1fr;
      }}
      .hero h1 {{
        font-size:26px;
      }}
    }}
  </style>
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
    <section class="card hero">
      <div class="h">Automation Status</div>
      <h1>자동 발행이 오늘 실제로 살아 있었는지 바로 보는 페이지</h1>
      <p>이 페이지는 GitHub 메인 배치와 macmini backup 배치의 최근 상태를 함께 보여줍니다. "돌아가는 것 같음"이 아니라 마지막 확인 결과를 바로 확인할 수 있게 두었습니다.</p>
    </section>

    <section class="status-grid">
      <article class="status-card {github_class}">
        <div class="label">GitHub Main</div>
        <div class="value">{github_result}</div>
        <p>{github_line}</p>
      </article>
      <article class="status-card {backup_class}">
        <div class="label">macmini Backup</div>
        <div class="value">{backup_result}</div>
        <p>{payload["backup"].get("summary", "")}</p>
      </article>
      <article class="status-card">
        <div class="label">Last Update</div>
        <div class="value">{payload["local_date"]}</div>
        <p>{payload["updated_at_local"]}</p>
      </article>
    </section>

    <section class="card detail">
      <div class="h">Details</div>
      <ul>
        <li><strong>최근 갱신 시각</strong>: {payload["updated_at_local"]}</li>
        <li><strong>로컬 기준일</strong>: {payload["local_date"]} ({payload["timezone"]})</li>
        <li><strong>GitHub 메인 배치</strong>: {github_line}</li>
        <li><strong>맥미니 백업 배치</strong>: {backup_result}</li>
      </ul>
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
