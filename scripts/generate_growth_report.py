#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import json
import pathlib
import subprocess

import build_tag_index as tag_index


ROOT = pathlib.Path(__file__).resolve().parent.parent
STATE_DIR = ROOT / "content" / "archive" / "state"
QUALITY_REPORT_FILE = STATE_DIR / "content_quality_report.json"
QUEUE_FILE = STATE_DIR / "queue_snapshot.json"
LAB_STATE_FILE = STATE_DIR / "lab_publish_state.json"
OUTPUT_JSON = STATE_DIR / "growth_report.json"
OUTPUT_HTML = ROOT / "GROWTH.html"
RECENTLY_IMPROVED_DAYS = 3

GUIDE_PATHS = [
    "railway-predictive-maintenance-guide.html",
    "bearing-fault-diagnosis-guide.html",
    "wayside-condition-monitoring-guide.html",
    "predictive-maintenance-kpi-roi-guide.html",
    "railway-bearing-sensor-guide.html",
    "phm-alert-governance-guide.html",
    "phm-inspection-evidence-pack-guide.html",
]


def load_json(path: pathlib.Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def count_words(path: pathlib.Path) -> int:
    if not path.exists():
        return 0
    text = path.read_text(encoding="utf-8")
    cleaned = tag_index.clean_text(text)
    return len(cleaned.split())


def last_commit_date_for_url(url: str) -> dt.datetime | None:
    relative = url.lstrip("/")
    if not relative:
        return None
    target = ROOT / relative
    if not target.exists():
        return None
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(ROOT),
                "log",
                "-1",
                "--format=%cI",
                "--",
                str(target.relative_to(ROOT)),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, ValueError):
        return None

    raw = result.stdout.strip()
    if not raw:
        return None
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def was_recently_improved(entry: dict) -> bool:
    committed_at = last_commit_date_for_url(entry.get("url", ""))
    if committed_at is None:
        return False
    now = dt.datetime.now().astimezone(committed_at.tzinfo)
    age = now - committed_at
    return age <= dt.timedelta(days=RECENTLY_IMPROVED_DAYS)


def summarize_guides() -> list[dict]:
    guides = []
    for name in GUIDE_PATHS:
        path = ROOT / name
        words = count_words(path)
        guides.append(
            {
                "path": f"/{name}",
                "name": name.replace(".html", ""),
                "word_count": words,
                "status": "strong" if words >= 700 else "solid" if words >= 500 else "needs_growth",
            }
        )
    return guides


def collect_site_entries() -> list[dict]:
    markdown_entries = tag_index.collect_markdown_entries()
    html_entries = tag_index.collect_html_only_entries({entry["url"] for entry in markdown_entries})
    return tag_index.dedupe_entries(markdown_entries + html_entries)


def top_pages(entries: list[dict]) -> list[dict]:
    ranked = sorted(
        [entry for entry in entries if not tag_index.is_low_value_entry(entry)],
        key=tag_index.entry_priority,
    )
    result = []
    for entry in ranked[:8]:
        result.append(
            {
                "title": entry["title"],
                "url": entry["url"],
                "type": entry["type"],
                "quality_band": entry["quality_band"],
                "word_count": entry.get("word_count", 0),
            }
        )
    return result


def choose_revenue_priorities(entries: list[dict], guides: list[dict], queue: dict, lab_state: dict) -> list[dict]:
    priorities: list[dict] = []
    weak_guides = [guide for guide in guides if guide["word_count"] < 700]
    if weak_guides:
        guide = sorted(weak_guides, key=lambda item: item["word_count"])[0]
        priorities.append(
            {
                "label": "대표 가이드 보강",
                "reason": f"{guide['name']} 분량이 {guide['word_count']}단어로 아직 짧아 검색 자산 페이지로 더 키울 여지가 큽니다.",
                "target": guide["path"],
            }
        )

    queue_count = len(queue.get("queued_titles", []))
    if queue_count:
        priorities.append(
            {
                "label": "대기 논문 선별 유지",
                "reason": f"발행 대기 논문이 {queue_count}건 있어도 메인 발행은 주 1~2회만 유지하는 것이 품질과 승인 관점에서 안전합니다.",
                "target": "/AUTOMATION.html",
            }
        )

    lab_posts = lab_state.get("lab_posts") or []
    if len(lab_posts) < 2:
        priorities.append(
            {
                "label": "실험실 연속성 확보",
                "reason": "실험실 글이 아직 1편 수준이라, 한 편만 더 쌓여도 주간 검증 섹션의 신뢰도가 크게 올라갑니다.",
                "target": "/LAB.html",
            }
        )

    posts = [
        entry
        for entry in entries
        if entry.get("type") == "Post"
        and entry.get("quality_band") != "strong"
        and not tag_index.is_low_value_entry(entry)
    ]
    candidate_posts = [
        entry
        for entry in posts
        if not (
            was_recently_improved(entry)
            and entry.get("word_count", 0) >= 320
            and entry.get("quality_band") == "solid"
        )
    ]
    if not candidate_posts:
        candidate_posts = posts
    if candidate_posts:
        post = sorted(
            candidate_posts,
            key=lambda item: (
                item.get("quality_score", 0),
                item.get("word_count", 0),
                item["date"],
            ),
        )[0]
        priorities.append(
            {
                "label": "심층 포스트 추가 보강",
                "reason": f"{post['title']}는 이미 해설형이지만 아직 더 두꺼워질 여지가 있습니다.",
                "target": post["url"],
            }
        )
    return priorities[:4]


