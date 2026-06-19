#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import html
import json
import pathlib
import re
from collections import defaultdict

import yaml


ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "posts"
DRAFTS_DIR = ROOT / "content" / "drafts"
TAGS_DIR = ROOT / "tags"
STATE_DIR = ROOT / "content" / "archive" / "state"
STATE_FILE = STATE_DIR / "tag_index.json"
QUALITY_REPORT_FILE = STATE_DIR / "content_quality_report.json"
POSTS_INDEX = ROOT / "posts.html"
LOW_VALUE_SLUGS = {
    "2026-02-25-FFT-1DCNN-Train-Fault-Diagnosis",
    "2026-02-24-continual-learning-railway-wheel-fault",
}

TAG_HINTS = [
    (["railway", "metro", "track", "wheel", "bogie"], ["Railway"]),
    (["bearing", "wheelset", "rolling bearing"], ["Bearing"]),
    (["phm", "predictive maintenance", "condition monitoring", "cbm", "pdm"], ["PHM", "Condition Monitoring"]),
    (["fault diagnosis", "anomaly detection", "diagnosis"], ["Fault Diagnosis"]),
    (["wayside", "wayside monitoring"], ["Wayside"]),
    (["sensor", "sensing", "vibration", "acoustic", "ae"], ["Sensors"]),
    (["agent", "agentic", "llm", "runtime"], ["Agentic AI"]),
    (["observability", "monitoring", "audit"], ["Observability"]),
    (["validation", "reproduction", "benchmark", "experiment", "lab"], ["Validation", "실험실"]),
    (["guide", "playbook", "editorial"], ["Guide"]),
    (["maintenance", "repair", "asset"], ["Maintenance"]),
]

