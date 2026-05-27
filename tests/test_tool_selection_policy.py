import copy
import json
import threading
import tempfile
import unittest
from datetime import datetime

from smarti.config import DEFAULT_SETTINGS
import smarti.core as core_module
from smarti.core import SmartiCore


def make_core():
    core = object.__new__(SmartiCore)
    core.settings = copy.deepcopy(DEFAULT_SETTINGS)
    core.audit_logger = None
    core.agent_runtime = None
    core.policy_engine = None
    core._execution_context = threading.local()
    core.mode = "openai"
    core.system_prompt = ""
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

    def test_daily_token_usage_excludes_local_memory_accounting(self):
        core = make_core()
        today = datetime.now().strftime("%Y-%m-%d")

        with tempfile.TemporaryDirectory() as tmp:
            usage_path = f"{tmp}/usage.json"
            with open(usage_path, "w", encoding="utf-8") as fp:
                json.dump({
                    today: {
                        "gemini-test": {"prompt": 100, "completion": 100, "total": 200},
                        "memory-rag/local": {"prompt": 400, "completion": 500, "total": 900},
                    }
                }, fp)
            old_usage_file = core_module.USAGE_FILE
            core_module.USAGE_FILE = usage_path
            try:
                self.assertEqual(core._daily_token_usage(today), 200)
                core.settings["budgets"]["budget_exclude_local_accounting"] = False
                self.assertEqual(core._daily_token_usage(today), 1100)
            finally:
                core_module.USAGE_FILE = old_usage_file

    def test_budget_warning_is_injected_without_mutating_messages(self):
        core = make_core()
        today = datetime.now().strftime("%Y-%m-%d")
        core.settings["budgets"]["daily_token_budget"] = 1000

        with tempfile.TemporaryDirectory() as tmp:
            usage_path = f"{tmp}/usage.json"
            with open(usage_path, "w", encoding="utf-8") as fp:
                json.dump({today: {"openai-test": {"total": 750}}}, fp)
            old_usage_file = core_module.USAGE_FILE
            core_module.USAGE_FILE = usage_path
            try:
                messages = [{"role": "user", "content": "hello"}]
                prepared = core._prepare_messages_for_budget("openai-test", messages)
            finally:
                core_module.USAGE_FILE = old_usage_file

        self.assertEqual(messages, [{"role": "user", "content": "hello"}])
        self.assertEqual(prepared[0]["role"], "system")
        self.assertIn("SMARTI_DAILY_TOKEN_BUDGET_WARNING", prepared[0]["content"])
        self.assertEqual(prepared[1], messages[0])

    def test_simple_direct_response_skips_final_verifier(self):
        core = make_core()
        task_state = core._base_task_state("hello", planner_enabled=False)

        self.assertFalse(core._should_run_final_verifier_for_task(task_state, "x" * 300, {}, 1))

    def test_tool_backed_response_runs_final_verifier(self):
        core = make_core()
        task_state = core._base_task_state("read this file", planner_enabled=False)

        self.assertTrue(core._should_run_final_verifier_for_task(task_state, "done", {"file_manager": 1}, 1))


if __name__ == "__main__":
    unittest.main()
