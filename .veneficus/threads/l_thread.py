#!/usr/bin/env python3
"""L-Thread (Loop) — Iterate until a test command passes.

Spawns a debugger agent that loops: run test → if fail, diagnose and fix → repeat.
Stops when the test passes or max retries reached.

Features:
- Stagnation detection: detects spinning (identical outputs), oscillation (A→B→A→B),
  and diminishing returns (output barely changing)
- Lateral thinking: rotates through alternative personas (simplifier, contrarian)
  when stagnation is detected, to break out of unproductive loops

Usage:
    uv run l_thread.py "pytest test_auth.py"
    uv run l_thread.py "npm test -- --testPathPattern=auth" --max-retries 15
"""

import argparse
import hashlib
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from emit import emit


def find_project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".veneficus").is_dir():
            return p
        p = p.parent
    return Path.cwd()


def run_test(cmd: str, cwd: str) -> tuple[bool, str]:
    """Run the test command. Returns (passed, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True,
            capture_output=True, text=True,
            timeout=120, cwd=cwd,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Test timed out after 120s"


def _hash_output(output: str) -> str:
    """Hash test output for comparison."""
    return hashlib.sha256(output.encode()).hexdigest()[:16]


def detect_stagnation(output_hashes: list[str]) -> str | None:
    """Detect stagnation patterns in recent outputs.

    Returns a stagnation type string or None:
    - "spinning": last 3+ outputs are identical
    - "oscillation": alternating between two states (A→B→A→B)
    - None: no stagnation detected
    """
    if len(output_hashes) < 3:
        return None

    recent = output_hashes[-3:]

    # Spinning: last 3 outputs are identical
    if len(set(recent)) == 1:
        return "spinning"

    # Oscillation: A→B→A or B→A→B pattern in last 4+
    if len(output_hashes) >= 4:
        last4 = output_hashes[-4:]
        if last4[0] == last4[2] and last4[1] == last4[3] and last4[0] != last4[1]:
            return "oscillation"

    return None


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


# Persona rotation order when stagnation is detected
LATERAL_PERSONAS = [
    ("simplifier", ".veneficus/agents/simplifier.md"),
    ("contrarian", ".veneficus/agents/contrarian.md"),
    ("debugger", ".veneficus/agents/debugger.md"),  # back to default with fresh eyes
]


def build_prompt(
    test_cmd: str,
    output: str,
    iteration: int,
    max_retries: int,
    stagnation: str | None,
    persona_index: int,
) -> str:
    """Build the agent prompt, adapting based on stagnation state."""
    persona_name, persona_file = LATERAL_PERSONAS[persona_index % len(LATERAL_PERSONAS)]

    parts = [f"Read {persona_file} for your instructions.\n"]

    # Add stagnation context if detected
    if stagnation == "spinning":
        parts.append(
            "⚠️ STAGNATION DETECTED: Your last 3 attempts produced identical test output. "
            "The current approach is NOT working. You MUST try a fundamentally different strategy.\n"
            "Consider: different root cause, different fix location, different algorithmic approach.\n"
        )
    elif stagnation == "oscillation":
        parts.append(
            "⚠️ OSCILLATION DETECTED: The test output is alternating between two states. "
            "Your fixes are undoing each other or toggling between two failure modes.\n"
            "Step back: read BOTH failure outputs, identify what they have in common, "
            "and find a fix that resolves BOTH states simultaneously.\n"
        )

    if persona_name == "simplifier" and stagnation:
        parts.append(
            "You are approaching this as a SIMPLIFIER. Ask: what is the simplest thing "
            "that could possibly work? Strip away complexity. Consider rewriting the "
            "problematic code from scratch rather than patching it.\n"
        )
    elif persona_name == "contrarian" and stagnation:
        parts.append(
            "You are approaching this as a CONTRARIAN. Challenge every assumption. "
            "What if the test expectation is wrong? What if the bug is in a dependency? "
            "What if the approach itself is flawed? Question everything.\n"
        )

    parts.append(
        f"A test is failing. Fix it.\n\n"
        f"Test command: {test_cmd}\n\n"
        f"Current failure output (last 500 chars):\n"
        f"```\n{output[-500:]}\n```\n\n"
        f"This is iteration {iteration} of {max_retries}. "
        f"Diagnose the root cause and fix it. "
        f"Do NOT just retry — actually fix the code. "
        f"When done, the test should pass."
    )

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="L-Thread: loop until test passes")
    parser.add_argument("test_cmd", help="Test command to run")
    parser.add_argument("--max-retries", type=int, default=10, help="Maximum iterations")
    args = parser.parse_args()

    root = find_project_root()
    test_cmd = args.test_cmd
    max_retries = args.max_retries

    print(f"[L-Thread] Loop until passes: {test_cmd}")
    print(f"[L-Thread] Max retries: {max_retries}")

    emit("ThreadStart", thread_type="L-Thread",
         test_cmd=test_cmd, max_retries=max_retries)

    # Initial test run
    passed, output = run_test(test_cmd, str(root))

    if passed:
        print(f"\n[L-Thread] Test already passes! Nothing to do.")
        sys.exit(0)

    print(f"\n[L-Thread] Initial failure:\n{output[-500:]}")

    output_hashes: list[str] = [_hash_output(output)]
    persona_index = 2  # Start with debugger (default)
    stagnation_count = 0

    for iteration in range(1, max_retries + 1):
        print(f"\n[L-Thread] Iteration {iteration}/{max_retries}")

        # Detect stagnation from output history
        stagnation = detect_stagnation(output_hashes)

        if stagnation:
            stagnation_count += 1
            # Rotate persona on each stagnation detection
            persona_index = stagnation_count - 1
            persona_name = LATERAL_PERSONAS[persona_index % len(LATERAL_PERSONAS)][0]
            print(f"[L-Thread] ⚠ Stagnation detected: {stagnation}")
            print(f"[L-Thread] Rotating to '{persona_name}' persona")
            emit("StagnationDetected", thread_type="L-Thread",
                 pattern=stagnation, iteration=iteration, persona=persona_name)
        else:
            # Reset to debugger when not stagnating
            stagnation_count = 0
            persona_index = 2  # debugger

        prompt = build_prompt(
            test_cmd, output, iteration, max_retries,
            stagnation, persona_index,
        )

        # Parse environment for the current persona
        current_persona_file = LATERAL_PERSONAS[persona_index % len(LATERAL_PERSONAS)][1]
        agent_env = parse_agent_env(root / current_persona_file)
        # Merge agent env with current process env
        run_env = os.environ.copy()
        run_env.update(agent_env)

        # Run Claude to fix
        print(f"[L-Thread] Launching agent...")
        fix_result = subprocess.run(
            ["claude", "--dangerously-skip-permissions", "-p", prompt],
            capture_output=False,
            cwd=str(root),
            env=run_env,
        )

        # Re-run the test
        print(f"[L-Thread] Re-running test...")
        passed, output = run_test(test_cmd, str(root))
        output_hashes.append(_hash_output(output))

        if passed:
            emit("ThreadComplete", thread_type="L-Thread",
                 test_cmd=test_cmd, iterations=iteration, result="pass",
                 stagnation_events=stagnation_count)
            print(f"\n[L-Thread] ✓ Test passes after {iteration} iteration(s)!")
            if stagnation_count > 0:
                print(f"[L-Thread] (Recovered from {stagnation_count} stagnation event(s))")
            sys.exit(0)

        emit("ThreadIteration", thread_type="L-Thread",
             test_cmd=test_cmd, iteration=iteration, max_retries=max_retries,
             result="fail")
        print(f"[L-Thread] Still failing after iteration {iteration}")
        print(f"[L-Thread] Output: {output[-200:]}")

    emit("ThreadComplete", thread_type="L-Thread",
         test_cmd=test_cmd, iterations=max_retries, result="fail",
         stagnation_events=stagnation_count)
    print(f"\n[L-Thread] ✗ Max retries ({max_retries}) reached. Test still failing.")
    print(f"[L-Thread] Last output:\n{output[-500:]}")
    if stagnation_count > 0:
        print(f"[L-Thread] Stagnation was detected {stagnation_count} time(s) during this run.")
    print(f"\n[L-Thread] Consider:")
    print(f"  - Reviewing the test itself — is it correct?")
    print(f"  - Manual investigation: just debug \"{test_cmd}\"")
    print(f"  - Trying a different approach: just fusion \"fix {test_cmd}\"")
    sys.exit(1)


if __name__ == "__main__":
    main()
