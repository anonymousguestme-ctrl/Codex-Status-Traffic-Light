#!/usr/bin/env python3
"""Drive an Arduino traffic light from Codex CLI lifecycle-hook state."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import serial
from serial.tools import list_ports

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOOK_STATE_DIR = PROJECT_ROOT / "runtime" / "sessions"
STATE_TO_LIGHT = {"working": "GREEN", "approval": "YELLOW", "finished": "RED"}


class TranscriptTracker:
    """Incrementally follow local Codex rollout events without reading message text."""

    def __init__(self, sessions_dir: Path, max_age_seconds: float):
        self.sessions_dir = sessions_dir
        self.max_age_seconds = max_age_seconds
        self.offsets: dict[Path, int] = {}
        self.states: dict[Path, tuple[str, float]] = {}

    @staticmethod
    def _event_state(value: dict) -> tuple[str, float] | None:
        payload = value.get("payload", {})
        event_type = str(payload.get("type", ""))
        if event_type == "task_started":
            state = "working"
        elif event_type in ("task_complete", "turn_aborted"):
            state = "finished"
        elif "approval" in event_type.lower() and "request" in event_type.lower():
            state = "approval"
        else:
            return None
        timestamp = value.get("timestamp")
        try:
            updated = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).timestamp()
        except (TypeError, ValueError):
            updated = time.time()
        return state, updated

    def poll(self, now: float | None = None) -> set[str]:
        current_time = time.time() if now is None else now
        if not self.sessions_dir.is_dir():
            return set()
        # Rollout paths include YYYY/MM/DD, so the newest filenames cover active sessions
        # even while Windows delays updating an open file's mtime.
        cutoff_date = datetime.fromtimestamp(current_time, timezone.utc).date() - timedelta(days=1)
        candidates = []
        for path in self.sessions_dir.rglob("rollout-*.jsonl"):
            try:
                rollout_date = datetime.strptime(path.name[8:18], "%Y-%m-%d").date()
            except ValueError:
                continue
            if rollout_date >= cutoff_date:
                candidates.append(path)
        candidates = sorted(candidates, reverse=True)[:20]
        for path in candidates:
            try:
                size = path.stat().st_size
                offset = self.offsets.get(path, 0)
                if size < offset:
                    offset = 0
                with path.open("r", encoding="utf-8") as stream:
                    stream.seek(offset)
                    for line in stream:
                        try:
                            event = self._event_state(json.loads(line))
                            if event is not None:
                                self.states[path] = event
                        except json.JSONDecodeError:
                            continue
                    self.offsets[path] = stream.tell()
            except OSError:
                continue
        active: set[str] = set()
        for path, (state, updated) in list(self.states.items()):
            if current_time - updated <= self.max_age_seconds:
                active.add(state)
            else:
                self.states.pop(path, None)
        return active


def hook_states(state_dir: Path, max_age_seconds: float, now: float | None = None) -> set[str]:
    """Aggregate all Codex sessions into one light: approval > working > finished."""
    if not (state_dir.parent / "hooks-installed.json").is_file():
        raise RuntimeError("Codex CLI hooks 尚未安装；请先运行 .\\install-hooks.ps1")
    current_time = time.time() if now is None else now
    states: set[str] = set()
    state_dir.mkdir(parents=True, exist_ok=True)
    for marker in state_dir.glob("*.json"):
        try:
            if current_time - marker.stat().st_mtime > max_age_seconds:
                marker.unlink(missing_ok=True)
                continue
            state = json.loads(marker.read_text(encoding="utf-8")).get("state")
            if state not in STATE_TO_LIGHT:
                raise ValueError("invalid session state")
            states.add(state)
        except (OSError, ValueError, json.JSONDecodeError):
            marker.unlink(missing_ok=True)
    return states


def aggregate_light(states: set[str]) -> str:
    if "approval" in states:
        return "YELLOW"
    if "working" in states:
        return "GREEN"
    return "RED"


def hook_light_state(state_dir: Path, max_age_seconds: float, now: float | None = None) -> str:
    return aggregate_light(hook_states(state_dir, max_age_seconds, now))


def choose_serial_port(configured: str) -> str:
    if configured != "auto":
        return configured
    ports = list(list_ports.comports())
    if not ports:
        raise RuntimeError("没有发现串口。请插入 Arduino，或在 config.json 中填写 COM 端口")
    preferred_tokens = ("arduino", "ch340", "wch", "usb serial", "cp210")
    candidates = [p for p in ports if any(t in (p.description or "").lower() for t in preferred_tokens)] or ports
    if len(candidates) > 1:
        names = ", ".join(f"{p.device} ({p.description})" for p in candidates)
        raise RuntimeError(f"发现多个可能串口：{names}。请在 config.json 中指定 serial_port")
    return candidates[0].device


@dataclass
class Settings:
    serial_port: str = "auto"
    baud_rate: int = 115200
    poll_interval_seconds: float = 0.75
    hook_state_dir: str = "auto"
    hook_state_max_age_seconds: float = 7200
    codex_sessions_dir: str = "auto"

    @classmethod
    def load(cls, path: Path) -> "Settings":
        if not path.exists():
            return cls()
        values = json.loads(path.read_text(encoding="utf-8"))
        return cls(**{key: values[key] for key in cls.__annotations__ if key in values})


def write_light(board: serial.Serial, state: str) -> None:
    board.write((state + "\n").encode("ascii"))
    board.flush()


def run(settings: Settings, dry_run: bool = False, once: bool = False) -> int:
    board: serial.Serial | None = None
    state_dir = DEFAULT_HOOK_STATE_DIR if settings.hook_state_dir == "auto" else Path(settings.hook_state_dir)
    sessions_dir = Path.home() / ".codex" / "sessions" if settings.codex_sessions_dir == "auto" else Path(settings.codex_sessions_dir)
    transcript_tracker = TranscriptTracker(sessions_dir, settings.hook_state_max_age_seconds)
    try:
        if not dry_run:
            port = choose_serial_port(settings.serial_port)
            print(f"Arduino 串口：{port}")
            board = serial.Serial(port, settings.baud_rate, timeout=1, write_timeout=1)
            time.sleep(2.0)
        previous = ""
        while True:
            try:
                states = hook_states(state_dir, settings.hook_state_max_age_seconds)
                states.update(transcript_tracker.poll())
                state = aggregate_light(states)
            except Exception as exc:
                print(f"Codex CLI hook 状态读取失败：{exc}", file=sys.stderr)
                state = "RED"
            if state != previous:
                print(f"信号灯：{state}")
                previous = state
            if board is not None:
                write_light(board, state)
            if once:
                return 0
            time.sleep(max(0.2, settings.poll_interval_seconds))
    finally:
        if board is not None:
            try:
                write_light(board, "RED")
            finally:
                board.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex 状态 Arduino 信号灯")
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config.json")
    parser.add_argument("--dry-run", action="store_true", help="不连接 Arduino，只打印检测状态")
    parser.add_argument("--once", action="store_true", help="检测一次后退出")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return run(Settings.load(args.config), dry_run=args.dry_run, once=args.once)
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"启动失败：{exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
