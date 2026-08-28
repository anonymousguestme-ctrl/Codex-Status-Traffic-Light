#!/usr/bin/env python3
"""Drive an Arduino traffic light from the local Codex app-server status."""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import serial
from serial.tools import list_ports


DEFAULT_CODEX_PATH = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/OpenAI/Codex/bin/codex.exe"


def active_flags(thread: dict[str, Any]) -> set[str]:
    """Return active flags across current and older protocol shapes."""
    status = thread.get("status", {})
    if isinstance(status, str):
        return {status}
    if not isinstance(status, dict):
        return set()
    flags = status.get("activeFlags", status.get("active_flags", []))
    if isinstance(flags, str):
        return {flags}
    return {str(flag) for flag in flags} if isinstance(flags, list) else set()


def requires_attention(threads: list[dict[str, Any]], include_user_input: bool = False) -> bool:
    wanted = {"waitingOnApproval"}
    if include_user_input:
        wanted.add("waitingOnUserInput")
    return any(active_flags(thread) & wanted for thread in threads)


def find_codex(configured: str) -> str:
    if configured != "auto":
        return configured
    discovered = shutil.which("codex")
    if discovered:
        return discovered
    if DEFAULT_CODEX_PATH.is_file():
        return str(DEFAULT_CODEX_PATH)
    raise FileNotFoundError("找不到 codex.exe；请在 config.json 中设置 codex_executable")


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


class JsonRpcClient:
    def __init__(self, codex_executable: str) -> None:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.process = subprocess.Popen(
            [codex_executable, "app-server", "proxy"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            bufsize=1,
            creationflags=creationflags,
        )
        self.responses: queue.Queue[dict[str, Any]] = queue.Queue()
        self.next_id = 1
        self.reader = threading.Thread(target=self._read_stdout, daemon=True)
        self.reader.start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in message:
                self.responses.put(message)

    def send(self, method: str, params: dict[str, Any], timeout: float = 5.0) -> Any:
        request_id = self.next_id
        self.next_id += 1
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + timeout
        deferred: list[dict[str, Any]] = []
        try:
            while time.monotonic() < deadline:
                response = self.responses.get(timeout=max(0.05, deadline - time.monotonic()))
                if response.get("id") != request_id:
                    deferred.append(response)
                    continue
                if "error" in response:
                    raise RuntimeError(f"Codex RPC 错误：{response['error']}")
                return response.get("result")
        except queue.Empty as exc:
            raise TimeoutError(f"等待 Codex RPC {method} 超时") from exc
        finally:
            for response in deferred:
                self.responses.put(response)
        raise TimeoutError(f"等待 Codex RPC {method} 超时")

    def initialize(self) -> None:
        self.send(
            "initialize",
            {
                "clientInfo": {"name": "codex-traffic-light", "title": "Codex Traffic Light", "version": "1.0.0"},
                "capabilities": {"experimentalApi": True},
            },
        )
        assert self.process.stdin is not None
        notification = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
        self.process.stdin.write(json.dumps(notification, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def list_threads(self) -> list[dict[str, Any]]:
        result = self.send(
            "thread/list",
            {
                "archived": False,
                "limit": 100,
                "sortKey": "updated_at",
                "sortDirection": "desc",
                "useStateDbOnly": True,
                "sourceKinds": [],
            },
        )
        data = result.get("data", []) if isinstance(result, dict) else []
        return data if isinstance(data, list) else []

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()


@dataclass
class Settings:
    serial_port: str = "auto"
    baud_rate: int = 115200
    poll_interval_seconds: float = 0.75
    codex_executable: str = "auto"
    include_waiting_on_user_input: bool = False

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
    codex = find_codex(settings.codex_executable)
    rpc = JsonRpcClient(codex)
    board: serial.Serial | None = None
    try:
        rpc.initialize()
        if not dry_run:
            port = choose_serial_port(settings.serial_port)
            print(f"Arduino 串口：{port}")
            board = serial.Serial(port, settings.baud_rate, timeout=1, write_timeout=1)
            time.sleep(2.0)  # Uno resets when the serial port is opened.

        previous = ""
        while True:
            try:
                threads = rpc.list_threads()
                state = "RED" if requires_attention(threads, settings.include_waiting_on_user_input) else "GREEN"
            except Exception as exc:  # Keep the physical warning state visible on transient errors.
                print(f"Codex 状态读取失败：{exc}", file=sys.stderr)
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
        rpc.close()


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
