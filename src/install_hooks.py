#!/usr/bin/env python3
"""Safely merge Codex Traffic Light lifecycle hooks into ~/.codex/hooks.json."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HOOK_SCRIPT = PROJECT_ROOT / "src" / "hook_state.py"
VENV_PYTHON = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
INSTALL_MARKER = PROJECT_ROOT / "runtime" / "hooks-installed.json"
EVENT_ACTIONS = {
    "UserPromptSubmit": "set-working",
    "PermissionRequest": "set-approval",
    "PostToolUse": "set-working",
    "Stop": "set-finished",
    "SessionStart": "set-finished",
    "SessionEnd": "remove-session",
}


def hook_command(action: str) -> str:
    return f'"{VENV_PYTHON}" "{HOOK_SCRIPT}" {action}'


def is_ours(handler: dict[str, Any]) -> bool:
    command = str(handler.get("command", ""))
    return str(HOOK_SCRIPT).lower() in command.lower()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"hooks": {}}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError("hooks.json 顶层必须是 JSON object")
    if not isinstance(value.get("hooks", {}), dict):
        raise ValueError("hooks.json 的 hooks 字段必须是 JSON object")
    value.setdefault("hooks", {})
    return value


def remove_managed(config: dict[str, Any]) -> None:
    hooks = config.setdefault("hooks", {})
    for event in list(hooks):
        groups = hooks[event]
        if not isinstance(groups, list):
            continue
        kept_groups = []
        for group in groups:
            if not isinstance(group, dict):
                kept_groups.append(group)
                continue
            handlers = group.get("hooks", [])
            if isinstance(handlers, list):
                group["hooks"] = [handler for handler in handlers if not (isinstance(handler, dict) and is_ours(handler))]
            if group.get("hooks"):
                kept_groups.append(group)
        if kept_groups:
            hooks[event] = kept_groups
        else:
            hooks.pop(event, None)


def install(config: dict[str, Any]) -> None:
    remove_managed(config)
    hooks = config.setdefault("hooks", {})
    for event, action in EVENT_ACTIONS.items():
        handler: dict[str, Any] = {
            "type": "command",
            "command": hook_command(action),
            "timeout": 5,
        }
        if event == "PermissionRequest":
            handler["statusMessage"] = "Codex is waiting for your approval"
        hooks.setdefault(event, []).append({"hooks": [handler]})


def write_atomic(path: Path, value: dict[str, Any]) -> Path | None:
    path.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    if path.exists():
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup = path.with_name(f"{path.name}.backup-{timestamp}")
        shutil.copy2(path, backup)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Codex Traffic Light CLI hooks")
    parser.add_argument("--hooks-file", type=Path, default=Path.home() / ".codex" / "hooks.json")
    parser.add_argument("--uninstall", action="store_true")
    args = parser.parse_args()

    if not VENV_PYTHON.is_file() and not args.uninstall:
        raise FileNotFoundError(f"找不到项目虚拟环境：{VENV_PYTHON}")
    config = load_config(args.hooks_file)
    if args.uninstall:
        remove_managed(config)
    else:
        install(config)
    backup = write_atomic(args.hooks_file, config)

    if args.uninstall:
        INSTALL_MARKER.unlink(missing_ok=True)
        print(f"已卸载 Codex Traffic Light hooks：{args.hooks_file}")
    else:
        INSTALL_MARKER.parent.mkdir(parents=True, exist_ok=True)
        INSTALL_MARKER.write_text(json.dumps({"hooks_file": str(args.hooks_file)}, ensure_ascii=False), encoding="utf-8")
        print(f"已安装 Codex Traffic Light hooks：{args.hooks_file}")
    if backup:
        print(f"原配置备份：{backup}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"安装失败：{exc}", file=sys.stderr)
        raise SystemExit(1)
