# Review — Code Review and Security Audit

Perform a thorough code review of recent changes, focusing on correctness, security, and architecture compliance.

## Input
Scope of review (branch, commit range, or files): $ARGUMENTS

## Protocol

### 1. Identify Changes
- If branch/commit specified: `git diff <range>`
- If no scope: review all uncommitted changes + last commit
- List all modified files

### 2. Code Review Checklist
For each changed file:

**Correctness**
- [ ] Logic handles all cases (happy path + edge cases)
- [ ] Error handling is appropriate (not swallowed, not excessive)
- [ ] No off-by-one errors, null dereferences, or type mismatches
- [ ] Concurrent/async code handles race conditions

**Security** (OWASP Top 10)
- [ ] No SQL injection (parameterized queries used)
- [ ] No XSS (output is escaped/sanitized)
- [ ] No command injection (inputs validated before shell use)
- [ ] No exposed secrets (API keys, passwords, tokens)
- [ ] No path traversal (file paths validated)
- [ ] Authentication/authorization checked where needed

**Architecture**
- [ ] Follows patterns in `.veneficus/docs/architecture.md`
- [ ] No circular dependencies introduced
- [ ] Interfaces/contracts respected
- [ ] Appropriate separation of concerns

**Quality**
- [ ] Tests cover the changes
- [ ] No dead code or unused imports
- [ ] Naming is clear and consistent
- [ ] No obvious performance issues

**IDE Health**
- [ ] `mcp__ide__getDiagnostics` shows no errors for changed files
- [ ] No new warnings introduced

### 3. Report
```
## Code Review: [Scope]

### Summary
[1-2 sentence overview of the changes]

### Findings
#### Critical (must fix)
- [file:line] [description]

#### Important (should fix)
- [file:line] [description]

#### Minor (nice to have)
- [file:line] [description]

### Security
[Any security concerns or "No security issues found"]

### Verdict
APPROVE / REQUEST CHANGES / BLOCK
[Reasoning]
```

## Consensus Mode

When invoked with `--consensus` (or for high-stakes changes: security-sensitive code, public API changes, architectural modifications), run **three independent review passes** with different lenses, then synthesize:

### Pass 1: Correctness Lens
Focus exclusively on:
- Logic errors, edge cases, off-by-one, null handling
- Concurrency/async correctness
- Error handling completeness
- Test coverage of changed code paths

### Pass 2: Security Lens
Focus exclusively on:
- OWASP Top 10 vulnerabilities
- Input validation and sanitization
- Authentication/authorization gaps
- Secrets exposure, path traversal, injection vectors
- Dependency vulnerabilities

### Pass 3: Architecture Lens
Focus exclusively on:
- Compliance with `.veneficus/docs/architecture.md`
- Separation of concerns, coupling, cohesion
- API contract changes and backward compatibility
- Performance implications (N+1 queries, unbounded loops, memory leaks)

### Synthesis
After all three passes, produce a **unified report**:
1. Merge findings, deduplicating across passes
2. Assign final severity (Critical/Important/Minor) — a finding is Critical if ANY pass flagged it as Critical
3. Final verdict: **APPROVE** only if all three passes approve; **BLOCK** if any pass blocks; otherwise **REQUEST CHANGES**
4. Note which lens caught each finding (helps calibrate future reviews)

```
## Consensus Review: [Scope]

### Findings (merged)
| # | Severity | Lens | File:Line | Finding |
|---|----------|------|-----------|---------|
| 1 | Critical | Security | src/auth.ts:42 | SQL injection via unsanitized input |
| 2 | Important | Architecture | src/api/users.ts:15 | Bypasses repository layer |

### Per-Lens Verdicts
- Correctness: APPROVE / REQUEST CHANGES / BLOCK
- Security: APPROVE / REQUEST CHANGES / BLOCK
- Architecture: APPROVE / REQUEST CHANGES / BLOCK

### Final Verdict
APPROVE / REQUEST CHANGES / BLOCK
[Reasoning — what drove the decision]
```

## Rules
- **Read-only**. Don't fix issues — report them.
- **Be specific**. File paths, line numbers, exact code.
- **Prioritize**. Critical > Important > Minor.
- **No nitpicks in BLOCK**. Only block for real issues.
- **In consensus mode**, each pass must be independent — don't let Pass 2 see Pass 1's findings.
