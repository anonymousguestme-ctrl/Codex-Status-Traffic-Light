#!/usr/bin/env python3
"""Maintain privacy-minimal state markers for Codex CLI lifecycle hooks."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_DIR = PROJECT_ROOT / "runtime" / "approvals"


def safe_id(value: Any) -> str:
    text = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", text)[:160]


def state_dir() -> Path:
    configured = os.environ.get("CODEX_TRAFFIC_LIGHT_STATE_DIR")
    return Path(configured) if configured else DEFAULT_STATE_DIR


def marker_path(data: dict[str, Any]) -> Path:
    session = safe_id(data.get("session_id"))
    turn = safe_id(data.get("turn_id"))
    return state_dir() / f"{session}__{turn}.json"


def mark(data: dict[str, Any]) -> None:
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    marker = marker_path(data)
    payload = {
        "session_id": data.get("session_id"),
        "turn_id": data.get("turn_id"),
        "created_at_unix": time.time(),
        "hook_event_name": "PermissionRequest",
    }
    temporary = marker.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, marker)


def clear_turn(data: dict[str, Any]) -> None:
    marker_path(data).unlink(missing_ok=True)


def clear_session(data: dict[str, Any]) -> None:
    directory = state_dir()
    session = safe_id(data.get("session_id"))
    if directory.is_dir():
        for marker in directory.glob(f"{session}__*.json"):
            marker.unlink(missing_ok=True)


def load_input() -> dict[str, Any]:
    content = sys.stdin.read()
    return json.loads(content) if content.strip() else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("mark", "clear-turn", "clear-session"))
    args = parser.parse_args()
    data = load_input()

    if args.action == "mark":
        mark(data)
    elif args.action == "clear-turn":
        clear_turn(data)
    else:
        clear_session(data)

    # Stop hooks require valid JSON on stdout. Empty JSON is harmless for all clear hooks.
    if data.get("hook_event_name") == "Stop":
        print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
