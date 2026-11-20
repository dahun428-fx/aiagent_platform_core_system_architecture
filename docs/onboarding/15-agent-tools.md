# Agent Tools

> 개발자 가이드 문서입니다. 규범은 [Agent Tools](../agent-tools.md), [Agent Identity](../identity-and-credentials.md), [Durable / HITL](../execution.md) 기술 표준 문서가 기준입니다.

{{journey:4}}

<div class="sofar" markdown="1">
**지금까지** 서연이 "청구서 INV-2048 요약해 줘"를 보냈습니다. 정문이 서연을 확인했고, 민준이 등록한 `invoice-summary`의 코드가 실행되기 시작했습니다.
</div>

<p class="part">설명</p>

## 장면

민준의 코드는 이제 ERP에서 청구서를 읽어 와야 합니다. 그런데 코드 어디에도 ERP 주소나 API 키가 없고, Manifest에 `tool-erp-read`라는 이름 하나만 적혀 있습니다. 잠시 뒤 서연이 "이 요약을 한빛상사 담당자에게 메일로 보내 줘"라고 합니다. 보내는 일은 다른 Agent인 `invoice-mailer`가 맡는데, 메일은 바로 나가지 않고 재무팀장 지훈의 승인을 기다립니다. 읽기는 바로 되고 보내기는 멈추는 이유가 이 장의 내용입니다.

<div class="point" markdown="1">
**{{icon:bulb}} Agent Tools가 없다면** Agent마다 ERP 비밀번호를 들고 다니고, 메일은 누구의 확인도 없이 나갑니다.
</div>

## 무슨 일이 일어나나

<ol class="flow">
<li data-say="Agent 코드는 도구의 이름과 버전, 그리고 조회어만 넘깁니다. 주소나 비밀번호를 넣을 자리가 없습니다.">{{icon:runtime}}<b>1. 이름과 조회어를 넘긴다</b><span>Agent 코드<br><strong>주소·자격증명 없음</strong></span></li>
<li data-say="플랫폼이 이 도구가 Manifest에 적혀 있는지, 호출자에게 읽기 권한이 있는지를 봅니다.">{{icon:gateway}}<b>2. 써도 되는 도구인지 본다</b><span>Agent Gateway 도구 경로</span></li>
<li data-say="플랫폼이 이 호출 한 번에만 쓸 수 있는 출입증(lease)을 받아 ERP를 대신 부릅니다. 출입증은 Agent에게 가지 않습니다." class="hi">{{icon:key}}<b>3. 플랫폼이 ERP를 대신 부른다</b><span>Credential Broker의 lease</span></li>
<li data-say="ERP가 돌려준 내용만 Agent에게 돌아옵니다. 응답 어디에도 토큰이나 주소는 없습니다.">{{icon:tools}}<b>4. 결과만 돌아온다</b><span>청구서 내용</span></li>
<li data-say="메일 보내기처럼 바깥을 바꾸는 일은 사람이 승인할 때까지 실행이 멈춥니다.">{{icon:approve}}<b>5. 보내는 일은 승인까지 멈춘다</b><span>쓰기 도구 + 사람 승인</span></li>
</ol>

## 실물 보기

Agent가 도구를 부르는 코드 한 줄입니다.

<!-- kind: example -->

```python
found = ctx.call_tool("tool-erp-read", "1.0.0", {"query": "INV-2048"})
```

- `"tool-erp-read"`: 주소가 아니라 이름입니다. 주소와 자격증명은 플랫폼이 압니다.
- `"1.0.0"`: 도구도 버전이 있습니다. 도구가 바뀌어도 Agent가 모르는 사이에 동작이 달라지지 않습니다.
- `{"query": ...}`: 도구가 받겠다고 선언한 인자만 보낼 수 있습니다. 주소를 넣을 자리가 없습니다.

플랫폼이 이 이름으로 찾아보는 도구 등록 정보(descriptor)입니다. 저장소의 `examples/fixtures/tool-descriptor.json`과 같은 필드입니다.

<!-- kind: example -->

```json
{
  "toolId": "tool-erp-read",
  "version": "1.0.0",
  "protocol": "rest-openapi",
  "effect": "read",
  "allowedScopes": ["tools.read"],
  "inputSchema": "…/tool-input.schema.json",
  "outputSchema": "…/tool-output.schema.json"
}
```

- `effect`: `read`는 읽기만 합니다. 메일 도구 `tool-mail-send`는 여기가 `write`이고, `write`인 도구는 승인이 있어야 실행됩니다.
- `allowedScopes`: 이 도구를 쓰려면 호출자에게 있어야 하는 권한입니다. 서연에게 `tools.read`가 있어서 조회가 됩니다.
- `inputSchema`, `outputSchema`: 들어가는 값과 나오는 값의 형식입니다. 형식에 맞지 않으면 ERP까지 가지 않습니다.

