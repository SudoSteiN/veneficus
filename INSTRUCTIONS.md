# Building an App with Veneficus — Step by Step

This guide walks you through building a complete app using the Veneficus framework, from initial setup to shipping a release.

---

## Phase 1: Setup

### Prerequisites

You need the Claude Code CLI installed. Get it from https://claude.ai/code.

You also need Homebrew. Everything else gets installed automatically.

### Create your project

```bash
mkdir my-app && cd my-app
git init
```

### Get Veneficus into your project

Copy or clone the Veneficus repo so that `.veneficus/`, `justfile`, and `dashboard/` are at your project root.

### Install dependencies

```bash
just deps
```

This installs via Homebrew:
- **bun** — JavaScript runtime (dashboard, Playwright)
- **uv** — Python package manager (framework scripts)
- **just** — command runner (you already have this if you ran the command)
- **tmux** — terminal multiplexer (parallel threads)
- **jq** — JSON processor (event logs)

It also installs Playwright's Chromium browser for QA automation and checks for the Claude Code CLI.

**Optional environment variables** (add to `~/.zshrc`):
```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1  # Enable native Agent Teams
```

### Initialize the framework

```bash
just init
```

This creates the following structure in your project:

```
.veneficus/docs/
  PRD.md                  # Product requirements (from template)
  architecture.md         # System design (from template)
  features.json           # Feature queue (from template)
  decisions.md            # Technical decisions log (empty)
.veneficus/events/logs/   # Runtime event logs (gitignored)
.claude/
  commands/               # SDLC command prompts (copied from framework)
  settings.json           # Claude Code hook configuration
tasks/                    # Task files for Agent Teams
DESIGN_SPEC.md            # Design spec template
CLAUDE.md                 # Claude Code project instructions (from template)
.claudeignore             # Files Claude should ignore
.gitignore                # Updated with framework entries
```

Files that already exist are never overwritten.

---

## Phase 2: Define Your Project

Before building anything, you need three context documents populated. These are the contract that all agents work against — they read these files before writing any code.

### Option A: Guided conversation (recommended)

Run the plan command with a description of your idea:

```bash
just plan "a CLI task manager for developers"
```

When context docs are empty, `plan` automatically runs a guided ideation interview — about 15 questions over ~10 minutes. It produces all four context documents (PRD.md, architecture.md, decisions.md, features.json) from your answers, then continues into implementation planning.

### Option B: Fill in docs manually

#### PRD.md

Open `.veneficus/docs/PRD.md` and replace the placeholders:

```markdown
# Product Requirements Document

## Project Name
TaskFlow — a CLI task manager

## Problem Statement
Developers need a fast, keyboard-driven task manager that lives in the
terminal. Existing tools require a browser or have slow startup times.

## Success Criteria
1. Users can create, list, complete, and delete tasks from the CLI
2. Tasks persist across sessions (SQLite)
3. Startup time under 100ms

## Scope

### In Scope
- CRUD operations for tasks
- SQLite persistence
- Priority levels (low, medium, high)
- Filtering and sorting

### Out of Scope
- GUI or web interface
- Multi-user / sync
- Recurring tasks

## User Stories
- As a developer, I want to add a task quickly so I don't lose my thought
- As a developer, I want to see my high-priority tasks first so I focus on what matters
- As a developer, I want tasks to survive terminal restarts so nothing gets lost

## Technical Constraints
- Python 3.12+
- No external service dependencies
- Single binary distribution via PyInstaller

## Dependencies
- click (CLI framework)
- SQLite (built-in)
- rich (terminal formatting)
```

#### architecture.md

Open `.veneficus/docs/architecture.md`:

````markdown
# Architecture

## Overview
TaskFlow is a single-process CLI app with a layered architecture:
CLI → Service → Repository → SQLite.

## System Diagram
```
┌──────────┐    ┌───────────┐    ┌────────────┐    ┌────────┐
│ CLI (click)│───→│  Service  │───→│ Repository │───→│ SQLite │
└──────────┘    └───────────┘    └────────────┘    └────────┘
```

## Components

### CLI Layer
- **Purpose**: Parse commands and options, format output
- **Technology**: Python, click, rich
- **Interface**: `taskflow add/list/done/rm`

### Service Layer
- **Purpose**: Business logic, validation, sorting
- **Technology**: Python
- **Interface**: TaskService class

### Repository Layer
- **Purpose**: Data access, SQL queries
- **Technology**: Python, sqlite3
- **Data**: tasks table (id, title, priority, status, created_at)

## Conventions
- **File naming**: snake_case.py
- **Code style**: ruff (default rules)
- **Error handling**: Raise domain exceptions, catch at CLI layer
- **Testing**: pytest, one test file per module
````

#### features.json

Open `.veneficus/docs/features.json`:

