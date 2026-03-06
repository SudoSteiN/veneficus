# Plan Team — Generate Plan + DESIGN_SPEC.md + tasks/*.md for Native Agent Teams

Generate a structured implementation plan AND produce the artifacts needed for Claude Code's native Agent Teams: a populated `DESIGN_SPEC.md` and individual `tasks/task-NN-name.md` files.

## Input
The user will describe what they want to build or change: $ARGUMENTS

## Process

### 0. Context Readiness Check
Read `.veneficus/docs/PRD.md` and `.veneficus/docs/features.json`.
If PRD.md contains `[Your project name]` or features.json contains `"project-name"`, stop and tell the user:
"Your project doesn't have context docs yet. Run `just plan "your idea"` first — it will guide you through setup."

1. **Read context**:
   - `.veneficus/docs/PRD.md`
   - `.veneficus/docs/architecture.md`
   - `.veneficus/docs/features.json`
   - `.veneficus/templates/DESIGN_SPEC.template.md`
   - `.veneficus/templates/task.template.md`
   - Relevant existing source files

2. **Decompose into tasks**:
   - Break the work into self-contained tasks that can be assigned to individual agents
   - Each task should touch an independent set of files (minimize conflicts)
   - Identify dependencies between tasks (which must complete before others can start)
   - Identify tasks that can run in parallel (no shared files, no dependency)
   - Assign each task an agent role: `builder`, `validator`, `researcher`, `debugger`, or `qa`

3. **Generate DESIGN_SPEC.md** in the project root with this structure:

```markdown
# Design Specification

## Overview
[High-level description of what this project/feature does]

## Goals
1. [Primary goal]
2. [Secondary goal]

## Architecture
[How the system is organized — components, data flow, key abstractions]

## Tasks

| Task ID | Description | Dependencies | Assignee | Parallel |
|---------|-------------|--------------|----------|----------|
| task-01-name | [description] | none | builder | yes |
| task-02-name | [description] | task-01 | builder | no |
| task-03-name | [description] | none | validator | yes (with 01) |

## Constraints
- [Technical constraint from architecture.md]
- [Scope constraint from PRD.md]

## Acceptance Criteria
1. [Measurable criterion]
2. [Measurable criterion]
```

4. **Generate individual task files** in `tasks/` directory. For each task, create `tasks/task-NN-name.md`:

```markdown
# Task: task-NN-name

## Description
[What this task accomplishes — specific enough for an agent to execute independently]

## Dependencies
- [task-id]: [why this must complete first]
(or "none" if independent)

## Acceptance Criteria
1. [Specific, testable criterion]
2. [Specific, testable criterion]

## Files to Create/Modify
- `path/to/file.py` — [what changes]

## Validation
```bash
[command to verify this task is complete]
```

## Agent Role
[builder|validator|researcher|debugger|qa]

## Notes
- [Context the agent needs]
- [Patterns to follow from existing code]
```

5. **Update features.json** — Add a new feature entry with the plan's acceptance criteria

6. **Print summary** showing:
   - Total tasks created
   - Dependency graph (which tasks block which)
   - Which tasks can run in parallel
   - Command to execute: `just team-build`

## Rules
- Every task must have a clear, verifiable outcome via its validation command
- Tasks that touch the same files MUST have a dependency between them
- Prefer many small tasks over few large tasks — agents work best with focused scope
- Each task file must be self-contained — an agent should be able to execute it without reading other task files
- Always create at least one validation/QA task at the end that depends on all builder tasks
- Clean up any existing `tasks/*.md` files before generating new ones (warn first)
