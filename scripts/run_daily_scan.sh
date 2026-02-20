#!/bin/bash
# Run the daily automation intelligence scan.
# Can be invoked manually or by OpenClaw cron job.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

export PYTHONPATH="$PROJECT_DIR"

# Load env file if it exists
if [ -f "$PROJECT_DIR/.env" ]; then
    export $(grep -v '^#' "$PROJECT_DIR/.env" | xargs)
fi

echo "[$(date)] Starting automation intelligence daily scan..."

/usr/bin/python3 -m src "$@"

echo "[$(date)] Scan complete."
