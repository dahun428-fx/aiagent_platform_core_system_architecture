"""Every scenario in impl/scenarios/scenarios.json must pass against the real multi-process stack."""
import sys
import unittest
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))
sys.path.insert(0, str(IMPL / "scenarios"))

from common import call_json, load_ref  # noqa: E402
import run  # noqa: E402
from stack import Stack  # noqa: E402


class ScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.stack = Stack().__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.stack.close()

    def test_all_scenarios_pass(self):
        for scenario in run.load_scenarios():
            with self.subTest(scenario["id"]):
                result = run.run_scenario(self.stack, scenario)
                failed = [c for c in result["checks"] if not c["passed"]]
                self.assertEqual(failed, [], scenario["title"])

    def test_model_route_rejects_missing_idempotency_key(self):
        ref = load_ref()
        trace = run.new_traceparent()
        body = {"capability": "chat", "messages": [{"role": "user", "content": "hi"}],
                "identity": ref.load("identity"), "policy": ref.load("policy"), "traceparent": trace}
        status, _, problem = call_json("POST", self.stack.urls["model-route"] + "/v1/model-invocations", body,
                                       {"traceparent": trace})
        self.assertEqual(status, 422)
        ref.validate("problem", problem)
        self.assertEqual(problem["traceId"], trace.split("-")[1])

    def test_model_route_validates_contract(self):
        status, _, problem = call_json("POST", self.stack.urls["model-route"] + "/v1/model-invocations",
                                       {"capability": "chat"}, {"Idempotency-Key": "k"})
        self.assertEqual(status, 422)
        self.assertEqual(problem["code"], "VALIDATION_ERROR")

    def test_platform_reports_unreachable_gateway_as_503(self):
        sys.path.insert(0, str(IMPL))
        import platform_api
        route = platform_api.HttpModelRoute("http://127.0.0.1:9")
        ref = load_ref()
        with self.assertRaises(ref.Fault) as caught:
            route.invoke("hi", ref.load("identity"), ref.load("policy"), run.new_traceparent())
        self.assertEqual(caught.exception.status, 503)


if __name__ == "__main__":
    unittest.main()
