import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "codex_traffic_light.py"
SPEC = importlib.util.spec_from_file_location("codex_traffic_light", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class StateTests(unittest.TestCase):
    def make_state_dir(self, temporary):
        state_dir = Path(temporary) / "runtime" / "sessions"
        state_dir.mkdir(parents=True)
        (state_dir.parent / "hooks-installed.json").write_text("{}", encoding="utf-8")
        return state_dir

    def write_state(self, state_dir, name, state):
        (state_dir / f"{name}.json").write_text(json.dumps({"state": state}), encoding="utf-8")

    def test_working_is_green(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = self.make_state_dir(temporary)
            self.write_state(state_dir, "one", "working")
            self.assertEqual(MODULE.hook_light_state(state_dir, 7200), "GREEN")

    def test_approval_is_yellow_and_has_priority(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = self.make_state_dir(temporary)
            self.write_state(state_dir, "one", "working")
            self.write_state(state_dir, "two", "approval")
            self.assertEqual(MODULE.hook_light_state(state_dir, 7200), "YELLOW")

    def test_finished_or_no_session_is_red(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = self.make_state_dir(temporary)
            self.assertEqual(MODULE.hook_light_state(state_dir, 7200), "RED")
            self.write_state(state_dir, "one", "finished")
            self.assertEqual(MODULE.hook_light_state(state_dir, 7200), "RED")

    def test_stale_state_is_removed_and_red(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = self.make_state_dir(temporary)
            self.write_state(state_dir, "one", "working")
            marker = state_dir / "one.json"
            self.assertEqual(MODULE.hook_light_state(state_dir, 10, now=time.time() + 20), "RED")
            self.assertFalse(marker.exists())

    def test_missing_hook_installation_is_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                MODULE.hook_light_state(Path(temporary) / "sessions", 7200)


if __name__ == "__main__":
    unittest.main()
