#!/usr/bin/env python3
import html
import json
import pathlib
import re
import sys
from urllib.parse import urlparse


ARCHIVE_DIR = pathlib.Path("content/archive/sources")


def strip_html(text: str) -> str:
    text = re.sub(r"<pre.*?</pre>", "", text, flags=re.S)
    text = re.sub(r"<code.*?</code>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def strip_markdown(text: str) -> str:
    text = re.sub(r"^---.*?---\s*", "", text, flags=re.S)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"^>\s*", "", text, flags=re.M)
    text = re.sub(r"[*_#-]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_title(text: str, suffix: str) -> str:
    if suffix == ".md":
        m = re.search(r"^#\s+(.+)$", text, flags=re.M)
        if m:
            return m.group(1).strip()
    else:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, flags=re.S | re.I)
        if m:
            return strip_html(m.group(1))
        m = re.search(r"<title>(.*?)</title>", text, flags=re.S | re.I)
        if m:
            return strip_html(m.group(1))
    return pathlib.Path("untitled").stem


def parse_urls(text: str) -> list[dict]:
    urls = re.findall(r"https?://[^\s)>\"]+", text)
    seen = []
    for url in urls:
        clean = url.rstrip(".,")
        if clean not in seen:
            seen.append(clean)
    items = []
    for url in seen[:6]:
        host = urlparse(url).netloc.replace("www.", "")
        items.append({"label": host or "source", "url": url})
    return items


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?다])\s+", text)
    return [part.strip() for part in parts if len(part.strip()) > 30]


def extract_md_sections(raw: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^##\s+(.+)$", raw, flags=re.M))
    sections = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        body = raw[start:end].strip()
        sections.append((match.group(1).strip(), strip_markdown(body)))
    return sections


def extract_html_sections(raw: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"<h2[^>]*>(.*?)</h2>", raw, flags=re.S | re.I))
    sections = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw)
        body = raw[start:end].strip()
        sections.append((strip_html(match.group(1)), strip_html(body)))
    return sections


def pick_section_sentences(raw: str, suffix: str) -> list[str]:
    sections = extract_md_sections(raw) if suffix == ".md" else extract_html_sections(raw)
    preferred = []
    keywords = ["왜", "요약", "핵심", "summary", "개요", "결론", "시사점"]
    for heading, body in sections:
        if any(keyword.lower() in heading.lower() for keyword in keywords):
            preferred.extend(split_sentences(body)[:3])
    if preferred:
        return preferred
    plain = extract_plain_text(raw, suffix)
    return split_sentences(plain)


def extract_plain_text(raw: str, suffix: str) -> str:
    if suffix == ".md":
        return strip_markdown(raw)
    return strip_html(raw)


def infer_date_and_slug(path: pathlib.Path) -> tuple[str, str]:
    name = path.stem
    m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)", name)
    if m:
        return m.group(1), m.group(2)
    return "2026-06-15", re.sub(r"[^a-z0-9\-]+", "-", name.lower()).strip("-")


def build_payload(path: pathlib.Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    plain = extract_plain_text(raw, path.suffix)
    title = parse_title(raw, path.suffix)
    date, slug = infer_date_and_slug(path)
    sentences = pick_section_sentences(raw, path.suffix)

    summary = sentences[:3] or [plain[:180]]
    key_points = sentences[3:6] or sentences[:3]
    operator_view = [
        "MALT는 기존 아카이브 글을 다시 읽어 핵심 주장과 운영 시사점을 재조합한다.",
        "기존 논문 프리뷰를 단순 재게시하지 않고, 후속 발행 후보의 소스로 재사용한다.",
    ]
    application_notes = [
        "기존 프리뷰 글의 핵심 주장과 출처를 추출해 새 시리즈나 비교 글의 재료로 활용한다.",
        "비슷한 주제의 아카이브 글 여러 개를 모아 종합 리포트 초안을 만드는 데 사용할 수 있다.",
    ]
    limitations = [
        "기존 글의 서술 품질에 따라 추출 품질도 달라질 수 있다.",
        "정제 전에는 중복 문장이나 오래된 표현이 남아 있을 수 있다.",
    ]

    repo_relative = path.relative_to(pathlib.Path.cwd())
    category_map = [
        part for part in repo_relative.parts[:-1]
        if part not in {"posts", "malt", "phm", "ai"} and not re.fullmatch(r"\d{4}", part) and not re.fullmatch(r"\d{2}", part)
    ]
    categories = []
    relative_parts = repo_relative.parts
    if "malt" in relative_parts:
        categories.append("malt")
    if "phm" in relative_parts:
        categories.append("phm")
    if "ai" in relative_parts:
        categories.append("ai")
    categories.extend(part for part in category_map[:2] if part and not part.endswith((".md", ".html")))

    return {
        "date": date,
        "slug": slug,
        "title": title,
        "source_path": str(path),
        "source_type": "internal-archive-preview",
        "categories": categories[:3] or ["archive"],
        "tags": ["MALT", "Archive", "InternalSource"],
        "summary": summary,
        "key_points": key_points,
        "operator_view": operator_view,
        "application_notes": application_notes,
        "limitations": limitations,
        "sources": parse_urls(raw) or [{"label": "internal-archive", "url": f"file://{path}"}],
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/extract_internal_source.py <article-path>")

    article_path = pathlib.Path(sys.argv[1])
    if not article_path.is_absolute():
        article_path = pathlib.Path.cwd() / article_path

    payload = build_payload(article_path)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARCHIVE_DIR / f"{payload['date']}-{payload['slug']}.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
