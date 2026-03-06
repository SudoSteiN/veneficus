#!/usr/bin/env python3
"""Scope guard — prevents agents from editing files outside their assigned scope.

Reads hook JSON from stdin. Checks tool_input.file_path against allowed patterns.
When no scope is configured, allows all edits (open mode).
Exit 0 = allowed, Exit 2 = blocked.

Configuration via environment variables:
  VENEFICUS_SCOPE_ALLOW         — comma-separated glob patterns of allowed paths
  VENEFICUS_SCOPE_DENY          — comma-separated glob patterns of denied paths
  VENEFICUS_PROTECT_TESTS=1     — block edits to test files (critical for TDD)
"""

import fnmatch
import json
import os
import sys


def main() -> None:
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = hook_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Test protection — block edits to test files when enabled (TDD integrity)
    protect_tests = os.environ.get("VENEFICUS_PROTECT_TESTS", "1")
    if protect_tests == "1":
        # Normalize path for matching
        cwd = hook_data.get("cwd", os.getcwd())
        rel = file_path[len(cwd):].lstrip("/") if file_path.startswith(cwd) else file_path

        test_patterns = [
            "tests/*", "test/*", "test_*", "*_test.*",
            "*.test.*", "*.spec.*", "__tests__/*",
            "*/tests/*", "*/test/*", "*/__tests__/*",
        ]
        for pattern in test_patterns:
            if fnmatch.fnmatch(rel, pattern):
                print(
                    f"TEST PROTECTION: Edit to '{rel}' blocked — test files are read-only "
                    f"when VENEFICUS_PROTECT_TESTS=1. Disable with: unset VENEFICUS_PROTECT_TESTS",
                    file=sys.stderr,
                )
                sys.exit(2)

    # Get scope config from environment
    allow_raw = os.environ.get("VENEFICUS_SCOPE_ALLOW", "")
    deny_raw = os.environ.get("VENEFICUS_SCOPE_DENY", "")

    allow_patterns = [p.strip() for p in allow_raw.split(",") if p.strip()]
    deny_patterns = [p.strip() for p in deny_raw.split(",") if p.strip()]

    # If no scope configured, allow everything (open mode)
    if not allow_patterns and not deny_patterns:
        sys.exit(0)

    # Normalize path
    cwd = hook_data.get("cwd", os.getcwd())
    if file_path.startswith(cwd):
        rel_path = file_path[len(cwd):].lstrip("/")
    else:
        rel_path = file_path

    # Check deny patterns first
    for pattern in deny_patterns:
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(file_path, pattern):
            print(
                f"SCOPE VIOLATION: Edit to '{rel_path}' blocked by deny pattern '{pattern}'",
                file=sys.stderr
            )
            sys.exit(2)

    # Check allow patterns (if specified, file must match at least one)
    if allow_patterns:
        allowed = any(
            fnmatch.fnmatch(rel_path, p) or fnmatch.fnmatch(file_path, p)
            for p in allow_patterns
        )
        if not allowed:
            print(
                f"SCOPE VIOLATION: Edit to '{rel_path}' not in allowed scope: {allow_patterns}",
                file=sys.stderr
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
