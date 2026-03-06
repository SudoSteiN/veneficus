# Prime — Load Context and Show Current State

You are starting a development session. Load the project context and provide a situation report.

## Steps

1. **Read context documents** (in order):
   - `.veneficus/docs/PRD.md` — What we're building and why
   - `.veneficus/docs/architecture.md` — How it's designed
   - `.veneficus/docs/decisions.md` — Past decisions and their rationale
   - `.veneficus/docs/features.json` — Current build queue with status

2. **Summarize current state**:
   - Project: one-line description from PRD
   - Architecture: key components and their relationships
   - Progress: features done / in-progress / pending (from features.json)
   - Recent decisions: last 3 entries from decisions.md

3. **Identify next actions**:
   - What feature should be built next (first `pending` item in features.json)?
   - Are there any `in_progress` features that need attention?
   - Any blockers or open questions?

4. **Output format**:
```
## Session Context

**Project**: [name] — [one-line description]
**Architecture**: [key components summary]

## Progress
| Status | Count | Features |
|--------|-------|----------|
| Done   | N     | feat-a, feat-b |
| Active | N     | feat-c |
| Pending| N     | feat-d, feat-e |

## Recent Decisions
- [date]: [decision summary]

## Recommended Next Action
[What to do next and why]
```

If any context files are missing, note which ones and suggest running `just init` to set up the framework.
