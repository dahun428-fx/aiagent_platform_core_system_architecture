import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples/python"))
import conformance  # noqa: E402
import platform_ref as ref  # noqa: E402

FIXTURES = ROOT / "tests/fixtures/agents"
TRACE = conformance.TRACE


def failed(agent_dir):
    return {r["id"] for r in conformance.run(agent_dir) if not r["passed"]}


class ConformanceTests(unittest.TestCase):
    def test_templates_pass_every_check(self):
        for template in sorted((ROOT / "templates/agents").iterdir()):
            with self.subTest(template=template.name):
                self.assertEqual(failed(template), set())

    def test_builtin_agent_demo_passes(self):
        self.assertEqual(failed(ROOT / "examples/agents/agent-demo"), set())

    def test_broken_adapters_fail_the_matching_check(self):
        self.assertIn("C2", failed(FIXTURES / "bad-output"))
        self.assertIn("C8", failed(FIXTURES / "leaks-credential"))
        self.assertIn("C1", failed(FIXTURES / "bad-profile"))
        self.assertIn("C1", failed(FIXTURES / "bad-entrypoint"))

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, "scripts/agentctl.py", "conformance", "templates/agents/tool"],
                            cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
        bad = subprocess.run([sys.executable, "scripts/agentctl.py", "conformance", "tests/fixtures/agents/bad-output"],
                             cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(bad.returncode, 1)


class LocalRegistryTests(unittest.TestCase):
    def body(self):
        return ref.load("invocation")

    def test_new_agent_id_is_callable_without_core_changes(self):
        platform = ref.Platform(agents_dir=ROOT / "templates/agents")
        self.assertEqual(set(platform.agents), {"agent-demo", "my-message-agent", "my-tool-agent"})
        result = platform.invoke("my-tool-agent", self.body(), "Bearer mock-user", "k", TRACE)
        self.assertEqual(result["status"], "succeeded")
        components = [e["component"] for e in platform.audit]
        self.assertIn("tool-gateway", components)
        self.assertIn("credential-broker", components)

    def test_entrypoint_and_profile_rules(self):
        for name in ["bad-entrypoint", "bad-profile"]:
            with self.subTest(name=name), self.assertRaises(ref.AgentLoadError):
                ref.load_agent(FIXTURES / name)

    def test_entrypoint_outside_folder_is_rejected(self):
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            outer = Path(tmp)
            agent = outer / "agent"
            shutil.copytree(ROOT / "templates/agents/message", agent)
            (agent / "agent.py").unlink()
            (outer / "agent.py").write_text("def create():\n    raise SystemExit('must not load')\n", encoding="utf-8")
            try:
                (agent / "agent.py").symlink_to(outer / "agent.py")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks not permitted on this system")
            with self.assertRaises(ref.AgentLoadError):
                ref.load_agent(agent)

    def test_same_module_name_loads_independently(self):
        platform = ref.Platform(agents_dir=FIXTURES / "twins")
        a = platform.invoke("twin-a", self.body(), "Bearer mock-user", "a", TRACE)
        b = platform.invoke("twin-b", self.body(), "Bearer mock-user", "b", TRACE)
        self.assertEqual((a["output"]["content"], b["output"]["content"]), ("from-a", "from-b"))

    def test_agent_without_model_call_gets_valid_result(self):
        platform = ref.Platform(agents_dir=FIXTURES / "twins")
        result = platform.invoke("twin-a", self.body(), "Bearer mock-user", "a", TRACE)
        ref.validate("result", result)
        self.assertEqual(result["routeDecisionId"], "route-none")
        self.assertEqual(result["usage"], {"inputTokens": 0, "outputTokens": 0})

    def test_duplicate_agent_id_is_rejected(self):
        platform = ref.Platform()
        import shutil
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "agent-demo"
            shutil.copytree(ROOT / "examples/agents/agent-demo", copy)
            with self.assertRaises(ref.AgentLoadError):
                platform.register(copy)


if __name__ == "__main__":
    unittest.main()
