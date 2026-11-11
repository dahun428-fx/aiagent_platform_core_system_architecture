"""scenarios.json 의 시나리오를 새로 띄운 로컬 스택에 모두 실행하고, 통과·실패 표를 출력한다.

python impl/scenarios/run.py           표 출력. 하나라도 실패하면 종료 코드 1
python impl/scenarios/run.py --json    같은 결과를 JSON으로 출력
자동 테스트(impl/tests)와 시나리오 화면(impl/demo)도 같은 scenarios.json 과 이 파일의 함수를 쓴다.
"""
from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from common import SIGNATURE_HEADER, call_json, load_ref, sign  # noqa: E402
from stack import Stack  # noqa: E402

SCENARIOS = HERE / "scenarios.json"


# 시나리오 정의 목록을 읽는다.
def load_scenarios(path=SCENARIOS):
    return json.loads(Path(path).read_text(encoding="utf-8"))["scenarios"]


# W3C traceparent 를 새로 만든다: 00-<trace id 32자리>-<span id 16자리>-01
def new_traceparent():
    return "00-" + uuid.uuid4().hex + "-" + uuid.uuid4().hex[:16] + "-01"


# 앱처럼 Platform APIs에 Agent 호출을 보낸다.
def call_platform(stack, req, trace):
    # Idempotency-Key 뒤에 무작위 값을 붙여서, 다시 실행해도 이전 결과(멱등성 캐시)가 돌아오지 않게 한다.
    headers = {"Authorization": req["authorization"], "Idempotency-Key": req["idempotencyKey"] + "-" + uuid.uuid4().hex[:8],
               "traceparent": trace}
    url = stack.urls["platform-api"] + "/v1/agents/" + req["agentId"] + "/invocations"
    return call_json("POST", url, req["body"], headers)


# Platform을 건너뛰고 모델 경로에 직접 model-request를 보낸다. 내부 구간에 끼어든 호출자를 흉내 낸다.
# identity·policy는 예제 fixture에 시나리오의 값을 덮어써서 만든다.
# sign: true면 스택의 키로 서명하고(기본), false면 서명을 빼며, afterSigning 의 값은 서명한 뒤에 본문에 덮어쓴다(변조).
def call_model_route(stack, req, trace):
    ref = load_ref()
    body = {"capability": "chat", "messages": [{"role": "user", "content": "hello"}],
            "identity": {**ref.load("identity"), **req.get("identity", {})},
            "policy": {**ref.load("policy"), **req.get("policy", {})}, "traceparent": trace}
    headers = {"Idempotency-Key": "scenario-" + uuid.uuid4().hex, "traceparent": trace}
    if req.get("sign", True):
        headers[SIGNATURE_HEADER] = sign(stack.internal_key, body)
    for part, values in req.get("afterSigning", {}).items():
        body[part] = {**body[part], **values}
    return call_json("POST", stack.urls["model-route"] + "/v1/model-invocations", body, headers)


# 서비스의 감사 기록 중 이번 trace id로 남은 것만 돌려준다. 다른 요청의 기록과 섞이지 않게 한다.
def trace_records(stack, service, trace_id):
    return [r for r in call_json("GET", stack.urls[service] + "/_audit")[2] if r["traceparent"].split("-")[1] == trace_id]


# 시나리오 하나를 실행하고, 기대값과 실제값을 항목별로 비교한 결과를 돌려준다.
def run_scenario(stack, scenario):
    req, expect = scenario["request"], scenario["expect"]
    # 가짜 모델의 호출 횟수를 0으로 맞춰서, 이번 요청이 부른 횟수만 세게 한다.
    call_json("POST", stack.urls["fake-model"] + "/_reset", {})
    trace = new_traceparent()
    trace_id = trace.split("-")[1]
    # target 이 model-route 면 모델 경로에 직접, 아니면 Platform APIs로 보낸다.
    send = call_model_route if req.get("target") == "model-route" else call_platform
    status, resp_headers, body = send(stack, req, trace)

    # 판정 항목을 (이름, 기대값, 실제값)으로 모은다.
    checks = [("status", expect["status"], status)]
    if "outputContent" in expect:
        actual = body.get("output", {}).get("content") if isinstance(body, dict) else None
        checks.append(("output", expect["outputContent"], actual))
    # 응답 본문의 최상위 필드(예: 오류 code, routeDecisionId)
    for field, value in expect.get("body", {}).items():
        checks.append((field, value, body.get(field) if isinstance(body, dict) else None))
    # 서비스별 upstream 호출 횟수
    for service, count in expect.get("upstreamCalls", {}).items():
        checks.append((service + " calls", count, call_json("GET", stack.urls[service] + "/_stats")[2]["calls"]))
    # 서비스별 감사 기록: 이번 trace id로 남은 것만 골라서, 어떤 컴포넌트가 기록했는지 비교한다.
    audit = {}
    for service, components in expect.get("auditComponents", {}).items():
        records = audit[service] = trace_records(stack, service, trace_id)
        seen = sorted({r["component"] for r in records})
        checks.append((service + " audit", sorted(components), seen))
    # 감사 기록의 특정 필드 값(예: 라우팅에 쓰인 classification). 이번 trace id의 기록에서 나온 값들을 모아 비교한다.
    for service, fields in expect.get("auditFields", {}).items():
        records = trace_records(stack, service, trace_id)
        for field, value in fields.items():
            checks.append((f"{service} audit {field}", [value], sorted({r[field] for r in records if field in r})))
    # trace id가 끝까지 이어졌는지: 성공이면 응답 헤더, 실패면 Problem 본문의 traceId로 확인한다.
    echoed = {k.lower(): v for k, v in resp_headers.items()}.get("traceparent")
    if status == 200:
        checks.append(("trace id echoed", trace_id, echoed.split("-")[1] if echoed else None))
    else:
        checks.append(("problem traceId", trace_id, body.get("traceId") if isinstance(body, dict) else None))

    results = [{"name": n, "expected": e, "actual": a, "passed": e == a} for n, e, a in checks]
    return {"id": scenario["id"], "title": scenario["title"], "slice": scenario.get("slice"),
            "passed": all(r["passed"] for r in results), "traceId": trace_id, "status": status,
            "checks": results, "response": body, "audit": audit}


# 스택을 새로 띄워 모든 시나리오를 실행하고, 끝나면 스택을 끈다.
def run_all(path=SCENARIOS):
    with Stack() as stack:
        return [run_scenario(stack, s) for s in load_scenarios(path)]


# 터미널용 표: 시나리오마다 한 줄, 틀린 항목은 기대·실제를 덧붙이고, 마지막에 초록·빨강 개수와 감사 기록을 출력한다.
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


# make scenarios 의 진입점. Windows 터미널에서도 한글이 깨지지 않게 출력을 UTF-8로 맞춘다.
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
