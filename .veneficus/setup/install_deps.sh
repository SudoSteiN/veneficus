#!/usr/bin/env bash
set -euo pipefail

# Veneficus dependency installer
# Installs all prerequisites via Homebrew

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[veneficus]${NC} $1"; }
warn()  { echo -e "${YELLOW}[veneficus]${NC} $1"; }
error() { echo -e "${RED}[veneficus]${NC} $1" >&2; }

check_cmd() {
    command -v "$1" &>/dev/null
}

# Check for Homebrew
if ! check_cmd brew; then
    error "Homebrew is required. Install from https://brew.sh"
    exit 1
fi

DEPS_NEEDED=()

# Check each dependency
if ! check_cmd bun; then
    DEPS_NEEDED+=("oven-sh/bun/bun")
else
    info "bun $(bun --version) ✓"
fi

if ! check_cmd uv; then
    DEPS_NEEDED+=("astral-sh/uv/uv")
else
    info "uv $(uv --version 2>&1 | head -1) ✓"
fi

if ! check_cmd just; then
    DEPS_NEEDED+=("just")
else
    info "just $(just --version) ✓"
fi

if ! check_cmd tmux; then
    DEPS_NEEDED+=("tmux")
else
    info "tmux $(tmux -V) ✓"
fi

if ! check_cmd jq; then
    DEPS_NEEDED+=("jq")
else
    info "jq $(jq --version) ✓"
fi

# Install missing deps
if [ ${#DEPS_NEEDED[@]} -gt 0 ]; then
    info "Installing: ${DEPS_NEEDED[*]}"
    brew install "${DEPS_NEEDED[@]}"
    info "Dependencies installed."
else
    info "All dependencies present."
fi

# Install Playwright chromium
if ! bun pm ls 2>/dev/null | grep -q playwright 2>/dev/null; then
    info "Installing Playwright chromium..."
    bunx playwright install chromium 2>/dev/null || warn "Playwright install skipped (install manually if needed)"
fi

# Check Claude Code CLI
if check_cmd claude; then
    CLAUDE_VERSION=$(claude --version 2>/dev/null || echo "unknown")
    info "Claude Code CLI: $CLAUDE_VERSION"
else
    warn "Claude Code CLI not found. Install from https://claude.ai/code"
fi

# Recommend setting ENABLE_EXPERIMENTAL_MCP_CLI for token savings
if [ -z "${ENABLE_EXPERIMENTAL_MCP_CLI:-}" ]; then
    warn "Tip: Set ENABLE_EXPERIMENTAL_MCP_CLI=true in your shell profile to save 40-50k tokens/session"
    warn "  echo 'export ENABLE_EXPERIMENTAL_MCP_CLI=true' >> ~/.zshrc"
fi

# Recommend setting CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS for native team orchestration
if [ -z "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" ]; then
    warn "Tip: Set CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1 to enable native Agent Teams (TeamCreate/SpawnAgent)"
    warn "  echo 'export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1' >> ~/.zshrc"
fi

info "All dependencies ready."
