#!/usr/bin/env python3
import pathlib
import re
import subprocess
import sys


POSTS_DIR = pathlib.Path("posts")
REQUIRED_MARKERS = [
    "출처",
]
AI_DISCLOSURE_MARKERS = [
    "MALT 큐레이션",
    "AI",
]


def changed_posts():
    commands = [
        ["git", "diff", "--name-only", "HEAD", "--", "posts"],
        ["git", "ls-files", "--others", "--exclude-standard", "--", "posts"],
    ]

    seen = set()
    paths = []
    for command in commands:
        try:
            output = subprocess.check_output(command, text=True)
        except subprocess.CalledProcessError:
            continue

        for line in output.splitlines():
            path = pathlib.Path(line.strip())
            if path.suffix != ".md" or not path.exists() or path in seen:
                continue
            seen.add(path)
            paths.append(path)
    return paths


def check_post(path: pathlib.Path):
    text = path.read_text(encoding="utf-8")
    issues = []

    if len(text.strip()) < 800:
        issues.append("content_too_short")

    if not any(marker in text for marker in REQUIRED_MARKERS):
        issues.append("missing_source_section")

    if not any(marker in text for marker in AI_DISCLOSURE_MARKERS):
        issues.append("missing_ai_context")

    headings = re.findall(r"^##\s+.+$", text, flags=re.M)
    if len(headings) < 3:
        issues.append("not_enough_sections")

    return issues


def main():
    targets = changed_posts()
    if not targets:
        print("validation skipped: no changed markdown posts")
        return 0

    failures = []
    for path in targets:
        issues = check_post(path)
        if issues:
            failures.append((path, issues))

    if not failures:
        print("validation passed")
        return 0

    for path, issues in failures:
        print(f"{path}: {', '.join(issues)}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
