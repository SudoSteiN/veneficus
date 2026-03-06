# LLM Agnostic AI Development Guidelines

Based on the provided transcript, specifically from the "Claude Code" workflow demonstration, here is a technical analysis of the **Task System** and **Multi-Agent Orchestration** approach.

This analysis extracts the **LLM-agnostic methodologies** demonstrated, which you can use to build your guidelines for brainstorming and planning.

## 1. Executive Summary

The video introduces the **Claude Code Task System**, a structured framework for "Agentic Orchestration." It moves beyond simple "to-do lists" by enabling a primary agent to plan, delegate, and manage a team of specialized sub-agents (e.g., Builders and Validators) with strict dependencies.
**Verdict:** **Game-Changer.** It shifts the paradigm from "chatting with code" to designing deterministic, self-validating engineering workflows that can be replicated regardless of the underlying model.

## 2. Core Capabilities & Features (Claude Code Specifics)

The video demonstrates a custom implementation of the Claude Code CLI, heavily utilizing its "Hooks" and "Task" systems.

* **Commands & Terminal Interactions:**
  * **`/plan_w_team`**: A custom slash command that accepts a user prompt and an orchestration prompt to generate a detailed implementation plan.
  * **`/build`**: Triggers the execution of the generated plan using the task system.
  * **`TaskCreate` / `TaskUpdate` / `TaskGet`**: Specialized tools the primary agent uses to manage the state of the workflow and communicate with sub-agents.
* **Agentic Behaviors:**
  * **Parallel Execution:** The system identifies tasks that do not depend on each other (e.g., building 5 different webhooks) and executes them simultaneously.
  * **Blocking Dependencies:** It respects task order (e.g., Task 10 waits for Task 9 to complete).
  * **Hooks System:**
    * **`ValidateNewFile.py`**: Automatically checks if a file exists and has the correct extension *immediately* after generation.
    * **`ValidateFileContains.py`**: Verifies that specific content (like headers or function definitions) exists in the file before marking the task as complete.

## 3. Key Insights & Differentiators (LLM-Agnostic Approaches)

To answer your request for **guidelines on brainstorming and planning**, the video demonstrates three specific methodologies that are model-agnostic:

### A. The Template Meta-Prompt (For Planning)

Instead of asking an LLM to "make a plan," you force it to fill out a strict template. This ensures consistency and prevents "lazy" planning.

* **The Guideline:** Create a "Meta-Prompt" that takes a user request and fills a Markdown template.
* **Required Template Sections:**
  * `## Task Description`: Detailed breakdown.
  * `## Team Orchestration`: Defining *who* does the work (see below).
  * `## Step-by-Step Tasks`: A list of tasks with specific attributes: `id`, `depends_on`, `assigned_tool` (Agent), and `parallel` (true/false).
  * `## Validation Rules`: Explicit criteria for success.

### B. The Builder-Validator Pattern (For Team Structure)

Never rely on a single agent to do the work and check it. The video champions a **2-Agent Team** structure for every task:

* **The Builder Agent:** Has permission to `write` and `edit`. Its sole focus is implementation.
* **The Validator Agent:** Has `read-only` access. Its sole focus is to verify the Builder's work against the acceptance criteria. It reports `PASS/FAIL`.
* **Why it works:** It doubles the compute but exponentially increases trust and reduces hallucinated "fixes."

### C. Specialized Self-Validation (For Quality Control)

Agents cannot be trusted to validate themselves via text. Validation must be programmatic.

* **The Guideline:** Build "Hooks" or scripts that run automatically when an agent finishes a turn.
* **Example:** If an agent creates a Python file, a script immediately runs `python -m py_compile` to check syntax. If it fails, the agent is fed the error log automatically and forced to retry *before* the human ever sees it.

## 4. Technical Constraints & Limitations

* **Complexity Overhead:** This approach requires significant upfront setup (creating the hook scripts, defining the meta-prompts, setting up the environment). It is overkill for simple "fix a bug" requests.
* **Loop Risks:** Without strict "max retry" logic, a Builder/Validator loop could theoretically spin indefinitely if the Validator keeps rejecting the code and the Builder cannot solve it.
* **Context Fragmentation:** Orchestrating multiple agents requires careful management of context. You must decide what information flows from the Primary Agent to the Sub-Agents (e.g., passing specific file paths vs. the whole codebase).

## 5. Actionable Takeaways for Your Guidelines

To implement these approaches in an LLM-agnostic way:

1. **Standardize Planning:** Create a `plan_template.md` file. Your first step in *any* development session should be to have your LLM fill this template based on your requirements.
2. **Define Roles Explicitly:** Do not use a "General Purpose Agent." In your prompts, define a **Builder** (implements code) and a **Validator** (reviews code/runs tests).
3. **Script Your Validation:** Write small shell/Python scripts for common tasks (e.g., `check_syntax.sh`, `lint_file.py`). Instruct your LLM to run these scripts as the final step of any task.
4. **Adopt "Thread-Based" Work:** Treat every feature as a "Thread" composed of a list of tasks. Do not allow the LLM to proceed to Task B until Task A's validation script returns `exit code 0`.
