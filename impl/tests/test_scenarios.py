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

    # 모델 경로가 422를 주거나 계약에 안 맞는 200을 줘도, 앱에는 4xx가 아닌 502로 알린다.
    def test_platform_reports_bad_gateway_answers_as_502(self):
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
            self.assertEqual((caught.exception.status, caught.exception.code), (502, "UPSTREAM_ERROR"))

    # Request-Timeout-Ms가 1 이상의 정수가 아니면 모델 경로는 422로 거부한다(계약 0.2.0).
    def test_model_route_rejects_bad_timeout_header(self):
        ref = load_ref()
        body = {"capability": "chat", "messages": [{"role": "user", "content": "hi"}],
                "identity": ref.load("identity"), "policy": ref.load("policy"), "traceparent": run.new_traceparent()}
        for value in ("0", "-5", "1.5", "soon"):
            with self.subTest(value):
                status, _, problem = call_json("POST", self.stack.urls["model-route"] + "/v1/model-invocations", body,
                                               {"Idempotency-Key": "k", "Request-Timeout-Ms": value,
                                                SIGNATURE_HEADER: sign(self.stack.internal_key, body)})
                self.assertEqual((status, problem["code"]), (422, "VALIDATION_ERROR"))

    # 모델 경로 자체가 답하지 않아도 Platform은 deadline에 맞춰 504로 끝낸다(연결만 받고 아무 말도 하지 않는 서버).
    def test_platform_times_out_silent_gateway(self):
        import socket
        import time
        import platform_api
        ref = load_ref()
        silent = socket.create_server(("127.0.0.1", 0))
        self.addCleanup(silent.close)
        route = platform_api.HttpModelRoute(f"http://127.0.0.1:{silent.getsockname()[1]}", "test-key")
        platform_api.current.deadline = time.monotonic() + 0.2
        self.addCleanup(setattr, platform_api.current, "deadline", None)
        started = time.monotonic()
        with self.assertRaises(ref.Fault) as caught:
            route.invoke("hi", ref.load("identity"), ref.load("policy"), run.new_traceparent())
        self.assertEqual((caught.exception.status, caught.exception.code), (504, "UPSTREAM_TIMEOUT"))
        self.assertLess(time.monotonic() - started, 1.0)

    # upstream에 연결조차 안 되면 모델 경로는 3번 시도한 뒤 503을 주고, 오류에 upstream 주소를 넣지 않는다.
    # Windows는 닫힌 포트에 연결을 거부당하기까지 시도마다 약 2초를 다시 시도하므로 deadline을 넉넉히 준다.
    def test_model_route_hides_unreachable_upstream_address(self):
        import json
        from gateway import model_route
        ref = load_ref()
        route = model_route.ModelRoute("http://127.0.0.1:9", "test-key")
        with self.assertRaises(ref.Fault) as caught:
            route.call_upstream([{"role": "user", "content": "hi"}], "self-hosted", run.new_traceparent(),
                                model_route.time.monotonic() + 15)
        self.assertEqual((caught.exception.status, caught.exception.code), (503, "UPSTREAM_UNAVAILABLE"))
        self.assertNotIn("127.0.0.1", json.dumps(caught.exception.problem()))

    # circuit: 연속 실패 3번에 열리고, 대기 시간 뒤 시험 호출 1번만 통과시키며, 시험이 실패하면 바로 다시 열린다.
    def test_circuit_breaker_reopens_when_trial_fails(self):
        from unittest import mock
        from gateway import model_route
        ref = load_ref()
        breaker = model_route.CircuitBreaker()
        with mock.patch.object(model_route, "BREAKER_COOLDOWN_S", 0.05):
            for _ in range(3):
                breaker.before_call()
                breaker.after_call(ok=False)
            with self.assertRaises(ref.Fault) as caught:  # 열림: 바로 503
                breaker.before_call()
            self.assertEqual((caught.exception.status, caught.exception.retry_after), (503, 1))
            # 쉬는 대신 열린 시각을 cooldown만큼 앞으로 당긴다. Windows는 시계 단위가 약 15ms라 짧은 sleep 뒤에도 시간이 덜 흐른 것으로 보일 수 있다.
            breaker.opened_at -= 0.06
            breaker.before_call()  # 반열림: 시험 호출 하나는 통과
            with self.assertRaises(ref.Fault):  # 시험 중에는 다른 호출을 막는다
                breaker.before_call()
            breaker.after_call(ok=False)  # 시험 실패 → 다시 열림
            with self.assertRaises(ref.Fault):
                breaker.before_call()


if __name__ == "__main__":
    unittest.main()