ACRONYM_MAP = {
    "phm": "PHM",
    "pdm": "PdM",
    "cbm": "CBM",
    "kpi": "KPI",
    "roi": "ROI",
    "ae": "AE",
    "llm": "LLM",
    "wild": "WILD",
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9가-힣\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "tag"


def parse_front_matter(text: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", text, re.S)
    if not match:
        return {}, text
    meta = yaml.safe_load(match.group(1)) or {}
    body = text[match.end() :]
    return meta, body


def parse_date(raw: object, fallback: str) -> str:
    if raw is not None:
        value = str(raw).strip()
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
            try:
                return dt.datetime.strptime(value, fmt).date().isoformat()
            except ValueError:
                continue
        try:
            return dt.date.fromisoformat(value[:10]).isoformat()
        except ValueError:
            pass
    match = re.match(r"(\d{4}-\d{2}-\d{2})", fallback)
    return match.group(1) if match else dt.date.today().isoformat()


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def first_paragraph(text: str, limit: int = 170) -> str:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    for chunk in chunks:
        if chunk.startswith("#") or chunk.startswith("- ") or chunk.startswith("**") or chunk.startswith("---"):
            continue
        line = clean_text(chunk)
        if len(line) > 30:
            return line[:limit].rstrip() + ("..." if len(line) > limit else "")
    cleaned = clean_text(text)
    return cleaned[:limit].rstrip() + ("..." if len(cleaned) > limit else "")


def humanize_token(token: str) -> str:
    token = str(token).strip()
    if not token:
        return ""
    mapped = ACRONYM_MAP.get(token.lower())
    if mapped:
        return mapped
    if re.search(r"[가-힣]", token):
        return token
    if token.isupper():
        return token
    if "-" in token or "_" in token:
        parts = re.split(r"[-_]+", token)
        return " ".join(part.upper() if part.isupper() else part.title() for part in parts if part)
    if token.islower():
        return token.title()
    return token


def normalize_tags(raw_tags: list[object], raw_categories: list[object]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for item in list(raw_tags or []) + list(raw_categories or []):
        label = humanize_token(str(item))
        key = slugify(label)
        if label and key not in seen:
            merged.append(label)
            seen.add(key)
    return merged


def infer_tags(title: str, body: str) -> list[str]:
    merged = f"{title} {body}".lower()
    inferred: list[str] = []
    for keywords, labels in TAG_HINTS:
        if any(keyword in merged for keyword in keywords):
            for label in labels:
                if label not in inferred:
                    inferred.append(label)
    return inferred


def looks_like_slug(title: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9-]{18,}", title.strip()))


def read_html_title(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
    chosen = clean_text((h1_match or title_match).group(1) if (h1_match or title_match) else "")
    chosen = re.sub(r"\s*\|\s*MALT Tech Blog\s*$", "", chosen)
    return chosen


def detect_entry_type(url: str, tags: list[str], title: str) -> str:
    lowered = title.lower()
    if "/posts/" in url and any(tag in tags for tag in ["실험실", "Validation"]):
        return "Lab"
    if "/posts/" in url and "[arxiv daily]" in lowered:
        return "Daily arXiv"
    if "/posts/" in url:
        return "Post"
    if "Guide" in title or "guide" in lowered:
        return "Guide"
    return "Page"


def compute_quality(entry: dict) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []
    words = int(entry.get("word_count", 0))
    kind = entry.get("type", "Post")
    summary = entry.get("summary", "")
    title = entry.get("title", "")
    tags = entry.get("tags", [])

    if words >= 1000:
        score += 5
        reasons.append("긴 본문")
    elif words >= 700:
        score += 4
        reasons.append("충분한 본문")
    elif words >= 500:
        score += 3
        reasons.append("중간 이상 본문")
    elif words >= 350:
        score += 2
        reasons.append("기본 분량 충족")
    elif words >= 220:
        score += 1
        reasons.append("최소 분량")
    else:
        reasons.append("짧은 본문")

    if kind == "Guide":
        score += 3
        reasons.append("가이드형")
    elif kind == "Lab":
        score += 3
        reasons.append("실험실형")
    elif kind == "Post":
        score += 2
        reasons.append("해설형")
    elif kind == "Daily arXiv":
        score += 1
        reasons.append("일간 해설형")

    if len(summary) >= 140:
        score += 1
        reasons.append("요약 밀도 양호")
    if len(tags) >= 4:
        score += 1
        reasons.append("주제 연결성")

    merged = f"{title} {summary}"
    if any(token in merged for token in ["삭제됨", "중복 발행 정리", "보존 처리"]):
        score -= 5
        reasons.append("중복/공지성")
    if kind == "Daily arXiv" and words < 320:
        score -= 3
        reasons.append("얇은 일간 글")
    elif kind in {"Post", "Page"} and words < 220:
        score -= 2
        reasons.append("얇은 해설")

    if score >= 8:
        band = "strong"
    elif score >= 5:
        band = "solid"
    elif score >= 2:
        band = "thin"
    else:
        band = "weak"
    return score, band, reasons


def entry_priority(entry: dict) -> tuple[int, int, int, int]:
    type_rank = {
        "Guide": 0,
        "Lab": 1,
        "Post": 2,
        "Daily arXiv": 3,
        "Page": 4,
    }
    band_rank = {
        "strong": 0,
        "solid": 1,
        "thin": 2,
        "weak": 3,
    }
    date_rank = int(str(entry.get("date", "1900-01-01")).replace("-", ""))
    return (
        band_rank.get(entry.get("quality_band", "solid"), 9),
        type_rank.get(entry.get("type", "Post"), 9),
        -date_rank,
        -int(entry.get("quality_score", 0)),
    )


def build_entry(url: str, title: str, date: str, summary: str, tags: list[str]) -> dict:
    all_tags = list(tags)
    for inferred in infer_tags(title, summary):
        if inferred not in all_tags:
            all_tags.append(inferred)
    entry = {
        "title": title.strip(),
        "url": url,
        "date": date,
        "summary": summary,
        "tags": all_tags,
        "type": detect_entry_type(url, all_tags, title),
    }
    score, band, reasons = compute_quality(entry)
    entry["quality_score"] = score
    entry["quality_band"] = band
    entry["quality_reasons"] = reasons
    return entry


def entry_slug(entry: dict) -> str:
    return pathlib.Path(entry["url"]).stem


def is_low_value_entry(entry: dict) -> bool:
    title = entry.get("title", "")
    summary = entry.get("summary", "")
    slug = entry_slug(entry)
    merged = f"{title} {summary}"
    if slug in LOW_VALUE_SLUGS:
        return True
    return any(token in merged for token in ["삭제됨", "중복 발행 정리", "보존 처리되었습니다", "대체 문서"])


def collect_markdown_entries() -> list[dict]:
    entries: list[dict] = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        heading_match = re.search(r"^#\s+(.+)$", body, re.M)
        title = str(meta.get("title") or (heading_match.group(1).strip() if heading_match else path.stem))
        if looks_like_slug(title):
            html_title = read_html_title(POSTS_DIR / f"{path.stem}.html")
            if html_title:
                title = html_title
        date = parse_date(meta.get("date"), path.stem)
        tags = normalize_tags(meta.get("tags") or [], meta.get("categories") or [])
        summary = first_paragraph(body)
        entry = build_entry(f"/posts/{path.stem}.html", title, date, summary, tags)
        entry["word_count"] = len(re.findall(r"\S+", body))
        score, band, reasons = compute_quality(entry)
        entry["quality_score"] = score
        entry["quality_band"] = band
        entry["quality_reasons"] = reasons
        entries.append(entry)

    for path in sorted(DRAFTS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(text)
        slug = str(meta.get("slug") or path.stem)
        html_path = ROOT / f"{slug}.html"
        if not html_path.exists():
            continue
        title = str(meta.get("title") or slug)
        date = parse_date(meta.get("date"), path.stem)
        tags = normalize_tags(meta.get("tags") or [], meta.get("categories") or [])
        summary = first_paragraph(body)
        entry = build_entry(f"/{slug}.html", title, date, summary, tags)
        entry["word_count"] = len(re.findall(r"\S+", body))
        score, band, reasons = compute_quality(entry)
        entry["quality_score"] = score
        entry["quality_band"] = band
        entry["quality_reasons"] = reasons
        entries.append(entry)
    return entries


def collect_html_only_entries(existing_urls: set[str]) -> list[dict]:
    entries: list[dict] = []
    for path in sorted(POSTS_DIR.glob("*.html")):
        url = f"/posts/{path.stem}.html"
        if url in existing_urls:
            continue
        text = path.read_text(encoding="utf-8")
        title_match = re.search(r"<title>(.*?)</title>", text, re.I | re.S)
        h1_match = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
        paragraph_match = re.search(r"<p>(.*?)</p>", text, re.I | re.S)
        title = clean_text((h1_match or title_match).group(1) if (h1_match or title_match) else path.stem)
        title = re.sub(r"\s*\|\s*MALT Tech Blog\s*$", "", title)
        summary = clean_text(paragraph_match.group(1)) if paragraph_match else ""
        date = parse_date(None, path.stem)
        entry = build_entry(url, title, date, summary, [])
        entry["word_count"] = len(re.findall(r"\S+", clean_text(text)))
        score, band, reasons = compute_quality(entry)
        entry["quality_score"] = score
        entry["quality_band"] = band
        entry["quality_reasons"] = reasons
        entries.append(entry)
    return entries


def dedupe_entries(entries: list[dict]) -> list[dict]:
    deduped: dict[str, dict] = {}
    for entry in entries:
        current = deduped.get(entry["url"])
        if current is None:
            deduped[entry["url"]] = entry
            continue
        if len(entry.get("tags", [])) > len(current.get("tags", [])):
            deduped[entry["url"]] = entry
    return sorted(deduped.values(), key=lambda item: (item["date"], item["title"]), reverse=True)


def group_by_tag(entries: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        if is_low_value_entry(entry):
            continue
        for tag in entry.get("tags", []):
            grouped[tag].append(entry)
    for tag, items in grouped.items():
        grouped[tag] = sorted(
            items,
            key=lambda item: (
                {"strong": 3, "solid": 2, "thin": 1, "weak": 0}.get(item.get("quality_band", "solid"), 0),
                item.get("quality_score", 0),
                item["date"],
                item["title"],
            ),
            reverse=True,
        )
    return dict(sorted(grouped.items(), key=lambda pair: (-len(pair[1]), pair[0].lower())))


def render_tag_overview(grouped: dict[str, list[dict]], total_entries: int) -> str:
    top_tags = list(grouped.items())[:18]
    chips = "\n".join(
        f'            <a class="tag-chip" href="/tags/{slugify(tag)}.html">{html.escape(tag)} <span>{len(items)}</span></a>'
        for tag, items in top_tags
    )
    if not chips:
        chips = '            <span class="tag-empty">태그 데이터가 아직 없습니다.</span>'
    return f"""        <div class="section-head">
          <h2>태그로 탐색</h2>
          <p>{total_entries}개 항목을 태그 축으로 다시 묶었습니다. 주제별로 이어 읽기 좋게 설계했습니다.</p>
        </div>
        <div class="tag-cloud">
{chips}
        </div>"""


def update_posts_overview(grouped: dict[str, list[dict]], total_entries: int) -> None:
    content = POSTS_INDEX.read_text(encoding="utf-8")
    start_marker = "<!-- TAG_OVERVIEW_AUTOGEN_START -->"
    end_marker = "<!-- TAG_OVERVIEW_AUTOGEN_END -->"
    start = content.find(start_marker)
    end = content.find(end_marker)
    if start == -1 or end == -1:
        raise SystemExit("posts.html tag overview markers not found")
    block = render_tag_overview(grouped, total_entries)
    new_content = content[: start + len(start_marker)] + "\n" + block + "\n        " + content[end:]
    POSTS_INDEX.write_text(new_content, encoding="utf-8")


def prune_low_value_archive_links(entries: list[dict]) -> None:
    excluded = {entry["url"] for entry in entries if is_low_value_entry(entry)}
    if not excluded:
        return
    content = POSTS_INDEX.read_text(encoding="utf-8")
    filtered_lines = []
    for line in content.splitlines():
        if any(f'href="{url}"' in line for url in excluded):
            continue
        filtered_lines.append(line)
    POSTS_INDEX.write_text("\n".join(filtered_lines) + "\n", encoding="utf-8")


def apply_noindex_to_low_value_pages(entries: list[dict]) -> None:
    for entry in entries:
        if not is_low_value_entry(entry):
            continue
        path = ROOT / entry["url"].lstrip("/")
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        if 'name="robots"' not in content.lower():
            if "<head>" in content:
                content = content.replace("<head>", '<head>\n<meta name="robots" content="noindex,follow" />', 1)
            else:
                content = '<meta name="robots" content="noindex,follow" />\n' + content
        path.write_text(content, encoding="utf-8")


def render_tag_index(grouped: dict[str, list[dict]], total_entries: int) -> str:
    cards = []
    for tag, items in list(grouped.items())[:24]:
        lead = sorted(items, key=entry_priority)[0]
        cards.append(
            f'''        <a class="tag-card" href="/tags/{slugify(tag)}.html">
          <strong>{html.escape(tag)}</strong>
          <span>{len(items)}개 항목</span>
          <small>{html.escape(lead["title"])}</small>
        </a>'''
        )
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Tags | MALT Tech Blog</title>
  <meta name="description" content="MALT Tech Blog 태그 허브" />
  <style>
    :root {{
      --bg:#eef4f8; --panel:#ffffff; --line:#c9d9e7; --text:#15283d; --muted:#5f738a; --accent:#0f8aa8;
    }}
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:"Pretendard","SF Pro Display","Segoe UI",sans-serif;background:radial-gradient(900px 480px at 10% -10%, rgba(45,108,223,.12), transparent 60%), radial-gradient(900px 520px at 100% 0%, rgba(15,138,168,.10), transparent 58%), var(--bg);color:var(--text)}}
    .wrap{{max-width:1120px;margin:0 auto;padding:28px 16px 48px}}
    .shell{{border:1px solid var(--line);border-radius:22px;background:linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,251,254,.98));box-shadow:0 18px 54px rgba(24,54,84,.10);overflow:hidden}}
    .topbar{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:18px 20px;border-bottom:1px solid rgba(15,138,168,.12);background:linear-gradient(180deg, rgba(15,138,168,.08), transparent)}}
    .brand{{font-size:13px;letter-spacing:.16em;font-weight:800;color:var(--accent)}}
    .nav{{display:flex;gap:10px;flex-wrap:wrap}}
    .nav a{{color:var(--text);text-decoration:none;border:1px solid #d6e3ee;border-radius:999px;padding:8px 12px;font-size:13px;background:#fff}}
    .hero{{padding:24px 20px 8px}}
    .hero h1{{margin:8px 0 10px;font-size:38px;line-height:1.08}}
    .hero p{{margin:0;color:var(--muted);max-width:64ch;line-height:1.7}}
    .stats{{margin-top:14px;color:var(--muted);font-size:14px}}
    .tag-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;padding:18px 20px 22px}}
    .tag-card{{display:flex;flex-direction:column;gap:6px;padding:18px;border:1px solid #d6e3ee;border-radius:18px;background:linear-gradient(180deg,#fff,#f8fbfe);text-decoration:none;color:var(--text);box-shadow:0 8px 22px rgba(24,54,84,.05)}}
    .tag-card strong{{font-size:18px;color:#10253a}}
    .tag-card span{{font-size:13px;color:#0f8aa8;font-weight:700}}
    .tag-card small{{font-size:13px;color:var(--muted);line-height:1.55}}
    @media (max-width:900px){{.tag-grid{{grid-template-columns:1fr}} .hero h1{{font-size:30px}}}}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="shell">
      <header class="topbar">
        <div class="brand">MALT TAGS</div>
        <nav class="nav">
          <a href="/">Home</a>
          <a href="/posts.html">Posts</a>
          <a href="/GUIDES.html">Guides</a>
          <a href="/LAB.html">LAB</a>
        </nav>
      </header>
      <section class="hero">
        <div class="kicker">TAG HUB</div>
        <h1>모든 글을 주제 축으로 다시 묶는 태그 허브</h1>
        <p>날짜순 아카이브만으로는 이어 읽기가 어렵기 때문에, 가이드와 일간 글, 실험실 글을 태그 기준으로 다시 묶었습니다. 비슷한 문제를 다루는 글끼리 빠르게 연결해서 볼 수 있습니다.</p>
        <div class="stats">총 {total_entries}개 항목 · 태그 {len(grouped)}개</div>
      </section>
      <section class="tag-grid">
{chr(10).join(cards)}
      </section>
    </section>
  </main>
</body>
</html>
"""


def render_tag_page(tag: str, items: list[dict]) -> str:
    featured = sorted(items, key=entry_priority)[0] if items else None
    remaining = [item for item in items if item is not featured]
    cards = []
    for item in remaining:
        cards.append(
            f'''        <a class="entry-card" href="{item["url"]}">
          <div class="meta"><span>{html.escape(item["type"])}</span><span>{html.escape(item["date"])}</span></div>
          <strong>{html.escape(item["title"])}</strong>
          <p>{html.escape(item["summary"])}</p>
        </a>'''
        )
    related = [other for other in items[0]["tags"] if other != tag][:6] if items else []
    related_html = "".join(
        f'<a class="mini-chip" href="/tags/{slugify(label)}.html">{html.escape(label)}</a>' for label in related
    ) or '<span class="mini-empty">이 태그와 함께 자주 보이는 보조 태그가 아직 적습니다.</span>'
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(tag)} | MALT Tags</title>
  <meta name="description" content="{html.escape(tag)} 태그로 묶인 MALT 글 목록" />
  <style>
    :root {{
      --bg:#eef4f8; --panel:#ffffff; --line:#c9d9e7; --text:#15283d; --muted:#5f738a; --accent:#0f8aa8;
    }}
    *{{box-sizing:border-box}}
    body{{margin:0;font-family:"Pretendard","SF Pro Display","Segoe UI",sans-serif;background:radial-gradient(900px 480px at 10% -10%, rgba(45,108,223,.12), transparent 60%), radial-gradient(900px 520px at 100% 0%, rgba(15,138,168,.10), transparent 58%), var(--bg);color:var(--text)}}
    .wrap{{max-width:1120px;margin:0 auto;padding:28px 16px 48px}}
    .shell{{border:1px solid var(--line);border-radius:22px;background:linear-gradient(180deg, rgba(255,255,255,.98), rgba(248,251,254,.98));box-shadow:0 18px 54px rgba(24,54,84,.10);overflow:hidden}}
    .topbar{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:18px 20px;border-bottom:1px solid rgba(15,138,168,.12);background:linear-gradient(180deg, rgba(15,138,168,.08), transparent)}}
    .brand{{font-size:13px;letter-spacing:.16em;font-weight:800;color:var(--accent)}}
    .nav{{display:flex;gap:10px;flex-wrap:wrap}}
    .nav a{{color:var(--text);text-decoration:none;border:1px solid #d6e3ee;border-radius:999px;padding:8px 12px;font-size:13px;background:#fff}}
    .hero{{padding:24px 20px 10px}}
    .hero h1{{margin:8px 0 8px;font-size:36px;line-height:1.08}}
    .hero p{{margin:0;color:var(--muted);max-width:64ch;line-height:1.7}}
    .mini-row{{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px}}
    .mini-chip{{display:inline-flex;align-items:center;padding:8px 12px;border-radius:999px;border:1px solid #d6e3ee;background:#fff;text-decoration:none;color:#0f8aa8;font-size:13px;font-weight:700}}
    .mini-empty{{font-size:13px;color:var(--muted)}}
    .featured{{margin:0 20px 0;padding:18px;border:1px solid #cfe0eb;border-radius:18px;background:linear-gradient(135deg, rgba(15,138,168,.12), rgba(45,108,223,.06)), linear-gradient(180deg,#fff,#f8fbfe);box-shadow:0 10px 24px rgba(24,54,84,.06)}}
    .featured .eyebrow{{font-size:11px;letter-spacing:.12em;color:#0f8aa8;font-weight:800}}
    .featured strong{{display:block;margin-top:8px;font-size:24px;line-height:1.3;color:#10253a}}
    .featured p{{margin:10px 0 0;color:var(--muted);line-height:1.7;font-size:14px}}
    .featured .meta{{display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;font-size:12px;color:#0f8aa8;font-weight:700}}
    .entry-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;padding:18px 20px 22px}}
    .entry-card{{display:flex;flex-direction:column;gap:10px;padding:18px;border:1px solid #d6e3ee;border-radius:18px;background:linear-gradient(180deg,#fff,#f8fbfe);text-decoration:none;color:var(--text);box-shadow:0 8px 22px rgba(24,54,84,.05)}}
    .entry-card .meta{{display:flex;justify-content:space-between;gap:10px;font-size:12px;color:#0f8aa8;font-weight:700;letter-spacing:.04em}}
    .entry-card strong{{font-size:18px;line-height:1.35;color:#10253a}}
    .entry-card p{{margin:0;color:var(--muted);line-height:1.65;font-size:14px}}
    @media (max-width:900px){{.entry-grid{{grid-template-columns:1fr}} .hero h1{{font-size:30px}}}}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="shell">
      <header class="topbar">
        <div class="brand">TAG · {html.escape(tag)}</div>
        <nav class="nav">
          <a href="/tags/index.html">All Tags</a>
          <a href="/posts.html">Posts</a>
          <a href="/">Home</a>
        </nav>
      </header>
      <section class="hero">
        <div class="kicker">TAG VIEW</div>
        <h1>{html.escape(tag)}로 묶인 글</h1>
        <p>이 태그와 연결된 글 {len(items)}개를 최신순으로 정리했습니다. 가이드, 일간 발행, 실험실 글을 한 흐름으로 이어 읽을 수 있습니다.</p>
        <div class="mini-row">{related_html}</div>
      </section>
      {f'''<a class="featured" href="{featured["url"]}">
        <div class="eyebrow">START HERE</div>
        <strong>{html.escape(featured["title"])}</strong>
        <p>{html.escape(featured["summary"])}</p>
        <div class="meta"><span>{html.escape(featured["type"])}</span><span>{html.escape(featured["date"])}</span><span>대표 글</span></div>
      </a>''' if featured else ''}
      <section class="entry-grid">
{chr(10).join(cards)}
      </section>
    </section>
  </main>
</body>
</html>
"""


def write_outputs(entries: list[dict], grouped: dict[str, list[dict]]) -> None:
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (TAGS_DIR / "index.html").write_text(render_tag_index(grouped, len(entries)), encoding="utf-8")
    for tag, items in grouped.items():
        (TAGS_DIR / f"{slugify(tag)}.html").write_text(render_tag_page(tag, items), encoding="utf-8")
    STATE_FILE.write_text(
        json.dumps(
            {
                "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "entry_count": len(entries),
                "tag_count": len(grouped),
                "tags": [
                    {
                        "tag": tag,
                        "slug": slugify(tag),
                        "count": len(items),
                        "latest_title": items[0]["title"],
                    }
                    for tag, items in grouped.items()
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    weak_candidates = [
        {
            "title": entry["title"],
            "url": entry["url"],
            "type": entry["type"],
            "date": entry["date"],
            "word_count": entry.get("word_count", 0),
            "quality_score": entry.get("quality_score", 0),
            "quality_band": entry.get("quality_band", ""),
            "quality_reasons": entry.get("quality_reasons", []),
        }
        for entry in sorted(entries, key=lambda item: (item.get("quality_score", 0), item.get("date", "")))
        if entry.get("quality_band") in {"thin", "weak"}
    ]
    QUALITY_REPORT_FILE.write_text(
        json.dumps(
            {
                "generated_at": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
                "entry_count": len(entries),
                "thin_or_weak_count": len(weak_candidates),
                "candidates": weak_candidates[:20],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    entries = collect_markdown_entries()
    entries.extend(collect_html_only_entries({entry["url"] for entry in entries}))
    deduped = dedupe_entries(entries)
    grouped = group_by_tag(deduped)
    curated_count = len([entry for entry in deduped if not is_low_value_entry(entry)])
    update_posts_overview(grouped, curated_count)
    prune_low_value_archive_links(deduped)
    apply_noindex_to_low_value_pages(deduped)
    write_outputs([entry for entry in deduped if not is_low_value_entry(entry)], grouped)
    print(json.dumps({"entries": curated_count, "tags": len(grouped)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
