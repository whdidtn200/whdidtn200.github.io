import datetime
import pathlib
import re
import yaml

POSTS_DIR = pathlib.Path("posts")
INDEX_FILE = pathlib.Path("index.html")
POSTS_INDEX_FILE = pathlib.Path("posts.html")


def read_front_matter(text: str):
    m = re.match(r"^---\s*(.*?)\s*---\s*", text, re.S)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


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
        url = f"/posts/{path.stem}.html"
        entries.append({"title": title, "url": url, "date": date_obj})
    return sorted(entries, key=lambda e: e["date"], reverse=True)


def render_links(entries):
    lines = []
    for entry in entries[:6]:
        lines.append(f"  <a href=\"{entry['url']}\">{entry['title']}</a>")
    return "\n" + "\n".join(lines) + "\n"


def render_posts_cards(entries):
    lines = []
    for entry in entries:
        lines.append(f'  <li><a href="{entry["url"]}">{entry["title"]}</a></li>')
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


def update_posts_html(cards_block: str):
    content = POSTS_INDEX_FILE.read_text(encoding="utf-8")
    start_marker = '        <ul class="archive-grid">'
    start = content.find(start_marker)
    if start < 0:
        raise SystemExit("archive-grid marker not found")
    end = content.find("        </ul>", start)
    if end < 0:
        raise SystemExit("archive-grid closing tag not found")
    new_content = content[: start + len(start_marker)] + "\n" + cards_block.strip() + "\n" + content[end:]
    POSTS_INDEX_FILE.write_text(new_content, encoding="utf-8")


def main():
    posts = load_posts()
    if not posts:
        raise SystemExit("no posts found")
    links = render_links(posts)
    cards = render_posts_cards(posts)
    update_index_html(links)
    update_posts_html(cards)


if __name__ == "__main__":
    main()
