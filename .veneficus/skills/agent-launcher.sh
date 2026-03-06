#!/usr/bin/env bash
# Agent Launcher — reads an agent persona file, parses its Environment block,
# sets corresponding VENEFICUS_* env vars, and launches Claude with the persona + task.
#
# Usage: agent-launcher.sh <agent-name> <task-description>
# Example: agent-launcher.sh builder "implement user authentication"

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENEFICUS_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$VENEFICUS_DIR")"

AGENT_NAME="${1:?Usage: agent-launcher.sh <agent-name> <task>}"
TASK="${2:?Usage: agent-launcher.sh <agent-name> <task>}"

PERSONA_FILE="$VENEFICUS_DIR/agents/${AGENT_NAME}.md"

if [[ ! -f "$PERSONA_FILE" ]]; then
    echo "Error: Agent persona not found: $PERSONA_FILE" >&2
    exit 1
fi

# Parse the Environment YAML block from the persona file using Python
ENV_VARS=$(python3 - "$PERSONA_FILE" << 'PYEOF'
import sys, re

persona_file = sys.argv[1]
with open(persona_file) as f:
    content = f.read()

# Extract YAML block after ## Environment
match = re.search(r'## Environment\s*```yaml\s*\n(.*?)```', content, re.DOTALL)
if not match:
    sys.exit(0)  # No environment block — use defaults

yaml_text = match.group(1)

# Simple YAML key: value parser (no external deps)
for line in yaml_text.strip().splitlines():
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    if ':' not in line:
        continue
    key, value = line.split(':', 1)
    key = key.strip()
    value = value.strip()

    if key == 'protect_tests':
        val = '1' if value.lower() == 'true' else '0'
        print(f'export VENEFICUS_PROTECT_TESTS="{val}"')
    elif key == 'tdd_enforce':
        val = '1' if value.lower() == 'true' else '0'
        print(f'export VENEFICUS_TDD_ENFORCE="{val}"')
    elif key == 'read_only':
        if value.lower() == 'true':
            print('export VENEFICUS_READ_ONLY="1"')
    elif key == 'scope_deny':
        # Parse YAML list: [item1, item2]
        items = value.strip('[]').split(',')
        items = [i.strip().strip('"').strip("'") for i in items if i.strip()]
        if items:
            print(f'export VENEFICUS_SCOPE_DENY="{",".join(items)}"')
    elif key == 'doc_enforce':
        val = '1' if value.lower() == 'true' else '0'
        print(f'export VENEFICUS_DOC_ENFORCE="{val}"')
PYEOF
)

# Apply environment variables
if [[ -n "$ENV_VARS" ]]; then
    eval "$ENV_VARS"
fi

# Read persona content for the prompt
PERSONA_CONTENT=$(cat "$PERSONA_FILE")

# Build and launch
PROMPT="${PERSONA_CONTENT}

Task: ${TASK}"

echo "[agent-launcher] Launching '${AGENT_NAME}' agent"
if [[ -n "$ENV_VARS" ]]; then
    echo "[agent-launcher] Environment:"
    echo "$ENV_VARS" | sed 's/^export /  /'
fi
echo ""

exec claude --dangerously-skip-permissions -p "$PROMPT"