<details class="more" markdown="1"><summary>더 보기: 도구 경로가 실제로 받는 요청과 돌려주는 결과</summary>

Agent 코드의 한 줄이 도구 경로에 도착할 때는 플랫폼이 신원과 정책 정보를 덧붙인 모습입니다. 로컬 fixture `examples/fixtures/tool-invoke.json`의 발췌입니다.

<!-- kind: run boundary: local -->

```json
{
  "invocationId": "inv-demo",
  "toolId": "tool-search",
  "version": "0.1.0",
  "arguments": {"query": "hello"},
  "identity": {"tenantId": "tenant-demo", "mode": "delegated", "principalId": "user-demo", "scopes": ["tools.read", "agents.invoke", "models.invoke"]},
  "policy": {"decisionId": "policy-demo", "allowed": true, "allowedResources": ["tool-search", "model-self-hosted", "model-external"]},
  "idempotencyKey": "fixture-tool"
}
```

`identity`, `policy`, `idempotencyKey`는 Agent 코드가 적은 것이 아닙니다. Runtime이 붙입니다. 결과(`tool-result.json`)에는 `status`와 `output`만 있고 자격증명은 없습니다.

```json
{"invocationId": "inv-demo", "toolId": "tool-search", "status": "succeeded", "output": {"content": "tool:hello"}}
```
</details>

## 직접 해 보기

<div class="sim" data-sim="tool-call"></div>

<ol class="mission">
<li>코드에서 Manifest에 없는 도구를 불러 보세요. 이것은 등록 실패인가요, 등록한 코드가 실행 중에 거절된 것인가요.</li>
<li>쓰기 도구에 다른 요청에서 받은 승인을 붙여 보세요. 앱은 무엇을 받나요. 승인이 아예 없을 때와 구별할 수 있나요.</li>
</ol>

## 잘못되면

**민준의 코드가 Manifest에 적지 않은 도구를 부르면** 서연의 요청은 실행 중에 403을 받습니다. 로컬 mock의 응답 본문에는 `Tool is not declared in the Agent Manifest`라고 적혀 있습니다. Manifest는 유효했고 등록도 됐고 코드도 실행된 뒤에 나는 실패입니다. 고치려면 `capabilities.tools`에 도구 이름을 추가하고 새 버전으로 등록합니다. 도구 목록을 아예 비운 Manifest는 여기까지 오지 못하고 등록 전 검증에서 멈춥니다([Agent Factory와 Manifest](05-agents-and-manifest.md)).

**승인이 붙지 않은 채 메일 도구를 부르면** 앱은 403 `Policy denied`를 받습니다. 평소에는 플랫폼이 승인까지 실행을 멈춰 주지만, 어떤 이유로든 승인 없는 호출이 도구 앞까지 오면 도구 경로가 마지막으로 거절합니다. 운영자가 도구 경로를 직접 보면 이유가 `Write tool requires approval`로 적혀 있습니다. 코드로 고칠 일이 아니라 승인자가 승인해야 풀립니다.

<details class="more" markdown="1"><summary>더 보기: 앱에서는 같아 보이는 거절 셋, 그리고 응답이 끊겼을 때</summary>

| 상황 | 앱이 받은 응답 | 도구 경로의 내부 진단 | 참조 구현 시나리오 |
|---|---|---|---|
| 등록되지 않은 도구를 부름 | 403 `Policy denied` | `Tool not approved` | S5 `tool-not-approved` |
| 승인 없이 쓰기 도구를 부름 | 403 `Policy denied` | `Write tool requires approval` | S6a `write-no-approval` |
| 만료됐거나 다른 요청의 승인을 붙임 | 403 `Policy denied` | `Approval is stale or not bound to this request` | S6a `write-approval-expired`, `write-approval-other-request` |
| 메일 서버의 응답이 오다가 끊김 | 실패 응답 | `unknown_outcome` | S6a `write-response-lost` |
| 다시 실행할 때 같은 키에 다른 인자가 실림 | 409 `CONFLICT` | 같은 키, 다른 내용 | S5 `tool-key-conflict` |

앞의 셋은 앱에서 모두 같은 `Policy denied`입니다. 거절 이유를 바깥에 자세히 알려 주면 공격자에게도 알려 주는 셈이기 때문입니다. 어느 것인지는 호출 번호(`invocationId`)로 운영자에게 묻습니다.