```json
{
  "project": "taskflow",
  "features": [
    {
      "id": "feat-001",
      "name": "Task CRUD",
      "description": "Create, read, update, and delete tasks via CLI",
      "status": "pending",
      "priority": 1,
      "acceptance_criteria": [
        "taskflow add 'Buy groceries' creates a task",
        "taskflow list shows all tasks with IDs",
        "taskflow done <id> marks a task complete",
        "taskflow rm <id> deletes a task"
      ],
      "files": ["src/cli.py", "src/service.py", "src/repository.py"],
      "validate": "pytest tests/",
      "depends_on": [],
      "notes": "Start with in-memory store, add SQLite in feat-002"
    },
    {
      "id": "feat-002",
      "name": "SQLite Persistence",
      "description": "Persist tasks to a local SQLite database",
      "status": "pending",
      "priority": 2,
      "acceptance_criteria": [
        "Tasks survive process restart",
        "Database created automatically on first run",
        "Database location: ~/.taskflow/tasks.db"
      ],
      "files": ["src/repository.py", "src/db.py"],
      "validate": "pytest tests/",
      "depends_on": ["feat-001"],
      "notes": ""
    },
    {
      "id": "feat-003",
      "name": "Priority and Filtering",
      "description": "Assign priority levels and filter/sort tasks",
      "status": "pending",
      "priority": 3,
      "acceptance_criteria": [
        "taskflow add --priority high 'Urgent thing' sets priority",
        "taskflow list --priority high shows only high-priority tasks",
        "Default sort: high → medium → low"
      ],
      "files": ["src/cli.py", "src/service.py"],
      "validate": "pytest tests/",
      "depends_on": ["feat-001"],
      "notes": ""
    }
  ]
}
```

**Field reference:**
- `id` — Unique identifier, used with `just build feat-001`
- `status` — `"pending"` | `"in_progress"` | `"done"`
- `priority` — Build order (1 = first)
- `acceptance_criteria` — What must be true for the feature to be complete
- `files` — Expected files to create or modify
- `validate` — Command to run to verify the feature works
- `depends_on` — Feature IDs that must be done first

#### CLAUDE.md

Open `CLAUDE.md` at the project root and fill in your tech stack, commands, and conventions. This is what Claude reads first in every session.

#### Verify everything loads

```bash
just prime
```

This reads all your context docs and outputs a status report:

```
## Session Context

**Project**: TaskFlow — a CLI task manager
**Architecture**: CLI (click) → Service → Repository → SQLite

## Progress
| Status  | Count | Features                          |
|---------|-------|-----------------------------------|
| Done    | 0     |                                   |
| Active  | 0     |                                   |
| Pending | 3     | feat-001, feat-002, feat-003      |

## Recommended Next Action
Build feat-001 (Task CRUD) — it has no dependencies and is highest priority.
```

If any context files are missing, `prime` will tell you which ones.

---

## Phase 3: Plan

Before writing code, generate a structured plan. This forces you to think through the implementation before any code is written.

> If you used the guided conversation in Phase 2, `just plan` already produced an implementation plan for your first feature — skip to "Review before building" below. Otherwise, generate a plan manually:

### Single feature

```bash
just plan "Add CRUD operations for tasks"
```

This reads your context docs and outputs a plan:

```markdown
## Plan: Task CRUD

### Task Description
Implement create, list, complete, and delete operations for tasks.

### Acceptance Criteria
1. taskflow add 'Buy groceries' creates a task
2. taskflow list shows all tasks with IDs
3. taskflow done <id> marks a task complete
4. taskflow rm <id> deletes a task

### Implementation Steps
| ID | Step                        | Depends On | Agent   |
|----|-----------------------------|-----------|---------|
| 1  | Create Task data model      | —         | builder |
| 2  | Write tests for CRUD ops    | 1         | builder |
| 3  | Implement repository layer  | 1         | builder |
| 4  | Implement service layer     | 3         | builder |
| 5  | Wire CLI commands           | 4         | builder |

### Files to Create/Modify
- src/models.py — Task dataclass
- src/repository.py — In-memory task store
- src/service.py — Business logic
- src/cli.py — Click commands
- tests/test_service.py — Unit tests

### Validation Rules
- [ ] All acceptance criteria have corresponding tests
- [ ] Tests pass
- [ ] No lint errors

### Risks & Mitigations
- **Risk**: ID generation collisions
  **Mitigation**: Use UUID or auto-incrementing integer
```

The plan also adds a feature entry to `features.json` if one doesn't exist.

### Multiple features / full app

```bash
just plan-team "Build the complete TaskFlow app"
```

This generates:
- `DESIGN_SPEC.md` — Overall design and task breakdown
- `tasks/task-01-name.md` — One file per task, with dependencies, acceptance criteria, and validation commands

These files are used by the Agent Teams build mode (Phase 4, Option C).

