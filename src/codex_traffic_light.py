#!/usr/bin/env python3
"""Drive an Arduino traffic light from Codex CLI PermissionRequest hook state."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import serial
from serial.tools import list_ports


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOOK_STATE_DIR = PROJECT_ROOT / "runtime" / "approvals"


def hook_requires_attention(
    state_dir: Path,
    max_age_seconds: float,
    now: float | None = None,
) -> bool:
    """Return whether a Codex CLI PermissionRequest hook is currently pending."""
    install_marker = state_dir.parent / "hooks-installed.json"
    if not install_marker.is_file():
        raise RuntimeError("Codex CLI hooks 尚未安装；请先运行 .\\install-hooks.ps1")

    current_time = time.time() if now is None else now
    pending = False
    state_dir.mkdir(parents=True, exist_ok=True)
    for marker in state_dir.glob("*.json"):
        try:
            age = current_time - marker.stat().st_mtime
            if age > max_age_seconds:
                marker.unlink(missing_ok=True)
                continue
            json.loads(marker.read_text(encoding="utf-8"))
            pending = True
        except (OSError, json.JSONDecodeError):
            marker.unlink(missing_ok=True)
    return pending


def choose_serial_port(configured: str) -> str:
    if configured != "auto":
        return configured
    ports = list(list_ports.comports())
    if not ports:
        raise RuntimeError("没有发现串口。请插入 Arduino，或在 config.json 中填写 COM 端口")

    preferred_tokens = ("arduino", "ch340", "wch", "usb serial", "cp210")
    preferred = [p for p in ports if any(t in (p.description or "").lower() for t in preferred_tokens)]
    candidates = preferred or ports
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

    @classmethod
    def load(cls, path: Path) -> "Settings":
        if not path.exists():
            return cls()
        values = json.loads(path.read_text(encoding="utf-8"))
        known = {key: values[key] for key in cls.__annotations__ if key in values}
        return cls(**known)


def write_light(board: serial.Serial, state: str) -> None:
    board.write((state + "\n").encode("ascii"))
    board.flush()


def run(settings: Settings, dry_run: bool = False, once: bool = False) -> int:
    board: serial.Serial | None = None
    state_dir = DEFAULT_HOOK_STATE_DIR if settings.hook_state_dir == "auto" else Path(settings.hook_state_dir)
    try:
        if not dry_run:
            port = choose_serial_port(settings.serial_port)
            print(f"Arduino 串口：{port}")
            board = serial.Serial(port, settings.baud_rate, timeout=1, write_timeout=1)
            time.sleep(2.0)  # Uno resets when the serial port is opened.

        previous = ""
        while True:
            try:
                state = "RED" if hook_requires_attention(
                    state_dir,
                    settings.hook_state_max_age_seconds,
                ) else "GREEN"
            except Exception as exc:  # Keep the physical warning state visible on transient errors.
                print(f"Codex CLI hook 状态读取失败：{exc}", file=sys.stderr)
                state = "YELLOW"

            if state != previous:
                print(f"信号灯：{state}")
                previous = state
            if board is not None:
                write_light(board, state)  # Also acts as the firmware heartbeat.
            if once:
                return 0
            time.sleep(max(0.2, settings.poll_interval_seconds))
    finally:
        if board is not None:
            try:
                write_light(board, "YELLOW")
            finally:
                board.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex 审批状态 Arduino 信号灯")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parents[1] / "config.json")
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
