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
DEFAULT_STATE_DIR = PROJECT_ROOT / "runtime" / "sessions"
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
    return json.loads(content) if content.strip() else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("set-working", "set-approval", "set-finished", "remove-session"))
    args = parser.parse_args()
    data = load_input()
    if args.action == "remove-session":
        remove_session(data)
    else:
        set_state(data, args.action.removeprefix("set-"))
    if data.get("hook_event_name") == "Stop":
        print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
