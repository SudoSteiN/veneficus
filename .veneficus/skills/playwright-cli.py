#!/usr/bin/env python3
"""Playwright CLI wrapper for browser automation.

Provides a simple CLI for common browser actions. Uses compact accessibility
tree output (200-400 tokens) rather than full DOM.

Usage:
    uv run playwright-cli.py navigate "http://localhost:3000"
    uv run playwright-cli.py click "button.submit"
    uv run playwright-cli.py type "#email" "test@example.com"
    uv run playwright-cli.py screenshot "screenshots/page.png"
    uv run playwright-cli.py assert-text ".status" "Success"
    uv run playwright-cli.py accessibility
    uv run playwright-cli.py eval "document.title"
    uv run playwright-cli.py --session my-cart navigate "http://shop.example.com"
"""

import json
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    print("Error: Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

# Global state for persistent browser session
_browser: Browser | None = None
_page: Page | None = None
_session_name: str | None = None

# Named sessions store browser state (cookies, localStorage) in a directory
SESSIONS_DIR = Path.home() / ".veneficus-sessions"


def get_page() -> Page:
    """Get or create browser page, optionally with a named session for persistent state."""
    global _browser, _page
    if _page is None:
        pw = sync_playwright().start()
        launch_kwargs: dict = {"headless": False}

        if _session_name:
            session_dir = SESSIONS_DIR / _session_name
            session_dir.mkdir(parents=True, exist_ok=True)
            # Use persistent context to retain cookies/localStorage across runs
            context = pw.chromium.launch_persistent_context(
                user_data_dir=str(session_dir),
                **launch_kwargs,
            )
            _page = context.pages[0] if context.pages else context.new_page()
        else:
            _browser = pw.chromium.launch(**launch_kwargs)
            _page = _browser.new_page()
    return _page


def compact_accessibility(page: Page) -> str:
    """Get compact accessibility tree (200-400 tokens)."""
    snapshot = page.accessibility.snapshot()
    if not snapshot:
        return "(empty page)"

    lines: list[str] = []

    def walk(node: dict, depth: int = 0) -> None:
        indent = "  " * depth
        role = node.get("role", "")
        name = node.get("name", "")
        value = node.get("value", "")

        if role in ("none", "generic", "presentation") and not name:
            pass  # Skip noise
        else:
            parts = [role]
            if name:
                parts.append(f'"{name}"')
            if value:
                parts.append(f"[{value}]")
            lines.append(f"{indent}{' '.join(parts)}")

        for child in node.get("children", []):
            walk(child, depth + 1)

    walk(snapshot)

    # Truncate to ~400 tokens (~1600 chars)
    result = "\n".join(lines)
    if len(result) > 1600:
        result = result[:1600] + "\n... (truncated)"

    return result


def cmd_navigate(url: str) -> None:
    page = get_page()
    page.goto(url, wait_until="networkidle", timeout=30000)
    print(f"Navigated to: {page.url}")
    print(f"Title: {page.title()}")
    print(f"\nAccessibility tree:")
    print(compact_accessibility(page))


def cmd_click(selector: str) -> None:
    page = get_page()
    page.click(selector, timeout=10000)
    page.wait_for_load_state("networkidle", timeout=10000)
    print(f"Clicked: {selector}")
    print(f"Current URL: {page.url}")


def cmd_type(selector: str, text: str) -> None:
    page = get_page()
    page.fill(selector, text, timeout=10000)
    print(f"Typed into {selector}: {text}")


def cmd_screenshot(path: str) -> None:
    page = get_page()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=path, full_page=True)
    print(f"Screenshot saved: {path}")


def cmd_assert_text(selector: str, expected: str) -> None:
    page = get_page()
    try:
        element = page.wait_for_selector(selector, timeout=10000)
        if element:
            actual = element.text_content() or ""
            if expected in actual:
                print(f"PASS: '{selector}' contains '{expected}'")
            else:
                print(f"FAIL: '{selector}' text is '{actual}', expected to contain '{expected}'")
                sys.exit(1)
        else:
            print(f"FAIL: Selector '{selector}' not found")
            sys.exit(1)
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)


def cmd_accessibility() -> None:
    page = get_page()
    print(compact_accessibility(page))


def cmd_eval(expression: str) -> None:
    page = get_page()
    result = page.evaluate(expression)
    print(json.dumps(result, indent=2, default=str))


def main() -> None:
    global _session_name

    argv = sys.argv[1:]

    # Parse --session flag before command
    if argv and argv[0] == "--session":
        if len(argv) < 3:
            print("Usage: playwright-cli.py --session <name> <command> [args...]")
            sys.exit(1)
        _session_name = argv[1]
        argv = argv[2:]
        print(f"Using persistent session: {_session_name}")

    if not argv:
        print("Usage: playwright-cli.py [--session <name>] <command> [args...]")
        print("Commands: navigate, click, type, screenshot, assert-text, accessibility, eval")
        sys.exit(1)

    command = argv[0]
    args = argv[1:]

    try:
        if command == "navigate":
            cmd_navigate(args[0] if args else "http://localhost:3000")
        elif command == "click":
            cmd_click(args[0])
        elif command == "type":
            cmd_type(args[0], args[1])
        elif command == "screenshot":
            cmd_screenshot(args[0] if args else "screenshots/screenshot.png")
        elif command == "assert-text":
            cmd_assert_text(args[0], args[1])
        elif command == "accessibility":
            cmd_accessibility()
        elif command == "eval":
            cmd_eval(args[0])
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    except IndexError:
        print(f"Error: Missing arguments for '{command}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
