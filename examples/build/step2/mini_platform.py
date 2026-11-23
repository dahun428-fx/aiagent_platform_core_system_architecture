"""2단계 조각: 도구 경로. 비밀번호는 플랫폼이 쥐고, Agent는 도구 이름만 넘깁니다."""
import json
from pathlib import Path

import world

USERS = {"token-analyst": "finance.analyst", "token-viewer": "finance.viewer"}  # 회사 IdP를 흉내 낸 가짜 사용자 목록(토큰 -> 역할)
done = {}  # 요청 번호 -> (내용, 결과)
VAULT = {"erp": world.ERP_PASSWORD}  # Credential Broker를 흉내 낸 가짜 보관소
TOOLS = {"tool-erp-read": lambda args: world.erp_read(VAULT["erp"], args["invoice_id"])}
MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))


class Context:
    """Agent가 플랫폼에 부탁할 수 있는 일의 전부입니다."""

    def call_tool(self, tool_id, args):
        if tool_id not in MANIFEST["tools"]:
            raise PermissionError(tool_id + "는 Manifest에 없는 도구입니다")
        call = TOOLS[tool_id]
        return call(args)


def enter(request, agent):
    if request.get("token") not in USERS:
        return {"status": 401}
    if request["key"] in done:
        content, result = done[request["key"]]
        return result if content == request["content"] else {"status": 409}
    result = {"status": 200, "output": agent.handle(Context(), request["content"])}
    done[request["key"]] = (request["content"], result)
    return result