def build_payload() -> dict:
    entries = collect_site_entries()
    guides = summarize_guides()
    quality = load_json(QUALITY_REPORT_FILE)
    queue = load_json(QUEUE_FILE)
    lab_state = load_json(LAB_STATE_FILE)

    payload = {
        "generated_at": dt.datetime.now().astimezone().isoformat(timespec="minutes"),
        "entry_count": len(entries),
        "thin_or_weak_count": quality.get("thin_or_weak_count", 0),
        "queued_count": len(queue.get("queued_titles", [])),
        "lab_post_count": len(lab_state.get("lab_posts", [])),
        "guides": guides,
        "top_pages": top_pages(entries),
        "priorities": choose_revenue_priorities(entries, guides, queue, lab_state),
    }
    return payload


def render_html(payload: dict) -> str:
    guide_cards = "\n".join(
        f'''        <article class="metric-card">
          <div class="label">{guide["name"]}</div>
          <div class="value">{guide["word_count"]}</div>
          <p>{guide["status"]}</p>
        </article>'''
        for guide in payload["guides"]
    )
    top_links = "\n".join(
        f'''          <a href="{item["url"]}"><strong>{item["title"]}</strong><span>{item["type"]} · {item["quality_band"]}</span></a>'''
        for item in payload["top_pages"]
    )
    priorities = "\n".join(
        f'''        <article class="priority-card">
          <h2>{item["label"]}</h2>
          <p>{item["reason"]}</p>
          <a href="{item["target"]}">바로 보기</a>
        </article>'''
        for item in payload["priorities"]
    )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Growth Report | MALT Tech Blog</title>
  <meta name="description" content="MALT Tech Blog 수익화 우선순위와 자기 보완 루프를 보여주는 성장 리포트" />
  <link rel="stylesheet" href="./assets/hud.css" />
  <style>
    .hero{{margin-top:14px;padding:22px}}
    .hero h1{{margin:6px 0 10px;font-size:34px;line-height:1.15;max-width:15ch}}
    .hero p{{margin:0;color:var(--muted);line-height:1.7;max-width:70ch}}
    .stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:16px}}
    .metric-card,.priority-card{{background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(247,251,254,.98));border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 14px 30px rgba(24,54,84,.06)}}
    .metric-card .label{{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}}
    .metric-card .value{{font-size:30px;font-weight:800;line-height:1.1;margin:8px 0}}
    .metric-card p{{margin:0;color:var(--muted)}}
    .section{{margin-top:16px}}
    .priority-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}}
    .priority-card h2{{margin:0 0 8px;font-size:20px;line-height:1.3}}
    .priority-card p{{margin:0;color:var(--muted);line-height:1.7}}
    .priority-card a{{display:inline-block;margin-top:12px;font-weight:700}}
    .top-list{{display:grid;gap:10px}}
    .top-list a{{display:flex;justify-content:space-between;gap:12px;padding:14px;border:1px solid #d6e3ee;border-radius:14px;background:#fff;text-decoration:none;color:var(--text)}}
    .top-list strong{{display:block;line-height:1.45}}
    .top-list span{{font-size:13px;color:var(--muted);white-space:nowrap}}
    @media (max-width:900px){{.stats,.priority-grid{{grid-template-columns:1fr}} .hero h1{{font-size:28px;max-width:none}} .top-list a{{display:block}} .top-list span{{display:block;margin-top:6px;white-space:normal}}}}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div class="brand">GROWTH · MALT HUD</div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <a class="badge" href="./index.html">HOME</a>
        <a class="badge" href="./AUTOMATION.html">AUTOMATION</a>
        <a class="badge" href="./GUIDES.html">GUIDES</a>
      </div>
    </div>
    <section class="card hero">
      <div class="h">Revenue-Oriented Improvement Loop</div>
      <h1>다음에 무엇을 보완하면 수익 가능성이 더 올라가는지 자동으로 보여주는 페이지</h1>
      <p>이 리포트는 콘텐츠 품질, 대표 가이드 분량, 주간 실험실 축적 상태, 발행 대기 풀을 함께 읽어서 MALT가 다음에 무엇을 우선 고치면 좋은지 보여줍니다. 한 번 고치고 끝나는 구조가 아니라, 상태를 보고 계속 보완할 수 있게 만드는 것이 목표입니다.</p>
      <p class="tiny">Generated at: {payload["generated_at"]}</p>
    </section>

    <section class="stats">
      <article class="metric-card"><div class="label">Entries</div><div class="value">{payload["entry_count"]}</div><p>공개 항목 수</p></article>
      <article class="metric-card"><div class="label">Thin / Weak</div><div class="value">{payload["thin_or_weak_count"]}</div><p>낮을수록 좋음</p></article>
      <article class="metric-card"><div class="label">Queued</div><div class="value">{payload["queued_count"]}</div><p>대기 논문 수</p></article>
      <article class="metric-card"><div class="label">Lab Posts</div><div class="value">{payload["lab_post_count"]}</div><p>주간 실험실 누적</p></article>
    </section>

    <section class="section">
      <div class="card">
        <div class="h">Next Best Actions</div>
        <div class="priority-grid">
{priorities}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="card">
        <div class="h">Guide Depth</div>
        <div class="stats">
{guide_cards}
        </div>
      </div>
    </section>

    <section class="section">
      <div class="card">
        <div class="h">Current Best Assets</div>
        <div class="top-list">
{top_links}
        </div>
      </div>
    </section>
  </div>
</body>
</html>
"""


def main() -> int:
    payload = build_payload()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    OUTPUT_HTML.write_text(render_html(payload), encoding="utf-8")
    print(json.dumps({"growth_html": str(OUTPUT_HTML.relative_to(ROOT)), "growth_json": str(OUTPUT_JSON.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
