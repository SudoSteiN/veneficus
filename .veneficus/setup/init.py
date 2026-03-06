#!/usr/bin/env python3
"""Veneficus framework initializer.

Run from project root: uv run .veneficus/setup/init.py
Creates directory structure, copies templates, wires hooks and commands.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def info(msg: str) -> None:
    print(f"\033[0;32m[veneficus]\033[0m {msg}")


def warn(msg: str) -> None:
    print(f"\033[1;33m[veneficus]\033[0m {msg}")


def error(msg: str) -> None:
    print(f"\033[0;31m[veneficus]\033[0m {msg}", file=sys.stderr)


def main() -> None:
    project_root = Path.cwd()
    veneficus_dir = project_root / ".veneficus"
    claude_dir = project_root / ".claude"

    # Locate the framework source (where this script lives)
    framework_src = Path(__file__).resolve().parent.parent

    info("Initializing Veneficus framework...")

    # 1. Check/install dependencies
    install_script = framework_src / "setup" / "install_deps.sh"
    if install_script.exists():
        info("Checking dependencies...")
        result = subprocess.run(["bash", str(install_script)], capture_output=False)
        if result.returncode != 0:
            warn("Some dependencies may be missing. Continuing anyway.")

    # 2. Create directory structure
    dirs = [
        veneficus_dir / "docs",
        veneficus_dir / "events" / "logs",
        claude_dir / "commands",
        project_root / "tasks",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        info(f"  Directory: {d.relative_to(project_root)}")

    # 3. Copy templates to docs/ if they don't exist
    templates_dir = framework_src / "templates"
    docs_dir = veneficus_dir / "docs"

    template_mappings = {
        "PRD.template.md": "PRD.md",
        "architecture.template.md": "architecture.md",
        "features.template.json": "features.json",
    }

    if templates_dir.exists():
        for template_name, target_name in template_mappings.items():
            src = templates_dir / template_name
            dst = docs_dir / target_name
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
                info(f"  Created: {dst.relative_to(project_root)}")
            elif dst.exists():
                info(f"  Exists:  {dst.relative_to(project_root)} (skipped)")

    # Copy DESIGN_SPEC.md template if missing
    design_spec = project_root / "DESIGN_SPEC.md"
    design_spec_template = templates_dir / "DESIGN_SPEC.template.md"
    if not design_spec.exists() and design_spec_template.exists():
        shutil.copy2(design_spec_template, design_spec)
        info(f"  Created: DESIGN_SPEC.md")
    elif design_spec.exists():
        info(f"  Exists:  DESIGN_SPEC.md (skipped)")

    # Create decisions.md if missing
    decisions_file = docs_dir / "decisions.md"
    if not decisions_file.exists():
        decisions_file.write_text(
            "# Technical Decisions Log\n\n"
            "Append-only log of architectural and technical decisions.\n\n"
            "---\n\n"
            "<!-- Format:\n"
            "## YYYY-MM-DD: Decision Title\n"
            "**Context**: Why this decision was needed\n"
            "**Decision**: What was decided\n"
            "**Consequences**: What changes as a result\n"
            "-->\n"
        )
        info(f"  Created: {decisions_file.relative_to(project_root)}")

    # 4. Write .claude/settings.json with hooks config
    settings_file = claude_dir / "settings.json"
    settings_src = framework_src / ".." / ".claude" / "settings.json"
    if settings_src.exists() and not settings_file.exists():
        shutil.copy2(settings_src, settings_file)
        info(f"  Created: {settings_file.relative_to(project_root)}")
    elif not settings_file.exists():
        warn("  settings.json source not found — create manually")

    # 5. Copy commands to .claude/commands/
    commands_src = framework_src / "commands"
    commands_dst = claude_dir / "commands"
    if commands_src.exists():
        for cmd_file in commands_src.glob("*.md"):
            dst = commands_dst / cmd_file.name
            shutil.copy2(cmd_file, dst)
            info(f"  Command: {dst.relative_to(project_root)}")

    # 6. Update .gitignore
    gitignore = project_root / ".gitignore"
    ignore_entries = [
        ".veneficus/events/",
        "dashboard/node_modules/",
        "dashboard/dist/",
        "screenshots/",
        "*.db",
        "*.db-journal",
    ]

    existing = gitignore.read_text() if gitignore.exists() else ""
    new_entries = []
    for entry in ignore_entries:
        if entry not in existing:
            new_entries.append(entry)

    if new_entries:
        with open(gitignore, "a") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write("\n# Veneficus framework\n")
            for entry in new_entries:
                f.write(f"{entry}\n")
        info(f"  Updated: .gitignore")

    # 7. Copy .claudeignore if none exists
    claudeignore = project_root / ".claudeignore"
    claudeignore_template = framework_src / "templates" / "claudeignore.template"
    if not claudeignore.exists() and claudeignore_template.exists():
        shutil.copy2(claudeignore_template, claudeignore)
        info("  Created: .claudeignore")
    elif claudeignore.exists():
        info("  Exists:  .claudeignore (skipped)")

    # 8. Generate CLAUDE.md if none exists (skip if already present)
    claude_md = project_root / "CLAUDE.md"
    if not claude_md.exists():
        template_claude = framework_src / "templates" / "CLAUDE.template.md"
        if template_claude.exists():
            shutil.copy2(template_claude, claude_md)
            info("  Created: CLAUDE.md from template")
        else:
            warn("  No CLAUDE.md template found — create manually")
    else:
        info("  Exists:  CLAUDE.md (skipped)")

    info("")
    info("Veneficus initialized! Next steps:")
    info("  1. Edit .veneficus/docs/PRD.md with your project details")
    info("  2. Edit .veneficus/docs/architecture.md with your system design")
    info("  3. Run: just prime")


if __name__ == "__main__":
    main()
