# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Veneficus is a **Claude Code development framework** that turns a single developer into an engineering team. It contains curated research documents AND a fully functional framework template (`.veneficus/`) that provides hooks, validators, agent personas, SDLC commands, thread-based orchestration, and a real-time dashboard.

## Repository Structure

```
Research/                    # 8 research documents on advanced Claude Code patterns
.veneficus/                  # THE FRAMEWORK ENGINE
  setup/                     # One-command initialization (init.py, install_deps.sh)
  docs/                      # Context-as-Contract (PRD, architecture, decisions, features.json)
  agents/                    # Specialized agent personas (builder, validator, researcher, debugger, qa, simplifier, contrarian)
  commands/                  # SDLC orchestration prompts (prime, plan, build, debug, review, ship, retro, continue)
  hooks/                     # Claude Code hook scripts
    validators/              # PostToolUse: syntax/lint/test validation
    emitters/                # Async event emission to dashboard
    guards/                  # PreToolUse: scope enforcement
  threads/                   # P/F/C/L thread type implementations
  insights/                  # Self-improvement system (collector, analyzer)
  skills/                    # Reusable CLI tools (git-worktree, context-loader, snapshot, playwright)
  templates/                 # Blank starting points for new projects
  events/logs/               # Runtime event logs (gitignored)
dashboard/                   # Real-time observability UI (Bun + SolidJS)
.claude/                     # Claude Code native config (settings.json + commands/)
justfile                     # Human interface — all commands via `just`
```

## Key Frameworks

- **Thread Types**: P-Threads (parallel), F-Threads (fusion/best-of-N, deprecated), C-Threads (chained+checkpoints), L-Threads (loop until pass, with stagnation detection and persona rotation)
- **Builder-Validator Pattern**: Builder writes code; validator (read-only) audits against acceptance criteria
- **Agent Hooks**: PreToolUse guards (scope), PostToolUse validators (syntax/lint/test), async event emitters
- **Context as Contract**: PRD.md, architecture.md, decisions.md, features.json anchor all agent work
- **4-Layer Architecture**: Skills → Agents → Commands → Interface (justfile)

## SDLC Commands

| Command | Purpose |
|---------|---------|
| `just init` | Initialize framework in a project |
| `just prime` | Load context, show current state |
| `just plan "desc"` | Generate structured implementation plan (with ambiguity gate) |
| `just plan-team "desc"` | Plan + generate DESIGN_SPEC.md and tasks/*.md for native Agent Teams |
| `just build feat-id` | TDD build cycle (red→green→refactor→optimize) |
| `just optimize feat-id` | Standalone performance optimization pass |
| `just team-build` | Native Agent Teams build (TeamCreate/SpawnAgent) from tasks/*.md |
| `just debug "desc"` | Reproduce→diagnose→fix→verify loop |
| `just review` | Code review + security audit (supports `--consensus` multi-lens mode) |
| `just ship version` | Release prep, changelog, version bump |
| `just retro` | Self-improvement analysis |
| `just continue` | Resume an interrupted build session |
| `just rollback` | Restore most recent pre-build snapshot |
| `just sync-commands` | Sync `.veneficus/commands/` → `.claude/commands/` |

## Native Agent Teams

To use Claude Code's native Agent Teams (TeamCreate, SpawnAgent, TaskCreate, Mailbox):
1. Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in your shell profile
2. Run `just plan-team "description"` to generate DESIGN_SPEC.md + tasks/*.md
3. Run `just team-build` to orchestrate via native team tools

## Agent Behavioral Rules

- **Do not poll TaskList more than 5 times** without making progress on a task
- **Fix validation errors immediately** — do not accumulate or ignore hook feedback
- **Read context docs before writing code** — always load PRD + architecture first
- **One feature at a time** — complete or explicitly defer before starting the next
- **Never self-validate** — the builder writes, the validator checks
- **Max 10 retry iterations** — if stuck after 10 attempts, report findings and escalate
- **Small commits** — each logical change is one commit with a descriptive message
- **Log non-obvious decisions** in `.veneficus/docs/decisions.md`

## Working with Research Documents

- Documents in `Research/` are standalone reference material
- Load selectively into sessions via `/read` when relevant
- Format: Executive Summary → Core Capabilities → Key Insights → Constraints → Actionable Takeaways
- New research docs go in `Research/` following existing format
