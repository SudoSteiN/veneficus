#!/usr/bin/env python3
"""P-Thread (Parallel) — Spawn independent agents in separate git worktrees.

Takes N feature names, creates a worktree + tmux pane for each,
launches a Claude agent per worktree, and waits for all to complete.

Usage:
    uv run p_thread.py feat-auth feat-payments feat-notifications
"""

import os
import re
import subprocess
import sys
import time
from pathlib import Path

from emit import emit


def find_project_root() -> Path:
    """Walk up to find .veneficus/ directory."""
    p = Path.cwd()
    while p != p.parent:
        if (p / ".veneficus").is_dir():
            return p
        p = p.parent
    print("Error: Not in a Veneficus project", file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run a command with output."""
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def parse_agent_env(persona_file: Path) -> dict[str, str]:
    """Read a persona file and extract environment variables from its ## Environment block."""
    if not persona_file.exists():
        return {}

    content = persona_file.read_text()
    match = re.search(r'## Environment\s*```yaml\s*\n(.*?)```', content, re.DOTALL)
    if not match:
        return {}

    env_vars: dict[str, str] = {}
    for line in match.group(1).strip().splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()

        if key == 'protect_tests':
            env_vars['VENEFICUS_PROTECT_TESTS'] = '1' if value.lower() == 'true' else '0'
        elif key == 'tdd_enforce':
            env_vars['VENEFICUS_TDD_ENFORCE'] = '1' if value.lower() == 'true' else '0'
        elif key == 'read_only':
            if value.lower() == 'true':
                env_vars['VENEFICUS_READ_ONLY'] = '1'
        elif key == 'scope_deny':
            items = value.strip('[]').split(',')
            items = [i.strip().strip('"').strip("'") for i in items if i.strip()]
            if items:
                env_vars['VENEFICUS_SCOPE_DENY'] = ','.join(items)

    return env_vars


def create_worktree(root: Path, branch: str) -> Path:
    """Create a git worktree for the branch."""
    worktree_script = root / ".veneficus" / "skills" / "git-worktree.sh"
    result = run(["bash", str(worktree_script), "create", branch], cwd=str(root))
    if result.returncode != 0:
        print(f"Error creating worktree for {branch}: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return Path(result.stdout.strip())


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: p_thread.py <feature-1> <feature-2> [feature-N...]")
        sys.exit(1)

    features = sys.argv[1:]
    root = find_project_root()
    session_name = f"veneficus-parallel-{int(time.time())}"

    print(f"[P-Thread] Starting parallel work on {len(features)} features")
    print(f"[P-Thread] tmux session: {session_name}")

    emit("ThreadStart", thread_type="P-Thread", session=session_name,
         features=features, count=len(features))

    # Parse builder agent environment
    builder_persona = root / ".veneficus" / "agents" / "builder.md"
    agent_env = parse_agent_env(builder_persona)
    env_exports = " ".join(f'export {k}="{v}" &&' for k, v in agent_env.items())

    # Create tmux session
    subprocess.run(
        ["tmux", "new-session", "-d", "-s", session_name, "-x", "200", "-y", "50"],
        check=True,
    )

    worktrees: list[tuple[str, Path]] = []

    for i, feature in enumerate(features):
        branch = f"veneficus/{feature}"
        print(f"[P-Thread] Creating worktree for {feature}...")
        wt_path = create_worktree(root, branch)
        worktrees.append((feature, wt_path))

        # Create tmux pane (first feature uses the initial pane)
        if i > 0:
            subprocess.run(
                ["tmux", "split-window", "-t", session_name, "-h"],
                check=True,
            )
            subprocess.run(
                ["tmux", "select-layout", "-t", session_name, "tiled"],
                check=True,
            )

        # Launch Claude agent in the pane
        safe_feature = feature.replace("'", "'\\''")
        agent_prompt = (
            f"You are working on feature '{safe_feature}' in a git worktree. "
            f"Read .veneficus/agents/builder.md for your instructions. "
            f"Read .veneficus/docs/features.json and find feature '{safe_feature}'. "
            f"Follow the TDD build protocol. When done, commit your changes."
        )

        cmd = (
            f"cd '{wt_path}' && "
            f"{env_exports} "
            f"claude --dangerously-skip-permissions -p \"{agent_prompt}\""
        )

        subprocess.run(
            ["tmux", "send-keys", "-t", session_name, cmd, "Enter"],
            check=True,
        )

    emit("ThreadAgentsLaunched", thread_type="P-Thread", session=session_name,
         features=features, count=len(features))

    print(f"\n[P-Thread] All {len(features)} agents launched.")
    print(f"[P-Thread] Attach to watch: tmux attach -t {session_name}")
    print(f"\n[P-Thread] Worktrees:")
    for feature, wt_path in worktrees:
        print(f"  {feature}: {wt_path}")

    print(f"\n[P-Thread] When all agents complete:")
    print(f"  1. Review each worktree's changes")
    print(f"  2. Merge branches: git merge veneficus/<feature>")
    print(f"  3. Clean up: just clean")


if __name__ == "__main__":
    main()
