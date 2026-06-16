#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_PLIST="$REPO_ROOT/ops/com.malt.daily-arxiv-backup.plist"
TARGET_PLIST="$HOME/Library/LaunchAgents/com.malt.daily-arxiv-backup.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"
cp "$SOURCE_PLIST" "$TARGET_PLIST"
launchctl bootout "gui/$(id -u)" "$TARGET_PLIST" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$TARGET_PLIST"
launchctl enable "gui/$(id -u)/com.malt.daily-arxiv-backup"
launchctl kickstart -k "gui/$(id -u)/com.malt.daily-arxiv-backup"
echo "Installed $TARGET_PLIST"
