import copy
import threading
import unittest

from smarti.config import DEFAULT_SETTINGS
from smarti.core import SmartiCore


def make_core():
    core = object.__new__(SmartiCore)
    core.settings = copy.deepcopy(DEFAULT_SETTINGS)
    core.audit_logger = None
    core.agent_runtime = None
    core.policy_engine = None
    core._execution_context = threading.local()
    return core


class ToolSelectionPolicyTests(unittest.TestCase):
    def test_project_check_accepts_known_test_build_commands(self):
        core = make_core()

        self.assertTrue(core._project_check_command_allowed("pytest -q"))
        self.assertTrue(core._project_check_command_allowed("python -m pytest tests"))
        self.assertTrue(core._project_check_command_allowed("npm run build"))
        self.assertTrue(core._project_check_command_allowed("pnpm lint"))

    def test_project_check_rejects_shell_control_operators(self):
        core = make_core()

        self.assertFalse(core._project_check_command_allowed("pytest > out.txt"))
        self.assertFalse(core._project_check_command_allowed("pytest | tee out.txt"))
        self.assertFalse(core._project_check_command_allowed("npm run build && del out.txt"))

    def test_project_check_rejects_non_project_commands(self):
        core = make_core()

        self.assertFalse(core._project_check_command_allowed("pip install requests"))
        self.assertFalse(core._project_check_command_allowed("git status"))

    def test_subprocess_env_forces_utf8_python_io(self):
        core = make_core()

        env = core._subprocess_env({})

        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(env["PYTHONUTF8"], "1")

    def test_mcp_env_forces_utf8_python_io(self):
        core = make_core()

        env = core._mcp_env()

        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")
        self.assertEqual(env["PYTHONUTF8"], "1")


if __name__ == "__main__":
    unittest.main()
