#!/usr/bin/env python3
"""Language-aware PostToolUse validator.

Reads hook JSON from stdin, validates the edited file based on its type.
Exit 0 = success, Exit 2 = blocking error (stderr fed back to Claude).
"""

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Circuit breaker: track consecutive failures per file to prevent infinite loops.
# After MAX_CONSECUTIVE_FAILURES for the same file, stop blocking and warn instead.
MAX_CONSECUTIVE_FAILURES = 5
FAILURE_STATE_DIR = os.path.join(
    os.environ.get("CLAUDE_PROJECT_DIR", "."), ".veneficus", "events", "logs"
)
FAILURE_STATE_FILE = os.path.join(FAILURE_STATE_DIR, ".validator_failures.json")
DOC_FRESHNESS_FILE = os.path.join(FAILURE_STATE_DIR, ".doc_freshness.json")

# Doc files that reset the freshness counter
DOC_FILES = {
    "features.json", "decisions.md", "architecture.md",
    "PRD.md", "README.md", "CHANGELOG.md",
}

DOC_FRESHNESS_THRESHOLD = 5


def truncate(msg: str, limit: int = 500) -> str:
    """Keep error output under limit to avoid context window saturation."""
    if len(msg) <= limit:
        return msg
    return msg[:limit - 3] + "..."


