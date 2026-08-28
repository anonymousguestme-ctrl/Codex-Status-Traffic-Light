import importlib.util
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
    def test_cli_hook_marker_is_red(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary) / "runtime" / "approvals"
            state_dir.mkdir(parents=True)
            (state_dir.parent / "hooks-installed.json").write_text("{}", encoding="utf-8")
            (state_dir / "session__turn.json").write_text('{"session_id":"session"}', encoding="utf-8")
            self.assertTrue(MODULE.hook_requires_attention(state_dir, 7200))

    def test_cli_hook_without_pending_marker_is_green(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary) / "runtime" / "approvals"
            (state_dir.parent).mkdir(parents=True)
            (state_dir.parent / "hooks-installed.json").write_text("{}", encoding="utf-8")
            self.assertFalse(MODULE.hook_requires_attention(state_dir, 7200))

    def test_stale_hook_marker_is_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            state_dir = Path(temporary) / "runtime" / "approvals"
            state_dir.mkdir(parents=True)
            (state_dir.parent / "hooks-installed.json").write_text("{}", encoding="utf-8")
            marker = state_dir / "session__turn.json"
            marker.write_text("{}", encoding="utf-8")
            self.assertFalse(MODULE.hook_requires_attention(state_dir, 10, now=time.time() + 20))
            self.assertFalse(marker.exists())

    def test_missing_hook_installation_is_yellow_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(RuntimeError):
                MODULE.hook_requires_attention(Path(temporary) / "approvals", 7200)


if __name__ == "__main__":
    unittest.main()
