# Veneficus

A Claude Code development framework that turns a single developer into an engineering team.

## What It Does

Veneficus wraps Claude Code with automated validation hooks, specialized agent personas, and structured SDLC workflows. You describe what to build; the framework enforces code quality, runs tests on every file write, and coordinates parallel workstreams, so you ship faster without sacrificing rigor.

## How It Works

**Agent Hooks** run automatically on every tool call. Guards enforce scope *before* Claude writes. Validators check syntax, lint, and tests *after* every edit. Event emitters stream everything to a real-time dashboard.

**Specialized Agents** handle distinct roles: builder (writes code via TDD), validator (read-only audits against acceptance criteria), debugger (reproduce → diagnose → fix → verify), researcher (explores codebases and docs), and QA (browser automation with Playwright), plus **simplifier** and **contrarian** recovery personas for when agents get stuck.

**Context as Contract** anchors all work to four documents — `PRD.md`, `architecture.md`, `decisions.md`, and `features.json` — so every agent operates from the same source of truth.

**Thread Types** enable multi-session orchestration:
- **P-Threads** — parallel independent work in git worktrees
- **C-Threads** — chained sequential steps with human checkpoints
- **L-Threads** — loop until a test command passes, with stagnation detection and automatic persona rotation

**Real-time Dashboard** (Bun + SolidJS) shows live hook events, validation stats, and agent activity.

## Quick Start

### Prerequisites

- [Claude Code CLI](https://claude.ai/code)
- [Homebrew](https://brew.sh) (macOS)

### Install

```bash
# Clone the repo
git clone <repo-url> && cd veneficus

# Install dependencies (bun, uv, just, tmux, jq)
just deps

# Initialize the framework in your project
just init
```

### Configure

Fill in the context docs that `just init` creates in `.veneficus/docs/`:

| File | Purpose |
|------|---------|
| `PRD.md` | What you're building and why |
| `architecture.md` | System design and tech stack |
| `decisions.md` | Non-obvious choices and rationale |
| `features.json` | Feature list with status and acceptance criteria |

### Run

```bash
# Load context and see current state
just prime

# Plan a feature
just plan "add user authentication"

# Build it (TDD: red → green → refactor)
just build auth-feature

# Review the result
just review

# Ship a release
just ship v1.0.0
```

## Commands

### SDLC

| Command | Description |
|---------|-------------|
| `just init` | Initialize framework in current project |
| `just prime` | Load context, show current state |
| `just plan "desc"` | Generate structured implementation plan (with ambiguity gate) |
| `just build feat-id` | TDD build cycle (red → green → refactor → optimize) |
| `just optimize feat-id` | Standalone performance optimization pass |
| `just debug "desc"` | Bug investigation: reproduce → diagnose → fix → verify |
| `just review` | Code review + security audit (supports `--consensus` multi-lens mode) |
| `just ship version` | Release prep, changelog, version bump |
| `just retro` | Session retrospective and self-improvement |

### Agent Teams

| Command | Description |
|---------|-------------|
| `just plan-team "desc"` | Plan + generate DESIGN_SPEC.md and tasks for native Agent Teams |
| `just team-build` | Orchestrate build from generated task files |
| `just team agent task` | Run a specific agent (builder, validator, debugger, researcher, qa) |
| `just qa` | Run QA agent with user stories |
| `just browse "task"` | Ad-hoc browser automation |

### Threads

| Command | Description |
|---------|-------------|
| `just parallel feat1 feat2 ...` | P-Thread: parallel work in git worktrees |
| `just chain steps.yaml` | C-Thread: chained steps with human checkpoints |
| `just loop "test cmd"` | L-Thread: loop until test passes |

### Utilities

| Command | Description |
|---------|-------------|
| `just deps` | Install all dependencies |
| `just dashboard` | Start the real-time dashboard |
| `just status` | Show framework status in the terminal |
| `just events` | Show recent hook events |
| `just snapshot "msg"` | Create a rollback snapshot |
| `just snapshots` | List all snapshots |
| `just insights` | Run self-improvement analysis |
| `just context` | Show full project context |
| `just continue` | Resume an interrupted build session |
| `just rollback` | Restore the most recent pre-build snapshot |
| `just sync-commands` | Sync `.veneficus/commands/` → `.claude/commands/` |
| `just clean` | Clean up worktrees and event logs |

## Project Structure

```
.veneficus/
  setup/        # One-command init and dependency installer
  docs/         # Context-as-Contract (PRD, architecture, decisions, features.json)
  agents/       # Agent personas (builder, validator, debugger, researcher, qa, simplifier, contrarian)
  commands/     # SDLC prompts (prime, plan, build, debug, review, ship, retro)
  hooks/        # Claude Code hooks — guards, validators, emitters
  threads/      # P/C/L thread orchestration
  insights/     # Self-improvement collector and analyzer
  skills/       # Reusable tools (git-worktree, context-loader, snapshot, playwright)
  templates/    # Blank starting points for new projects
dashboard/      # Real-time observability UI (Bun + SolidJS)
Research/       # Reference documents on advanced Claude Code patterns
justfile        # Human interface — all commands via `just`
```

## Research

The `Research/` directory contains 8 standalone documents covering advanced Claude Code patterns — agent hooks, thread-based orchestration, autonomous browser automation, agentic DevOps workflows, and more. Load them selectively into sessions with `/read` when relevant.
