#!/usr/bin/env python3
"""C-Thread (Chained) — Sequential steps with human checkpoints.

Reads a YAML steps file, executes each step sequentially. At steps marked
with `checkpoint: true`, pauses and sends a macOS notification, waiting
for human approval before continuing.

Usage:
    uv run c_thread.py steps.yaml

Steps file format (YAML):
    steps:
      - name: "Create database schema"
        prompt: "Create the migration file for the users table"
        checkpoint: false
      - name: "Run migration"
        prompt: "Run the migration: python manage.py migrate"
        checkpoint: true   # Pauses for human approval
      - name: "Update API endpoints"
        prompt: "Add CRUD endpoints for users"
        checkpoint: false
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from emit import emit

# Try to import yaml; fall back to simple parser if not available
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_steps_file(path: str) -> list[dict]:
    """Parse steps file (YAML or JSON)."""
    content = Path(path).read_text()

    if path.endswith(".json"):
        data = json.loads(content)
        return data.get("steps", data)

    if HAS_YAML:
        data = yaml.safe_load(content)
        return data.get("steps", data)

    # Fallback: simple YAML-like parser for basic structure
    print("Warning: PyYAML not installed. Install with: uv pip install pyyaml")
    print("Attempting basic parsing...")

    steps = []
    current: dict = {}

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("- name:"):
            if current:
                steps.append(current)
            current = {"name": line.split(":", 1)[1].strip().strip('"')}
        elif line.startswith("prompt:"):
            current["prompt"] = line.split(":", 1)[1].strip().strip('"')
        elif line.startswith("checkpoint:"):
            current["checkpoint"] = "true" in line.lower()

    if current:
        steps.append(current)

    return steps


def notify_macos(title: str, message: str) -> None:
    """Send macOS notification via osascript."""
    try:
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}" sound name "Glass"'
        ], capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def wait_for_approval(step_name: str) -> bool:
    """Wait for human approval at a checkpoint."""
    print(f"\n{'='*60}")
    print(f"  CHECKPOINT: {step_name}")
    print(f"{'='*60}")
    print(f"\n  Review the results above, then:")
    print(f"  [Enter] to continue  |  [s] to skip  |  [q] to quit\n")

    notify_macos("Veneficus Checkpoint", f"Approval needed: {step_name}")

    response = input("  > ").strip().lower()

    if response == "q":
        print("[C-Thread] Aborted by user.")
        sys.exit(0)
    if response == "s":
        print(f"[C-Thread] Skipping: {step_name}")
        return False

    return True


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: c_thread.py <steps-file.yaml>")
        sys.exit(1)

    steps_file = sys.argv[1]
    if not Path(steps_file).exists():
        print(f"Error: Steps file not found: {steps_file}", file=sys.stderr)
        sys.exit(1)

    steps = parse_steps_file(steps_file)
    total = len(steps)

    emit("ThreadStart", thread_type="C-Thread",
         steps_file=steps_file, total_steps=total,
         step_names=[s.get("name", f"Step {i}") for i, s in enumerate(steps, 1)])

    print(f"[C-Thread] Loaded {total} steps from {steps_file}")
    for i, step in enumerate(steps, 1):
        checkpoint = "checkpoint" if step.get("checkpoint") else ""
        print(f"  {i}. {step['name']} {checkpoint}")

    print(f"\n[C-Thread] Starting execution...\n")

    for i, step in enumerate(steps, 1):
        name = step.get("name", f"Step {i}")
        prompt = step.get("prompt", "")
        is_checkpoint = step.get("checkpoint", False)

        print(f"\n[C-Thread] Step {i}/{total}: {name}")
        print(f"[C-Thread] Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")

        # Execute step via Claude
        result = subprocess.run(
            ["claude", "--dangerously-skip-permissions", "-p", prompt],
            capture_output=False,
        )

        if result.returncode != 0:
            print(f"\n[C-Thread] Step {i} failed with exit code {result.returncode}")
            if not wait_for_approval(f"Step {i} failed — continue anyway?"):
                continue

        # Checkpoint: wait for human approval
        if is_checkpoint:
            approved = wait_for_approval(name)
            if not approved:
                continue

        emit("ThreadStepComplete", thread_type="C-Thread",
             step=i, total=total, step_name=name)
        print(f"[C-Thread] Step {i}/{total} complete ✓")

    emit("ThreadComplete", thread_type="C-Thread",
         steps_file=steps_file, total_steps=total)
    print(f"\n[C-Thread] All {total} steps complete.")


if __name__ == "__main__":
    main()
