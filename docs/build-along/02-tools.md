# 2. 도구 경로를 붙인다

> 두 번째 조각은 Agent Tools입니다. Agent는 도구의 이름만 알고, 비밀번호는 플랫폼이 쥡니다.

{{blocks:2}}

## 지금 코드의 아픈 곳

1장의 Agent에는 이 줄이 남아 있습니다.

```python
ERP_PASSWORD = "erp-s3cret"
```

이 한 줄 때문에 세 가지 일이 생깁니다.

- 비밀번호가 코드와 함께 저장소에 올라가, 저장소를 볼 수 있는 모든 사람이 ERP에 들어갈 수 있습니다.
- ERP 비밀번호를 바꾸는 날, 이 비밀번호를 적어 둔 Agent를 전부 찾아 고쳐서 다시 배포해야 합니다.
- 비밀번호를 가진 코드는 ERP에서 무엇이든 할 수 있습니다. 청구서 읽기만 하겠다던 Agent가 내일 송금 API를 불러도 막을 곳이 없습니다.

## 붙이는 조각: 도구 경로

비밀번호를 Agent에서 플랫폼으로 옮깁니다. Agent는 "`tool-erp-read`를 이 청구서 번호로 불러 줘"라고 이름만 넘기고, 실제 호출은 플랫폼이 대신 합니다. 그리고 Agent가 부를 수 있는 도구의 이름을 Manifest라는 신청서에 미리 적어 둡니다.

<!-- kind: example -->
```json
{"id": "invoice-summary", "tools": ["tool-erp-read"]}
```

## 조각 안에서 일어나는 일

```text
도구_호출(도구 이름, 인자):
    이 Agent의 Manifest에 없는 이름이면
        거절한다                              # 신청하지 않은 도구는 부를 수 없다
    보관소에서 그 도구의 비밀번호를 꺼낸다    # Agent는 이 값을 보지 못한다
    플랫폼이 도구를 대신 부른다
    결과만 Agent에게 돌려준다
```

`examples/build/step2/mini_platform.py`에서 1장의 정문에 더해진 부분입니다.

<!-- kind: example -->
```python
# examples/build/step2/mini_platform.py 에 새로 생긴 부분
VAULT = {"erp": world.ERP_PASSWORD}  # 비밀번호 보관소의 대역
TOOLS = {"tool-erp-read": lambda args: world.erp_read(VAULT["erp"], args["invoice_id"])}
MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))


class Context:
    """Agent가 플랫폼에 부탁할 수 있는 일의 전부입니다."""

    def call_tool(self, tool_id, args):
        if tool_id not in MANIFEST["tools"]:
            raise PermissionError(tool_id + "는 Manifest에 없는 도구입니다")
        call = TOOLS[tool_id]
        return call(args)
```

정문은 한 줄만 바뀝니다. Agent를 부를 때 `Context`를 함께 건넵니다.

```diff
-    result = {"status": 200, "output": agent.handle(request["content"])}
+    result = {"status": 200, "output": agent.handle(Context(), request["content"])}
```

## 내 코드에서 바뀌는 것

<!-- kind: example -->
```diff
 # examples/build/step1/agent.py  →  examples/build/step2/agent.py
-ERP_PASSWORD = "erp-s3cret"
-
-
-def handle(content):
+def handle(ctx, content):
     invoice_id = re.search(r"INV-\d+", content).group()
-    invoice = world.erp_read(ERP_PASSWORD, invoice_id)
+    invoice = ctx.call_tool("tool-erp-read", {"invoice_id": invoice_id})
     return world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
```

비밀번호 줄이 사라졌고, ERP를 직접 부르던 줄이 `ctx.call_tool`로 바뀌었습니다. `ctx`는 플랫폼이 건네주는 손잡이입니다. Agent가 바깥에 손을 뻗을 길이 이 손잡이 하나로 좁아지면, 플랫폼은 그 한 곳에서만 검사하고 기록하면 됩니다.

## 검사를 다시 돌린다

```bash
python examples/build/check.py step2
```

<!-- kind: run boundary: local -->
```text
응답 {'status': 200, 'output': '요약: 한빛상사 12,400,000원, 납기 2026-11-30'}
PASS 1 토큰 없는 요청은 거절한다
PASS 2 같은 요청이 두 번 와도 한 번만 실행한다
PASS 3 Agent 코드에 ERP 비밀번호가 없다
PASS 4 Manifest에 없는 도구는 부를 수 없다
FAIL 5 권한이 모자란 하준은 거절한다
FAIL 6 Agent 코드가 모델을 직접 부르지 않는다
4/6
```

이번에도 서연이 받는 응답은 그대로입니다. 검사 3은 `agent.py` 파일에 비밀번호 문자열이 있는지 찾고, 검사 4는 Manifest에 없는 `tool-mail-send`를 불렀을 때 거절되는지 확인합니다.

<ol class="mission">
<li><code>step2/agent.py</code>에서 도구 이름을 <code>tool-mail-send</code>로 바꿔 실행해 보세요. 어디에서 막히나요.</li>
<li><code>manifest.json</code>의 <code>tools</code>를 빈 배열로 바꾸면 응답 줄이 어떻게 달라지는지 먼저 예상하고 확인해 보세요.</li>
</ol>

## 실제 플랫폼에서는

| 이 장의 코드 | 실제 플랫폼 |
|---|---|
| `TOOLS` | Tool Registry. 도구의 이름, 버전, 읽기·쓰기 구분을 등록합니다 |
| `VAULT` | Credential Broker. 비밀번호 대신 이 호출 한 번에만 쓰는 출입증(lease)을 발급합니다 |
| `Context.call_tool` | Agent Gateway의 도구 경로. 호출마다 정책을 확인하고 기록합니다 |
| `manifest.json` | Agent Manifest. 도구 말고도 scope와 신원 모드를 적습니다 |

이 장은 읽기 도구만 다뤘습니다. 메일 보내기처럼 바깥을 바꾸는 쓰기 도구는 사람이 승인할 때까지 실행이 멈추는데, 그 흐름은 [Agent Tools](../onboarding/15-agent-tools.md)에 있습니다.

## 지금까지 만든 것

- Agent 코드. 비밀번호도 ERP 주소도 없습니다.
- 플랫폼 조각 둘: 정문, 도구 경로.
- Manifest 한 줄: 이 Agent는 `tool-erp-read`만 부릅니다.
- 검사 4/6.

남은 FAIL 두 줄이 다음에 붙일 조각을 가리킵니다. 검사 5는 같은 Agent를 불러도 사람에 따라 결과가 달라야 한다는 것이고(Agent Identity), 검사 6은 모델도 도구처럼 플랫폼을 거쳐 불러야 한다는 것입니다(Agent Gateway).
