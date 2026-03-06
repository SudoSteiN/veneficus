"""Shared event emitter for thread scripts.

Appends events to the local JSONL log and POSTs to dashboard (fails silently).
"""

import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _find_project_root() -> Path:
    p = Path.cwd()
    while p != p.parent:
        if (p / ".veneficus").is_dir():
            return p
        p = p.parent
    return Path.cwd()


def emit(event_type: str, **data: object) -> None:
    """Emit a thread lifecycle event."""
    root = _find_project_root()
    log_dir = root / ".veneficus" / "events" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    event = {
        "hook_event_name": event_type,
        "received_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        **data,
    }

    payload = json.dumps(event)

    # Append to local log
    try:
        with open(log_dir / "events.jsonl", "a") as f:
            f.write(payload + "\n")
    except OSError:
        pass

    # POST to dashboard (fail silently)
    dashboard_url = os.environ.get("VENEFICUS_DASHBOARD_URL", "http://localhost:7777/api/events")
    try:
        req = urllib.request.Request(
            dashboard_url,
            data=payload.encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=3)
    except Exception:
        pass
