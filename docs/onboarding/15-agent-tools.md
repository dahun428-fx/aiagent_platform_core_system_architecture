# Agent Tools

> 개발자 가이드 문서입니다. 규범은 [Agent Tools](../agent-tools.md), [Agent Identity](../identity-and-credentials.md), [Durable / HITL](../execution.md) 기술 표준 문서가 기준입니다.

{{journey:4}}

<p class="part">본문</p>

## 개요

Agent Tools는 Agent가 쓰는 도구를 등록하고 관리하는 Core System입니다. Tool Registry, 도구 등록 정보(descriptor), REST/OpenAPI/MCP adapter, 도구 정책과 감사를 소유합니다. 실제 호출은 Agent Gateway의 도구 경로가 집행합니다.

Agent 코드는 도구의 ID, 버전, 인자만 넘깁니다. 도구의 주소와 자격증명은 플랫폼만 알고, 도구 경로는 Credential Broker가 발급한 lease를 adapter 안에서만 실제 자격증명으로 교환해 도구를 호출합니다. 외부 시스템에 영향을 주는 쓰기 도구는 그 요청에 묶인 승인이 있어야 실행됩니다.

<div class="point" markdown="1">
**{{icon:bulb}} Agent Tools가 없다면** Agent마다 도구의 자격증명을 코드에 가지고 다니고, 쓰기 작업은 아무 확인 없이 실행됩니다.
</div>

## 처리 흐름

<ol class="flow">
<li data-say="Agent 코드는 도구의 이름과 버전, 그리고 검색어(query)만 넘깁니다. 주소나 비밀번호를 넣을 자리가 없습니다.">{{icon:runtime}}<b>1. 이름과 검색어를 넘긴다</b><span>Agent 코드<br><strong>주소·자격증명 없음</strong></span></li>
<li data-say="플랫폼이 이 도구가 Manifest에 적혀 있는지, 호출자에게 읽기 권한이 있는지를 봅니다.">{{icon:gateway}}<b>2. 써도 되는 도구인지 본다</b><span>Agent Gateway 도구 경로</span></li>
<li data-say="플랫폼이 Credential Broker에서 lease를 받아 ERP를 대신 호출합니다. lease는 이 호출에만 묶인, 실제 자격증명을 가리키는 불투명 참조이고 Agent에게 전달되지 않습니다." class="hi">{{icon:key}}<b>3. 플랫폼이 ERP를 대신 호출한다</b><span>Credential Broker의 lease</span></li>
<li data-say="ERP가 돌려준 내용만 Agent에게 돌아옵니다. 응답 어디에도 토큰이나 주소는 없습니다.">{{icon:tools}}<b>4. 결과만 돌아온다</b><span>청구서 내용</span></li>
<li data-say="메일 보내기처럼 외부 시스템에 영향을 주는 작업은 사람이 승인할 때까지 실행이 멈춥니다.">{{icon:approve}}<b>5. 보내는 일은 승인까지 멈춘다</b><span>쓰기 도구 + 사람 승인</span></li>
</ol>

## 인터페이스

Agent 코드는 `ctx.call_tool(도구 ID, 버전, 인자)`로 도구를 호출합니다.

| 인자 | 의미 |
|---|---|
| 도구 ID | 주소가 아니라 Tool Registry에 등록된 이름입니다. 주소와 자격증명은 플랫폼만 압니다 |
| 버전 | 도구에도 버전이 있어서, 도구가 바뀌어도 Agent가 모르는 사이에 동작이 달라지지 않습니다 |
| 인자 | 도구가 `inputSchema`로 선언한 값만 보낼 수 있습니다. 주소를 넣을 자리가 없습니다 |

도구 경로는 도구 ID로 descriptor를 찾습니다. 형식은 `contracts/tool-descriptor.schema.json`입니다.

