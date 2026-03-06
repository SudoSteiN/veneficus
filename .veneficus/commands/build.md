# Build — TDD Implementation Protocol

Execute a test-driven build cycle for a feature. The builder writes code, PostToolUse hooks auto-validate every edit, and the validator audits the result.

## Input
Feature ID or description: $ARGUMENTS

## Protocol

### 1. Load Context
- Read `.veneficus/docs/features.json` — find the target feature
- Read `.veneficus/docs/architecture.md` — understand design constraints
- Read relevant existing source files
- **Create a pre-build snapshot**: `bash .veneficus/skills/snapshot.sh save "pre-build-$ARGUMENTS"` — rollback point if things go wrong

### 2. Write Tests (Red Phase)
- Create test file(s) that encode the feature's acceptance criteria
- Each acceptance criterion → at least one test
- Run tests — they should **all fail** (red)
- If any test passes before implementation, the criterion is already met or the test is wrong

**NOTE**: TDD is enforced by the PostToolUse validator. Edits to implementation files are blocked if no corresponding test file exists. Create tests first, then implement. The scope guard also blocks test file edits by default — this is intentional during Green/Refactor phases. During Red phase, set `VENEFICUS_PROTECT_TESTS=0` to write tests.

### 3. Implement (Green Phase)
- Write the minimum code to make tests pass
- Follow existing patterns and architecture
- The PostToolUse hook will auto-validate every file edit:
  - Python: syntax check + ruff lint
  - TypeScript: tsc type check
  - JSON: parse validation
- Fix any validation errors immediately — do not proceed with broken code

### 4. Refactor
- Clean up the implementation while keeping tests green
- Extract common patterns, improve naming, reduce duplication
- Run tests after each refactor step

### 4b. Optimize (when applicable)
Skip for features where performance is not a concern. Apply when:
- The feature involves data processing, I/O, or algorithmic work
- Acceptance criteria include performance targets
- The feature operates on collections or handles concurrent operations

**Process:**
1. Measure baseline (pytest --durations=0, vitest --reporter=verbose)
2. Profile if needed (cProfile, node --prof)
3. Apply ONE targeted optimization at a time
4. Re-run tests (must still pass) + compare timing
5. Document in decisions.md (what, before/after metrics, trade-offs)

**Rules:** Never optimize before Green. Never break tests. Measure before and after.

### 5. Validate
- Run the full test suite (not just new tests)
- If a validator agent is available, hand off for independent review
- Check: functional correctness, test coverage, code quality, security
- **Check IDE diagnostics**: If running in VS Code, call `mcp__ide__getDiagnostics`
  to check the Problems tab for errors/warnings in modified files. Fix any errors
  before proceeding. This catches cross-file type errors, missing imports, and
  language server issues that per-file linting may miss.

### 6. Update State (REQUIRED — do not skip)
- Update `features.json`: set feature status to `"done"` if all criteria pass
- Log any significant decisions in `.veneficus/docs/decisions.md`
- If the feature changed the public API or architecture, update `architecture.md`
- If a README exists and usage examples need updating, update it
- The PostToolUse hook tracks documentation freshness — if you see "DOC REMINDER" warnings, address them now
- Commit with a descriptive message referencing the feature ID

## Rules
- **Never skip red**. Always see tests fail before writing implementation.
- **Fix hook errors immediately**. Don't accumulate validation debt.
- **One feature at a time**. Don't start another feature until this one is done.
- **Commit at green**. Every time tests go from red to green, commit.
