#!/usr/bin/env bash
# Universal event emitter — reads hook JSON from stdin, enriches, POSTs to dashboard.
# Always exits 0 (never blocks Claude). Runs with async: true in settings.json.

DASHBOARD_URL="${VENEFICUS_DASHBOARD_URL:-http://localhost:7777/api/events}"
EVENT_LOG_DIR="${CLAUDE_PROJECT_DIR:-.}/.veneficus/events/logs"

# Read stdin (hook JSON)
INPUT=$(cat)

if [ -z "$INPUT" ]; then
    exit 0
fi

# Enrich with timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")
ENRICHED=$(echo "$INPUT" | jq -c --arg ts "$TIMESTAMP" '. + {received_at: $ts}' 2>/dev/null)

if [ -z "$ENRICHED" ] || [ "$ENRICHED" = "null" ]; then
    ENRICHED="$INPUT"
fi

# Append to local event log
mkdir -p "$EVENT_LOG_DIR"
echo "$ENRICHED" >> "$EVENT_LOG_DIR/events.jsonl" 2>/dev/null

# POST to dashboard (fail silently if not running)
curl -s -X POST "$DASHBOARD_URL" \
    -H "Content-Type: application/json" \
    -d "$ENRICHED" \
    --connect-timeout 1 \
    --max-time 3 \
    >/dev/null 2>&1

exit 0
