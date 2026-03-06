# Plan — Generate Structured Implementation Plan

Create a detailed, structured implementation plan for the given task. This is a meta-prompt that forces rigorous planning before any code is written.

## Input
The user will describe what they want to build or change: $ARGUMENTS

## Process

### 0a. Context Readiness Check

Before anything else, check whether the project has populated context documents.

Read `.veneficus/docs/PRD.md` and `.veneficus/docs/features.json`.

Context is **empty** if **any** of these are true:
- `PRD.md` does not exist OR contains `[Your project name]`
- `features.json` does not exist OR contains `"project": "project-name"` OR only has `"Example Feature"`

**If context is empty** → Load the ideator persona from `.veneficus/agents/ideator.md` and execute the ideation protocol from `.veneficus/commands/ideation-protocol.md`. Use $ARGUMENTS as the user's initial idea. After ideation completes (Phase 7 of the protocol), continue to Phase 0b below.

**If context is populated** → Skip directly to Phase 0b.

### 0b. Ambiguity Check

Before planning, assess the task description on four dimensions. For each, score 0.0 (completely clear) to 1.0 (completely unclear):

| Dimension | Question | Score |
|-----------|----------|-------|
| **Goals** | Is it clear what the end result should look like? | _/1.0 |
| **Constraints** | Are technical constraints, compatibility requirements, and boundaries known? | _/1.0 |
| **Success Criteria** | Can you write a concrete test or acceptance check for "done"? | _/1.0 |
| **Context** | Do you understand where this fits in the existing system? | _/1.0 |

**Average the four scores.** If the average ambiguity score is **> 0.3**, do NOT proceed to planning. Instead:

1. State the ambiguity score and which dimensions are unclear
2. Ask 3-5 **targeted clarifying questions** — specific, not open-ended:
   - Bad: "What do you want?" / "Can you tell me more?"
   - Good: "Should this endpoint return paginated results or all records?" / "Does this need to work with the existing auth middleware or replace it?"
3. Wait for answers before generating the plan

If ambiguity score is **≤ 0.3**, proceed directly to planning.

### 1. Read context
   - `.veneficus/docs/PRD.md`
   - `.veneficus/docs/architecture.md`
   - `.veneficus/docs/features.json`
   - Relevant existing source files

### 2. Generate plan using this exact structure:

```markdown
## Plan: [Title]

### Task Description
[Clear statement of what will be built/changed and why]

### Acceptance Criteria
1. [Measurable criterion]
2. [Measurable criterion]

### Team Orchestration
- **Builder**: [What the builder agent will do]
- **Validator**: [What criteria the validator will check]
- **Thread Type**: [P/F/C/L and why]

### Implementation Steps
| ID | Step | Depends On | Parallel | Agent |
|----|------|-----------|----------|-------|
| 1  | [description] | — | no | builder |
| 2  | [description] | 1 | no | builder |
| 3  | [description] | 1 | yes (with 2) | builder |

### Files to Create/Modify
- `path/to/file.ext` — [what changes]

### Validation Rules
- [ ] All acceptance criteria have corresponding tests
- [ ] Tests pass
- [ ] No lint errors
- [ ] Architecture constraints respected
- [ ] features.json updated

### Risks & Mitigations
- **Risk**: [what could go wrong]
  **Mitigation**: [how to handle it]
```

### 3. Add to features.json
Create a new feature entry with the plan's acceptance criteria

## Rules
- **Context gate**: If context docs are empty, run ideation first. Never plan against placeholder templates.
- **Ambiguity gate**: Do NOT skip the ambiguity check. Vague inputs produce bad plans. It's faster to ask 3 questions now than to redo the plan later.
- Every step must have a clear, verifiable outcome
- Identify parallelizable steps (multiple agents can work simultaneously)
- Default to the simplest thread type that works (usually serial, escalate to P/F/C/L when justified)
- Plans should be executable — no vague steps like "figure out the best approach"
