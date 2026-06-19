#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$REPO_ROOT/ops/mail-alert.env"
TMP_DIR="${TMPDIR:-/tmp}"

if [[ -f "$CONFIG_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$CONFIG_FILE"
fi

ALERT_EMAIL_TO="${ALERT_EMAIL_TO:-whdidtn200@icloud.com}"
ALERT_MAIL_ACCOUNT="${ALERT_MAIL_ACCOUNT:-whdidtn200@icloud.com}"
ALERT_SUBJECT_PREFIX="${ALERT_SUBJECT_PREFIX:-[MALT Blog]}"
WORKFLOW_REPO="${WORKFLOW_REPO:-whdidtn200/whdidtn200.github.io}"
WORKFLOW_FILE="${WORKFLOW_FILE:-weekly-lab-publish.yml}"
WORKFLOW_EVENT="${WORKFLOW_EVENT:-schedule}"
WORKFLOW_TIMEZONE="${WORKFLOW_TIMEZONE:-Asia/Seoul}"
LOCAL_DATE="$(TZ="$WORKFLOW_TIMEZONE" date +%F)"

send_alert() {
  local subject="$1"
  local body_file="$2"
  python3 "$SCRIPT_DIR/send_mail_alert.py" \
    --to "$ALERT_EMAIL_TO" \
    --subject "$subject" \
    --body "$(cat "$body_file")" \
    --account-address "$ALERT_MAIL_ACCOUNT"
}

status_file="$(mktemp "$TMP_DIR/malt-weekly-lab-status.XXXXXX.json")"
log_file="$(mktemp "$TMP_DIR/malt-weekly-lab-run.XXXXXX.log")"
trap 'rm -f "$status_file" "$log_file"' EXIT

python3 "$SCRIPT_DIR/check_workflow_status.py" \
  --repo "$WORKFLOW_REPO" \
  --workflow "$WORKFLOW_FILE" \
  --event "$WORKFLOW_EVENT" \
  --local-date "$LOCAL_DATE" \
  --timezone "$WORKFLOW_TIMEZONE" >"$status_file" || true

if bash "$SCRIPT_DIR/run_weekly_lab_publish.sh" >"$log_file" 2>&1; then
  if python3 - "$status_file" <<'PY'
import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text() or "{}")
raise SystemExit(0 if not data.get("run_found") else 1)
PY
  then
    printf 'GitHub weekly lab scheduled run was not found for %s.\n\nmacmini backup run completed successfully.\n' "$LOCAL_DATE" >"$log_file"
    cat "$status_file" >>"$log_file"
    send_alert "$ALERT_SUBJECT_PREFIX Weekly lab GitHub run missing, macmini backup covered" "$log_file" || true
  fi
  exit 0
fi

python3 - "$status_file" "$log_file" <<'PY'
import json
import sys
from pathlib import Path

status_path = Path(sys.argv[1])
log_path = Path(sys.argv[2])
data = json.loads(status_path.read_text() or "{}")
run = data.get("run") or {}
body = [
    "The macmini weekly lab backup run failed.",
    "",
    f"Local date: {data.get('local_date', 'n/a')} {data.get('timezone', '')}".strip(),
]
if data.get("run_found"):
    body.extend(
        [
            f"GitHub workflow URL: {run.get('html_url', 'n/a')}",
            f"GitHub status: {run.get('status', 'n/a')}",
            f"GitHub conclusion: {run.get('conclusion', 'n/a')}",
            "",
        ]
    )
body.extend(["Backup log:", log_path.read_text()])
log_path.write_text("\n".join(body))
PY

send_alert "$ALERT_SUBJECT_PREFIX macmini weekly lab backup failed" "$log_file" || true
exit 1