### Review before building

Always read the generated plan. Edit it if needed — it's just markdown. The build phase uses these files as its contract.

---

## Phase 4: Build

### Option A: Single feature at a time (recommended for starting out)

```bash
just build feat-001
```

The build agent follows a strict TDD cycle:

1. **Red** — Write tests that encode the acceptance criteria. Run them. They all fail.
2. **Green** — Write the minimum code to make tests pass.
3. **Refactor** — Clean up while keeping tests green.

During the build, PostToolUse hooks automatically validate every file edit:
- **Python**: syntax check + ruff lint
- **TypeScript**: tsc type check
- **JSON**: parse validation

If a hook catches an error, the agent fixes it immediately before continuing.

When the feature is complete:
- `features.json` is updated (status → `"done"`)
- Significant decisions are logged in `decisions.md`
- Changes are committed with a message referencing the feature ID

Then move to the next feature:
```bash
just build feat-002
```

### Option B: Parallel features

For independent features that don't depend on each other:

```bash
just parallel feat-002 feat-003
```

This creates separate git worktrees and runs each build in a tmux pane. Both features build simultaneously. When both finish, you merge the worktrees back.

Use this when features don't share files. If they touch the same code, build them sequentially.

### Option C: Agent Teams

For larger projects with many tasks:

```bash
# Requires: export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
just team-build
```

This reads `DESIGN_SPEC.md` and `tasks/*.md` (generated by `just plan-team`) and orchestrates multiple agents working on tasks with dependency tracking.

---

## Phase 5: Debug (as needed)

When something breaks, don't just hack at it. Use the systematic debug protocol:

```bash
just debug "taskflow list crashes when database is empty"
```

The debug agent follows a strict loop:
1. **Reproduce** — Write a test that captures the failure
2. **Diagnose** — Trace the data flow, read stack traces, check recent changes
3. **Fix** — Apply the minimal change that fixes the root cause
4. **Verify** — Run the reproduction test + full suite, no regressions

Max 10 iterations. If the agent can't solve it in 10 attempts, it reports findings and escalates to you.

### L-Thread: loop until a test passes

For tight fix-verify loops:

```bash
just loop "pytest tests/test_repository.py::test_empty_db -x"
```

This runs the test, reads the failure, makes a fix, and repeats until the test passes (max 10 retries).

---

## Phase 6: Review

Before shipping, run a code review:

```bash
just review
```

By default this reviews the last commit. You can specify a range:

```bash
just review "main..HEAD"
```

The review agent checks every changed file against four categories:

- **Correctness** — Logic handles edge cases, no off-by-one errors, proper error handling
- **Security** — OWASP Top 10: no SQL injection, XSS, command injection, exposed secrets
- **Architecture** — Follows patterns in `architecture.md`, no circular dependencies
- **Quality** — Tests cover changes, no dead code, clear naming

Output is a structured report with findings ranked Critical → Important → Minor, ending with a verdict: APPROVE, REQUEST CHANGES, or BLOCK.

The review agent is read-only — it reports issues but doesn't fix them.

---

## Phase 7: Ship

When you're ready to release:

```bash
just ship v1.0.0
```

This runs through a release checklist:

1. **Pre-flight** — Runs full test suite, checks for uncommitted changes, verifies all features are done or deferred
2. **Changelog** — Reads commits since the last tag, categorizes them (Added/Changed/Fixed/Removed), writes CHANGELOG.md
3. **Version bump** — Updates version in package.json, pyproject.toml, or wherever your version lives
4. **Commit and tag** — Creates a release commit (`chore: release v1.0.0`) and git tag

The ship command **never pushes**. You review the release commit and push manually:

```bash
git push && git push --tags
```

---

## Phase 8: Retrospective (optional)

After a session or a milestone, run a retrospective:

```bash
just retro
```

This analyzes your event logs and git history to identify patterns:
- Which validation hooks fail most often?
- Did any agent get stuck in retry loops?
- How was time distributed across plan/build/test/review?
- What could be improved?

The output is a set of actionable recommendations with supporting data. You decide which ones to apply — the retro agent never makes changes automatically.

---

## Appendix A: Context Doc Templates

These are the templates that `just init` copies into your project. They're shown here for reference — the actual templates live in `.veneficus/templates/`.

### PRD.md

```markdown
# Product Requirements Document

## Project Name
[Your project name]

## Problem Statement
[What problem does this project solve? Who has this problem?]

## Success Criteria
1. [Measurable outcome that defines "done"]
2. [Measurable outcome]

## Scope

### In Scope
- [Feature or capability]

### Out of Scope
- [Explicitly excluded]

## User Stories
- As a [user type], I want [action] so that [benefit]

## Technical Constraints
- [Runtime/platform requirements]
- [Performance requirements]

## Dependencies
- [External services, APIs, libraries]

## Timeline
- Phase 1: [description] — [target]
```

