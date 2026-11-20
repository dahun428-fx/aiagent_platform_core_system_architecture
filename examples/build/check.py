"""단계마다 같은 검사를 돌려 조각이 얼마나 붙었는지 보여 줍니다.

    python examples/build/check.py step0
"""
import importlib
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
step = HERE / sys.argv[1]
sys.path[:0] = [str(step), str(HERE)]
import world  # noqa: E402

agent = importlib.import_module("agent")
platform = importlib.import_module("mini_platform") if (step / "mini_platform.py").exists() else None
send = getattr(agent, "invoke", None) or (lambda request: platform.enter(request, agent))
source = (step / "agent.py").read_text(encoding="utf-8")
ask = {"key": "k1", "content": "청구서 INV-2048 요약해 줘"}


def rejects_missing_token():
    return send({**ask, "key": "k0"})["status"] == 401


def runs_once():
    before = world.model_calls
    send({**ask, "token": "token-seoyeon"})
    send({**ask, "token": "token-seoyeon"})
    return world.model_calls - before == 1


def no_password_in_agent():
    return world.ERP_PASSWORD not in source


def undeclared_tool_denied():
    try:
        platform.Context().call_tool("tool-mail-send", {})
    except PermissionError:
        return True
    return False


def intern_denied():
    return send({**ask, "key": "k2", "token": "token-hajun"})["status"] == 403


def no_direct_model_call():
    return "world.model" not in source


CHECKS = [
    ("토큰 없는 요청은 거절한다", rejects_missing_token),
    ("같은 요청이 두 번 와도 한 번만 실행한다", runs_once),
    ("Agent 코드에 ERP 비밀번호가 없다", no_password_in_agent),
    ("Manifest에 없는 도구는 부를 수 없다", undeclared_tool_denied),
    ("권한이 모자란 하준은 거절한다", intern_denied),
    ("Agent 코드가 모델을 직접 부르지 않는다", no_direct_model_call),
]
print("응답", send({**ask, "key": "k-show", "token": "token-seoyeon"}))
passed = 0
for number, (name, check) in enumerate(CHECKS, 1):
    try:
        ok = check()
    except Exception:  # 아직 붙지 않은 조각을 부르면 실패로 셉니다
        ok = False
    passed += ok
    print(("PASS" if ok else "FAIL"), number, name)
print(f"{passed}/{len(CHECKS)}")
