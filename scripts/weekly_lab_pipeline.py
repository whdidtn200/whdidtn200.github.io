#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import re


ROOT = pathlib.Path(__file__).resolve().parent.parent
PUBLISHED_DIR = ROOT / "content" / "archive" / "published"
STATE_DIR = ROOT / "content" / "archive" / "state"
STATE_FILE = STATE_DIR / "lab_publish_state.json"
POSTS_DIR = ROOT / "posts"
POSTS_INDEX = ROOT / "posts.html"
LAB_HUB = ROOT / "LAB.html"

TOPIC_PRIORITY = {
    "railway-phm": 0,
    "bearing-diagnosis": 1,
    "agent-ops": 2,
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9가-힣\\s-]", "", value)
    value = re.sub(r"\\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "weekly-lab-note"


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"published_sources": [], "lab_posts": []}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def load_candidates() -> list[dict]:
    items = []
    for path in sorted(PUBLISHED_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["_path"] = path
        items.append(payload)
    return items


def has_lab_value(source: dict) -> bool:
    merged = f"{source.get('title', '')} {source.get('abstract', '')}".lower()
    signals = [
        "experiment",
        "benchmark",
        "validation",
        "cross-domain",
        "cross dataset",
        "cross-condition",
        "bearing",
        "railway",
        "fault diagnosis",
        "condition monitoring",
        "real-time",
    ]
    return any(signal in merged for signal in signals)


def candidate_score(source: dict) -> tuple:
    context = source.get("paper_context") or {}
    experiment = context.get("experiment", "")
    analysis = source.get("analysis") or {}
    merged = f"{source.get('title', '')} {source.get('abstract', '')}".lower()
    return (
        0 if experiment else 1,
        0 if has_lab_value(source) else 1,
        TOPIC_PRIORITY.get(source.get("topic", ""), 9),
        0 if analysis.get("operational_takeaways") else 1,
        0 if any(token in merged for token in ["railway", "bearing", "fault", "condition monitoring"]) else 1,
        source.get("published_at", ""),
    )


def choose_candidate(state: dict) -> dict | None:
    published_sources = set(state.get("published_sources", []))
    candidates = [
        source
        for source in load_candidates()
        if source["_path"].name not in published_sources and has_lab_value(source)
    ]
    if not candidates:
        return None
    candidates.sort(key=candidate_score)
    return candidates[0]


def lab_post_basename(source: dict) -> str:
    today = dt.date.today().isoformat()
    short_slug = slugify(source.get("title", ""))[:72].strip("-")
    return f"{today}-lab-{short_slug}"


def build_lab_title(source: dict) -> str:
    return f"[시험실] {source.get('title', 'Untitled Paper')}: 재현 관점에서 다시 읽기"


def build_retest_points(source: dict) -> list[str]:
    context = source.get("paper_context") or {}
    analysis = source.get("analysis") or {}
    merged = f"{source.get('title', '')} {source.get('abstract', '')}".lower()
    points = []
    if context.get("experiment"):
        points.append("논문이 제시한 실험 조건과 데이터 분할 방식이 데이터 누출 없이 재현 가능한지 다시 확인합니다.")
    if "cross" in merged or "domain" in merged:
        points.append("교차 조건 또는 교차 데이터셋 일반화가 실제로 유지되는지 별도 검증 기준을 둡니다.")
    if "real-time" in merged or "online" in merged:
        points.append("실시간 또는 온라인 감시를 주장하는 경우, 지연 시간과 오탐 부담을 함께 다시 봅니다.")
    if not points:
        points.append("정확도 숫자만 복제하지 않고, 운영 의사결정에 필요한 기준선이 재현되는지를 먼저 확인합니다.")
    points.extend((analysis.get("limitations") or [])[:2])
    return points[:4]


def build_metrics_to_watch(source: dict) -> list[str]:
    context = source.get("paper_context") or {}
    experiment = context.get("experiment", "")
    metrics = []
    metric_pattern = re.compile(r"\\b(?:AP|mAP|F1|AUC|Recall|Precision|Accuracy|IoU|FPS)\\s*(?:=|:)?\\s*[\\d.]+%?\\b", re.I)
    for match in metric_pattern.findall(experiment):
        cleaned = re.sub(r"\\s+", " ", match).strip()
        if cleaned not in metrics:
            metrics.append(cleaned)
    if not metrics:
        metrics = ["Accuracy / F1", "False alarm burden", "Cross-condition robustness"]
    return metrics[:4]


def render_sources(source: dict, basename: str) -> str:
    lines = [
        f"- [원문 논문]({next((item.get('url') for item in source.get('sources', []) if item.get('label') == 'arXiv abs'), source.get('entry_id', '#'))})",
        f"- [기존 일간 해설](/posts/{source.get('slug')}.html)",
        f"- [시험실 허브](/LAB.html)",
    ]
    pdf_url = next((item.get("url") for item in source.get("sources", []) if item.get("label") == "arXiv pdf"), "")
    if pdf_url:
        lines.insert(1, f"- [PDF]({pdf_url})")
    return "\\n".join(lines)


def render_markdown(source: dict) -> str:
    basename = lab_post_basename(source)
    title = build_lab_title(source)
    analysis = source.get("analysis") or {}
    review = source.get("review") or {}
    context = source.get("paper_context") or {}
    published_date = dt.date.today().isoformat()
    metrics = build_metrics_to_watch(source)
    retest = build_retest_points(source)
    retest_block = "".join(f"- {item}\n" for item in retest)
    metrics_block = "".join(f"- {item}\n" for item in metrics)
    operational_block = "".join(
        f"- {item}\n"
        for item in (analysis.get("operational_takeaways") or ["현장 데이터 조건과 경보 흐름을 함께 점검해야 합니다."])[:4]
    )
    tags = ["시험실", "Validation", "Reproduction", *(source.get("tags") or [])[:4]]
    categories = ["lab", "validation", *(source.get("categories") or [])[:2]]
    return f"""---
title: "{title}"
date: {published_date}
slug: "{basename}"
categories: [{", ".join(json.dumps(item, ensure_ascii=False) for item in categories)}]
tags: [{", ".join(json.dumps(item, ensure_ascii=False) for item in tags)}]
generated_by: "MALT"
workflow: "weekly-lab-publication"
---

# {title}

이 글은 <strong>MALT 주간 시험실 파이프라인</strong>이 발행하는 자동 검토본입니다. 일반 일간 요약과 달리, 논문의 주장과 실험 조건을 `재현 가능성`, `운영 적용성`, `검증 리스크` 관점으로 다시 읽습니다.

## 왜 이 논문을 시험실 후보로 골랐나
- {review.get("why_selected", "철도 PHM 및 운영 자동화 관점에서 다시 검토할 가치가 있는 주제입니다.")}
- {analysis.get("why_now", "운영 현장에서 흔들릴 가능성이 큰 조건을 포함하고 있어 깊게 볼 가치가 있습니다.")}
- 원문 공개일: {source.get("published_at", "n/a")}

## 논문이 주장하는 핵심
- {analysis.get("one_line", source.get("abstract", "")[:180])}
- {analysis.get("problem", "현장 적용 전에 실험 조건과 한계를 함께 봐야 합니다.")}
- {analysis.get("method_overview", "방법론보다 운영에 연결되는 구조를 먼저 읽는 편이 좋습니다.")}

## 시험실에서 다시 확인할 항목
{retest_block}

## 다시 봐야 할 지표와 실험 조건
{metrics_block}
- {analysis.get("experiment_read", "최고 수치보다도 다른 조건에서 결과가 유지되는지 먼저 보는 편이 맞습니다.")}
- {((context.get("experiment") or source.get("abstract", ""))[:280]).strip()}

## 운영 적용 판단
{operational_block}

## 1차 판정
- {review.get("interpretation", "단순 성능 수치보다 운영 연결성 기준으로 보는 편이 낫습니다.")}
- {review.get("applicability", "직접 도입보다는 파일럿 검증을 먼저 붙이는 접근이 안전합니다.")}
- 결론적으로 이 논문은 `바로 운영 투입`보다 `재현 실험과 경보 기준선 검토`를 먼저 해볼 가치가 있는 후보로 분류합니다.

## 출처
{render_sources(source, basename)}

## 발행 메모
- MALT 큐레이션 자동 발행본
- AI가 생성한 주간 시험실 리뷰
- 주기: 매주 수요일 오전 10시(KST) 후보 1건 검토
"""


def render_html(source: dict) -> str:
    title = build_lab_title(source)
    analysis = source.get("analysis") or {}
    review = source.get("review") or {}
    context = source.get("paper_context") or {}
    retest = build_retest_points(source)
    metrics = build_metrics_to_watch(source)
    operational = (analysis.get("operational_takeaways") or ["현장 데이터 조건과 경보 흐름을 함께 점검해야 합니다."])[:4]
    experiment_excerpt = ((context.get("experiment") or source.get("abstract", ""))[:280]).strip()

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)} | MALT Tech Blog</title>
  <meta name="description" content="MALT 시험실이 논문을 재현 관점에서 다시 읽는 주간 검토 페이지" />
  <meta property="article:published_time" content="{dt.datetime.now().astimezone().isoformat(timespec='minutes')}" />
  <style>
    body{{margin:0;font-family:"Pretendard","Avenir Next","Segoe UI",sans-serif;background:#edf4f7;color:#10253a;line-height:1.75}}
    .wrap{{max-width:920px;margin:0 auto;padding:28px 16px 48px}}
    .hero{{padding:24px;border:1px solid #c7d8e5;border-radius:20px;background:linear-gradient(180deg,rgba(255,255,255,.98),rgba(245,250,253,.98));box-shadow:0 16px 36px rgba(24,54,84,.08)}}
    .eyebrow{{font-size:12px;letter-spacing:.12em;color:#0b8b95;font-weight:700}}
    h1{{margin:10px 0 12px;font-size:34px;line-height:1.12;color:#0d1a28}}
    h2{{margin:28px 0 10px;font-size:22px;color:#10253a}}
    p,li{{font-size:16px;color:#42586d}}
    .meta{{margin-top:10px;font-size:13px;color:#5f738a}}
    .card{{margin-top:16px;padding:22px;border:1px solid #d3e1eb;border-radius:18px;background:#fff}}
    a{{color:#1f5fd6}}
    ul{{padding-left:20px}}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="hero">
      <div class="eyebrow">MALT TESTING LAB</div>
      <h1>{html.escape(title)}</h1>
      <p>일간 요약이 아니라, 재현 가치가 있는 논문을 골라 실험 조건과 운영 적합성을 다시 읽는 주간 시험실 발행본입니다.</p>
      <div class="meta">발행일: {dt.date.today().isoformat()} · 허브: <a href="/LAB.html">LAB</a> · 전체 글: <a href="/posts.html">Posts</a></div>
    </section>
    <article class="card">
      <h2>왜 이 논문을 시험실 후보로 골랐나</h2>
      <ul>
        <li>{html.escape(review.get("why_selected", "철도 PHM 및 운영 자동화 관점에서 다시 검토할 가치가 있는 주제입니다."))}</li>
        <li>{html.escape(analysis.get("why_now", "운영 현장에서 흔들릴 가능성이 큰 조건을 포함하고 있어 깊게 볼 가치가 있습니다."))}</li>
        <li>원문 공개일: {html.escape(source.get("published_at", "n/a"))}</li>
      </ul>

      <h2>논문이 주장하는 핵심</h2>
      <ul>
        <li>{html.escape(analysis.get("one_line", source.get("abstract", "")[:180]))}</li>
        <li>{html.escape(analysis.get("problem", "현장 적용 전에 실험 조건과 한계를 함께 봐야 합니다."))}</li>
        <li>{html.escape(analysis.get("method_overview", "방법론보다 운영에 연결되는 구조를 먼저 읽는 편이 좋습니다."))}</li>
      </ul>

      <h2>시험실에서 다시 확인할 항목</h2>
      <ul>
        {"".join(f"<li>{html.escape(item)}</li>" for item in retest)}
      </ul>

      <h2>다시 봐야 할 지표와 실험 조건</h2>
      <ul>
        {"".join(f"<li>{html.escape(item)}</li>" for item in metrics)}
        <li>{html.escape(analysis.get("experiment_read", "최고 수치보다도 다른 조건에서 결과가 유지되는지 먼저 보는 편이 맞습니다."))}</li>
      </ul>
      <p>{html.escape(experiment_excerpt)}</p>

      <h2>운영 적용 판단</h2>
      <ul>
        {"".join(f"<li>{html.escape(item)}</li>" for item in operational)}
      </ul>

      <h2>1차 판정</h2>
      <ul>
        <li>{html.escape(review.get("interpretation", "단순 성능 수치보다 운영 연결성 기준으로 보는 편이 낫습니다."))}</li>
        <li>{html.escape(review.get("applicability", "직접 도입보다는 파일럿 검증을 먼저 붙이는 접근이 안전합니다."))}</li>
        <li>결론적으로 이 논문은 바로 운영 투입보다 재현 실험과 경보 기준선 검토를 먼저 해볼 가치가 있는 후보로 분류합니다.</li>
      </ul>

      <h2>출처</h2>
      <ul>
        <li><a href="{html.escape(next((item.get('url') for item in source.get('sources', []) if item.get('label') == 'arXiv abs'), source.get('entry_id', '#')))}">원문 논문</a></li>
        <li><a href="/posts/{html.escape(source.get('slug', ''))}.html">기존 일간 해설</a></li>
        <li><a href="/LAB.html">시험실 허브</a></li>
      </ul>
    </article>
  </main>
</body>
</html>
"""


def write_post_files(source: dict) -> tuple[pathlib.Path, pathlib.Path]:
    basename = lab_post_basename(source)
    md_path = POSTS_DIR / f"{basename}.md"
    html_path = POSTS_DIR / f"{basename}.html"
    md_path.write_text(render_markdown(source), encoding="utf-8")
    html_path.write_text(render_html(source), encoding="utf-8")
    return md_path, html_path


def update_posts_listing(title: str, html_filename: str) -> None:
    content = POSTS_INDEX.read_text(encoding="utf-8")
    marker = '<ul class="archive-grid">'
    list_start = content.find(marker)
    list_end = content.find("</ul>", list_start)
    if list_start == -1 or list_end == -1:
        raise SystemExit("posts.html list block not found")
    new_item = f'  <li><a href="/posts/{html_filename}">{html.escape(title)}</a></li>\\n'
    block = content[list_start + len(marker):list_end]
    if new_item.strip() in block:
        return
    new_block = "\\n" + new_item + block.lstrip("\\n")
    POSTS_INDEX.write_text(content[:list_start + len(marker)] + new_block + content[list_end:], encoding="utf-8")


def update_lab_hub(state: dict) -> None:
    entries = []
    for item in reversed(state.get("lab_posts", [])[-4:]):
        entries.append(
            f'''      <article class="lab-card">
        <div class="eyebrow">Weekly Lab Automation</div>
        <h2>{html.escape(item["title"])}</h2>
        <p>{html.escape(item["summary"])}</p>
        <a href="/posts/{item["html_filename"]}">리포트 읽기</a>
      </article>'''
        )
    if not entries:
        entries = [
            '''      <article class="lab-card">
        <div class="eyebrow">Weekly Lab Automation</div>
        <h2>주간 시험실 발행이 여기에 쌓입니다</h2>
        <p>매주 한 편씩, 재현 가치가 높은 논문을 골라 실험 조건, 지표, 운영 한계를 다시 읽는 시험실 글이 이 영역에 추가됩니다.</p>
        <a href="./posts.html">전체 글 보기</a>
      </article>'''
        ]
    content = LAB_HUB.read_text(encoding="utf-8")
    start_marker = "<!-- LAB_AUTOGEN_START -->"
    end_marker = "<!-- LAB_AUTOGEN_END -->"
    start = content.find(start_marker)
    end = content.find(end_marker, start)
    if start == -1 or end == -1:
        raise SystemExit("LAB.html autogen markers not found")
    replacement = start_marker + "\n" + "\n".join(entries) + "\n      "
    LAB_HUB.write_text(content[:start] + replacement + content[end:], encoding="utf-8")


def publish_once() -> dict | None:
    state = load_state()
    candidate = choose_candidate(state)
    if candidate is None:
        return None
    title = build_lab_title(candidate)
    md_path, html_path = write_post_files(candidate)
    update_posts_listing(title, html_path.name)
    state.setdefault("published_sources", []).append(candidate["_path"].name)
    state.setdefault("lab_posts", []).append(
        {
            "title": title,
            "html_filename": html_path.name,
            "summary": (candidate.get("analysis", {}).get("why_now") or candidate.get("abstract", ""))[:160].strip(),
            "source_title": candidate.get("title", ""),
        }
    )
    state["lab_posts"] = state["lab_posts"][-12:]
    save_state(state)
    update_lab_hub(state)
    return {
        "source_title": candidate["title"],
        "post_title": title,
        "md_path": str(md_path.relative_to(ROOT)),
        "html_path": str(html_path.relative_to(ROOT)),
        "source_path": str(candidate["_path"].relative_to(ROOT)),
    }


if __name__ == "__main__":
    result = publish_once()
    if result is None:
        print("no weekly lab candidate available")
    else:
        print(json.dumps(result, ensure_ascii=False))
