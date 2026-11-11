"""impl/scenarios/scenarios.json 의 모든 시나리오가 실제 멀티 프로세스 스택에서 통과해야 한다."""
import sys
import unittest
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))
sys.path.insert(0, str(IMPL / "scenarios"))

from common import SIGNATURE_HEADER, call_json, load_ref, sign  # noqa: E402
import run  # noqa: E402
from stack import Stack  # noqa: E402


class ScenarioTests(unittest.TestCase):
    # 테스트 클래스 전체에서 스택을 한 번만 띄우고 끝나면 끈다.
    @classmethod
    def setUpClass(cls):
        cls.stack = Stack().__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.stack.close()

    # scenarios.json 의 시나리오마다 모든 판정 항목이 일치해야 한다.
    def test_all_scenarios_pass(self):
        for scenario in run.load_scenarios():
            with self.subTest(scenario["id"]):
                result = run.run_scenario(self.stack, scenario)
                failed = [c for c in result["checks"] if not c["passed"]]
                self.assertEqual(failed, [], scenario["title"])

    # 모델 경로에 Idempotency-Key 없이 보내면 422 Problem이고, 요청의 trace id가 그대로 담겨야 한다.
    def test_model_route_rejects_missing_idempotency_key(self):
        ref = load_ref()
        trace = run.new_traceparent()
        body = {"capability": "chat", "messages": [{"role": "user", "content": "hi"}],
                "identity": ref.load("identity"), "policy": ref.load("policy"), "traceparent": trace}
        # 서명은 맞게 붙여서, 서명 검사가 아니라 키 검사에서 걸리는지 본다.
        status, _, problem = call_json("POST", self.stack.urls["model-route"] + "/v1/model-invocations", body,
                                       {"traceparent": trace, SIGNATURE_HEADER: sign(self.stack.internal_key, body)})
        self.assertEqual(status, 422)
        ref.validate("problem", problem)
        self.assertEqual(problem["traceId"], trace.split("-")[1])

    # 계약에 맞지 않는 본문은 422 VALIDATION_ERROR.
    def test_model_route_validates_contract(self):
        body = {"capability": "chat"}
        status, _, problem = call_json("POST", self.stack.urls["model-route"] + "/v1/model-invocations", body,
                                       {"Idempotency-Key": "k", SIGNATURE_HEADER: sign(self.stack.internal_key, body)})
        self.assertEqual(status, 422)
        self.assertEqual(problem["code"], "VALIDATION_ERROR")

    # 모델 경로 서비스에 연결이 안 되면 Platform은 503으로 알린다.
    def test_platform_reports_unreachable_gateway_as_503(self):
        import platform_api
        route = platform_api.HttpModelRoute("http://127.0.0.1:9", "test-key")
        ref = load_ref()
        with self.assertRaises(ref.Fault) as caught:
            route.invoke("hi", ref.load("identity"), ref.load("policy"), run.new_traceparent())
        self.assertEqual(caught.exception.status, 503)

    # 모델 경로가 422를 주거나 계약에 안 맞는 200을 줘도, 앱에는 4xx가 아닌 503으로 알린다.
    def test_platform_reports_bad_gateway_answers_as_503(self):
        import threading
        import platform_api
        from common import JsonHandler, serve
        ref = load_ref()
        answers = [(422, {"code": "VALIDATION_ERROR", "detail": "x"}), (200, {"content": "no provider field"})]

        # 미리 정해 둔 잘못된 응답을 차례로 돌려주는 가짜 모델 경로
        class BadRoute(JsonHandler):
            def do_POST(self):
                self.read_json()
                self.send_json(*answers.pop(0))

        server = serve(BadRoute, 0)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        route = platform_api.HttpModelRoute(f"http://127.0.0.1:{server.server_address[1]}", "test-key")
        for case in ("route 422", "invalid 200 result"):
            with self.subTest(case), self.assertRaises(ref.Fault) as caught:
                route.invoke("hi", ref.load("identity"), ref.load("policy"), run.new_traceparent())
            self.assertEqual((caught.exception.status, caught.exception.code), (503, "UPSTREAM_UNAVAILABLE"))


if __name__ == "__main__":
    unittest.main()
