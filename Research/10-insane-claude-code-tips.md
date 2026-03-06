# 10 Insane Claude Code Tips

This technical analysis focuses on the advanced workflows and features of **Claude Code** (v2.1.37+), extracting concrete strategies to build a robust, agentic development system.

## 1. Executive Summary

The video outlines a shift from using Claude Code as a simple chat interface to an orchestrated agentic system driven by rigorous documentation, custom hooks, and adversarial verification.
**Verdict:** This is a **game-changer** for developers looking to move beyond "copilot" style interactions toward autonomous, multi-agent project execution.

---

## 2. Core Capabilities & Features ("Claude Code" Specifics)

* **`/insights` Command:** A powerful diagnostic tool that analyzes historical session data (1,000+ messages) to identify "primary friction types" (e.g., Wrong Approach, Hallucinations) and suggests specific prompt improvements for the `CLAUDE.md` file.
* **Custom Skills (`SKILL.md`):** Reusable prompt templates triggered by custom commands (e.g., `/animation`) to maintain style consistency and reduce repetitive instructions.
* **Claude Hooks:** User-defined shell commands that execute during the Claude lifecycle. Key triggers include:
  * `SessionStart`, `PreToolUse`, `PostToolUse`, `SubagentStart`.
  * **Exit Code Logic:** **`Exit 0`** (Success), **`Exit 2`** (Blocking Error - feeds `stderr` back to Claude as an error message).
* **Experimental MCP-CLI Mode:**
  * Flag: `export ENABLE_EXPERIMENTAL_MCP_CLI=true`
  * Benefit: Prevents "context bloat" by not loading all MCP tool schemas upfront. Claude calls tools via bash commands (`mcp-cli call`) only when needed, potentially saving 40k-50k tokens per session.
* **Agentic Browser Tools:** Use of `agent-browser` (Vercel) over standard MCP tools because it uses a **compact accessibility tree** (200-400 tokens) rather than the full DOM (3k-11k tokens).

---

## 3. Key Insights & Differentiators

* **Adversarial Agent Workflows:** The presenter demonstrates a "Researcher vs. Fact-Checker" setup. One agent performs the task; a second agent is blocked until the first finishes, then rigorously audits the output for inaccuracies.
* **Git Worktrees for Parallelism:** Unlike Cursor or Copilot, which often struggle with branch switching, Claude Code can spawn multiple agents in **Isolated Git Worktrees**. This allows 4+ agents to work on separate features in separate directories simultaneously without merge conflicts or state pollution.
* **Context as a Contract:** The system relies on four core markdown/JSON files to "anchor" the AI:
    1. `PRD.md`: Problem statement and scope.
    2. `architecture.md`: Data models, file structure, and API contracts.
    3. `decisions.md`: A log of technical trade-offs made during the session.
    4. `features.json`: A token-efficient, machine-readable build queue with "pass/fail" states.

---

## 4. Technical Constraints & Limitations

* **Token Consumption:** Heavy use of multi-agent swarms and browser tools can consume 150k+ tokens in a single complex session.
* **Hallucination in Research:** Even with sources provided, the model (Sonnet 3.5/Opus 4.6) still hallucinates facts during deep research, necessitating the "Fact-Checker" agent.
* **Looping Issues:** Agents can get stuck "polling" a task list indefinitely. The fix involves a `CLAUDE.md` instruction: *"Do not poll TaskList more than 5 times; if stalling, report status and ask for help."*

---

## 5. Actionable Takeaways: Building the "Bulletproof" System

To implement this framework, configure your environment as follows:

1. **Initialize the Environment:**
    * Enable **Strict Mode** in `tsconfig.json` (or language equivalent) to force Claude to fix types at build-time.
    * Configure `.claude/settings.json` with a **PreToolUse** hook to run a script (e.g., `protect-tests.sh`) that returns **Exit 2** if Claude tries to modify the `tests/` directory.

2. **Define the "Source of Truth":**
    * Before coding, run a prompt to generate the `docs/` folder containing the PRD, Architecture, and User Stories.
    * Generate `features.json` to act as the agent's master checklist.

3. **Execute via Isolated Worktrees:**
    * When building multiple features, instruct Claude: `"Use background agents in separate worktrees for Feature A and Feature B."`

4. **Implement the Verification Loop:**
    * Use the **Context7 MCP** server to provide up-to-date documentation for libraries.
    * Finalize features by asking Claude to: `"Analyze the project and check in production for all possible failure cases our tests might have missed (e.g., race conditions, edge cases)."`

5. **Audit and Refine:**
    * Weekly, run `/insights` and copy the suggested "Custom Skills" directly into your `CLAUDE.md` to prune inefficient behaviors.
