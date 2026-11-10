# 내 Agent 연결과 적합성 검증

> 개발자 가이드 문서입니다. 규범은 [Core Systems](../core-systems.md)와 Agent Adapter 결정([ADR-037](../../adr/ADR-037.md))이 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Adapter](09-glossary.md#term-adapter-kit) [AgentContext](09-glossary.md#term-agent-context) [적합성 검사](09-glossary.md#term-conformance) [Manifest](09-glossary.md#term-manifest) [Agent Factory](09-glossary.md#term-factory)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 실습 목표**

- 템플릿을 복사해 자신의 Agent adapter와 Manifest를 작성합니다.
- 플랫폼 핵심 코드를 수정하지 않고 새 Agent ID로 Agent를 호출합니다.
- `agentctl conformance`로 11개 적합성 검사를 통과하고, 각 검사가 무엇을 보장하는지 구분합니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> 예제 Agent를 호출하는 것만으로는, 자신의 Agent를 어떤 인터페이스로 구현하고 어떻게 등록하는지 알 수 없습니다.

<span class="tag">{{icon:eye}} 현황</span> Agent마다 프레임워크와 로직이 다르지만, 인증·인가·데이터 분류·멱등성·도구 권한 같은 규칙은 모든 Agent에 동일하게 적용되어야 합니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> Agent는 **업무 로직만 담은 adapter**를 구현하고, 규칙은 플랫폼이 적용합니다. 규칙 준수 여부는 **적합성 검사**로 자동 확인합니다.
</div>

## Adapter 인터페이스

Agent는 `handle(ctx, message)` 하나를 구현합니다. `message`는 호출 요청의 `input`(`type`, `content`)이고, 반환값은 결과의 `output`(`{"type": "message", "content": "..."}`)입니다.

```python
class MyAgent:
    def handle(self, ctx, message):
        answer = ctx.generate("Answer briefly: " + message["content"])
        return {"type": "message", "content": answer}


def create():
    return MyAgent()
```

<div class="cards">
<div class="card">{{icon:model}}<b>ctx.generate(prompt)</b><p>Agent Gateway 모델 경로를 호출하고 응답 텍스트를 반환합니다. 데이터 분류에 따른 경로 선택은 플랫폼이 수행합니다.</p></div>
<div class="card">{{icon:tools}}<b>ctx.call_tool(id, version, args)</b><p>Manifest `capabilities.tools`에 선언한 도구만 호출합니다. 자격증명은 플랫폼 내부에서 발급·사용되며, 결과 텍스트만 반환됩니다.</p></div>
<div class="card">{{icon:eye}}<b>ctx.log(event, **fields)</b><p>감사 기록에 이벤트를 남깁니다. 허용된 필드만 기록됩니다.</p></div>
</div>

<div class="compare" markdown="1">
<div class="good" markdown="1">
**{{icon:check}} 플랫폼이 담당하는 것**

- 인증·인가, tenant 확인, 멱등성
- 데이터 분류에 따른 모델 경로
- 도구 권한 교집합, 자격증명 발급
- `invocationId`, `traceparent`, `routeDecisionId`, `usage` 등 결과 필드
</div>
<div class="bad" markdown="1">
**{{icon:cross}} adapter가 받지 않는 것**

- Identity, 정책, 토큰, lease
- Platform·Gateway 내부 객체
- 요청 헤더와 원본 envelope
</div>
</div>

## 연결 절차

<ol class="flow">
<li data-say="templates/agents/ 아래 템플릿 폴더를 통째로 복사해 시작합니다.">{{icon:code}}<b>템플릿 복사</b><span><code>templates/agents/</code></span></li>
<li data-say="Manifest에서 Agent ID, 이름, 사용할 도구를 내 Agent에 맞게 바꿉니다.">{{icon:manifest}}<b>Manifest 수정</b><span>ID·이름·도구</span></li>
<li data-say="agent.py의 handle 함수에 Agent가 할 일을 작성합니다. 모델과 도구는 ctx로만 부릅니다.">{{icon:runtime}}<b>adapter 작성</b><span><code>agent.py</code>의 <code>handle</code></span></li>
<li data-say="validate로 Manifest를, conformance로 플랫폼 규칙 11가지를 확인합니다.">{{icon:test}}<b>검증·적합성</b><span><code>validate</code> · <code>conformance</code></span></li>
<li data-say="로컬 플랫폼을 띄우고 새 Agent ID로 호출해 응답을 확인합니다." class="hi">{{icon:gateway}}<b>호출</b><span>새 Agent ID로 실행</span></li>
</ol>

<div class="sim" data-sim="conformance"></div>

### 1. 템플릿 복사

```sh
mkdir -p my-agents
cp -r templates/agents/tool my-agents/order-agent
```

| 템플릿 | 내용 |
|---|---|
| `templates/agents/message` | 모델만 호출하는 `message` 유형 Agent |
| `templates/agents/tool` | 로컬 mock 도구 `tool-search` 0.1.0(인자 `{"query": str}`)을 호출한 뒤 모델로 요약하는 `tool` 유형 Agent |

### 2. Manifest 수정

`my-agents/order-agent/agent-manifest.json`에서 다음을 바꿉니다.

| 필드 | 값 | 규칙 |
|---|---|---|
| `metadata.id` | `order-agent` | 소문자로 시작, 다른 Agent와 중복 불가 |
| `metadata.name` | `Order Agent` | 표시 이름 |
| `capabilities.tools` | `["tool-search"]` | 호출할 도구를 모두 선언 |
| `runtime.adapter` | `python-inprocess-v1` | 변경하지 않음 |
| `runtime.entrypoint` | `agent:create` | `모듈:factory`. 모듈은 Agent 폴더 바로 아래 파일이어야 함 |
| `deployment.profile` | `local` | 로컬 Registry는 `local`만 허용 |
| `governance.classification` | `internal` | 이 Agent가 다루는 데이터의 서버 측 분류. 호출자가 낮출 수 없음 |

### 3. adapter 작성

`agent.py`의 `handle()`에 업무 로직을 작성합니다. `create()`는 adapter 인스턴스를 반환합니다.

### 4. 검증과 적합성

```sh
.venv/bin/python scripts/agentctl.py validate my-agents/order-agent/agent-manifest.json
.venv/bin/python scripts/agentctl.py conformance my-agents/order-agent
```

```text
PASS  C1   manifest-loading      Manifest and registration  Manifest valid, adapter python-inprocess-v1, profile local
PASS  C2   adapter-path          Successful call  200, result.schema valid
...
PASS  C11  platform-enforcement  Manifest identity.mode  delegated runs as the caller; independent runs as the Agent workload ...
NOTE  Local conformance covers Manifest loading, this adapter's basic path and platform rule enforcement. It is not a business-quality, security or production certification.
```

검사가 하나라도 실패하면 종료 코드 1을 반환합니다. CI에서 그대로 사용할 수 있습니다.

### 5. 실행과 호출

```sh
.venv/bin/python scripts/agentctl.py run --agents-dir my-agents
```

```text
Local synthetic Agent Gateway: http://127.0.0.1:8765 ; agents: agent-demo, order-agent ; Ctrl-C to stop
```

다른 터미널에서 새 Agent ID로 호출합니다.

```sh
curl -X POST http://127.0.0.1:8765/v1/agents/order-agent/invocations \
  -H "Content-Type: application/json" -H "Authorization: Bearer mock-user" -H "Idempotency-Key: order-1" \
  -d '{"input":{"type":"message","content":"hello"},"context":{"tenantId":"tenant-demo","dataClassification":"internal"},"execution":{"mode":"sync","timeoutMs":5000}}'
```

## 적합성 검사 11항목

| ID | 구분 | 검사 | 기대 결과 |
|---|---|---|---|
| C1 | manifest-loading | Manifest와 등록 | Manifest 유효, `python-inprocess-v1`, `local` 프로파일 |
| C2 | adapter-path | 정상 호출 | 200, `result.schema` 적합 |
| C3 | platform-enforcement | 토큰 없음 | 401, adapter 미실행 |
| C4 | platform-enforcement | tenant 위조 | 403, adapter 미실행 |
| C5 | platform-enforcement | 같은 멱등성 키 재전송 | 저장 결과 반환, adapter 1회 실행 |
| C6 | platform-enforcement | 같은 키·다른 내용 | 409 |
| C7 | platform-enforcement | 분류 하향 선언 + 외부 모델만 가용 | 외부 모델 경로 미사용. 모델을 호출하지 않는 adapter는 플랫폼 규칙만 확인됨을 결과에 표시 |
| C8 | platform-enforcement | 미선언 도구 호출, 응답의 자격증명 형태 문자열 | 403, 응답에 자격증명 형태 문자열 없음 |
| C9 | platform-enforcement | adapter 예외 | 500, 예외 메시지 미포함, 실패 결과 미저장 |
| C10 | platform-enforcement | Manifest `requiredScopes`에 호출자가 갖지 않은 scope 추가 | 403, adapter 미실행 |
| C11 | platform-enforcement | Manifest `identity.mode` | `delegated`는 호출자 신원, `independent`는 사용자 principal 없는 workload 신원 |

모든 판정은 응답, 감사 기록, 호출 횟수 등 플랫폼 경계에서 수행합니다. 구분별 보장 범위는 다음과 같습니다.

| 구분 | PASS의 의미 | 보장하지 않는 것 |
|---|---|---|
| `manifest-loading` | Manifest가 유효하고 로컬 Registry가 받아들임 | 소스·artifact의 실제 내용 |
| `adapter-path` | 이 adapter가 자기 코드 경로로 유효한 결과를 만듦 | 응답의 정확성·업무 품질 |
| `platform-enforcement` | 이 adapter 주변에서 플랫폼 규칙이 집행되고 adapter가 규칙을 약화하지 못함 | adapter의 모든 실패 동작, 모든 형태의 정보 유출 탐지 |

C8의 자격증명 형태 검사는 일부 문자열 패턴을 찾는 휴리스틱이며 모든 자격증명·개인정보 유출을 탐지하지 않습니다. 업무 품질은 [평가 3단계](12-observability-evaluation.md), 운영 승인은 [수명주기](06-lifecycle.md)에서 별도로 판단합니다. 적합성 PASS는 업무 품질·보안·프로덕션 인증이 아닙니다.

## 신원 모드: delegated와 independent

`identity.mode`는 adapter가 누구의 권한으로 모델과 도구를 호출하는지 정합니다. 두 모드 모두 호출자는 `requiredScopes`를 모두 보유해야 하며, 차이는 adapter 실행 중에 쓰이는 신원과 권한입니다.

| 항목 | `delegated` | `independent` |
|---|---|---|
| 실행 신원 | 호출자 신원 | Agent workload 신원 |
| 사용자 principal | 포함 | 포함하지 않음 |
| 위임 체인(delegation) | 호출자의 위임 그대로 | 빈 목록 |
| 모델·도구 호출 권한 | 호출자 권한과 정책의 교집합 | Manifest `requiredScopes`와 정책의 교집합 |
| 적합한 용도 | 사용자를 대신해 그 사용자의 데이터에 접근 | 사용자와 무관한 배치·집계 작업 |

`independent` Agent의 권한은 Manifest에 선언한 scope에서만 나옵니다. 따라서 adapter가 쓰는 경로의 scope를 모두 선언해야 합니다(MUST).

| adapter가 호출하는 경로 | 필요한 scope |
|---|---|
| Agent 호출 자체 | `agents.invoke` |
| `ctx.generate` (모델 경로) | `models.invoke` |
| `ctx.call_tool` (도구 경로) | `tools.read` |

`tool` 템플릿을 `independent`로 바꾼 예입니다. 도구와 모델을 모두 호출하므로 세 scope가 필요합니다.

```json
"identity": {
  "mode": "independent",
  "requiredScopes": ["agents.invoke", "models.invoke", "tools.read"]
}
```

음성 예입니다. 같은 Agent에서 `tools.read`를 빼면 adapter는 실행되지만 `ctx.call_tool`에서 403으로 실패합니다. `models.invoke`를 빼면 `ctx.generate`에서 같은 이유로 실패합니다. `delegated` 모드에서는 호출자가 해당 scope를 보유하므로 같은 Manifest가 성공할 수 있습니다. 모드를 바꾼 뒤 403이 발생하면 먼저 이 표와 `requiredScopes`를 대조합니다.

신원 원문은 응답에 포함되지 않습니다. 모드별 신원은 테스트에서 실행 envelope으로 확인합니다(`tests/test_conformance.py`의 `ManifestEnforcementTests`: 사용자 principal 유무, workload 모드, 허용 scope). 로컬 mock의 workload 권한은 Manifest와 정책에서 계산한 값이며, 실제 workload grant 발급·검증은 회사 Identity 연동 단계에서 제공합니다.

<div class="sim" data-sim="permission"></div>

## Manifest 필드 지원 범위 (로컬 mock)

| 필드 | 처리 | 내용 |
|---|---|---|
| `apiVersion`, `kind`, 전체 구조 | 검증됨 | JSON Schema(계약 0.1.1) 검증 |
| `metadata.id`, `metadata.version` | 실행에 사용 | Agent ID 라우팅, 결과의 `agentVersion`, 멱등성 키 |
| `metadata.owner`, `metadata.name` | 검증만 | 실행 동작에 영향 없음 |
| `source.*` | 검증만 | 불변 revision·digest 형식 검사. 실제 artifact 대조는 하지 않음 |
| `runtime.adapter` | 실행에 사용 | `python-inprocess-v1`만 허용, 그 외 등록 거부 |
| `runtime.entrypoint` | 실행에 사용 | `module:factory`, Agent 폴더 안의 파일만 |
| `runtime.executionMode` | 실행에 사용 | `sync`만 허용, 그 외 등록 거부 |
| `runtime.framework` | 메타데이터만 | 실행 동작에 영향 없음 |
| `capabilities.type` | 검증만 | 유형별 필수 목록 검사(`tool`은 도구 1개 이상) |
| `capabilities.tools` | 실행에 사용 | 선언한 도구만 `ctx.call_tool` 허용, 정책과 교집합 |
| `capabilities.knowledge`, `capabilities.agents` | 미지원 | 로컬 mock에 검색·하위 Agent 호출 경로 없음 |
| `identity.requiredScopes` | 실행에 사용 | 호출자가 모두 보유해야 adapter 실행. `independent`에서는 정책과 교집합한 값이 Agent workload 권한 |
| `identity.mode` | 실행에 사용 | `delegated`는 호출자 신원, `independent`는 사용자 principal 없는 Agent workload 신원으로 실행 |
| `governance.classification` | 실행에 사용 | 서버 측 분류. 호출자 선언·정책과 비교해 가장 높은 값 적용 |
| `governance.risk`, `policyProfile`, `evaluationProfile` | 메타데이터만 | 위험도별 승인·평가 연동은 미구현 |
| `deployment.profile` | 실행에 사용 | `local`만 등록 |
| `deployment.environmentRef` | 메타데이터만 | 실행 동작에 영향 없음 |
| `contracts.inputSchema`, `outputSchema` | 메타데이터만 | 실제 입출력은 플랫폼의 invocation·result 스키마로 검증 |

## 제약과 한계

<div class="point" markdown="1">
**{{icon:warn}} in-process 로딩은 격리 경계가 아닙니다** 로딩된 adapter 코드는 같은 프로세스의 내부 객체에 접근할 수 있습니다. 이 방식은 로컬 학습과 적합성 확인 전용이며, 신뢰하지 않는 코드에 사용해서는 안 됩니다(MUST NOT). 격리된 실행은 후속 단계의 원격 adapter로 제공합니다.
</div>

- entrypoint 모듈은 Agent 폴더 바로 아래 파일만 허용합니다. 폴더 밖 경로와 폴더 밖을 가리키는 링크는 거부합니다.
- adapter는 전역 잠금 안에서 실행되며 `timeoutMs`가 적용되지 않습니다.
- 로컬 mock 도구는 `tool-search` 0.1.0 하나입니다.
- `async`, `durable` 실행 모드는 지원하지 않습니다.

## 문제 해결

| 증상 | 원인 | 해결 |
|---|---|---|
| C1 `Unsupported runtime.adapter` | `runtime.adapter` 값이 다름 | `python-inprocess-v1`로 설정 |
| C1 `runtime.entrypoint must be module:factory` | 경로나 점이 포함됨 | `agent:create`처럼 식별자만 사용 |
| C1 `Duplicate Agent id` | 다른 Agent와 ID가 같음 | `metadata.id` 변경 |
| C2 `invalid result` | `content`가 비었거나 형식이 다름 | `{"type": "message", "content": "<비어 있지 않은 텍스트>"}` 반환 |
| C8 `credential-like text` | 응답에 토큰·lease 형태 문자열 포함 | 응답에서 해당 문자열 제거 |
| 호출 시 403 `Tool is not declared` | Manifest에 도구 미선언 | `capabilities.tools`에 추가 |
| `independent`로 바꾼 뒤 403 | workload 권한에 경로 scope 없음 | `requiredScopes`에 `models.invoke`·`tools.read` 선언 |

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. adapter가 사용자 Identity나 토큰에 접근할 수 있습니까?</summary>
공개 adapter 인터페이스(<code>AgentContext</code>의 <code>generate</code>, <code>call_tool</code>, <code>log</code>)는 Identity·정책·자격증명을 제공하지 않으며, 플랫폼이 호출 내부에서 주입합니다. 다만 in-process adapter는 같은 프로세스에서 실행되므로 언어 수준의 접근(비공개 속성, closure 조사 등)을 보안적으로 차단하지 않습니다. 이 방식은 신뢰된 코드에만 사용하며, 신뢰하지 않는 코드는 별도 프로세스·원격 adapter에서 실행해야 합니다.
</details>

<details markdown="1"><summary>Q2. 새 Agent를 연결할 때 플랫폼 코드를 수정해야 합니까?</summary>
수정하지 않습니다. Agent 폴더(Manifest와 adapter)를 만들고 <code>agentctl run --agents-dir</code>로 등록합니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- Agent는 `handle(ctx, message)`를 구현하는 adapter로 연결하며, `requiredScopes`·`identity.mode`·분류·도구 목록 등 Manifest 선언은 플랫폼이 집행합니다.
- 템플릿 복사 → Manifest 수정 → adapter 작성 → `conformance` 통과 → 새 ID로 호출 순서로 진행합니다.
- in-process 로딩은 로컬 학습·적합성 확인 전용이며 격리 경계가 아닙니다.
</div>

<nav class="pager"><a href="07-hands-on.md"><small>이전</small><b>로컬 환경 구성 및 호출 실습</b></a><a class="next" href="08-reading-the-spec.md"><small>다음</small><b>기술 표준 해석과 FAQ</b></a></nav>
