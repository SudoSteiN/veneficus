#!/usr/bin/env python3
"""Insights analyzer — identify recurring failure modes and generate recommendations.

DEPRECATED: Claude Code's native /insights command provides better analysis
across 1000+ messages. Use 'just insights' or '/insights' instead.
This analyzer is kept for backward compatibility but the retro command
now prioritizes the native /insights feature.

Takes metrics from the collector and applies heuristics to produce actionable
improvement suggestions.

Usage:
    uv run analyzer.py [--metrics metrics.json]

If no metrics file given, runs the collector first.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def find_project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".veneficus").is_dir():
            return p
        p = p.parent
    return Path.cwd()


def load_metrics(path: str | None) -> dict:
    """Load metrics from file or run collector."""
    if path:
        return json.loads(Path(path).read_text())

    # Run collector inline
    root = find_project_root()
    result = subprocess.run(
        ["uv", "run", str(root / ".veneficus" / "insights" / "collector.py")],
        capture_output=True, text=True,
    )
    if result.returncode == 0 and result.stdout.strip():
        return json.loads(result.stdout)
    return {"total_events": 0, "error": "Collector failed"}


class Recommendation:
    def __init__(self, title: str, impact: str, suggestion: str, data: str = ""):
        self.title = title
        self.impact = impact
        self.suggestion = suggestion
        self.data = data

    def to_markdown(self) -> str:
        lines = [
            f"### {self.title}",
            f"**Impact**: {self.impact}",
        ]
        if self.data:
            lines.append(f"**Evidence**: {self.data}")
        lines.append(f"**Recommendation**: {self.suggestion}")
        return "\n".join(lines)


def analyze(metrics: dict) -> list[Recommendation]:
    """Apply heuristics to metrics and generate recommendations."""
    recs: list[Recommendation] = []

    if metrics.get("error"):
        return [Recommendation(
            "No data available",
            "Cannot analyze",
            metrics["error"],
        )]

    total = metrics.get("total_events", 0)
    if total == 0:
        return [Recommendation(
            "No events recorded",
            "Cannot analyze without data",
            "Run a Claude Code session with hooks enabled, then re-run retro.",
        )]

    # 1. Validation pass rate
    pass_rate = metrics.get("validation_pass_rate", 100)
    failures = metrics.get("validation_failures", 0)

    if pass_rate < 70:
        recs.append(Recommendation(
            "Low validation pass rate",
            f"Only {pass_rate}% of edits pass validation — agents are spending time on fix loops",
            "Add more specific instructions to agent prompts about common errors. "
            "Consider adding CLAUDE.md rules for the most common failure types.",
            f"{failures} failures out of {total} events",
        ))
    elif pass_rate < 90:
        recs.append(Recommendation(
            "Moderate validation failure rate",
            f"{pass_rate}% pass rate — some room for improvement",
            "Review the most common validation errors and add preventive rules.",
            f"{failures} failures",
        ))

    # 2. Most edited files (potential churn)
    file_edits = metrics.get("most_edited_files", metrics.get("most_active_files", {}))
    for file_path, count in file_edits.items():
        if count > 10:
            recs.append(Recommendation(
                f"High churn on {Path(file_path).name}",
                f"File edited {count} times — may indicate unclear requirements or design issues",
                "Review if this file's interface is well-defined. Consider breaking it into smaller modules.",
                f"{file_path}: {count} edits",
            ))

    # 3. Agent utilization
    spawns = metrics.get("agent_spawns", 0)
    stops = metrics.get("agent_stops", 0)
    if spawns > 0 and stops < spawns * 0.8:
        recs.append(Recommendation(
            "Agents not completing cleanly",
            f"{spawns} agents spawned but only {stops} stopped — some may have been interrupted",
            "Check for timeout issues or context window exhaustion. "
            "Consider shorter, more focused agent tasks.",
            f"Spawned: {spawns}, Stopped: {stops}",
        ))

    # 4. Tool usage patterns
    tool_usage = metrics.get("tool_usage", {})
    reads = tool_usage.get("Read", 0)
    edits = tool_usage.get("Edit", 0) + tool_usage.get("Write", 0)
    if edits > 0 and reads < edits * 0.5:
        recs.append(Recommendation(
            "Low read-to-edit ratio",
            f"{reads} reads vs {edits} edits — agents may not be reading enough context before editing",
            "Reinforce 'read before write' in agent prompts. "
            "Add to CLAUDE.md: 'Always read a file before modifying it.'",
            f"Read: {reads}, Edit/Write: {edits}",
        ))

    # 5. Hook event distribution
    hook_counts = metrics.get("hook_event_counts", metrics.get("event_type_counts", {}))
    post_failures = hook_counts.get("PostToolUseFailure", 0)
    if post_failures > 5:
        recs.append(Recommendation(
            "Frequent PostToolUse failures",
            f"{post_failures} tool failures recorded",
            "Review the most common failure patterns. "
            "If a specific lint rule keeps failing, add it as a CLAUDE.md instruction.",
            f"{post_failures} failures",
        ))

    if not recs:
        recs.append(Recommendation(
            "Looking good!",
            "No significant issues detected",
            "Keep up the current workflow. Consider reviewing this analysis after larger sessions.",
        ))

    return recs


def write_recommendations(recs: list[Recommendation], metrics: dict, output_path: Path) -> None:
    """Write recommendations to markdown file."""
    date = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = metrics.get("total_events", 0)
    pass_rate = metrics.get("validation_pass_rate", "N/A")

    lines = [
        f"# Session Retrospective — {date}",
        "",
        "## Metrics",
        f"- Total events: {total}",
        f"- Validation pass rate: {pass_rate}%",
        f"- Agent spawns: {metrics.get('agent_spawns', 0)}",
        f"- Total tokens: {metrics.get('total_tokens', 'N/A')}",
        "",
        "## Findings and Recommendations",
        "",
    ]

    for rec in recs:
        lines.append(rec.to_markdown())
        lines.append("")

    lines.extend([
        "## Suggested Changes",
        "",
    ])

    for rec in recs:
        if "CLAUDE.md" in rec.suggestion or "agent prompt" in rec.suggestion:
            lines.append(f"- [ ] {rec.suggestion}")

    lines.extend([
        "",
        "---",
        f"*Generated by Veneficus insights analyzer on {date}*",
    ])

    output_path.write_text("\n".join(lines))
    print(f"Recommendations written to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Veneficus insights analyzer")
    parser.add_argument("--metrics", type=str, help="Path to metrics JSON from collector")
    args = parser.parse_args()

    root = find_project_root()
    metrics = load_metrics(args.metrics)
    recs = analyze(metrics)

    output_path = root / ".veneficus" / "insights" / "recommendations.md"
    write_recommendations(recs, metrics, output_path)

    # Also print to stdout
    for rec in recs:
        print(f"\n{rec.to_markdown()}")


if __name__ == "__main__":
    main()
