# Optimize — Performance Optimization Pass

Run a targeted performance optimization cycle for a feature. All tests must pass before and after every optimization step.

## Input
Feature ID or scope: $ARGUMENTS

## Protocol

### 1. Pre-flight
- Run the full test suite — **all tests must pass** before starting
- Create a pre-optimize snapshot: `bash .veneficus/skills/snapshot.sh save "pre-optimize-$ARGUMENTS"`
- Read `.veneficus/docs/features.json` for any performance-related acceptance criteria
- Read `.veneficus/docs/architecture.md` for constraints

### 2. Baseline
- Measure current performance:
  - Python: `python -m pytest --durations=0` or targeted timing
  - TypeScript/JS: `npx vitest --reporter=verbose` or targeted timing
- Record baseline numbers (document in output)
- Identify the specific files/functions in scope for optimization

### 3. Profile
- Profile the code to identify actual hot paths:
  - Python: `python -m cProfile -s cumtime` or `py-spy`
  - Node: `node --prof` or `0x`
- Focus on the top 3-5 time consumers
- Do NOT guess — measure

### 4. Optimize (iterative)
For each optimization:
1. Identify ONE specific optimization to apply
2. Apply the change
3. Re-run tests — they **must still pass**
4. Re-measure — compare against baseline
5. If improvement is negligible (<5%), consider reverting
6. If tests break, revert immediately

**Common optimizations** (in order of typical impact):
- Algorithmic improvements (O(n^2) → O(n log n))
- Reduce I/O (batch operations, caching)
- Eliminate redundant computation (memoization)
- Reduce allocations (reuse buffers, generators)
- Parallelize independent operations

### 5. Document
- Log results in `.veneficus/docs/decisions.md`:
  ```
  ## Optimization: [Feature/Component]
  - **What**: [Description of optimization]
  - **Before**: [Baseline metric]
  - **After**: [Optimized metric]
  - **Trade-offs**: [Any trade-offs introduced]
  ```
- Update `features.json` if performance criteria are now met

### 6. Final Verification
- Run full test suite one more time
- Compare total before/after metrics
- Commit with message: `perf: [description of optimization]`

## Rules
- **Never optimize before Green**. All tests must pass before you start.
- **Never break tests**. If an optimization breaks a test, revert it.
- **Measure before AND after**. No "I think this is faster" — prove it.
- **One optimization at a time**. Don't batch multiple changes.
- **Profile first**. Optimize the actual bottleneck, not what you assume is slow.
- **Know when to stop**. If the feature meets its performance criteria, stop.
