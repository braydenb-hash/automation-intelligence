#!/bin/bash
# Start the Automation Intelligence web dashboard.
# Runs on http://localhost:5050

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

export PYTHONPATH="$PROJECT_DIR"

echo "Starting Automation Intelligence Dashboard..."
echo "Open http://localhost:5050 in your browser"
echo ""

/usr/bin/python3 -m src.dashboard.app
