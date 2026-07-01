import datetime
import pathlib
import re
import yaml

POSTS_DIR = pathlib.Path("posts")
INDEX_FILE = pathlib.Path("index.html")
POSTS_INDEX_FILE = pathlib.Path("posts.html")
LOW_VALUE_FILE = pathlib.Path("ops/adsense-low-value-posts.txt")
MIN_REVIEW_WORDS = 600


CORE_TERMS = [
    "railway",
    "train",
    "metro",
    "track",
    "wayside",
    "wheel",
    "wheelset",
    "bearing",
    "phm",
    "predictive maintenance",
    "condition monitoring",
    "fault diagnosis",
    "철도",
    "차축",
    "베어링",
    "예지보전",
    "상태",
]

OFF_TOPIC_TERMS = [
    "github",
    "repo bootcamp",
    "leann",
    "scrapling",
    "multi-agent",
    "agentic",
    "agent runtime",
    "llm agent",
]

FEATURED_HOME_LINKS = [
    {
        "url": "/railway-predictive-maintenance-guide.html",
        "title": "Railway Predictive Maintenance Guide",
    },
    {
        "url": "/bearing-fault-diagnosis-guide.html",
        "title": "Bearing Fault Diagnosis Guide",
    },
    {
        "url": "/wayside-condition-monitoring-guide.html",
        "title": "Wayside Condition Monitoring Guide",
    },
]


def read_front_matter(text: str):
    m = re.match(r"^---\s*(.*?)\s*---\s*", text, re.S)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


def body_without_front_matter(text: str) -> str:
    return re.sub(r"^---\s*(.*?)\s*---\s*", "", text, count=1, flags=re.S)


def title_from_markdown(text: str, fallback: str) -> str:
    body = body_without_front_matter(text)
    heading = re.search(r"^#\s+(.+)$", body, re.M)
    return heading.group(1).strip() if heading else fallback


def load_low_value_slugs() -> set[str]:
    if not LOW_VALUE_FILE.exists():
        return set()
    return {
        line.strip()
        for line in LOW_VALUE_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def is_adsense_review_surface(path: pathlib.Path, text: str, title: str, excluded: set[str]) -> bool:
    slug = path.stem
    body = body_without_front_matter(text)
    words = len(re.findall(r"\S+", body))
    haystack = f"{slug} {title} {body[:1200]}".lower()
    if slug in excluded:
        return False
    if words < MIN_REVIEW_WORDS:
        return False
    if any(term in haystack for term in OFF_TOPIC_TERMS) and not any(term in haystack for term in CORE_TERMS):
        return False
    return True


def load_posts():
    entries = []
    excluded = load_low_value_slugs()
    for path in POSTS_DIR.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        meta = read_front_matter(text)
        title = meta.get("title") or title_from_markdown(text, path.stem)
        if not is_adsense_review_surface(path, text, str(title), excluded):
            continue
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
    for entry in FEATURED_HOME_LINKS + entries[:3]:
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
