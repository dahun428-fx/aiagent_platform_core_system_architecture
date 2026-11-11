"""The scenario page server serves the page and runs the shared scenarios against the real stack."""
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

    def test_page_is_served(self):
        with urlopen(self.url + "/", timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("text/html", resp.headers["Content-Type"])
            self.assertIn("/api/run", resp.read().decode("utf-8"))

    def test_scenarios_and_services_listed(self):
        status, _, data = call_json("GET", self.url + "/api/scenarios")
        self.assertEqual(status, 200)
        self.assertEqual([s["id"] for s in data["scenarios"]], [s["id"] for s in run.load_scenarios()])
        self.assertEqual(set(data["services"]), {"fake-model", "model-route", "platform-api"})

    def test_run_all_is_green(self):
        status, _, data = call_json("POST", self.url + "/api/run", {}, timeout=30)
        self.assertEqual(status, 200)
        self.assertEqual(len(data["results"]), len(run.load_scenarios()))
        for result in data["results"]:
            with self.subTest(result["id"]):
                self.assertTrue(result["passed"], [c for c in result["checks"] if not c["passed"]])

    def test_run_one_and_unknown(self):
        first = run.load_scenarios()[0]["id"]
        status, _, data = call_json("POST", self.url + "/api/run", {"id": first}, timeout=30)
        self.assertEqual((status, [r["id"] for r in data["results"]]), (200, [first]))
        status, _, _ = call_json("POST", self.url + "/api/run", {"id": "no-such-scenario"})
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()
