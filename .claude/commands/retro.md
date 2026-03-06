# Retro — Self-Improvement Analysis

Analyze the current session or recent sessions to identify friction patterns and generate improvement recommendations.

## Protocol

### 1. Run Native Insights (if available)
Claude Code's built-in `/insights` command analyzes your conversation history across 1000+ messages to identify friction patterns. Run it first for a high-level view:
```
/insights
```
Capture the output — it will inform the deeper analysis below.

### 2. Gather Data
- Read event logs: `.veneficus/events/logs/events.jsonl`
- If dashboard DB exists, query it for aggregated stats
- Read recent git history for commit patterns

### 3. Analyze Patterns
Run the insights collector for metrics:
```bash
uv run .veneficus/insights/collector.py
```

### 4. Review Areas
- **Validation failures**: Which hooks fail most? Same lint rule repeatedly?
- **Retry loops**: Did any agent get stuck in fix→fail cycles?
- **Scope violations**: Did agents try to edit files outside their scope?
- **Time distribution**: How long on each SDLC phase (plan/build/test/review)?
- **Agent utilization**: Which agents were used? Which were idle?
- **Thread effectiveness**: Did parallel work actually save time?

### 5. Generate Recommendations
Write actionable suggestions to `.veneficus/insights/recommendations.md`:

```markdown
## Session Retrospective — [Date]

### Metrics
- Total events: N
- Validation failures: N (pass rate: X%)
- Retry loops: N (avg iterations: X)
- Features completed: N

### Findings
1. **[Pattern]**: [Description with data]
   - Impact: [How it affected productivity]
   - Recommendation: [Specific action to take]

2. **[Pattern]**: ...

### Suggested Changes
- [ ] [Specific change to CLAUDE.md, hooks, or agent prompts]
- [ ] [Specific change]

### Meta
- Session duration: ~Xm
- Most active files: [list]
- Most common errors: [list]
```

### 6. Present to Human
Show the recommendations. The human decides which to apply — **never auto-apply meta-level changes**.

## Rules
- **Data-driven**. Every recommendation must cite specific events/patterns.
- **Actionable**. Don't say "improve tests" — say "add ruff rule X to prevent Y".
- **Human decides**. Present recommendations; don't auto-apply.
