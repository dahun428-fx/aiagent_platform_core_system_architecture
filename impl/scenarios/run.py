"""Run every scenario in scenarios.json against a freshly started local stack and print a pass/fail table.

python impl/scenarios/run.py           table, exit code 1 if any scenario fails
python impl/scenarios/run.py --json    the same results as JSON
The automated tests (impl/tests) and the scenario page read the same scenarios.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import call_json  # noqa: E402
from stack import Stack  # noqa: E402

SCENARIOS = HERE / "scenarios.json"


def load_scenarios(path=SCENARIOS):
    return json.loads(Path(path).read_text(encoding="utf-8"))["scenarios"]


def new_traceparent():
    return "00-" + uuid.uuid4().hex + "-" + uuid.uuid4().hex[:16] + "-01"


def run_scenario(stack, scenario):
    req, expect = scenario["request"], scenario["expect"]
    call_json("POST", stack.urls["fake-model"] + "/_reset", {})
    trace = new_traceparent()
    trace_id = trace.split("-")[1]
    headers = {"Authorization": req["authorization"], "Idempotency-Key": req["idempotencyKey"] + "-" + uuid.uuid4().hex[:8],
               "traceparent": trace}
    url = stack.urls["platform-api"] + "/v1/agents/" + req["agentId"] + "/invocations"
    status, resp_headers, body = call_json("POST", url, req["body"], headers)

    checks = [("status", expect["status"], status)]
    if "outputContent" in expect:
        actual = body.get("output", {}).get("content") if isinstance(body, dict) else None
        checks.append(("output", expect["outputContent"], actual))
    for service, count in expect.get("upstreamCalls", {}).items():
        checks.append((service + " calls", count, call_json("GET", stack.urls[service] + "/_stats")[2]["calls"]))
    audit = {}
    for service, components in expect.get("auditComponents", {}).items():
        records = [r for r in call_json("GET", stack.urls[service] + "/_audit")[2] if r["traceparent"].split("-")[1] == trace_id]
        audit[service] = records
        seen = sorted({r["component"] for r in records})
        checks.append((service + " audit", sorted(components), seen))
    echoed = {k.lower(): v for k, v in resp_headers.items()}.get("traceparent")
    if status == 200:
        checks.append(("trace id echoed", trace_id, echoed.split("-")[1] if echoed else None))
    else:
        checks.append(("problem traceId", trace_id, body.get("traceId") if isinstance(body, dict) else None))

    results = [{"name": n, "expected": e, "actual": a, "passed": e == a} for n, e, a in checks]
    return {"id": scenario["id"], "title": scenario["title"], "slice": scenario.get("slice"),
            "passed": all(r["passed"] for r in results), "traceId": trace_id, "status": status,
            "checks": results, "response": body, "audit": audit}


def run_all(path=SCENARIOS):
    with Stack() as stack:
        return [run_scenario(stack, s) for s in load_scenarios(path)]


def print_table(results):
    print(f"{'결과':4} {'조각':4} {'시나리오':16} {'상태':4} trace id")
    for r in results:
        mark = "초록" if r["passed"] else "빨강"
        print(f"{mark:4} {r['slice'] or '-':4} {r['title']:16} {r['status']:<4} {r['traceId']}")
        for c in r["checks"]:
            if not c["passed"]:
                print(f"       {c['name']}: 기대 {c['expected']!r}, 실제 {c['actual']!r}")
    green = sum(r["passed"] for r in results)
    print(f"\n초록 {green}개, 빨강 {len(results) - green}개")
    for r in results:
        for service, records in r["audit"].items():
            for rec in records:
                print(f"  감사 [{r['id']}] {service}: {json.dumps(rec, ensure_ascii=False)}")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    results = run_all()
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_table(results)
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