### architecture.md

````markdown
# Architecture

## Overview
[High-level description of the system and its purpose]

## System Diagram
```
[ASCII diagram of major components and their relationships]
```

## Components

### [Component Name]
- **Purpose**: [What it does]
- **Technology**: [Language, framework, runtime]
- **Interface**: [API endpoints, function signatures, message formats]
- **Data**: [What data it owns/manages]

## Data Models
```
[Schema definitions, type definitions, or entity descriptions]
```

## Key Design Decisions
- [Decision]: [Rationale]

## Conventions
- **File naming**: [convention]
- **Code style**: [convention]
- **Error handling**: [convention]
- **Testing**: [convention]
````

### features.json

```json
{
  "project": "project-name",
  "features": [
    {
      "id": "feat-001",
      "name": "Example Feature",
      "description": "Description of what this feature does",
      "status": "pending",
      "priority": 1,
      "acceptance_criteria": [
        "Criterion 1: specific, measurable outcome",
        "Criterion 2: specific, measurable outcome"
      ],
      "files": [],
      "validate": "",
      "depends_on": [],
      "notes": ""
    }
  ]
}
```

---

## Appendix B: Command Reference

### SDLC Commands

| Command | Description |
|---------|-------------|
| `just init` | Initialize framework in current project |
| `just deps` | Install all dependencies (bun, uv, just, tmux, jq) |
| `just prime` | Load context docs and show current project state |
| `just plan "desc"` | Generate structured implementation plan (auto-ideates if context docs are empty) |
| `just plan-team "desc"` | Plan + generate DESIGN_SPEC.md and tasks/*.md |
| `just build feat-id` | TDD build cycle (red → green → refactor) |
| `just team-build` | Agent Teams build from DESIGN_SPEC.md + tasks/*.md |
| `just debug "desc"` | Systematic bug investigation |
| `just review` | Code review + security audit (default: last commit) |
| `just review "range"` | Code review for a specific commit range |
| `just ship version` | Release prep: tests, changelog, version bump, tag |
| `just retro` | Session retrospective and improvement analysis |

### Thread Commands

| Command | Description |
|---------|-------------|
| `just parallel feat-1 feat-2` | P-Thread: build features in parallel worktrees |
| `just chain steps.yaml` | C-Thread: sequential steps with human checkpoints |
| `just loop "test cmd"` | L-Thread: repeat until test passes (max 10) |

### Agent Commands

| Command | Description |
|---------|-------------|
| `just team agent task` | Run a specific agent (builder, validator, researcher, debugger, qa) |
| `just qa stories.yaml` | Run QA agent against user stories |
| `just browse "task"` | Ad-hoc browser automation |

### Utility Commands

| Command | Description |
|---------|-------------|
| `just status` | Show framework status, worktrees, and event stats |
| `just events` | Show last 20 events |
| `just events 50` | Show last N events |
| `just snapshot "msg"` | Create a rollback snapshot |
| `just snapshots` | List snapshots |
| `just context` | Show full project context |
| `just dashboard` | Start the real-time observability dashboard |
| `just clean` | Clean up worktrees and event logs |

---

## Appendix C: Thread Types

Threads are orchestration patterns for running agents. Most of the time you'll just use `just build` (serial, single-feature). Use threads when you need parallelism or structured multi-step workflows.

### P-Thread (Parallel)

**When to use**: Two or more features that don't share files.

```bash
just parallel feat-002 feat-003
```

Creates a git worktree per feature and runs each build in a separate tmux pane. Merge results when done.

**Don't use when**: Features touch the same files — you'll get merge conflicts.

### C-Thread (Chained)

**When to use**: A multi-step workflow where each step must succeed before the next starts, and you want human checkpoints between steps.

Create a YAML file describing the steps:

```yaml
# steps.yaml
steps:
  - name: "Set up database schema"
    prompt: "Create the SQLite schema for tasks"
    checkpoint: true    # pause for human review

  - name: "Implement repository layer"
    prompt: "Implement TaskRepository using the schema"
    checkpoint: false   # continue automatically

  - name: "Wire CLI commands"
    prompt: "Add click commands that use the repository"
    checkpoint: true    # pause for human review
```

```bash
just chain steps.yaml
```

Each step runs sequentially. At checkpoints, execution pauses for your review.

### L-Thread (Loop)

**When to use**: A specific test is failing and you want the agent to iterate until it passes.

```bash
just loop "pytest tests/test_db.py::test_migration -x"
```

Runs the test → reads the failure → applies a fix → repeats. Stops when the test passes or after 10 iterations.

**Don't use when**: The test failure is caused by a systemic issue (wrong architecture, missing dependency). L-Threads are for targeted, isolated fixes.
