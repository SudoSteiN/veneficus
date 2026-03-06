#!/usr/bin/env bash
# SessionStart hook — runs when a new Claude Code session begins.
# Checks environment health and emits a session_start event.
# Always exits 0 (never blocks session startup).

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-.}"
VENEFICUS_DIR="$PROJECT_DIR/.veneficus"
EVENT_LOG_DIR="$VENEFICUS_DIR/events/logs"

# ── Environment health check ──────────────────────────────────────────

WARNINGS=""

# Check that docs exist
for doc in PRD.md architecture.md features.json; do
    if [ ! -f "$VENEFICUS_DIR/docs/$doc" ]; then
        WARNINGS="${WARNINGS}Missing: .veneficus/docs/$doc\n"
    fi
done

# Check recommended env vars
if [ -z "${ENABLE_EXPERIMENTAL_MCP_CLI:-}" ]; then
    WARNINGS="${WARNINGS}Set ENABLE_EXPERIMENTAL_MCP_CLI=true to save ~40-50k tokens/session\n"
fi

if [ -z "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" ]; then
    WARNINGS="${WARNINGS}Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 to enable native Agent Teams\n"
fi

# Check key tools
for cmd in jq tmux; do
    if ! command -v "$cmd" &>/dev/null; then
        WARNINGS="${WARNINGS}Missing tool: $cmd\n"
    fi
done

# Print warnings to stderr (shown to the agent as context)
if [ -n "$WARNINGS" ]; then
    echo -e "⚠ Veneficus environment warnings:\n$WARNINGS" >&2
fi

# ── Sync command copies ───────────────────────────────────────────────

cp "$VENEFICUS_DIR/commands/"*.md "$PROJECT_DIR/.claude/commands/" 2>/dev/null || true

# ── In-progress feature detection ─────────────────────────────────────

if [ -f "$VENEFICUS_DIR/docs/features.json" ]; then
    IN_PROGRESS=$(jq -r '.features[] | select(.status == "in_progress") | .id' "$VENEFICUS_DIR/docs/features.json" 2>/dev/null || true)
    if [ -n "$IN_PROGRESS" ]; then
        echo "" >&2
        echo "⚠ Previous session left features in_progress:" >&2
        echo "$IN_PROGRESS" | while read -r feat; do
            echo "  - $feat" >&2
        done
        echo "Run \`just continue\` to resume." >&2
        echo "" >&2
    fi
fi

# ── Emit session_start event ──────────────────────────────────────────

mkdir -p "$EVENT_LOG_DIR"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# Count features status if features.json exists
FEATURES_SUMMARY=""
if [ -f "$VENEFICUS_DIR/docs/features.json" ]; then
    FEATURES_SUMMARY=$(jq -c '{
        done: [.features[] | select(.status == "done")] | length,
        active: [.features[] | select(.status == "in_progress")] | length,
        pending: [.features[] | select(.status == "pending")] | length
    }' "$VENEFICUS_DIR/docs/features.json" 2>/dev/null || echo '{}')
fi

EVENT=$(jq -nc \
    --arg ts "$TIMESTAMP" \
    --arg dir "$PROJECT_DIR" \
    --argjson features "${FEATURES_SUMMARY:-{}}" \
    '{
        hook_event_name: "SessionStart",
        received_at: $ts,
        project_dir: $dir,
        features_status: $features
    }')

echo "$EVENT" >> "$EVENT_LOG_DIR/events.jsonl" 2>/dev/null

# POST to dashboard (fail silently)
DASHBOARD_URL="${VENEFICUS_DASHBOARD_URL:-http://localhost:7777/api/events}"
curl -s -X POST "$DASHBOARD_URL" \
    -H "Content-Type: application/json" \
    -d "$EVENT" \
    --connect-timeout 1 \
    --max-time 3 \
    >/dev/null 2>&1 || true

exit 0
