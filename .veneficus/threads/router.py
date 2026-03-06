#!/usr/bin/env python3
"""Thread type router — classify work into P/F/C/L thread types.

Interactive decision support to help choose the right orchestration pattern.

Usage:
    uv run router.py                    # Interactive mode
    uv run router.py --auto "description"  # Auto-classify based on heuristics
"""

import argparse
import sys


THREAD_TYPES = {
    "P": {
        "name": "Parallel (P-Thread)",
        "description": "Independent pieces of work that can run simultaneously in separate worktrees",
        "signals": ["multiple independent features", "no shared state", "parallelizable"],
        "example": "Build 3 unrelated API endpoints at the same time",
    },
    "F": {
        "name": "Fusion (F-Thread)",
        "description": "Best-of-N prototyping — multiple approaches to the same problem, pick the best",
        "signals": ["uncertain approach", "design exploration", "multiple valid solutions"],
        "example": "Design the auth system — try JWT, session, and OAuth approaches",
    },
    "C": {
        "name": "Chained (C-Thread)",
        "description": "Sequential steps with human checkpoints at risky transitions",
        "signals": ["risky operations", "database migrations", "deployment", "irreversible steps"],
        "example": "Database schema migration → data migration → API update → deploy",
    },
    "L": {
        "name": "Loop (L-Thread)",
        "description": "Iterate until a programmatic condition is met (test passes, lint clean, etc.)",
        "signals": ["single test to satisfy", "fix until green", "iterative refinement"],
        "example": "Fix auth module until `pytest test_auth.py` passes",
    },
}


def interactive_classify() -> str:
    """Walk user through classification questions."""
    print("\n=== Veneficus Thread Router ===\n")
    print("Answer these questions to determine the best thread type:\n")

    # Question 1: Independence
    print("1. Can the work be split into independent pieces with no shared state?")
    print("   (a) Yes — multiple features/tasks that don't depend on each other")
    print("   (b) No — the work is a single coherent task")
    q1 = input("   > ").strip().lower()

    if q1 == "a":
        print("\n→ Recommendation: P-Thread (Parallel)")
        print(f"   {THREAD_TYPES['P']['description']}")
        print(f"   Example: {THREAD_TYPES['P']['example']}")
        return "P"

    # Question 2: Uncertainty
    print("\n2. Are you uncertain about the best approach?")
    print("   (a) Yes — I want to try multiple approaches and compare")
    print("   (b) No — I know what to build, just need to execute")
    q2 = input("   > ").strip().lower()

    if q2 == "a":
        print("\n→ Recommendation: F-Thread (Fusion)")
        print(f"   {THREAD_TYPES['F']['description']}")
        print(f"   Example: {THREAD_TYPES['F']['example']}")
        return "F"

    # Question 3: Risk
    print("\n3. Does the work involve risky or irreversible steps?")
    print("   (a) Yes — I need human approval at key milestones")
    print("   (b) No — it's safe to run autonomously")
    q3 = input("   > ").strip().lower()

    if q3 == "a":
        print("\n→ Recommendation: C-Thread (Chained)")
        print(f"   {THREAD_TYPES['C']['description']}")
        print(f"   Example: {THREAD_TYPES['C']['example']}")
        return "C"

    # Default: L-Thread
    print("\n4. Can success be defined by a single test/command passing?")
    print("   (a) Yes — there's a specific test or condition that defines 'done'")
    print("   (b) No — it's more open-ended")
    q4 = input("   > ").strip().lower()

    if q4 == "a":
        print("\n→ Recommendation: L-Thread (Loop)")
        print(f"   {THREAD_TYPES['L']['description']}")
        print(f"   Example: {THREAD_TYPES['L']['example']}")
        return "L"

    # Fallback
    print("\n→ Recommendation: Simple serial execution (no special thread type needed)")
    print("   Use: just build <feature>")
    return "serial"


def auto_classify(description: str) -> str:
    """Heuristic auto-classification based on description keywords."""
    desc = description.lower()

    # P-Thread signals
    parallel_words = ["parallel", "independent", "simultaneously", "multiple features", "and also"]
    if any(w in desc for w in parallel_words):
        return "P"

    # F-Thread signals
    fusion_words = ["explore", "compare", "best approach", "prototype", "alternatives", "design"]
    if any(w in desc for w in fusion_words):
        return "F"

    # C-Thread signals
    chain_words = ["migrate", "deploy", "risky", "careful", "checkpoint", "step by step", "approval"]
    if any(w in desc for w in chain_words):
        return "C"

    # L-Thread signals
    loop_words = ["fix", "until", "passes", "green", "loop", "retry", "test"]
    if any(w in desc for w in loop_words):
        return "L"

    return "serial"


def main() -> None:
    parser = argparse.ArgumentParser(description="Thread type router")
    parser.add_argument("--auto", type=str, help="Auto-classify from description")
    args = parser.parse_args()

    if args.auto:
        thread_type = auto_classify(args.auto)
        info = THREAD_TYPES.get(thread_type, {})
        print(f"Thread type: {thread_type}")
        if info:
            print(f"Name: {info['name']}")
            print(f"Description: {info['description']}")
    else:
        thread_type = interactive_classify()

    print(f"\nSelected: {thread_type}")


if __name__ == "__main__":
    main()
