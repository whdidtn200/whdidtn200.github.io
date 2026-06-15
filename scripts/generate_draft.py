#!/usr/bin/env python3
import json
import pathlib
import re
import sys


DRAFT_DIR = pathlib.Path("content/drafts")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9\-가-힣]", "", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value or "draft"


def load_payload(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def render_list(items):
    return "\n".join(f"- {item}" for item in items)


def render_sources(items):
    return "\n".join(f"- [{item['label']}]({item['url']})" for item in items)


def build_markdown(payload: dict) -> str:
    date = payload["date"]
    slug = payload.get("slug") or slugify(payload["title"])
    categories = payload.get("categories", [])
    tags = payload.get("tags", [])

    return f"""---
title: "{payload['title']}"
date: {date}
slug: "{slug}"
categories: [{", ".join(json.dumps(item, ensure_ascii=False) for item in categories)}]
tags: [{", ".join(json.dumps(item, ensure_ascii=False) for item in tags)}]
draft: true
generated_by: "MALT"
workflow: "AI-managed publication"
---

# {payload['title']}

## 핵심 변화
{render_list(payload.get("summary", []))}

## 주요 포인트
{render_list(payload.get("key_points", []))}

## 운영자 해석
{render_list(payload.get("operator_view", []))}

## 현업 적용 판단
{render_list(payload.get("application_notes", []))}

## 주의할 한계
{render_list(payload.get("limitations", []))}

## 출처
{render_sources(payload.get("sources", []))}

## 발행 메모
- MALT 큐레이션 초안
- AI-managed workflow에서 생성된 초안
- 발행 전 사실 검토와 문장 다듬기 권장
"""


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: python3 scripts/generate_draft.py <inbox-json>")

    source_path = pathlib.Path(sys.argv[1])
    if not source_path.is_absolute():
        source_path = pathlib.Path.cwd() / source_path

    payload = load_payload(source_path)
    slug = payload.get("slug") or slugify(payload["title"])
    date = payload["date"]

    DRAFT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DRAFT_DIR / f"{date}-{slug}.md"
    out_path.write_text(build_markdown(payload), encoding="utf-8")
    print(out_path)


if __name__ == "__main__":
    main()
