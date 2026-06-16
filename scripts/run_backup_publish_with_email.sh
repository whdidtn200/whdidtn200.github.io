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
WORKFLOW_FILE="${WORKFLOW_FILE:-daily-arxiv-publish.yml}"
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

status_file="$(mktemp "$TMP_DIR/malt-workflow-status.XXXXXX.json")"
log_file="$(mktemp "$TMP_DIR/malt-backup-run.XXXXXX.log")"
trap 'rm -f "$status_file" "$log_file"' EXIT

if ! python3 "$SCRIPT_DIR/check_workflow_status.py" \
  --repo "$WORKFLOW_REPO" \
  --workflow "$WORKFLOW_FILE" \
  --event "$WORKFLOW_EVENT" \
  --local-date "$LOCAL_DATE" \
  --timezone "$WORKFLOW_TIMEZONE" >"$status_file"; then
  printf 'Unable to read GitHub workflow status on %s\n\n' "$LOCAL_DATE" >"$log_file"
  cat "$status_file" >>"$log_file"
  send_alert "$ALERT_SUBJECT_PREFIX Unable to inspect GitHub publish status" "$log_file" || true
fi

if bash "$SCRIPT_DIR/run_daily_publish.sh" >"$log_file" 2>&1; then
  if python3 - "$status_file" "$log_file" <<'PY'
import json
import sys
from pathlib import Path

status_path = Path(sys.argv[1])
log_path = Path(sys.argv[2])
data = json.loads(status_path.read_text() or "{}")
run = data.get("run") or {}
needs_recovery_alert = (
    data.get("run_found")
    and run.get("status") == "completed"
    and run.get("conclusion") != "success"
)
if not needs_recovery_alert:
    raise SystemExit(1)

body = [
    "GitHub main publish run failed, but the macmini backup run completed successfully.",
    "",
    f"Workflow URL: {run.get('html_url', 'n/a')}",
    f"GitHub conclusion: {run.get('conclusion', 'n/a')}",
    "",
    "Backup log:",
    log_path.read_text(),
]
log_path.write_text("\n".join(body))
PY
  then
    send_alert "$ALERT_SUBJECT_PREFIX GitHub publish failed, macmini backup recovered" "$log_file" || true
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
    "The macmini backup publish run failed.",
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

send_alert "$ALERT_SUBJECT_PREFIX macmini backup publish failed" "$log_file" || true
exit 1