`unknown_outcome`은 메일이 나갔는지 알 수 없는 상태입니다. 자동으로 다시 보내면 두 번 나갈 수 있으므로 다시 보내지 않고 메일 서버의 기록과 대조합니다. 도구 호출의 멱등성 키는 Agent 코드가 아니라 Runtime이 붙입니다.

Agent가 주소를 직접 넘기는 길은 계약에 없습니다. 주소를 넘길 수 있다면 문서에 숨은 지시문이 Agent에게 `http://10.0.0.5/admin` 같은 사내망 주소를 찔러 보게 할 수 있습니다.
</details>

## 내가 할 일

1. 쓸 도구의 ID와 버전을 확인합니다.
2. Manifest의 `capabilities.tools`에 그 ID를 적고, `identity.requiredScopes`에 도구가 요구하는 scope를 적습니다.
3. 코드에서 `ctx.call_tool(도구 ID, 버전, 인자)`로 부릅니다. 주소와 키는 넣지 않습니다.
4. 로컬에서 실행해 보고 적합성 검사의 C8(선언하지 않은 도구, 자격증명 노출)을 확인합니다.
5. 쓰기 도구가 필요하면 읽기 Agent에 덧붙이지 말고 별도 Agent로 나눕니다.

**내 PC에서 해 보기** 저장소 루트에서 실행합니다. 로컬에서는 이야기 속 이름 대신 아래 대역을 씁니다.

| 이야기 | 내 PC |
|---|---|
| `tool-erp-read` `1.0.0` | `tool-search` `0.1.0` |
| 테넌트 `finance` | `tenant-demo` |
| 서연의 토큰 | `Bearer mock-user` |

```bash
python scripts/agentctl.py run --port 8765 --agents-dir examples/agents
```

다른 터미널에서 요청을 보냅니다.

```bash
curl -s -X POST http://127.0.0.1:8765/v1/agents/invoice-summary/invocations \
  -H "Authorization: Bearer mock-user" -H "Idempotency-Key: demo-a1" -H "Content-Type: application/json" \
  -d '{"input":{"type":"message","content":"청구서 INV-2048 요약해 줘"},"context":{"tenantId":"tenant-demo","dataClassification":"confidential"},"execution":{"mode":"sync","timeoutMs":30000}}'
```

<!-- kind: run boundary: local -->

```json
{"invocationId":"inv-9946215c02f347bd8ba5de71ca079905","agentVersion":"0.1.0","status":"succeeded","output":{"type":"message","content":"mock:Summarize the invoice: tool:청구서 INV-2048 요약해 줘"},"traceparent":"00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01","routeDecisionId":"route-self-hosted","usage":{"inputTokens":7,"outputTokens":7}}
```

`output.content` 안의 `tool:청구서 INV-2048 요약해 줘`가 도구가 돌려준 값입니다. 로컬 도구는 받은 조회어 앞에 `tool:`을, 로컬 모델은 받은 글 앞에 `mock:`을 붙여 돌려주는 대역이라 실제 요약은 나오지 않습니다. 호출 번호와 추적 번호는 실행할 때마다 달라집니다. 쓰기와 승인은 `make scenarios`의 S5, S6a 줄에서 확인합니다(PostgreSQL이 필요합니다. [로컬 환경 구성](07-hands-on.md)).

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| 읽기 도구 호출, 선언하지 않은 도구 거절 | 실행 | 로컬 mock, 적합성 C8 |
| 쓰기 도구의 승인 검증, `unknown_outcome` | 실행 | 참조 구현 S5, S6a |
| 승인을 기다리며 멈추는 실행(`waiting_approval`) | 계약 | `contracts/execution.schema.json` |
| MCP 서버 연결, 새 도구 등록 절차 | 정의 | [Agent Tools](../agent-tools.md) |
</div>

## 규칙으로 정리

