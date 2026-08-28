import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


HOOK_STATE = load_module("hook_state", ROOT / "src" / "hook_state.py")
INSTALLER = load_module("install_hooks", ROOT / "src" / "install_hooks.py")


class HookStateTests(unittest.TestCase):
    def test_session_transitions_and_removal(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"CODEX_TRAFFIC_LIGHT_STATE_DIR": temporary}
        ):
            data = {"session_id": "session-1", "turn_id": "turn-1"}
            path = Path(temporary) / "session-1.json"
            for state in ("working", "approval", "finished"):
                HOOK_STATE.set_state(data, state)
                value = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(value["state"], state)
            HOOK_STATE.remove_session(data)
            self.assertFalse(path.exists())

    def test_sessions_do_not_overwrite_each_other(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"CODEX_TRAFFIC_LIGHT_STATE_DIR": temporary}
        ):
            HOOK_STATE.set_state({"session_id": "one"}, "working")
            HOOK_STATE.set_state({"session_id": "two"}, "approval")
            self.assertEqual({p.name for p in Path(temporary).glob("*.json")}, {"one.json", "two.json"})


class InstallerTests(unittest.TestCase):
    def test_install_preserves_unrelated_hooks_and_installs_transitions(self):
        existing = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "existing-tool"}]}]}}
        INSTALLER.install(existing)
        stop_commands = [handler["command"] for group in existing["hooks"]["Stop"] for handler in group["hooks"]]
        self.assertIn("existing-tool", stop_commands)
        self.assertTrue(any("set-finished" in command for command in stop_commands))
        expected = {"UserPromptSubmit", "PermissionRequest", "PostToolUse", "Stop", "SessionStart", "SessionEnd"}
        self.assertTrue(expected.issubset(existing["hooks"]))


if __name__ == "__main__":
    unittest.main()
