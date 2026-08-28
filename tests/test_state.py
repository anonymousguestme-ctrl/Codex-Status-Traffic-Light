import importlib.util
from pathlib import Path
import sys
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "codex_traffic_light.py"
SPEC = importlib.util.spec_from_file_location("codex_traffic_light", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class StateTests(unittest.TestCase):
    def test_waiting_on_approval_is_red(self):
        threads = [{"status": {"activeFlags": ["waitingOnApproval"]}}]
        self.assertTrue(MODULE.requires_attention(threads))

    def test_idle_is_green(self):
        threads = [{"status": {"activeFlags": []}}]
        self.assertFalse(MODULE.requires_attention(threads))

    def test_user_input_is_optional(self):
        threads = [{"status": {"activeFlags": ["waitingOnUserInput"]}}]
        self.assertFalse(MODULE.requires_attention(threads))
        self.assertTrue(MODULE.requires_attention(threads, include_user_input=True))


if __name__ == "__main__":
    unittest.main()