- Agent는 도구의 ID, 버전, 인자만 넘깁니다. 주소와 자격증명은 넘길 수 없습니다(MUST NOT). 장면 ④
- Manifest의 `capabilities.tools`에 없는 도구 호출은 거절합니다(MUST). 장면 ④
- 쓰기 도구는 그 요청에 묶인 유효한 승인이 있어야 실행합니다(MUST). 장면 ④ 뒷부분
- 쓰기의 성공 여부를 알 수 없으면 자동으로 다시 실행하지 않고 `unknown_outcome`으로 기록합니다(MUST).
- MCP 서버는 도구를 제공하는 방식 가운데 하나이며 같은 도구 경로를 지납니다. 토큰을 그대로 넘겨주는 방식(token passthrough)은 쓰지 않습니다(MUST NOT).

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Tools](09-glossary.md#term-agent-tools) [도구 경로](09-glossary.md#term-tool-gateway) [Credential Broker](09-glossary.md#term-credential-broker) [Lease](09-glossary.md#term-lease) [scope](09-glossary.md#term-scope) [HITL](09-glossary.md#term-hitl) [unknown_outcome](09-glossary.md#term-unknown) [MCP](09-glossary.md#term-mcp)
</div>

<p class="part">코드로 보기</p>

## 코드로 보기: 도구 경로를 붙인다

[정문을 붙인](03-one-request.md) 코드에 두 번째 조각을 붙입니다. 이번에 지울 것은 Agent 코드에 남아 있는 비밀번호 한 줄입니다.

{{blocks:2}}

### 도구 경로가 없을 때

정문까지 붙인 Agent의 코드입니다.

```python
ERP_PASSWORD = "erp-s3cret"


def handle(content):
    invoice_id = re.search(r"INV-\d+", content).group()
    invoice = world.erp_read(ERP_PASSWORD, invoice_id)
    return world.model(f"{invoice['vendor']} {invoice['amount']:,}원, 납기 {invoice['due']}")
```

첫 줄 때문에 세 가지 일이 생깁니다. 비밀번호가 코드와 함께 저장소에 올라가므로 저장소를 볼 수 있는 사람은 누구나 ERP에 들어갈 수 있습니다. ERP 비밀번호를 바꾸는 날에는 이 값을 적어 둔 Agent를 전부 찾아 고쳐서 다시 배포해야 합니다. 그리고 비밀번호를 가진 코드는 ERP에서 무엇이든 할 수 있어서, 청구서 읽기만 하겠다던 Agent가 내일 송금 API를 불러도 막을 곳이 없습니다.

### 도구 경로가 하는 일

비밀번호를 Agent에서 플랫폼으로 옮기고, Agent는 도구의 이름만 넘기게 합니다. Agent가 부를 수 있는 이름은 Manifest에 미리 적어 둡니다.

<!-- kind: example -->
```json
{"id": "invoice-summary", "tools": ["tool-erp-read"]}
```

```text
도구_호출(도구 이름, 인자):
    이 Agent의 Manifest에 없는 이름이면
        거절한다                              # 신청하지 않은 도구는 부를 수 없다
    보관소에서 그 도구의 비밀번호를 꺼낸다    # Agent는 이 값을 보지 못한다
    플랫폼이 도구를 대신 부른다
    결과만 Agent에게 돌려준다
```

코드로 옮기면 정문 코드에 다음이 더해집니다.

<!-- kind: example -->
```python
# examples/build/step2/mini_platform.py 에 새로 생긴 부분
# ① 비밀번호는 플랫폼이 가진다
VAULT = {"erp": world.ERP_PASSWORD}
# ② 이름과 실제로 할 일의 짝
TOOLS = {"tool-erp-read": lambda args: world.erp_read(VAULT["erp"], args["invoice_id"])}
MANIFEST = json.loads((Path(__file__).parent / "manifest.json").read_text(encoding="utf-8"))


class Context:
    """Agent가 플랫폼에 부탁할 수 있는 일의 전부입니다."""

    def call_tool(self, tool_id, args):
        # ③ Manifest에 없는 이름은 거절한다
        if tool_id not in MANIFEST["tools"]:
            raise PermissionError(tool_id + "는 Manifest에 없는 도구입니다")
        # ④ 플랫폼이 대신 부른다
        call = TOOLS[tool_id]
        return call(args)
```

- **①** 비밀번호가 사는 곳이 Agent 파일에서 플랫폼의 `VAULT`로 옮겨졌습니다. 이제 비밀번호를 바꿀 때 고칠 곳은 여기 한 곳입니다.
- **②** 도구 하나는 "이름과, 그 이름으로 실제로 할 일"의 짝입니다. 비밀번호를 꺼내 ERP를 부르는 코드가 이 안에 있으므로, 이름만 아는 쪽은 비밀번호를 만질 일이 없습니다.
- **③** 실제 호출보다 먼저 Manifest를 봅니다. 이름이 없으면 ④까지 가지 못하므로 ERP에는 아무 요청도 나가지 않습니다.
- **④** Manifest에 있는 이름만 여기까지 옵니다. 돌려주는 것은 ERP의 응답뿐이고 `VAULT`의 값은 `Context` 밖으로 나가지 않습니다.

정문은 한 줄만 바뀝니다. Agent를 부를 때 `Context`를 함께 건넵니다.

```diff
-    result = {"status": 200, "output": agent.handle(request["content"])}
+    result = {"status": 200, "output": agent.handle(Context(), request["content"])}
```

### 호출 두 개가 지나가는 모습

| 호출 | 끝나는 곳 | 결과 | ERP에 나간 요청 |
|---|---|---|---|
| `ctx.call_tool("tool-erp-read", {"invoice_id": "INV-2048"})` | ④ | `{'vendor': '한빛상사', 'amount': 12400000, 'due': '2026-11-30'}` | 1건 |
| `ctx.call_tool("tool-mail-send", {})` | ③ | `PermissionError: tool-mail-send는 Manifest에 없는 도구입니다` | 없음 |

두 번째 행에서 `tool-mail-send`라는 도구가 플랫폼에 있는지 없는지는 따지지도 않았습니다. Manifest에 없다는 이유만으로 먼저 거절됩니다.

### Agent 코드에서 바뀌는 것

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

비밀번호 줄이 사라졌고, ERP를 직접 부르던 줄이 `ctx.call_tool`로 바뀌었습니다. `ctx`는 플랫폼이 건네주는 손잡이입니다. Agent가 바깥으로 나가는 길이 이 손잡이 하나로 좁아지면, 플랫폼은 그 한 곳에서만 검사하고 기록하면 됩니다. 마지막 줄의 `world.model`은 아직 직접 호출로 남아 있습니다.

### 검사 결과

같은 검사 여섯 개를 다시 돌린 결과입니다(`python examples/build/check.py step2`).

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

이번에도 서연이 받는 응답은 그대로입니다. 새로 통과한 두 검사는 이렇게 생겼습니다.

<!-- kind: example -->
```python
def no_password_in_agent():
    return world.ERP_PASSWORD not in source                 # source는 agent.py 파일의 글자 전체


def undeclared_tool_denied():
    try:
        platform.Context().call_tool("tool-mail-send", {})  # 위 표의 두 번째 행
    except PermissionError:
        return True
    return False
```

검사 3은 실행 결과가 아니라 `agent.py` 파일의 글자를 봅니다. 비밀번호가 Agent 코드에 없다는 것은 동작으로는 드러나지 않기 때문입니다.

### 실제 플랫폼과의 대응

| 이 코드 | 실제 플랫폼 |
|---|---|
| `TOOLS` | Tool Registry. 도구의 이름, 버전, 읽기·쓰기 구분을 등록합니다 |
| `VAULT` | Credential Broker. 비밀번호 대신 이 호출 한 번에만 쓰는 출입증(lease)을 발급합니다 |
| `Context.call_tool` | Agent Gateway의 도구 경로. 호출마다 정책을 확인하고 기록합니다 |
| `manifest.json` | Agent Manifest의 `capabilities.tools` |
| `PermissionError` | 403 |

남은 FAIL 두 줄이 다음에 붙일 조각입니다. 검사 5는 같은 Agent를 불러도 사람에 따라 결과가 달라야 한다는 것이고(Agent Identity), 검사 6은 모델도 도구처럼 플랫폼을 거쳐 불러야 한다는 것입니다(Agent Gateway).

## 한 문장으로

Agent는 도구의 이름만 알고, 주소와 비밀번호는 플랫폼이 쥐고 대신 불러 줍니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 민준의 코드가 Manifest에 적지 않은 tool-mail-send를 부릅니다. 등록은 통과했습니다. 서연이 요청을 보내면 어떻게 되나요?</summary>
코드는 실행되지만 그 도구를 부르는 순간 403으로 거절됩니다. 등록 실패가 아니라 실행 중 거절입니다. Manifest에 도구를 추가해 새 버전으로 등록해야 합니다.
</details>

<details markdown="1"><summary>Q2. 서연의 앱이 403 Policy denied를 받았습니다. 승인이 없어서인지 승인이 만료돼서인지 앱이 구별할 수 있나요?</summary>
구별할 수 없습니다. 앱이 받는 응답은 같습니다. 호출 번호를 운영자에게 전달하면 도구 경로의 기록에서 이유를 확인할 수 있습니다.
</details>

<details markdown="1"><summary>Q3. 메일 도구를 부른 뒤 응답이 끊겼습니다. Agent가 한 번 더 보내면 안 되는 이유는 무엇인가요?</summary>
메일이 이미 나갔을 수 있기 때문입니다. 성공했는지 알 수 없는 쓰기는 다시 실행하지 않고 대상 시스템의 기록과 대조해 확정합니다.
</details>
</div>

다음 장면은 ⑤입니다. 같은 Agent인데 왜 서연이 부르면 되고 인턴 하준이 부르면 안 되는지를 봅니다.
