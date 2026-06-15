#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "scripts/validate_post.py" ]; then
  python3 scripts/validate_post.py
fi

git add .
git commit -m "MALT publish: $(date +'%Y-%m-%d %H:%M:%S')" || true
git push origin main
