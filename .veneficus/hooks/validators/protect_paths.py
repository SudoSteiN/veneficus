#!/usr/bin/env python3
"""Protect critical files from accidental modification.

Reads hook JSON from stdin. Blocks edits to protected paths.
Exit 0 = allowed, Exit 2 = blocked.
"""

import json
import sys
from pathlib import Path

# Paths that should never be modified by agents (relative to project root)
PROTECTED_PATTERNS = [
    ".veneficus/hooks/",
    ".veneficus/setup/",
    ".claude/settings.json",
]


def main() -> None:
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_input = hook_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    # Normalize to relative path
    cwd = hook_data.get("cwd", "")
    if cwd and file_path.startswith(cwd):
        rel = file_path[len(cwd):].lstrip("/")
    else:
        rel = file_path

    for pattern in PROTECTED_PATTERNS:
        if rel.startswith(pattern) or f"/{pattern}" in file_path:
            print(
                f"BLOCKED: {rel} is a protected framework file. "
                f"Modify manually if needed.",
                file=sys.stderr
            )
            sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
