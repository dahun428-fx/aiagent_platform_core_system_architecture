"""시나리오 화면 서버가 화면을 제공하고, 공유 시나리오를 실제 스택에 실행하는지 확인한다."""
import sys
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL))
sys.path.insert(0, str(IMPL / "demo"))
sys.path.insert(0, str(IMPL / "scenarios"))

from common import call_json  # noqa: E402
import run  # noqa: E402
import server as demo  # noqa: E402
from stack import Stack  # noqa: E402


class DemoServerTests(unittest.TestCase):
    # 스택과 화면 서버를 한 번만 띄운다. 화면 서버는 빈 포트(0)로 띄워 다른 실행과 충돌하지 않게 한다.
    @classmethod
    def setUpClass(cls):
        cls.stack = Stack().__enter__()
        cls.server = demo.make_server(cls.stack, port=0)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.url = f"http://127.0.0.1:{cls.server.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.stack.close()

    # / 가 HTML 화면을 돌려준다.
    def test_page_is_served(self):
        with urlopen(self.url + "/", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers["Content-Type"])
            self.assertIn("/api/run", resp.read().decode("utf-8"))

    # /api/scenarios 가 scenarios.json 과 같은 목록, 서비스 세 개의 주소를 돌려준다.
    def test_scenarios_and_services_listed(self):
        status, _, data = call_json("GET", self.url + "/api/scenarios")
        self.assertEqual(status, 200)
        self.assertEqual([s["id"] for s in data["scenarios"]], [s["id"] for s in run.load_scenarios()])
        self.assertEqual(set(data["services"]), {"fake-model", "fake-tool", "model-route", "tool-route", "platform-api"})

    # /api/run 으로 전부 실행하면 모두 초록이어야 한다.
    def test_run_all_is_green(self):
        status, _, data = call_json("POST", self.url + "/api/run", {}, timeout=30)
        self.assertEqual(status, 200)
        self.assertEqual(len(data["results"]), len(run.load_scenarios()))
        for result in data["results"]:
            with self.subTest(result["id"]):
                self.assertTrue(result["passed"], [c for c in result["checks"] if not c["passed"]])

    # id 하나만 실행할 수 있고, 없는 id 는 404.
    def test_run_one_and_unknown(self):
        first = run.load_scenarios()[0]["id"]
        status, _, data = call_json("POST", self.url + "/api/run", {"id": first}, timeout=30)
        self.assertEqual((status, [r["id"] for r in data["results"]]), (200, [first]))
        status, _, _ = call_json("POST", self.url + "/api/run", {"id": "no-such-scenario"})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
