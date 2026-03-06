# Veneficus — Claude Code Development Framework
# The human interface layer. Run `just` to see all commands.

set shell := ["bash", "-cu"]

project_dir := justfile_directory()
veneficus := project_dir / ".veneficus"
claude_bin := "claude"

# ─── Setup ───────────────────────────────────────────────────────────

# Initialize Veneficus framework in current project
init:
    uv run "{{veneficus}}/setup/init.py"

# Install all dependencies (bun, uv, just, tmux, jq)
deps:
    bash "{{veneficus}}/setup/install_deps.sh"

# ─── SDLC Commands ──────────────────────────────────────────────────

# Load context and show current project state
prime:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/prime.md)"

# Generate structured implementation plan (auto-ideates if context docs are empty)
plan description:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/plan.md | sed 's/\$ARGUMENTS/{{description}}/')"

# Plan + generate DESIGN_SPEC.md and tasks/*.md for native Agent Teams
plan-team description:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/plan-team.md | sed 's/\$ARGUMENTS/{{description}}/')"

# TDD build cycle for a feature
build feature:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/build.md | sed 's/\$ARGUMENTS/{{feature}}/')"

# Native Agent Teams orchestration from DESIGN_SPEC.md + tasks/*.md
team-build:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/team-build.md)"

# Bug investigation protocol
debug description:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/debug.md | sed 's/\$ARGUMENTS/{{description}}/')"

# Code review and security audit
review scope="HEAD~1..HEAD":
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/review.md | sed 's/\$ARGUMENTS/{{scope}}/')"

# Release preparation
ship version:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/ship.md | sed 's/\$ARGUMENTS/{{version}}/')"

# Resume an interrupted build session
continue:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/continue.md)"

# Performance optimization pass for a feature
optimize feature:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/optimize.md | sed 's/\$ARGUMENTS/{{feature}}/')"

# Session retrospective and self-improvement
retro:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/commands/retro.md)"

# ─── Thread Types ────────────────────────────────────────────────────

# P-Thread: parallel independent work in worktrees
parallel +features:
    uv run "{{veneficus}}/threads/p_thread.py" {{features}}

# F-Thread: best-of-N prototyping (DEPRECATED — 3x cost, marginal benefit)
fusion prompt:
    @echo "WARNING: F-Thread is deprecated. Consider 'just build' for iterative work."
    uv run "{{veneficus}}/threads/f_thread.py" "{{prompt}}"

# C-Thread: chained sequential with human checkpoints
chain steps_file:
    uv run "{{veneficus}}/threads/c_thread.py" "{{steps_file}}"

# L-Thread: loop until test passes
loop test_cmd:
    uv run "{{veneficus}}/threads/l_thread.py" "{{test_cmd}}"

# ─── Agent Teams ─────────────────────────────────────────────────────

# Run a specific agent with a task (uses agent-launcher for environment setup)
team agent task:
    bash "{{veneficus}}/skills/agent-launcher.sh" "{{agent}}" "{{task}}"

# Run QA agent with user stories
qa stories="user-stories.yaml":
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/agents/qa.md)\n\nRun all stories in {{stories}}"

# Ad-hoc browser automation task
browse task:
    {{claude_bin}} --dangerously-skip-permissions -p "$(cat {{veneficus}}/agents/qa.md)\n\nBrowser task: {{task}}"

# ─── Dashboard ───────────────────────────────────────────────────────

# Start the real-time dashboard
dashboard:
    cd "{{project_dir}}/dashboard" && bun run server/index.ts

# Show current framework status (CLI dashboard replacement)
status:
    @echo "=== Veneficus Status ==="
    @echo ""
    @uv run "{{veneficus}}/skills/context-loader.py" --summary
    @echo ""
    @echo "=== Active Worktrees ==="
    @bash "{{veneficus}}/skills/git-worktree.sh" list 2>/dev/null || echo "  (none)"
    @echo ""
    @echo "=== Validation Stats ==="
    @if [ -f "{{veneficus}}/events/logs/events.jsonl" ]; then \
        TOTAL=$(grep -c 'PostToolUse' "{{veneficus}}/events/logs/events.jsonl" 2>/dev/null || echo 0); \
        FAILS=$(grep -c 'PostToolUseFailure' "{{veneficus}}/events/logs/events.jsonl" 2>/dev/null || echo 0); \
        echo "  PostToolUse events: $TOTAL | Failures: $FAILS"; \
    else \
        echo "  (no events yet)"; \
    fi
    @echo ""
    @echo "=== Recent Events (last 5) ==="
    @tail -5 "{{veneficus}}/events/logs/events.jsonl" 2>/dev/null | jq -c '{event: .hook_event_name, tool: .tool_name, time: .received_at}' 2>/dev/null || echo "  (no events yet)"

# Show recent events
events n="20":
    @tail -{{n}} "{{veneficus}}/events/logs/events.jsonl" 2>/dev/null | jq '.' 2>/dev/null || echo "No events found."

# Run native Claude Code /insights analysis
insights:
    {{claude_bin}} --dangerously-skip-permissions -p "/insights"

# Restore the most recent pre-build snapshot
rollback:
    @LATEST=$(bash "{{veneficus}}/skills/snapshot.sh" list 2>/dev/null | grep "pre-build" | tail -1 | awk '{print $1}'); \
    if [ -z "$LATEST" ]; then \
        echo "No pre-build snapshots found."; \
    else \
        echo "Restoring snapshot: $LATEST"; \
        bash "{{veneficus}}/skills/snapshot.sh" restore "$LATEST"; \
    fi

# Sync .veneficus/commands/ → .claude/commands/
sync-commands:
    @cp "{{veneficus}}/commands/"*.md "{{project_dir}}/.claude/commands/" 2>/dev/null || true
    @echo "[sync] Commands synchronized"

# ─── Utilities ───────────────────────────────────────────────────────

# Create a rollback snapshot
snapshot message="auto":
    bash "{{veneficus}}/skills/snapshot.sh" save "{{message}}"

# List snapshots
snapshots:
    bash "{{veneficus}}/skills/snapshot.sh" list

# Clean up worktrees and event logs
clean:
    bash "{{veneficus}}/skills/git-worktree.sh" cleanup-all
    rm -rf "{{veneficus}}/events/logs/"*.jsonl
    @echo "Cleaned up worktrees and event logs."

# Show full context
context mode="--summary":
    uv run "{{veneficus}}/skills/context-loader.py" {{mode}}
