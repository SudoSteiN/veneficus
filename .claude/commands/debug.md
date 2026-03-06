# Debug — Bug Investigation Protocol

Systematic bug investigation using the reproduce→diagnose→fix→verify loop.

## Input
Bug description or failing test: $ARGUMENTS

## Protocol

### 1. Reproduce
- Create a minimal reproduction of the bug
- Write a test that captures the failure
- Confirm the test fails consistently
- If you can't reproduce, gather more information before proceeding

### 2. Diagnose
- Read the error output / stack trace carefully
- Trace the data flow from input to the point of failure
- Check recent changes: `git log --oneline -10`, `git diff HEAD~3`
- Add targeted logging to narrow down the root cause
- Identify the exact file and line where the bug originates

### 3. Fix
- Apply the **minimal** change that fixes the root cause
- Don't fix symptoms — fix the cause
- Don't refactor unrelated code in the same change
- PostToolUse hooks will auto-validate your edits

### 4. Verify
- Run the reproduction test — it should now pass
- Run the full test suite — no regressions
- Remove any temporary debug logging
- Confirm the original bug report scenario works correctly

### 5. Document
- If the bug reveals a design issue, log it in `.veneficus/docs/decisions.md`
- Update any relevant documentation
- Commit with a message explaining the bug and fix

## Stagnation Recovery
If you notice you're stuck (same error repeating, fixes not making progress):

- **After 3 identical failures**: Stop and try a fundamentally different approach. Read `.veneficus/agents/simplifier.md` — ask "what's the simplest thing that could work?"
- **If oscillating** (fix A breaks B, fix B breaks A): Step back and find a solution that addresses both failure modes simultaneously
- **After 5 failures**: Read `.veneficus/agents/contrarian.md` — challenge every assumption. Is the test correct? Is the bug where you think it is? Check environment, imports, caches.

The L-Thread (`uv run .veneficus/threads/l_thread.py`) automates this rotation for you.

## Rules
- **Max 10 iterations** on the fix loop. If you can't solve it in 10 attempts, report findings and escalate.
- **Detect stagnation early**. If your last 3 attempts produced the same error, you're spinning — change strategy, don't retry.
- **Don't guess**. Always reproduce before attempting a fix.
- **Clean up**. Remove all debug logging before declaring done.
- **One bug, one fix**. Don't bundle unrelated changes.

## Report Format
When done, output:
```
## Bug Fix: [Title]
**Symptom**: [What was observed]
**Root Cause**: [What was actually wrong — file:line]
**Fix**: [What was changed and why]
**Tests**: [Which tests verify the fix]
```
