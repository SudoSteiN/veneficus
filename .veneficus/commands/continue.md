# Continue — Resume Interrupted Build Session

Pick up where a previous session left off. Detects in-progress work, assesses what was completed, and resumes cleanly.

## Protocol

### 1. Detect In-Progress Work
- Read `.veneficus/docs/features.json` — find any feature with status `in_progress`
- If no in-progress features found, report "Nothing to resume" and exit
- If multiple in-progress features found, list them and ask which to resume

### 2. Assess Current State
For the target feature, gather:
- **Event log tail**: `tail -20 .veneficus/events/logs/events.jsonl` — what hooks fired, what failed last
- **Git state**: `git log --oneline -5` and `git diff --stat` — what was actually changed
- **Feature details**: Read the feature's acceptance criteria and implementation steps from features.json
- **Snapshot availability**: `bash .veneficus/skills/snapshot.sh list` — check for pre-build snapshots

### 3. Build Resume Assessment
Analyze the evidence to determine:
- Which implementation steps appear **done** (committed code, passing tests)
- Which step was **in progress** when the session ended (uncommitted changes, failing tests)
- Which steps are **remaining**

### 4. Resume
Present the assessment:
```
## Resuming: [Feature ID]

### Completed
- Step 1: [description] — committed in [sha]
- Step 2: [description] — committed in [sha]

### Current State
- Step 3: [description] — partially implemented, [uncommitted changes / failing test]

### Remaining
- Step 4: [description]
- Step 5: [description]

### Rollback Available
- Snapshot: pre-build-[feature-id] (run `just rollback` to restore)
```

Then continue the build from the current state, following the same TDD protocol as `build.md`:
- If there are uncommitted changes, assess whether they're valid progress or should be reverted
- Pick up at the current step and continue through remaining steps
- PostToolUse hooks will auto-validate as normal

## Rules
- **Don't redo completed work**. Trust committed code and passing tests.
- **Verify before continuing**. Run existing tests to confirm completed steps still pass.
- **One feature at a time**. If multiple features are in-progress, resolve one before starting another.
- **Snapshot first**. Before making any changes, create a snapshot of the current state.
