import datetime
import pathlib
import re
import yaml

BASE_URL = "/MALT-tech-blog"
POSTS_DIR = pathlib.Path("_posts")
INDEX_FILE = pathlib.Path("index.html")


def read_front_matter(text: str):
    m = re.match(r"^---\s*(.*?)\s*---\s*", text, re.S)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def compute_slug(path: pathlib.Path) -> str:
    stem = path.stem
    parts = stem.split("-", 3)
    if len(parts) < 4:
        return stem
    return parts[3]


def build_url(meta: dict, slug: str, date_obj: datetime.date):
    categories = meta.get("categories") or []
    if isinstance(categories, str):
        categories = [categories]
    if not categories:
        cat_path = "posts"
    else:
        cat_path = "/".join(c.strip().lower().replace(" ", "-") for c in categories if c)
    return f"{BASE_URL}/{cat_path}/{date_obj.year:04d}/{date_obj.month:02d}/{date_obj.day:02d}/{slug}.html"


def load_posts():
    entries = []
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        meta = read_front_matter(text)
        title = meta.get("title") or path.stem
        date_value = meta.get("date")
        date_obj = None
        if date_value:
            try:
                date_obj = datetime.datetime.fromisoformat(str(date_value)).date()
            except ValueError:
                try:
                    date_obj = datetime.datetime.strptime(str(date_value), "%Y-%m-%d %H:%M:%S %z").date()
                except (ValueError, TypeError):
                    pass
        if not date_obj:
            slug_parts = path.stem.split("-", 3)
            if len(slug_parts) >= 3:
                year, month, day = slug_parts[:3]
                try:
                    date_obj = datetime.date(int(year), int(month), int(day))
                except ValueError:
                    date_obj = datetime.date.today()
            else:
                date_obj = datetime.date.today()
        slug_override = meta.get("slug")
        slug = str(slug_override).strip("/") if slug_override else compute_slug(path)
        url = build_url(meta, slug, date_obj)
        entries.append({"title": title, "url": url, "date": date_obj})
    return sorted(entries, key=lambda e: e["date"], reverse=True)


def render_links(entries):
    lines = []
    for entry in entries[:13]:
        lines.append(f"  <a href=\"{entry['url']}\">{entry['title']}</a>")
    return "\n" + "\n".join(lines) + "\n"


def update_index_html(links_block: str):
    content = INDEX_FILE.read_text(encoding="utf-8")
    start_marker = "  <div id=\"latest-links\" class=\"links\">"
    start = content.find(start_marker)
    if start < 0:
        raise SystemExit("latest-links marker not found")
    end = content.find("</div>", start)
    if end < 0:
        raise SystemExit("latest-links closing tag not found")
    new_content = content[: start + len(start_marker)] + "\n" + links_block.strip() + "\n" + content[end:]
    INDEX_FILE.write_text(new_content, encoding="utf-8")


def main():
    posts = load_posts()
    if not posts:
        raise SystemExit("no posts found")
    links = render_links(posts)
    update_index_html(links)


if __name__ == "__main__":
    main()
