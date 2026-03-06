#!/usr/bin/env python3
"""Validate edits against features.json acceptance criteria.

Reads hook JSON from stdin. Checks if the edited file belongs to a feature
and runs the feature's validation command if defined.
Exit 0 = success, Exit 2 = validation failed.
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def find_features_json(cwd: str) -> Path | None:
    """Locate features.json walking up from cwd."""
    p = Path(cwd)
    while p != p.parent:
        candidate = p / ".veneficus" / "docs" / "features.json"
        if candidate.exists():
            return candidate
        p = p.parent
    return None


def main() -> None:
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    cwd = hook_data.get("cwd", os.getcwd())
    tool_input = hook_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if not file_path:
        sys.exit(0)

    features_path = find_features_json(cwd)
    if not features_path:
        sys.exit(0)

    try:
        with open(features_path) as f:
            features = json.load(f)
    except (json.JSONDecodeError, OSError):
        sys.exit(0)

    # Check each feature for relevant files and validation commands
    for feature in features.get("features", []):
        files = feature.get("files", [])
        validate_cmd = feature.get("validate", "")

        # Check if edited file matches any feature's file list
        matches = any(
            file_path.endswith(f) or Path(file_path).name == Path(f).name
            for f in files
        )

        if matches and validate_cmd:
            try:
                result = subprocess.run(
                    validate_cmd, shell=True,
                    capture_output=True, text=True,
                    timeout=30, cwd=cwd
                )
                if result.returncode != 0:
                    output = (result.stdout + result.stderr).strip()
                    msg = f"Feature '{feature.get('name', '?')}' validation failed:\n{output[-400:]}"
                    print(msg, file=sys.stderr)
                    sys.exit(2)
            except subprocess.TimeoutExpired:
                print(
                    f"Feature '{feature.get('name', '?')}' validation timed out",
                    file=sys.stderr
                )
                sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
