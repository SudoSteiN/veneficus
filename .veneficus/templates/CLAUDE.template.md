# CLAUDE.md

## Project Overview
[Brief description of what this project does]

## Tech Stack
- **Language**: [e.g., Python 3.12, TypeScript 5.x]
- **Framework**: [e.g., FastAPI, Next.js]
- **Database**: [e.g., PostgreSQL, SQLite]
- **Package Manager**: [e.g., uv, bun, npm]

## Commands
- **Install**: `[command]`
- **Dev server**: `[command]`
- **Test**: `[command]`
- **Lint**: `[command]`
- **Build**: `[command]`

## Architecture
See `.veneficus/docs/architecture.md` for full design.

Key patterns:
- [Pattern 1]
- [Pattern 2]

## Conventions
- [Naming conventions]
- [File organization]
- [Error handling approach]

## Veneficus Framework
This project uses the Veneficus development framework.

### SDLC Commands
- `/prime` — Load context and show current state
- `/plan [description]` — Generate implementation plan
- `/build [feature-id]` — TDD build cycle
- `/debug [description]` — Bug investigation
- `/review` — Code review and security audit
- `/ship [version]` — Release preparation
- `/retro` — Session retrospective

### Agent Behavioral Rules
- **Do not poll TaskList more than 5 times** without making progress
- **Fix validation errors immediately** — do not accumulate them
- **Read context docs before writing code** — always load PRD + architecture first
- **One feature at a time** — complete or defer before starting the next
- **Never self-validate** — the builder writes, the validator checks
- **Max 10 retry iterations** — escalate if stuck
