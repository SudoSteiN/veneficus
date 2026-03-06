# Agent Hooks The Game Changer

## Part 1: Technical Analysis of Video

### 1. Executive Summary

This video introduces a pivotal feature in the Claude Code ecosystem: **Agent Hooks**. It demonstrates how to transition from "vibe coding" (relying on probability) to rigorous engineering by building **Specialized Self-Validating Agents** that automatically run deterministic validation scripts after tool use, creating a closed-loop system where agents catch and fix their own errors before asking for human review.
**Verdict:** **Game-Changer.** This moves AI coding from a drafting tool to a reliable autonomous system by enforcing correct outputs through code execution rather than just text generation.

### 2. Core Capabilities & Features ("Claude Code" Specifics)

* **Custom Slash Commands & Agents:**
  * Define custom commands via Markdown files (e.g., `csv-edit.md`) containing YAML frontmatter and prompt instructions.
  * Commands operate via terminal: `/csv-edit`, `/review-finances`.
* **The "Hooks" System (The Core Feature):**
  * **`PreToolUse`**: Execute a command before the agent uses a specific tool.
  * **`PostToolUse`**: Execute a command immediately after a tool (like `Edit` or `Write`) is used.
  * **`Stop`**: Execute a command when the agent finishes its lifecycle.
* **Integration with External Scripts:**
  * Demonstrates using `uv run` (Python package manager) to trigger external validation scripts (`validator.py`) inside the hook.
  * **File System Access:** Agents can read/write files, and the hooks validate those specific file paths.
* **Parallelism:**
  * Demonstrates running multiple sub-agents in parallel (e.g., 4 agents editing 4 different CSV files simultaneously), each triggering its own validation hook.

### 3. Key Insights & Differentiators

* **Deterministic Validation vs. Textual Review:**
  * *Others (Cursor/Copilot):* Often ask the model, "Does this look right?" (Probabilistic).
  * *Claude Code (This Workflow):* Runs a Python script (e.g., using Pandas) to check if a CSV is valid. If the script throws an error, the error text is fed back to the agent.
* **The "Magic Moment":**
  * The presenter intentionally broke a CSV file (removed a closing quote).
  * The Agent ran the `Edit` tool.
  * The **PostToolUse Hook** triggered the validator.
  * The validator failed and returned a parsing error.
  * **The Agent read the error and fixed the syntax immediately** without user intervention.
* **Agent Specialization:**
  * Advocates for breaking monolithic tasks into micro-agents (e.g., one agent to normalize data, one to categorize, one to graph), each with its own specific validator.

### 4. Technical Constraints & Limitations

* **Setup Overhead:** This is not "zero-shot." You must write the validation logic (Python/Bash scripts) yourself. If your validator is buggy, the agent will loop or fail.
* **Latency & Compute:** The demo finance workflow took ~8 minutes. Running a validation script after *every* edit increases token usage and time-to-completion significantly.
* **Context Window Management:** While sub-agents help isolate context, passing massive error logs back to the agent could saturate the context window if not managed (truncated) properly.

### 5. Actionable Takeaways

* **Adopt "Agentic TDD":** Write your validation script (the test) *before* you prompt the agent.
* **Structure Your Project:** Create a `.claude/hooks/validators` directory to store reusable verification scripts.
* **Use `PostToolUse`:** This is the highest-leverage hook. Attach it to `Edit` and `Write` tools to ensure no file is saved without passing a syntax/logic check.
* **Parallelize:** Use sub-agents for repetitive tasks (like processing 10 different files) to speed up the workflow, relying on hooks to ensure each parallel worker is accurate.

---

## Part 2: The "Self-Validating" Claude Code Framework

Based on the engineering principles extracted from the video, here is a framework to build a robust, self-correcting development system.

### Phase 1: Directory Structure Setup

You must organize your project to support specialized agents. Do not dump everything in one file.

```bash
.claude/
├── commands/           # Entry points (e.g., /build-feature)
├── agents/             # Specialized personas (e.g., backend-agent.md)
├── skills/             # Reusable logic
└── hooks/
    └── validators/     # The "Truth" layer (Python/Bash scripts)
        ├── syntax-check.py
        ├── test-runner.py
        └── api-health-check.py
```

