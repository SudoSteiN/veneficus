#!/usr/bin/env python3
"""Smart context assembly from .veneficus/docs/.

Reads project context documents and outputs a combined, prioritized context
suitable for feeding into Claude Code sessions.

Usage:
    uv run context-loader.py [--full | --summary | --feature FEATURE_ID]
"""

import argparse
import json
import sys
from pathlib import Path


def find_docs_dir() -> Path:
    """Walk up from cwd to find .veneficus/docs/."""
    p = Path.cwd()
    while p != p.parent:
        candidate = p / ".veneficus" / "docs"
        if candidate.is_dir():
            return candidate
        p = p.parent
    print("Error: .veneficus/docs/ not found", file=sys.stderr)
    sys.exit(1)


def load_file(path: Path) -> str:
    """Load file contents or return placeholder."""
    if path.exists():
        return path.read_text().strip()
    return f"[{path.name} not found]"


def summary_mode(docs: Path) -> None:
    """Output a compact summary of project state."""
    # Parse features
    features_path = docs / "features.json"
    if features_path.exists():
        data = json.loads(features_path.read_text())
        features = data.get("features", [])
        done = [f for f in features if f.get("status") == "done"]
        active = [f for f in features if f.get("status") == "in_progress"]
        pending = [f for f in features if f.get("status") == "pending"]

        print("## Features")
        print(f"Done: {len(done)} | Active: {len(active)} | Pending: {len(pending)}")
        if active:
            print(f"\nActive: {', '.join(f['name'] for f in active)}")
        if pending:
            print(f"Next: {pending[0]['name']}" if pending else "")
    else:
        print("[features.json not found]")

    # Last 3 decisions
    decisions = load_file(docs / "decisions.md")
    lines = [l for l in decisions.split("\n") if l.startswith("## ")]
    if lines:
        print(f"\n## Recent Decisions")
        for line in lines[-3:]:
            print(f"- {line.lstrip('# ')}")


def full_mode(docs: Path) -> None:
    """Output all context documents."""
    for name in ["PRD.md", "architecture.md", "decisions.md"]:
        content = load_file(docs / name)
        print(f"\n{'='*60}")
        print(f"# {name}")
        print(f"{'='*60}\n")
        print(content)

    features_path = docs / "features.json"
    if features_path.exists():
        print(f"\n{'='*60}")
        print("# features.json")
        print(f"{'='*60}\n")
        print(features_path.read_text())


def feature_mode(docs: Path, feature_id: str) -> None:
    """Output context for a specific feature."""
    features_path = docs / "features.json"
    if not features_path.exists():
        print("features.json not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(features_path.read_text())
    feature = next(
        (f for f in data.get("features", []) if f.get("id") == feature_id),
        None
    )

    if not feature:
        print(f"Feature '{feature_id}' not found", file=sys.stderr)
        sys.exit(1)

    print(f"## Feature: {feature['name']} ({feature['id']})")
    print(f"Status: {feature['status']}")
    print(f"Description: {feature.get('description', 'N/A')}")
    print(f"\n### Acceptance Criteria")
    for i, c in enumerate(feature.get("acceptance_criteria", []), 1):
        print(f"{i}. {c}")

    if feature.get("files"):
        print(f"\n### Related Files")
        for f in feature["files"]:
            print(f"- {f}")

    if feature.get("depends_on"):
        print(f"\n### Dependencies")
        for d in feature["depends_on"]:
            print(f"- {d}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Veneficus context loader")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--full", action="store_true", help="Full context output")
    group.add_argument("--summary", action="store_true", help="Compact summary")
    group.add_argument("--feature", type=str, help="Context for specific feature ID")
    args = parser.parse_args()

    docs = find_docs_dir()

    if args.feature:
        feature_mode(docs, args.feature)
    elif args.full:
        full_mode(docs)
    else:
        summary_mode(docs)


if __name__ == "__main__":
    main()
