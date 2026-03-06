#!/usr/bin/env python3
"""F-Thread (Fusion) — Best-of-N prototyping.

DEPRECATED: Fusion threads run 3x the cost for marginal quality improvement.
In practice, iterating on one approach is faster than comparing three.
Consider using P-Thread for genuinely independent work, or iterate with
the build command instead.

Spawns 3 agents with different approach constraints, each in its own worktree.
After all complete, a researcher agent compares outputs and recommends the best.

Usage:
    uv run f_thread.py "Design the authentication system"
"""

import os
import subprocess
import sys
import time
from pathlib import Path

from emit import emit


APPROACHES = [
    {
        "name": "layered",
        "constraint": (
            "Use a layered architecture approach. Organize code into clear layers: "
            "presentation, business logic, data access. Prioritize separation of concerns."
        ),
    },
    {
        "name": "vertical-slice",
        "constraint": (
            "Use a vertical slice architecture. Organize code by feature, not layer. "
            "Each feature contains its own routes, logic, and data access. Prioritize cohesion."
        ),
    },
    {
        "name": "minimal",
        "constraint": (
            "Use the simplest possible approach. Minimize abstraction and files. "
            "Inline code where possible. Prioritize readability and fewer moving parts."
        ),
    },
]


def find_project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".veneficus").is_dir():
            return p
        p = p.parent
    print("Error: Not in a Veneficus project", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: f_thread.py "prompt describing what to build"')
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    root = find_project_root()
    session_name = f"veneficus-fusion-{int(time.time())}"

    print(f"[F-Thread] WARNING: F-Thread is deprecated. Consider 'just build' for iterative work instead.")
    print(f"[F-Thread] Fusion prototyping: {prompt}")
    print(f"[F-Thread] Launching 3 approaches (3x cost)...")

    emit("ThreadStart", thread_type="F-Thread", session=session_name,
         prompt=prompt, approaches=[a["name"] for a in APPROACHES])

    # Create tmux session
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session_name, "-x", "200", "-y", "50"],
        check=True,
    )

    worktrees: list[tuple[str, Path]] = []
    worktree_script = root / ".veneficus" / "skills" / "git-worktree.sh"

    for i, approach in enumerate(APPROACHES):
        branch = f"veneficus/fusion-{approach['name']}"

        # Create worktree
        result = subprocess.run(
            ["bash", str(worktree_script), "create", branch],
            capture_output=True, text=True, cwd=str(root),
        )
        if result.returncode != 0:
            print(f"Warning: Could not create worktree for {approach['name']}: {result.stderr}")
            continue

        wt_path = Path(result.stdout.strip())
        worktrees.append((approach["name"], wt_path))

        # Create tmux pane
        if i > 0:
            subprocess.run(["tmux", "split-window", "-t", session_name, "-h"], check=True)
            subprocess.run(["tmux", "select-layout", "-t", session_name, "tiled"], check=True)

        # Launch agent with approach constraint
        agent_prompt = (
            f"You are prototyping an approach for: {prompt}\n\n"
            f"YOUR APPROACH CONSTRAINT: {approach['constraint']}\n\n"
            f"Read .veneficus/agents/builder.md for build instructions. "
            f"Implement the solution following your constraint. "
            f"When done, commit with message: 'fusion({approach['name']}): {prompt[:50]}'"
        )

        cmd = (
            f"cd {wt_path} && "
            f"claude --dangerously-skip-permissions -p \"{agent_prompt}\""
        )

        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, cmd, "Enter"],
            check=True,
        )

        print(f"  [{approach['name']}] → {wt_path}")

    emit("ThreadAgentsLaunched", thread_type="F-Thread", session=session_name,
         approaches=[name for name, _ in worktrees], count=len(worktrees))

    print(f"\n[F-Thread] {len(worktrees)} agents launched.")
    print(f"[F-Thread] Watch: tmux attach -t {session_name}")
    print(f"\n[F-Thread] After all complete, compare with:")
    print(f"  1. Review each worktree's implementation")
    print(f"  2. Use researcher agent to compare:")
    print(f"     just team researcher \"Compare the 3 fusion approaches and recommend the best\"")
    print(f"  3. Merge the winning branch")
    print(f"  4. Clean up: just clean")


if __name__ == "__main__":
    main()
