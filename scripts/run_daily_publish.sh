#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOCK_DIR="$REPO_ROOT/.daily-publish.lock"
PUBLISH_DAYS="${MALT_PUBLISH_DAYS:-2,5}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cleanup() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

ensure_python_module() {
  local module_name="$1"
  local package_name="$2"
  if ! "$PYTHON_BIN" -c "import ${module_name}" >/dev/null 2>&1; then
    local venv_dir="$REPO_ROOT/.automation-venv"
    if [[ ! -x "$venv_dir/bin/python" ]]; then
      python3 -m venv "$venv_dir"
    fi
    PYTHON_BIN="$venv_dir/bin/python"
    if ! "$PYTHON_BIN" -c "import ${module_name}" >/dev/null 2>&1; then
      "$PYTHON_BIN" -m pip install --quiet "$package_name"
    fi
  fi
}

if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "daily publish already running"
  exit 0
fi
trap cleanup EXIT

cd "$REPO_ROOT"

today_dow="$(date +%u)"
if [[ "${MALT_FORCE_PUBLISH:-0}" != "1" ]]; then
  case ",$PUBLISH_DAYS," in
    *,"$today_dow",*)
      ;;
    *)
      echo "scheduled publish skipped on weekday $today_dow; allowed weekdays: $PUBLISH_DAYS"
      exit 0
      ;;
  esac
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "working tree is dirty; refusing automated publish"
  exit 1
fi

git fetch origin main
git pull --rebase origin main

ensure_python_module yaml PyYAML

"$PYTHON_BIN" scripts/generate_pillar_post_drafts.py
"$PYTHON_BIN" scripts/arxiv_pipeline.py
"$PYTHON_BIN" scripts/build_tag_index.py
"$PYTHON_BIN" scripts/build_sitemap.py
"$PYTHON_BIN" scripts/validate_post.py

git add content/archive content/drafts posts posts.html index.html tags sitemap.xml
if [[ -f automation-status.json ]]; then
  git add automation-status.json
fi
if [[ -f AUTOMATION.html ]]; then
  git add AUTOMATION.html
fi
if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi

git config user.name "${GIT_AUTHOR_NAME:-malt-bot}"
git config user.email "${GIT_AUTHOR_EMAIL:-actions@users.noreply.github.com}"
git commit -m "MALT daily arXiv publish"
git push origin main
