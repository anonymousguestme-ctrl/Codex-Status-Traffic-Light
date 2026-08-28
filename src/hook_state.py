#!/usr/bin/env python3
"""Maintain privacy-minimal per-session state for Codex CLI hooks."""

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
DEFAULT_STATE_DIR = Path.home() / ".codex" / "traffic-light" / "sessions"
VALID_STATES = ("working", "approval", "finished")


def safe_id(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", str(value or "unknown"))[:160]


def state_dir() -> Path:
    configured = os.environ.get("CODEX_TRAFFIC_LIGHT_STATE_DIR")
    return Path(configured) if configured else DEFAULT_STATE_DIR


def state_path(data: dict[str, Any]) -> Path:
    return state_dir() / f"{safe_id(data.get('session_id'))}.json"


def set_state(data: dict[str, Any], state: str) -> None:
    if state not in VALID_STATES:
        raise ValueError(f"Unsupported state: {state}")
    directory = state_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = state_path(data)
    payload = {
        "session_id": data.get("session_id"),
        "turn_id": data.get("turn_id"),
        "state": state,
        "updated_at_unix": time.time(),
        "hook_event_name": data.get("hook_event_name"),
    }
    temporary = target.with_suffix(f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, target)


def remove_session(data: dict[str, Any]) -> None:
    state_path(data).unlink(missing_ok=True)


def load_input() -> dict[str, Any]:
    content = sys.stdin.read()
    if not content.strip():
        return {}
    try:
        value = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def record_hook_error(exc: Exception) -> None:
    """Keep hook diagnostics local without allowing them to fail Codex."""
    try:
        log_path = state_dir().parent / "hook-errors.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as stream:
            stream.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')} {type(exc).__name__}: {exc}\n")
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("set-working", "set-approval", "set-finished", "remove-session"))
    args = parser.parse_args()
    try:
        data = load_input()
        if args.action == "remove-session":
            remove_session(data)
        else:
            set_state(data, args.action.removeprefix("set-"))
        if data.get("hook_event_name") == "Stop":
            print("{}")
    except Exception as exc:
        # A telemetry/status hook must never turn a successful Codex tool call
        # into a reported hook failure.
        record_hook_error(exc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