### Phase 2: The Validator Template (The "Truth")

Do not rely on Claude to check Claude. Use deterministic code.
*Create `validator_template.py` for any task.*

```python
# .claude/hooks/validators/generic_validator.py
import sys
import subprocess
import json

def validate_work(file_path):
    issues = []
    
    # 1. SYNTAX CHECK (Example for Python)
    if file_path.endswith(".py"):
        result = subprocess.run(["uv", "run", "ruff", "check", file_path], capture_output=True, text=True)
        if result.returncode != 0:
            issues.append(f"[LINT ERROR]: {result.stdout}")

    # 2. LOGIC CHECK (Custom business logic)
    # Check if specific functions exist or tests pass
    
    return issues

if __name__ == "__main__":
    # Input comes from the hook arguments
    target_file = sys.argv[1] 
    errors = validate_work(target_file)
    
    if errors:
        # RETURN ERROR TO CLAUDE
        # This text is what the Agent sees immediately after editing
        print(json.dumps({
            "status": "failed",
            "instruction": "The file edits caused validation errors. Fix these immediately.",
            "errors": errors
        }))
        sys.exit(1) # Signal failure
    else:
        print("Validation Passed.")
        sys.exit(0)
```

### Phase 3: The Agent Template (The "Worker")

This YAML configuration enforces the loop. It binds the agent to the validator.

```markdown
<!-- .claude/agents/feature-builder.md -->
---
name: feature-builder
description: An agent that builds features and validates them immediately.
model: claude-3-5-sonnet-20241022
tools: [Edit, Read, Write, Bash]

# THE CRITICAL COMPONENT
hooks:
  PostToolUse:
    - matcher: "Edit|Write" # Trigger after any file modification
      type: command
      # Runs the validator on the file that was just edited
      command: "uv run .claude/hooks/validators/generic_validator.py $TOOL_INPUT_PATH" 
---

## Purpose
You are a perfectionist software engineer. 

## Workflow
1. Analyze the request.
2. Edit the code.
3. **AUTOMATIC VALIDATION WILL RUN.**
4. If you see validation errors in the output, **YOU MUST FIX THEM** in the next turn.
5. Do not report completion until validation passes silently.
```

### Phase 4: The Execution Pipeline (The "Workflow")

**Step 1: Define the "Done" State (The Validator)**
Before asking Claude to "add a feature," write a small script that proves the feature works.

* *Example:* If adding a button, write a test that checks if the button renders.
* *Action:* Save this to `.claude/hooks/validators/task_specific.py`.

**Step 2: Initialize the Agent**
Use the slash command associated with your specialized agent.

* *Terminal:* `/feature-builder "Add a login button to navbar.tsx"`

**Step 3: The Loop Autonomous**
Simple loop list:

1. **Agent:** Writes code to `navbar.tsx`.
2. **System:** Triggers `PostToolUse`.
3. **Validator:** Runs `task_specific.py`.
    * *Scenario A (Success):* Validator exits with 0. Agent proceeds.
    * *Scenario B (Failure):* Validator prints "Error: Button not found." Agent receives this, reasons: "I missed the export," and edits the file again.

**Step 4: Final Human Verification**
You only review the code once the agent is no longer triggering validation errors.

#### Phase 5: Troubleshooting & Optimization

* **Loops of Death:** If the agent fails validation 3 times in a row on the same error, interrupt (`Ctrl+C`). Your prompt instructions likely need to be clearer, or your validator is too strict.
* **Token Costs:** Validation outputs consume context. Ensure your python validators output concise errors, not 500 lines of stack trace. Truncate logs in your validator script before printing to stdout.
* **Environment:** Ensure `uv` or your environment manager is configured in the `.claude/settings.json` permissions so the agent can execute commands without asking for permission every time.

```json
// .claude/settings.json
{
  "permissions": {
    "allow": ["uv run *", "python *"]
  }
}
```