| 필드 | 의미 |
|---|---|
| `toolId`, `version` | 도구의 이름과 버전입니다 |
| `protocol` | adapter 종류입니다. 예: `rest-openapi`, `mcp` |
| `effect` | `read`는 읽기만 합니다. `write`인 도구는 그 요청에 묶인 승인이 있어야 실행됩니다 |
| `allowedScopes` | 이 도구를 쓰려면 호출자에게 있어야 하는 scope입니다 |
| `inputSchema`, `outputSchema` | 들어가는 값과 나오는 값의 형식입니다. 형식에 맞지 않으면 도구까지 가지 않습니다 |

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

`identity`, `policy`, `idempotencyKey`는 Agent 코드가 적은 것이 아니라 Runtime이 붙인 것입니다. 결과(`tool-result.json`)에는 `status`와 `output`만 있고 자격증명은 없습니다.

```json
{"invocationId": "inv-demo", "toolId": "tool-search", "status": "succeeded", "output": {"content": "tool:hello"}}
```
</details>

## 오류와 실패 동작

Manifest의 `capabilities.tools`에 없는 도구를 코드가 호출하면 실행 중에 403으로 거절됩니다. Manifest가 유효했고 등록도 됐고 코드까지 실행된 뒤에 나는 실패이므로, `capabilities.tools`에 도구 ID를 추가해 새 버전으로 등록해야 합니다. 도구 목록을 아예 비운 Manifest는 여기까지 오지 못하고 등록 전 검증에서 멈춥니다([Agent Factory와 Manifest](05-agents-and-manifest.md)).

| 조건 | 앱이 받은 응답 | 도구 경로의 내부 진단 | 참조 구현 시나리오 |
|---|---|---|---|
| Manifest에 선언하지 않은 도구를 호출 | 403 `Tool is not declared in the Agent Manifest` | 등록한 코드가 실행 중에 거절됨 | 적합성 C8 |
| Tool Registry에 승인되지 않은 도구를 호출 | 403 `Policy denied` | `Tool not approved` | S5 `tool-not-approved` |
| 승인 없이 쓰기 도구를 호출 | 403 `Policy denied` | `Write tool requires approval` | S6a `write-no-approval` |
| 만료됐거나 다른 요청의 승인을 붙임 | 403 `Policy denied` | `Approval is stale or not bound to this request` | S6a `write-approval-expired`, `write-approval-other-request` |
| 쓰기 도구의 응답이 도중에 끊김 | 실패 응답 | `unknown_outcome` | S6a `write-response-lost` |
| 재실행할 때 같은 키에 다른 인자가 실림 | 409 `CONFLICT` | 같은 키, 다른 내용 | S5 `tool-key-conflict` |

- 앱에서는 정책 거절이 모두 같은 `Policy denied`로 보입니다. 거절 이유를 바깥에 자세히 알려 주면 공격자에게도 알려 주는 셈이라 일부러 구분하지 않습니다. 이유는 `invocationId`로 운영자가 도구 경로의 기록에서 확인합니다.
- 평소에는 플랫폼이 승인까지 실행을 멈춥니다(`waiting_approval`). 승인 없는 호출이 도구 앞까지 오면 도구 경로가 마지막으로 거절합니다. 코드를 고쳐서 풀 일이 아니고, 승인자가 승인해야 풀립니다.
- `unknown_outcome`은 쓰기가 실행됐는지 알 수 없는 상태입니다. 자동으로 재실행하면 두 번 실행될 수 있으므로 재실행하지 않고 대상 시스템의 기록과 대조합니다. 도구 호출의 멱등성 키는 Agent 코드가 아니라 Runtime이 붙입니다.
- Agent가 주소를 직접 넘기는 길은 계약에 없습니다. 그런 길이 있다면 문서에 숨은 지시문이 Agent를 시켜 `http://10.0.0.5/admin` 같은 사내망 주소를 호출하게 할 수 있기 때문입니다.

## 개발자가 할 일