def validate_python(file_path: str) -> tuple[bool, str]:
    """Validate Python: compile check + ruff lint."""
    # Compile check
    try:
        import py_compile
        py_compile.compile(file_path, doraise=True)
    except py_compile.PyCompileError as e:
        return False, f"Syntax error: {e}"

    # Ruff check (if available)
    try:
        result = subprocess.run(
            ["ruff", "check", "--no-fix", file_path],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return False, f"Lint errors:\n{result.stdout}"
    except FileNotFoundError:
        pass  # ruff not installed, skip
    except subprocess.TimeoutExpired:
        pass

    return True, ""


def validate_json(file_path: str) -> tuple[bool, str]:
    """Validate JSON syntax."""
    try:
        with open(file_path) as f:
            json.load(f)
        return True, ""
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"


def validate_typescript(file_path: str) -> tuple[bool, str]:
    """Validate TypeScript/JavaScript with tsc if available."""
    try:
        # Find nearest tsconfig.json
        p = Path(file_path).parent
        tsconfig = None
        while p != p.parent:
            candidate = p / "tsconfig.json"
            if candidate.exists():
                tsconfig = candidate
                break
            p = p.parent

        if tsconfig:
            result = subprocess.run(
                ["npx", "tsc", "--noEmit", "--pretty", "false"],
                capture_output=True, text=True, timeout=30,
                cwd=str(tsconfig.parent)
            )
            if result.returncode != 0:
                # Filter to only errors in the edited file
                basename = os.path.basename(file_path)
                errors = [
                    line for line in result.stdout.splitlines()
                    if basename in line
                ]
                if errors:
                    return False, "\n".join(errors[:5])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return True, ""


def is_test_file(path: str) -> bool:
    """Returns True if the file matches common test file patterns."""
    p = Path(path)
    name = p.name
    parts = p.parts

    if name.startswith("test_"):
        return True
    if ".test." in name or ".spec." in name:
        return True
    if p.stem.endswith("_test"):
        return True
    if "__tests__" in parts or "tests" in parts or "test" in parts:
        return True
    return False


def is_implementation_file(path: str) -> bool:
    """Returns True if path is a code file that is NOT a test, config, or setup file."""
    p = Path(path)
    ext = p.suffix.lower()
    name = p.name

    if ext not in (".py", ".ts", ".tsx", ".js", ".jsx"):
        return False
    if is_test_file(path):
        return False

    exclude_names = {"__init__.py", "setup.py", "conftest.py", "manage.py"}
    if name in exclude_names:
        return False

    exclude_dirs = {"migrations", "alembic", "node_modules", ".veneficus"}
    if any(d in p.parts for d in exclude_dirs):
        return False

    return True


def find_test_file(file_path: str) -> str | None:
    """Find associated test file if it exists."""
    p = Path(file_path)
    stem = p.stem
    parent = p.parent

    candidates = [
        parent / f"test_{p.name}",
        parent / f"{stem}_test{p.suffix}",
        parent / "tests" / f"test_{p.name}",
        parent / "__tests__" / p.name,
        parent / f"{stem}.test{p.suffix}",
        parent / f"{stem}.spec{p.suffix}",
    ]

    for c in candidates:
        if c.exists():
            return str(c)
    return None


def run_test(test_file: str, file_path: str) -> tuple[bool, str]:
    """Run associated test file."""
    ext = Path(test_file).suffix

    if ext == ".py":
        cmd = ["python", "-m", "pytest", test_file, "-x", "-q", "--tb=short"]
    elif ext in (".ts", ".js", ".tsx", ".jsx"):
        # Try common test runners
        for runner in ["npx vitest run", "npx jest"]:
            parts = runner.split() + [test_file]
            try:
                result = subprocess.run(
                    parts, capture_output=True, text=True, timeout=30,
                    cwd=str(Path(file_path).parent)
                )
                if "not found" not in result.stderr.lower():
                    if result.returncode != 0:
                        return False, f"Test failed:\n{result.stdout[-300:]}"
                    return True, ""
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        return True, ""
    else:
        return True, ""

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return False, f"Test failed:\n{result.stdout[-300:]}"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return True, ""


def load_failure_state() -> dict:
    """Load consecutive failure counts per file."""
    try:
        if os.path.exists(FAILURE_STATE_FILE):
            with open(FAILURE_STATE_FILE) as f:
                state = json.load(f)
            # Expire entries older than 10 minutes
            now = time.time()
            return {k: v for k, v in state.items()
                    if now - v.get("ts", 0) < 600}
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def save_failure_state(state: dict) -> None:
    """Persist failure counts."""
    try:
        os.makedirs(FAILURE_STATE_DIR, exist_ok=True)
        with open(FAILURE_STATE_FILE, "w") as f:
            json.dump(state, f)
    except OSError:
        pass


def record_failure(file_path: str) -> int:
    """Record a failure for file_path. Returns new count."""
    state = load_failure_state()
    entry = state.get(file_path, {"count": 0, "ts": time.time()})
    entry["count"] += 1
    entry["ts"] = time.time()
    state[file_path] = entry
    save_failure_state(state)
    return entry["count"]


def clear_failure(file_path: str) -> None:
    """Clear failure count on success."""
    state = load_failure_state()
    state.pop(file_path, None)
    if state:
        save_failure_state(state)
    elif os.path.exists(FAILURE_STATE_FILE):
        os.remove(FAILURE_STATE_FILE)


def load_doc_freshness() -> dict:
    """Load doc freshness tracking state."""
    try:
        if os.path.exists(DOC_FRESHNESS_FILE):
            with open(DOC_FRESHNESS_FILE) as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return {"impl_edits": 0, "last_doc_edit": 0}


def save_doc_freshness(state: dict) -> None:
    """Persist doc freshness state."""
    try:
        os.makedirs(FAILURE_STATE_DIR, exist_ok=True)
        with open(DOC_FRESHNESS_FILE, "w") as f:
            json.dump(state, f)
    except OSError:
        pass


def check_doc_freshness(file_path: str) -> None:
    """Track impl vs doc edits. Warn after too many impl edits without doc updates.

    Non-blocking — always returns without exiting.
    """
    if os.environ.get("VENEFICUS_DOC_ENFORCE", "1") != "1":
        return

    p = Path(file_path)
    name = p.name

    state = load_doc_freshness()

    # Check if this is a doc file edit — reset counter
    if name in DOC_FILES:
        state["impl_edits"] = 0
        state["last_doc_edit"] = time.time()
        save_doc_freshness(state)
        return

    # Check if this is an implementation file edit — increment counter
    if is_implementation_file(file_path):
        state["impl_edits"] = state.get("impl_edits", 0) + 1
        save_doc_freshness(state)

        if state["impl_edits"] >= DOC_FRESHNESS_THRESHOLD:
            print(
                f"DOC REMINDER: {state['impl_edits']} implementation file edits since last "
                f"documentation update. Consider updating features.json, decisions.md, "
                f"or architecture.md. Disable: VENEFICUS_DOC_ENFORCE=0",
                file=sys.stderr,
            )


def main() -> None:
    # Read hook data from stdin
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Can't parse input, don't block

    tool_name = hook_data.get("tool_name", "")
    tool_input = hook_data.get("tool_input", {})

    # Extract file path
    file_path = tool_input.get("file_path", "")
    if not file_path or not os.path.exists(file_path):
        sys.exit(0)

    ext = Path(file_path).suffix.lower()

    # Validate based on file type
    ok, err = True, ""

    if ext == ".py":
        ok, err = validate_python(file_path)
    elif ext == ".json":
        ok, err = validate_json(file_path)
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        ok, err = validate_typescript(file_path)

    if not ok:
        count = record_failure(file_path)
        if count >= MAX_CONSECUTIVE_FAILURES:
            print(
                f"CIRCUIT BREAKER: {file_path} has failed validation {count} times consecutively. "
                f"Allowing edit to proceed — fix the underlying issue manually.\n"
                f"Last error: {truncate(err)}",
                file=sys.stderr,
            )
            clear_failure(file_path)
            sys.exit(0)  # Stop blocking after too many failures
        print(truncate(err), file=sys.stderr)
        sys.exit(2)

    # TDD enforcement: block edits to impl files without test files
    if os.environ.get("VENEFICUS_TDD_ENFORCE", "1") == "1":
        if is_implementation_file(file_path) and find_test_file(file_path) is None:
            count = record_failure(file_path)
            if count >= MAX_CONSECUTIVE_FAILURES:
                print(
                    f"TDD WARNING: No test file for '{Path(file_path).name}'. "
                    f"Write tests first. (circuit breaker: allowing after {count} blocks)",
                    file=sys.stderr,
                )
                clear_failure(file_path)
                sys.exit(0)
            print(
                f"TDD VIOLATION: No test file for '{Path(file_path).name}'. "
                f"Create the test file first. Disable: VENEFICUS_TDD_ENFORCE=0",
                file=sys.stderr,
            )
            sys.exit(2)

    # Run associated tests if they exist
    test_file = find_test_file(file_path)
    if test_file:
        ok, err = run_test(test_file, file_path)
        if not ok:
            count = record_failure(file_path)
            if count >= MAX_CONSECUTIVE_FAILURES:
                print(
                    f"CIRCUIT BREAKER: {file_path} has failed validation {count} times consecutively. "
                    f"Allowing edit to proceed — fix the underlying issue manually.\n"
                    f"Last error: {truncate(err)}",
                    file=sys.stderr,
                )
                sys.exit(0)
            print(truncate(err), file=sys.stderr)
            sys.exit(2)

    # Success — clear any tracked failures for this file
    clear_failure(file_path)

    # Doc freshness check (non-blocking)
    check_doc_freshness(file_path)

    sys.exit(0)


if __name__ == "__main__":
    main()
