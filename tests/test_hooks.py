import importlib.util
import io
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
    def test_mark_and_clear_turn(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"CODEX_TRAFFIC_LIGHT_STATE_DIR": temporary}
        ):
            data = {"session_id": "session-1", "turn_id": "turn-1"}
            HOOK_STATE.mark(data)
            markers = list(Path(temporary).glob("*.json"))
            self.assertEqual(len(markers), 1)
            value = json.loads(markers[0].read_text(encoding="utf-8"))
            self.assertEqual(value["hook_event_name"], "PermissionRequest")
            HOOK_STATE.clear_turn(data)
            self.assertEqual(list(Path(temporary).glob("*.json")), [])

    def test_clear_session_keeps_other_sessions(self):
        with tempfile.TemporaryDirectory() as temporary, patch.dict(
            os.environ, {"CODEX_TRAFFIC_LIGHT_STATE_DIR": temporary}
        ):
            HOOK_STATE.mark({"session_id": "one", "turn_id": "a"})
            HOOK_STATE.mark({"session_id": "two", "turn_id": "b"})
            HOOK_STATE.clear_session({"session_id": "one"})
            names = [path.name for path in Path(temporary).glob("*.json")]
            self.assertEqual(names, ["two__b.json"])


class InstallerTests(unittest.TestCase):
    def test_install_preserves_unrelated_hooks(self):
        existing = {
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "existing-tool"}]}]
            }
        }
        INSTALLER.install(existing)
        stop_commands = [
            handler["command"]
            for group in existing["hooks"]["Stop"]
            for handler in group["hooks"]
        ]
        self.assertIn("existing-tool", stop_commands)
        self.assertTrue(any("hook_state.py" in command for command in stop_commands))
        self.assertIn("PermissionRequest", existing["hooks"])


if __name__ == "__main__":
    unittest.main()