1. 쓸 도구의 ID와 버전을 확인합니다.
2. Manifest의 `capabilities.tools`에 그 ID를 적고, `identity.requiredScopes`에 도구가 요구하는 scope를 적습니다.
3. 코드에서 `ctx.call_tool(도구 ID, 버전, 인자)`로 호출합니다. 주소와 키는 넣지 않습니다.
4. 로컬에서 실행해 보고 적합성 검사의 C8(선언하지 않은 도구, 자격증명 노출)을 확인합니다.
5. 쓰기 도구가 필요하면 읽기 Agent에 덧붙이지 말고 별도 Agent로 나눕니다.

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| 읽기 도구 호출, 선언하지 않은 도구 거절 | 실행 | 로컬 mock, 적합성 C8 |
| 쓰기 도구의 승인 검증, `unknown_outcome` | 실행 | 참조 구현 S5, S6a |
| 승인을 기다리며 멈추는 실행(`waiting_approval`) | 계약 | `contracts/execution.schema.json` |
| MCP 서버 연결, 새 도구 등록 절차 | 정의 | [Agent Tools](../agent-tools.md) |
</div>

## 규칙

- Agent는 도구의 ID, 버전, 인자만 넘깁니다. 주소와 자격증명은 넘길 수 없습니다(MUST NOT).
- Manifest의 `capabilities.tools`에 없는 도구 호출은 거절합니다(MUST).
- 쓰기 도구는 그 요청에 묶인 유효한 승인이 있어야 실행합니다(MUST).
- 쓰기의 성공 여부를 알 수 없으면 자동으로 다시 실행하지 않고 `unknown_outcome`으로 기록합니다(MUST).
- MCP 서버는 도구를 제공하는 방식 가운데 하나이며 같은 도구 경로를 지납니다. 토큰을 그대로 넘겨주는 방식(token passthrough)은 쓰지 않습니다(MUST NOT).

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Tools](09-glossary.md#term-agent-tools) [도구 경로](09-glossary.md#term-tool-gateway) [Credential Broker](09-glossary.md#term-credential-broker) [Lease](09-glossary.md#term-lease) [scope](09-glossary.md#term-scope) [HITL](09-glossary.md#term-hitl) [unknown_outcome](09-glossary.md#term-unknown) [MCP](09-glossary.md#term-mcp)
</div>

## 한 문장으로

Agent는 도구의 이름만 알고, 주소와 자격증명은 플랫폼이 가진 채 도구를 대신 호출합니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 등록을 통과한 Agent의 코드가 Manifest에 적지 않은 도구를 호출합니다. 요청이 오면 어떻게 되나요?</summary>
코드는 실행되지만 그 도구를 호출하는 순간 403으로 거절됩니다. 등록에 실패한 것이 아니라 실행 중에 거절된 것이므로, Manifest에 도구를 추가해 새 버전으로 등록해야 합니다.
</details>

<details markdown="1"><summary>Q2. 앱이 403 Policy denied를 받았습니다. 승인이 없어서인지 승인이 만료돼서인지 앱이 구별할 수 있나요?</summary>
앱이 받는 응답이 같아서 구별할 수 없습니다. 호출 ID를 전달하면 운영자가 도구 경로의 기록에서 이유를 확인합니다.
</details>

<details markdown="1"><summary>Q3. 쓰기 도구를 호출한 뒤 응답이 끊겼습니다. Agent가 한 번 더 호출하면 안 되는 이유는 무엇인가요?</summary>
쓰기가 이미 실행됐을 수 있기 때문입니다. 성공했는지 알 수 없는 쓰기는 재실행하지 않고 대상 시스템의 기록과 대조해 확정합니다.
</details>
</div>

<p class="part">예시: 청구서 요약 Agent</p>

## 사례 조건

`invoice-summary`가 ERP에서 청구서 `INV-2048`을 읽고, 이어서 재무팀 사용자가 그 요약을 거래처 담당자에게 메일로 보내 달라고 요청하는 경우입니다. 읽기는 바로 실행되고 메일 발송은 승인자가 승인할 때까지 멈추는 과정을 봅니다. 역할과 값은 [예시 구성](02-big-picture.md)과 같습니다.

| 항목 | 읽기 | 쓰기 |
|---|---|---|
| Agent | `invoice-summary` | `invoice-mailer` |
| Manifest `capabilities.tools` | `tool-erp-read` | `tool-mail-send` |
| 도구 `effect` | `read` | `write` |
| 호출자 | 재무팀 사용자 `finance.analyst` | 재무팀 사용자 `finance.analyst` |
| 입력 | `"청구서 INV-2048 요약해 줘"` | `"이 요약을 한빛상사 담당자에게 메일로 보내 줘"` |
| 승인 | 필요 없음 | 승인자 `finance.approver` |

## 호출과 등록 정보

`invoice-summary`가 ERP를 조회하는 코드입니다. 주소와 자격증명이 없습니다.

<!-- kind: example -->

```python
found = ctx.call_tool("tool-erp-read", "1.0.0", {"query": "INV-2048"})
```

도구 경로가 `tool-erp-read`로 찾는 descriptor입니다. 저장소의 `examples/fixtures/tool-descriptor.json`과 같은 필드입니다.

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

- `effect`가 `read`이므로 승인 없이 실행됩니다. `tool-mail-send`는 여기가 `write`입니다.
- `allowedScopes`의 `tools.read`를 `finance.analyst`가 가지고 있어 조회가 됩니다.

## 처리 단계

| 순서 | 단계 | 이 예시의 값 | 결과 |
|---|---|---|---|
| 1 | Agent 코드가 도구 호출 | `tool-erp-read` `1.0.0`, `{"query": "INV-2048"}` | 도구 경로로 전달 |
| 2 | Manifest 확인 | `invoice-summary`의 `capabilities.tools`에 `tool-erp-read` 있음 | 통과 |
| 3 | scope 확인 | `finance.analyst`에게 `tools.read` 있음 | 통과 |
| 4 | 자격증명 사용 | Credential Broker가 이 호출에 묶인 lease 발급, adapter 안에서 교환 | ERP 조회 1건 |
| 5 | 결과 반환 | 한빛상사, 12,400,000원, 납기 2026-11-30 | 응답에 토큰과 주소 없음 |
| 6 | 쓰기 요청 | `invoice-mailer`가 `tool-mail-send` 호출 | `waiting_approval`로 멈춤 |
| 7 | 승인 후 재개 | `finance.approver`가 이 요청에 묶인 승인 제출 | 메일 1건 발송 |

## 실패 사례

| 바꾼 조건 | 앱이 받은 응답 | 내부 진단 |
|---|---|---|
| `invoice-summary` 코드가 Manifest에 없는 `tool-mail-send`를 호출 | 403 `Tool is not declared in the Agent Manifest` | 실행 중 거절. Manifest에 추가해 새 버전으로 등록해야 합니다 |
| 등록되지 않은 `tool-fax-send`를 호출 | 403 `Policy denied` | `Tool not approved` |
| `invoice-mailer`가 승인 없이 `tool-mail-send`를 호출 | 403 `Policy denied` | `Write tool requires approval` |
| 만료된 승인, 또는 다른 요청에서 받은 승인을 붙임 | 403 `Policy denied` | `Approval is stale or not bound to this request` |
| 승인된 발송 중 메일 서버 응답이 끊김 | 실패 응답 | `unknown_outcome`. 메일 서버의 발송 기록과 대조합니다 |

## 직접 해 보기

<div class="sim" data-sim="tool-call"></div>

<ol class="mission">
<li>코드에서 Manifest에 없는 도구를 불러 보세요. 이것은 등록 실패인가요, 등록한 코드가 실행 중에 거절된 것인가요.</li>
<li>쓰기 도구에 다른 요청에서 받은 승인을 붙여 보세요. 앱은 무엇을 받나요. 승인이 아예 없을 때와 구별할 수 있나요.</li>
</ol>

**내 PC에서 해 보기** 저장소 루트에서 실행합니다. 로컬에서는 예시의 이름 대신 아래 mock 도구를 씁니다.

| 예시 | 내 PC |
|---|---|
| `tool-erp-read` `1.0.0` | `tool-search` `0.1.0` |
| 테넌트 `finance` | `tenant-demo` |
| `finance.analyst`의 토큰 | `Bearer mock-user` |

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

`output.content` 안의 `tool:청구서 INV-2048 요약해 줘`가 도구가 돌려준 값입니다. 로컬 mock 도구는 받은 검색어 앞에 `tool:`을, mock 모델은 받은 글 앞에 `mock:`을 붙여 돌려주므로 실제 요약은 나오지 않습니다. 호출 번호와 추적 번호는 실행할 때마다 달라집니다. 쓰기와 승인은 `make scenarios`의 S5, S6a 줄에서 확인합니다(PostgreSQL이 필요합니다. [로컬 환경 구성](07-hands-on.md)).

## 코드로 보기: 도구 경로를 붙인다

[Agent Platform APIs를 붙인](03-one-request.md) 코드에 두 번째 조각을 붙입니다. 이번에 지울 것은 Agent 코드에 남아 있는 비밀번호 한 줄입니다.

{{blocks:2}}

### 도구 경로가 없을 때

Agent Platform APIs까지 붙인 Agent의 코드입니다.

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

코드로 옮기면 `mini_platform.py`에 다음이 더해집니다.

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

`enter()`는 한 줄만 바뀝니다. Agent를 호출할 때 `Context` 객체를 함께 넘깁니다.

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

비밀번호 줄이 사라졌고, ERP를 직접 부르던 줄이 `ctx.call_tool`로 바뀌었습니다. `ctx`는 플랫폼이 넘겨주는 `Context` 객체입니다. Agent가 외부를 호출하는 경로가 이 객체 하나로 좁아지면, 플랫폼은 그 한 곳에서만 검사하고 기록하면 됩니다. 마지막 줄의 `world.model`은 아직 직접 호출로 남아 있습니다.

### 검사 결과

같은 검사 여섯 개를 다시 돌린 결과입니다(`python examples/build/check.py step2`).

<!-- kind: run boundary: local -->
```text
응답 {'status': 200, 'output': '요약: 한빛상사 12,400,000원, 납기 2026-11-30'}
PASS 1 토큰 없는 요청은 거절한다
PASS 2 같은 요청이 두 번 와도 한 번만 실행한다
PASS 3 Agent 코드에 ERP 비밀번호가 없다
PASS 4 Manifest에 없는 도구는 부를 수 없다
FAIL 5 권한이 모자란 사용자(finance.viewer)는 거절한다
FAIL 6 Agent 코드가 모델을 직접 부르지 않는다
4/6
```

이번에도 호출자가 받는 응답은 그대로입니다. 새로 통과한 두 검사는 이렇게 생겼습니다.

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
| `VAULT` | Credential Broker. 비밀번호 대신 이 호출에만 묶인 lease(실제 자격증명을 가리키는 불투명 참조)를 발급합니다 |
| `Context.call_tool` | Agent Gateway의 도구 경로. 호출마다 정책을 확인하고 기록합니다 |
| `manifest.json` | Agent Manifest의 `capabilities.tools` |
| `PermissionError` | 403 |

남은 FAIL 두 줄이 다음에 붙일 조각입니다. 검사 5는 같은 Agent를 호출해도 호출자의 권한에 따라 결과가 달라야 한다는 것이고(Agent Identity), 검사 6은 모델도 도구처럼 플랫폼을 거쳐 불러야 한다는 것입니다(Agent Gateway).

다음 단계는 ⑤ 권한 위임입니다. 같은 Agent라도 `finance.analyst`의 호출은 실행되고 `finance.viewer`의 호출은 거절되는 이유를 봅니다.
