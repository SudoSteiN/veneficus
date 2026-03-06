# Claude Code Agent Team Explained

This technical analysis focuses on the revolutionary "Agent Teams" feature introduced in **Claude Code** (v2.1.34+) and **Claude 4.6 (Opus)**.

## 1. Executive Summary

The video details the shift from isolated sub-agents to **Agent Teams**, an experimental framework allowing multiple Claude Code instances to collaborate via a shared mailbox and task list.

* **Verdict:** A **game-changer** for complex repo-wide refactors and greenfield development, moving AI coding from "linear assistant" to "autonomous engineering department."

---

## 2. Core Capabilities & Features ("Claude Code" Specifics)

The primary advancement is the move from the old **Sub-Agent** model (siloed, relay-only communication) to **Agent Teams** (peer-to-peer collaboration).

* **Activation Command:**

    ```bash
    export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
    ```

* **Core Architecture:**
  * **Team Lead:** The main session that spawns teammates, coordinates the `Task List`, and synthesizes final output.
  * **Teammates:** Fully independent terminal sessions (each with its own PID) that claim items from the task list.
  * **The Mailbox:** A messaging system enabling direct peer-to-peer collaboration (e.g., a "Reviewer" agent messaging a "Fixer" agent directly).
  * **Local Persistence:** Team configurations and task states are stored locally in:
    * `~/.claude/teams/{team-name}/config.json`
    * `~/.claude/tasks/{team-name}/`
* **Agentic Behaviors:**
  * **Parallelization:** Simultaneously performing research, environment setup, and feature implementation.
  * **Blocking/Unblocking:** Agents can "wait" for a foundation agent to finish installing dependencies before they begin UI work.

---

## 3. Key Insights & Differentiators

* **Direct Communication vs. Relay:** Unlike Cursor or older versions of Claude Code where the "orchestrator" is a mandatory bottleneck, Agent Teams communicate directly. This reduces "relay overhead" and speeds up the feedback loop.
* **The "Magic Moment":** The video demonstrates 4 agents investigating a bug from different angles (logs, code paths, test runner) and converging on a "State Closure" bug in a `useEffect` hook within 3 minutes—a task that typically takes a human or linear AI 10–15 minutes.
* **Context Independence:** Each teammate has its own context window, preventing the "context stuffing" that usually leads to model degradation in large projects.

---

## 4. Technical Constraints & Limitations

* **Token Consumption:** This is the biggest "tax." Because each agent maintains its own context window, parallelized tasks can consume 150k–200k tokens in minutes.
* **Lead Impatience:** The Team Lead may sometimes attempt to "take over" a task if a teammate takes too long, leading to duplicate work and file conflicts.
* **File Write Conflicts:** If two agents attempt to edit the same file (e.g., `page.tsx`) simultaneously, they can overwrite each other's changes.
* **Orchestration Overhead:** Tasks that are too small create more work in "messaging" than in "coding."

---

## 5. Actionable Takeaways for Your Framework

To build the "foolproof" system you requested, apply these insights:

1. **Strict Scope Definition:** Always start with a prompt that defines boundaries (e.g., `/use the agent team to ONLY check /api routes`).
2. **Task Documentation Workflow:** Don't just prompt; create a `tasks/` directory with Markdown files. Claude Code can read these to understand the specific "Definition of Done" for each teammate.
3. **Conflict Avoidance:** Force agents to work on independent files. Use the prompt: *"Assign teammates to separate modules to avoid file write conflicts."*
4. **The "Wait" Directive:** Explicitly tell the Team Lead: *"Wait for the environment agent to finish the `init` before spawning the frontend teammates."*

---

### Proposed "Master Builder" Workflow

Based on the video, here is the framework to build anything from scratch:

**Step 1: The Blueprint (`/init`)**
Create a `DESIGN_SPEC.md` and a `tasks/` folder. Populate the folder with `task1-foundation.md`, `task2-auth.md`, `task3-ui.md`.

**Step 2: Deployment**
See below:

```bash
claude "Use the agent team to build the app based on the tasks folder. Spawn a Researcher to verify UI patterns, a Foundation agent for setup, and 2 Coders for features."
```

**Step 3: Monitoring & Intervention**
Use the terminal to watch the "Mailbox" logs. If an agent goes off-track, use the **Teammate Intervention** capability:
`@code-fixer: ignore the low-priority linting issues, focus on the SQL injection risk.`

**Step 4: Synthesis**
Let the **Team Lead** verify the build and shut down the teammates gracefully to save on the final token count.
