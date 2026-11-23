"""1단계 조각: Agent Platform APIs. 호출자를 인증하고, 같은 멱등성 키의 요청은 한 번만 실행합니다."""
USERS = {"token-seoyeon": "서연", "token-hajun": "하준"}  # 회사 IdP를 흉내 낸 가짜 사용자 목록
done = {}  # 요청 번호 -> (내용, 결과)


def enter(request, agent):
    if request.get("token") not in USERS:
        return {"status": 401}
    if request["key"] in done:
        content, result = done[request["key"]]
        return result if content == request["content"] else {"status": 409}
    result = {"status": 200, "output": agent.handle(request["content"])}
    done[request["key"]] = (request["content"], result)
    return result
