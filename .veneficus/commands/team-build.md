# Team Build — Native Agent Teams Orchestration

Execute a build using Claude Code's native Agent Teams. Reads `DESIGN_SPEC.md` and `tasks/*.md`, then orchestrates agents via TeamCreate, TaskCreate, and SpawnAgent.

**Requires:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` environment variable.

## Input
Optional override: $ARGUMENTS (defaults to reading DESIGN_SPEC.md + tasks/*.md from project root)

## Protocol

### 1. Validate Prerequisites
- Confirm `DESIGN_SPEC.md` exists in the project root
- Confirm `tasks/` directory exists with at least one `task-*.md` file
- Read all task files and validate they have required sections (Description, Acceptance Criteria, Validation)
- Load `.veneficus/docs/architecture.md` for constraint awareness

### 2. Create Task List
For each `tasks/task-*.md` file:
- Use `TaskCreate` to register the task with:
  - `subject`: The task title from the markdown header
  - `description`: The full task content (description + acceptance criteria + files + validation)
- After all tasks are created, use `TaskUpdate` to set `blockedBy` dependencies based on each task's Dependencies section
- Tasks with no dependencies are immediately available for parallel execution

### 3. Spawn Agent Team
- Identify tasks that can run in parallel (no unresolved dependencies)
- For each parallel-ready task, use the Task tool to spawn a subagent:
  - Load the appropriate agent persona from `.veneficus/agents/{role}.md`
  - Pass the full task content as the prompt
  - Include architectural constraints from `.veneficus/docs/architecture.md`
  - Include scope rules: the agent should ONLY modify files listed in the task's "Files to Create/Modify" section
- As tasks complete, check for newly unblocked tasks and spawn agents for those

### 4. Monitor Progress
- After spawning agents, periodically check `TaskList` for completion
- When a task completes:
  - Mark it completed via `TaskUpdate`
  - Check if this unblocks downstream tasks
  - Spawn agents for any newly unblocked tasks
- If a task fails after 3 agent attempts, mark it blocked and report the error

### 5. Validation Phase
- Once all builder tasks are complete, spawn a validator agent:
  - Load `.veneficus/agents/validator.md` persona
  - Pass all acceptance criteria from `DESIGN_SPEC.md`
  - Run all validation commands from individual task files
  - Check for file conflicts or integration issues between tasks
- If validation fails, create fix tasks and re-enter the build loop

### 6. Completion
- Update `features.json` with results
- Print final summary:
  - Tasks completed / failed
  - Validation results
  - Files modified
  - Any issues found

## Orchestration Rules
- **Max parallel agents**: 4 (to avoid resource contention)
- **Max retries per task**: 3 (then escalate)
- **Do not poll TaskList more than 5 times** without progress
- **File isolation**: Each agent should only touch files listed in its task. If two tasks need the same file, they MUST have a dependency between them.
- **Checkpoint after each task**: Verify the task's validation command passes before marking complete

## Fallback
If native Agent Teams are unavailable (env var not set), fall back to sequential execution:
1. Sort tasks by dependency order
2. Execute each task serially using `just team <agent> <task-description>`
3. Run validation after each task
