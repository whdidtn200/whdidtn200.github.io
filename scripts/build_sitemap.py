#!/usr/bin/env python3
"""Build a sitemap from public hub pages and indexable post HTML files."""

from __future__ import annotations

import datetime as dt
import html
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://whdidtn200.github.io"
OUTPUT = ROOT / "sitemap.xml"
PUBLIC_PAGES = [
    ("/", "daily", "1.0"),
    ("/GUIDES.html", "weekly", "0.9"),
    ("/LAB.html", "weekly", "0.9"),
    ("/posts.html", "weekly", "0.85"),
    ("/railway-predictive-maintenance-guide.html", "monthly", "0.95"),
    ("/bearing-fault-diagnosis-guide.html", "monthly", "0.95"),
    ("/wayside-condition-monitoring-guide.html", "monthly", "0.95"),
    ("/predictive-maintenance-kpi-roi-guide.html", "monthly", "0.8"),
    ("/railway-bearing-sensor-guide.html", "monthly", "0.8"),
    ("/phm-alert-governance-guide.html", "monthly", "0.9"),
    ("/ABOUT.html", "monthly", "0.6"),
    ("/CONTACT.html", "monthly", "0.6"),
    ("/PRIVACY.html", "monthly", "0.6"),
    ("/EDITORIAL.html", "monthly", "0.6"),
]


def modified_date(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(r'article:published_time"\s+content="(\d{4}-\d{2}-\d{2})', text)
    if match:
        return match.group(1)
    match = re.match(r"(\d{4}-\d{2}-\d{2})", path.stem)
    if match:
        return match.group(1)
    return dt.date.fromtimestamp(path.stat().st_mtime).isoformat()


def is_indexable(path: Path) -> bool:
    text = path.read_text(encoding="utf-8").lower()
    return 'name="robots" content="noindex' not in text


def url_block(url: str, lastmod: str, changefreq: str, priority: str) -> str:
    return f"""  <url>
    <loc>{html.escape(SITE + url)}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{changefreq}</changefreq>
    <priority>{priority}</priority>
  </url>"""


def main() -> None:
    today = dt.date.today().isoformat()
    blocks = []
    for url, frequency, priority in PUBLIC_PAGES:
        path = ROOT / ("index.html" if url == "/" else url.lstrip("/"))
        blocks.append(url_block(url, modified_date(path) if path.exists() else today, frequency, priority))
    posts = [path for path in sorted((ROOT / "posts").glob("*.html"), reverse=True) if is_indexable(path)]
    for path in posts:
        blocks.append(url_block(f"/posts/{path.name}", modified_date(path), "monthly", "0.7"))
    OUTPUT.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(blocks)
        + "\n</urlset>\n",
        encoding="utf-8",
    )
    print(f"sitemap_urls={len(blocks)} indexable_posts={len(posts)}")


if __name__ == "__main__":
    main()
