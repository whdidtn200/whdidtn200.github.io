#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCK_DIR="$REPO_ROOT/.weekly-lab-publish.lock"

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "weekly lab publish already running"
  exit 0
fi
trap cleanup EXIT

cd "$REPO_ROOT"

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "working tree is dirty; refusing weekly lab publish"
  exit 1
fi

git fetch origin main
git pull --rebase origin main

python3 scripts/weekly_lab_pipeline.py
python3 scripts/validate_post.py

git add content/archive/state LAB.html index.html posts posts.html assets/lab-generated
if git diff --cached --quiet; then
  echo "No weekly lab changes to commit"
  exit 0
fi

git config user.name "${GIT_AUTHOR_NAME:-malt-bot}"
git config user.email "${GIT_AUTHOR_EMAIL:-actions@users.noreply.github.com}"
git commit -m "MALT weekly testing lab publish"
git push origin main
