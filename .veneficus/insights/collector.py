#!/usr/bin/env python3
"""Insights collector — parse event logs for friction patterns.

Reads events from .veneficus/events/logs/events.jsonl or the dashboard SQLite DB.
Outputs structured metrics for the analyzer.

Usage:
    uv run collector.py [--db veneficus.db | --log events.jsonl]
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


def find_project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".veneficus").is_dir():
            return p
        p = p.parent
    return Path.cwd()


def collect_from_jsonl(path: Path) -> dict:
    """Parse events.jsonl and extract metrics."""
    events: list[dict] = []

    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    if not events:
        return {"total_events": 0, "error": "No events found"}

    # Metrics
    hook_events = Counter()
    tool_usage = Counter()
    file_edits = Counter()
    validation_failures: list[dict] = []
    agent_events: list[dict] = []
    timestamps: list[str] = []

    for event in events:
        hook_name = event.get("hook_event_name", "unknown")
        hook_events[hook_name] += 1

        tool = event.get("tool_name", "")
        if tool:
            tool_usage[tool] += 1

        ts = event.get("received_at", "")
        if ts:
            timestamps.append(ts)

        # Track file edits
        tool_input = event.get("tool_input", {})
        if isinstance(tool_input, dict):
            fp = tool_input.get("file_path", "")
            if fp and hook_name in ("PostToolUse", "PreToolUse"):
                file_edits[fp] += 1

        # Track validation failures (PostToolUseFailure or exit code 2)
        if hook_name == "PostToolUseFailure":
            validation_failures.append({
                "tool": tool,
                "file": tool_input.get("file_path", "") if isinstance(tool_input, dict) else "",
                "timestamp": ts,
            })

        # Track agent lifecycle
        if hook_name in ("SubagentStart", "SubagentStop"):
            agent_events.append({
                "event": hook_name,
                "timestamp": ts,
            })

    # Compute derived metrics
    total_edits = tool_usage.get("Edit", 0) + tool_usage.get("Write", 0)
    validation_pass_rate = (
        (total_edits - len(validation_failures)) / total_edits * 100
        if total_edits > 0 else 100
    )

    return {
        "total_events": len(events),
        "hook_event_counts": dict(hook_events.most_common()),
        "tool_usage": dict(tool_usage.most_common()),
        "most_edited_files": dict(Counter(file_edits).most_common(10)),
        "validation_failures": len(validation_failures),
        "validation_failure_details": validation_failures[:20],
        "validation_pass_rate": round(validation_pass_rate, 1),
        "agent_spawns": sum(1 for e in agent_events if e["event"] == "SubagentStart"),
        "agent_stops": sum(1 for e in agent_events if e["event"] == "SubagentStop"),
        "time_range": {
            "first": timestamps[0] if timestamps else "",
            "last": timestamps[-1] if timestamps else "",
        },
    }


def collect_from_db(db_path: Path) -> dict:
    """Collect metrics from the dashboard SQLite database."""
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        total = conn.execute("SELECT COUNT(*) as c FROM events").fetchone()["c"]
        if total == 0:
            return {"total_events": 0, "error": "No events in database"}

        type_counts = {
            row["type"]: row["c"]
            for row in conn.execute(
                "SELECT type, COUNT(*) as c FROM events GROUP BY type ORDER BY c DESC"
            )
        }

        failures = conn.execute(
            "SELECT COUNT(*) as c FROM events WHERE type LIKE '%failure%'"
        ).fetchone()["c"]

        file_ops = {
            row["path"]: row["c"]
            for row in conn.execute(
                "SELECT path, COUNT(*) as c FROM file_activity GROUP BY path ORDER BY c DESC LIMIT 10"
            )
        }

        tokens = conn.execute(
            "SELECT COALESCE(SUM(tokens), 0) as t FROM token_estimates"
        ).fetchone()["t"]

        conn.close()

        return {
            "total_events": total,
            "event_type_counts": type_counts,
            "validation_failures": failures,
            "most_active_files": file_ops,
            "total_tokens": tokens,
        }
    except Exception as e:
        return {"error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Veneficus insights collector")
    parser.add_argument("--db", type=str, help="Path to dashboard SQLite DB")
    parser.add_argument("--log", type=str, help="Path to events.jsonl")
    parser.add_argument("--output", type=str, help="Output file (default: stdout)")
    args = parser.parse_args()

    root = find_project_root()

    # Determine data source
    if args.db:
        metrics = collect_from_db(Path(args.db))
    elif args.log:
        metrics = collect_from_jsonl(Path(args.log))
    else:
        # Auto-detect: try jsonl first, then db
        jsonl_path = root / ".veneficus" / "events" / "logs" / "events.jsonl"
        db_path = root / "dashboard" / "veneficus.db"

        if jsonl_path.exists():
            metrics = collect_from_jsonl(jsonl_path)
        elif db_path.exists():
            metrics = collect_from_db(db_path)
        else:
            metrics = {"total_events": 0, "error": "No event data found. Run a session first."}

    output = json.dumps(metrics, indent=2)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Metrics written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
