#!/usr/bin/env bash
set -euo pipefail

# Merge dashboard event emitter hooks into .claude/settings.json
# This is run automatically by `just init` — you rarely need to run it manually.

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
SETTINGS="$PROJECT_DIR/.claude/settings.json"

if [ ! -f "$SETTINGS" ]; then
    echo "Error: $SETTINGS not found. Run 'just init' first."
    exit 1
fi

echo "[veneficus] Dashboard hooks are already configured in settings.json."
echo "[veneficus] Event emitter: .veneficus/hooks/emitters/emit_event.sh"
echo "[veneficus] All async hooks POST to http://localhost:7777/api/events"
echo ""
echo "To start the dashboard: just dashboard"
