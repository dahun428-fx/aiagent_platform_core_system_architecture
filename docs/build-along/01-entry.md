# 1. 정문을 붙인다

> 첫 조각은 Agent Platform APIs입니다. 모든 요청이 Agent보다 먼저 지나는 정문입니다.

{{blocks:1}}

## 지금 코드의 아픈 곳

0장의 Agent는 `invoke(request)`가 요청을 직접 받습니다. 그래서 두 가지가 그대로 통과합니다.

```python
agent.invoke({"content": "청구서 INV-2048 요약해 줘"})              # 보낸 사람이 없어도 요약이 나갑니다
agent.invoke({"content": "청구서 INV-2048 요약해 줘", "key": "k1"})
agent.invoke({"content": "청구서 INV-2048 요약해 줘", "key": "k1"})  # 같은 요청인데 모델을 또 부릅니다
```

첫 번째는 회사 밖 누구라도 청구서 금액을 볼 수 있다는 뜻입니다. 두 번째는 흔한 상황입니다. 앱이 응답을 기다리다 시간이 넘어가면 같은 요청을 다시 보내는데, Agent는 그것이 재전송인지 알 길이 없어 처음부터 다시 실행합니다. 요약은 두 번 해도 비용만 더 들지만, 메일 보내기나 송금이었다면 두 번 나갑니다.

## 붙이는 조각: 정문

Agent 앞에 문을 하나 세우고, 요청은 그 문만 지나게 합니다. Agent는 더 이상 요청을 직접 받지 않고, 문을 통과한 요청의 내용만 건네받습니다.

## 조각 안에서 일어나는 일

```text
정문(요청):
    토큰이 없거나 모르는 토큰이면
        401로 돌려보낸다                      # Agent 코드는 한 줄도 실행되지 않는다
    처음 보는 요청 번호이면
        Agent를 실행하고, 결과를 번호와 함께 적어 둔다
    본 적 있는 번호이고 내용도 같으면
        적어 둔 결과를 그대로 돌려준다        # 다시 실행하지 않는다
    본 적 있는 번호인데 내용이 다르면
        409로 돌려보낸다                      # 실수이거나 누군가 번호를 훔쳐 쓴 것이다
```

이 의사코드를 그대로 옮긴 것이 `examples/build/step1/mini_platform.py`입니다. 열 줄 남짓이니 열어서 의사코드와 한 줄씩 맞춰 보기를 권합니다.

<!-- kind: example -->
```python
# examples/build/step1/mini_platform.py
USERS = {"token-seoyeon": "서연", "token-hajun": "하준"}  # 회사 IdP의 대역
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
```

## 내 코드에서 바뀌는 것

Agent 코드는 오히려 줄어듭니다. 요청 봉투를 열고 응답 봉투를 싸는 일이 정문으로 넘어갔기 때문에, Agent에는 내용을 받아 요약을 돌려주는 일만 남습니다.

<!-- kind: example -->
```diff
 # examples/build/step0/agent.py  →  examples/build/step1/agent.py
-def invoke(request):
-    invoice_id = re.search(r"INV-\d+", request["content"]).group()
+def handle(content):
+    invoice_id = re.search(r"INV-\d+", content).group()
     invoice = world.erp_read(ERP_PASSWORD, invoice_id)
-    summary = world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
-    return {"status": 200, "output": summary}
+    return world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
```

토큰 확인도 재전송 처리도 Agent 코드에는 한 줄도 들어가지 않았습니다. 다른 팀이 Agent를 새로 만들어도 같은 정문 뒤에 서기만 하면 두 가지를 그대로 얻습니다.

## 검사를 다시 돌린다

```bash
python examples/build/check.py step1
```

<!-- kind: run boundary: local -->
```text
응답 {'status': 200, 'output': '요약: 한빛상사 12,400,000원, 납기 2026-11-30'}
PASS 1 토큰 없는 요청은 거절한다
PASS 2 같은 요청이 두 번 와도 한 번만 실행한다
FAIL 3 Agent 코드에 ERP 비밀번호가 없다
FAIL 4 Manifest에 없는 도구는 부를 수 없다
FAIL 5 권한이 모자란 하준은 거절한다
FAIL 6 Agent 코드가 모델을 직접 부르지 않는다
2/6
```

서연이 받는 응답은 0장과 글자 하나 다르지 않고, 검사 1과 2만 통과로 바뀌었습니다. 검사 2는 같은 요청을 두 번 보낸 뒤 `world`가 센 모델 호출 횟수가 1인지 확인합니다.

<ol class="mission">
<li><code>step1/mini_platform.py</code>에서 <code>if request["key"] in done:</code>부터 세 줄을 지우고 검사를 다시 돌려 보세요. 어느 줄이 FAIL로 돌아가나요.</li>
<li>같은 번호에 다른 내용을 보내면 무엇이 돌아오는지 의사코드에서 먼저 찾고, 코드에서 확인해 보세요.</li>
</ol>

## 실제 플랫폼에서는

여기서 쓴 이름과 실제 계약의 이름은 이렇게 대응합니다.

| 이 장의 코드 | 실제 플랫폼 |
|---|---|
| `request["token"]` | `Authorization` 헤더의 사용자 토큰. 회사 IdP가 발급합니다 |
| `request["key"]` | `Idempotency-Key` 헤더. 없으면 422로 거절합니다 |
| `done` 딕셔너리 | 재시작해도 남는 저장소 |
| `enter()` | `POST /v1/agents/{agentId}/invocations` |

정문이 돌려주는 오류의 전체 목록과 요청·응답의 실물은 [Agent Platform APIs: 요청 하나 따라가기](../onboarding/03-one-request.md)에 있습니다.

## 지금까지 만든 것

- Agent 코드. 요청 봉투를 다루는 코드가 빠졌습니다.
- 플랫폼 조각 하나: 정문. 토큰 확인과 재전송 처리를 맡습니다.
- 검사 2/6.

Agent 코드에는 아직 `ERP_PASSWORD = "erp-s3cret"`이 남아 있습니다. 다음 장에서 도구 경로를 붙여 이 줄을 지웁니다.
