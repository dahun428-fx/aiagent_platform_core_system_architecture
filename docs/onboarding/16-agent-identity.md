# Agent Identity

> 개발자 가이드 문서입니다. 규범은 [Agent Identity](../identity-and-credentials.md), [보안 경계](../security.md) 기술 표준 문서가 기준입니다.

{{journey:5}}

<div class="sofar" markdown="1">
**지금까지** 서연이 부른 `invoice-summary`가 `tool-erp-read`로 청구서를 읽었습니다. 메일 보내기(요청 C)는 다른 Agent `invoice-mailer`가 맡고, 지훈의 승인을 기다립니다.
</div>

## 장면

같은 날 인턴 하준이 서연과 똑같은 문장으로 `invoice-summary`를 부릅니다. 서연은 요약을 받았는데 하준은 403을 받습니다. Agent도 같고 질문도 같습니다. 다른 것은 부른 사람입니다. 하준에게는 Agent를 부를 권한만 있고, 모델과 ERP 읽기 권한이 없습니다. Agent는 자기 권한으로 일하는 것이 아니라 부른 사람의 권한 안에서 일합니다.

<div class="point" markdown="1">
**{{icon:bulb}} Agent Identity가 없다면** Agent를 부를 수 있는 사람은 누구나 Agent가 닿는 모든 데이터를 볼 수 있게 됩니다.
</div>

## 무슨 일이 일어나나

<ol class="flow">
<li data-say="정문이 토큰에서 서연이 누구이고 어떤 권한을 가졌는지 확인합니다.">{{icon:user}}<b>1. 부른 사람의 권한을 확인한다</b><span>토큰 → 테넌트 · scope</span></li>
<li data-say="Agent의 Manifest가 요구하는 권한을 서연이 모두 갖고 있는지 맞춰 봅니다. 하나라도 없으면 코드를 실행하지 않습니다." class="hi">{{icon:manifest}}<b>2. Agent가 요구하는 권한과 맞춰 본다</b><span>requiredScopes</span></li>
<li data-say="실행 중에 도구를 부를 때 한 번 더 봅니다. 그 도구가 Manifest에 있는지, 그 도구가 요구하는 권한이 있는지입니다.">{{icon:tools}}<b>3. 도구를 부를 때 한 번 더 본다</b><span>도구 목록 · 실행 중 권한</span></li>
<li data-say="마지막으로 이 호출 한 번에만 쓸 수 있고 곧 사라지는 출입증(lease)으로 ERP에 들어갑니다. Agent는 이 출입증을 꺼내 갈 수 없습니다.">{{icon:key}}<b>4. 잠깐 쓰는 출입증으로 들어간다</b><span>lease</span></li>
</ol>

## 실물 보기

요청 A가 지나는 관문을 서연과 하준의 값으로 채운 표입니다.

<!-- kind: example -->

| 관문 | 보는 것 | 서연 | 하준 |
|---|---|---|---|
| 테넌트 | 본문에 적은 테넌트가 토큰의 테넌트와 같은가 | 통과 | 통과 |
| 진입 | Manifest `requiredScopes` 세 개가 모두 호출자 권한과 정책이 겹치는 범위에 있는가 | 통과 | 403. `models.invoke`와 `tools.read`가 없음. 코드가 실행되지 않음 |
| 도구 목록 | 부르려는 도구가 Manifest `capabilities.tools`에 있는가 | `tool-erp-read` 통과 | 여기까지 오지 않음 |
| 실행 중 권한 | 겹치는 범위에 도구가 요구하는 scope가 있는가 | `tools.read` 통과 | 여기까지 오지 않음 |

- 서연의 권한은 `agents.invoke`, `models.invoke`, `tools.read`, `tools.write`입니다. 하준은 `agents.invoke` 하나입니다.
- "겹치는 범위"는 호출자가 가진 권한과 회사 정책이 허용한 권한에 모두 들어 있는 것입니다. 서연이 권한을 가졌어도 정책이 막으면 없는 것과 같습니다.
- 403이 나면 위에서부터 봅니다. 앞 관문에서 막히면 뒤 관문은 보지 않기 때문입니다.

마지막 관문에서 쓰는 출입증(lease)입니다. 저장소 fixture `examples/fixtures/credential-lease.json`입니다.

<!-- kind: run boundary: local -->

```json
{
  "credentialRef": "lease-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "audience": "tool-search",
  "scopes": ["tools.read"],
  "expiresAt": "2099-01-01T00:00:00Z",
  "nonExportable": true
}
```

- `credentialRef`: 비밀번호가 아니라 번호표입니다. 이 값을 알아도 ERP에 직접 들어갈 수 없습니다.
- `audience`와 `scopes`: 어느 도구에 어떤 권한으로만 쓸 수 있는지입니다. 다른 도구에는 쓸 수 없습니다.
- `expiresAt`: 언제까지인지입니다. fixture는 형식 검증용이라 먼 날짜가 적혀 있고, 로컬 mock이 실제로 발급하는 lease는 60초 뒤 만료되며 한 번 쓰면 다시 쓸 수 없습니다.
- `nonExportable`: Agent 코드와 모델에게 넘어가지 않는다는 표시입니다. 실제 자격증명으로 바꾸는 일은 신뢰 경계 안쪽에서만 일어납니다.

<details class="more" markdown="1"><summary>더 보기: 요청 C의 관문, 그리고 "만약에" 다섯 가지</summary>

요청 C(`invoice-mailer`, 메일을 보냄)를 서연이 보낼 때입니다. `tools.write`라는 이름과 쓰기 승인은 로컬 mock에 없고 참조 구현의 S6a 시나리오에 있으므로 이 표는 예시입니다.

| 관문 | 보는 것 | 서연 |
|---|---|---|
| 진입 | `requiredScopes` 네 개(`tools.write` 포함) | 통과 |
| 도구 목록 | `tool-mail-send`가 `capabilities.tools`에 있는가 | 통과 |
| 실행 중 권한 | 겹치는 범위에 `tools.write`가 있는가 | 통과 |
| 쓰기 승인 | 이 요청에 묶인 유효한 승인이 있는가 | 지훈이 승인하기 전에는 실행이 멈춰 기다림. 승인 없는 호출이 도구 경로에 닿으면 앱은 403 `Policy denied` |

- **회사 정책이 이 테넌트의 `tools.read`를 막았다면** 서연이 권한을 가졌어도 진입 관문에서 403입니다.
- **민준이 `requiredScopes`에서 `tools.read`를 빠뜨렸다면** `tools.read`가 없는 사용자도 진입을 통과하고, 코드가 도구를 부르는 순간 실행 중 권한 관문에서 403이 납니다. 그래서 도구가 요구하는 scope를 `requiredScopes`에 모두 적어 일찍 막습니다.
- **서연에게 `tools.write`가 없었다면** 요청 A는 그대로 되고, 요청 C는 진입 관문에서 403이라 `invoice-mailer`의 코드가 실행되지 않습니다.
- **`invoice-summary`가 `tool-mail-send`를 부르려 하면** 서연의 권한과 상관없이 도구 목록 관문에서 403입니다.
- **신원 모드가 `independent`라면** 실행 중 권한은 호출자가 아니라 Manifest 선언과 정책이 겹치는 범위로 정해지고, 사용자의 신원은 실리지 않습니다. 사용자가 없는 예약 작업에 씁니다.

작은 사례 `expense-settlement`(출장 정산 Agent)가 `invoice-summary`를 부를 때, 하위 Agent에 넘어가는 권한은 상위 Agent가 가진 권한을 넘을 수 없습니다. Agent를 여러 번 거쳐도 권한은 줄어들 뿐 늘지 않습니다.
</details>

## 직접 해 보기

<div class="sim" data-sim="authz"></div>

<ol class="mission">
<li>"하준의 권한으로"를 눌러 보세요. 하준이 통과하려면 무엇이 필요한가요.</li>
<li>서연의 <code>tools.write</code>를 끄면 요청 A와 요청 C는 각각 어디까지 가나요.</li>
<li>Manifest의 <code>requiredScopes</code>에서 <code>tools.read</code>를 빠뜨리고 호출자의 <code>tools.read</code>를 꺼 보세요. 어느 관문에서 막히나요.</li>
</ol>

## 잘못되면

**하준이 `invoice-summary`를 부르면** 403을 받습니다. 로컬 mock의 응답 본문에는 `Caller lacks a scope required by the Agent Manifest`라고 적혀 있습니다. Agent 코드는 한 줄도 실행되지 않았습니다. 고치는 방법은 코드가 아니라 권한입니다. 하준에게 필요한 권한을 주거나, 하준이 부르지 않도록 합니다.

**민준이 테스트하면서 요청 본문에 다른 팀의 테넌트를 적으면** 403 `Tenant assertion does not match authenticated identity`를 받습니다. 테넌트는 토큰에서만 정해지고 본문의 값은 비교에만 쓰입니다. 본문을 바꿔 다른 팀의 데이터에 닿는 길은 없습니다.

<details class="more" markdown="1"><summary>더 보기: 만료된 lease, 그리고 내부 구간의 거절</summary>

**만료됐거나 이미 쓴 lease를 다시 쓰면** 로컬 mock은 403 `Credential lease binding or expiry denied`로 거절합니다. lease는 발급받은 workload, 호출 번호, 대상 도구에 묶여 있어 다른 호출이 주워 써도 통하지 않습니다.

아래는 앱이 보는 값이 아니라 참조 구현의 모델 경로를 직접 호출했을 때의 값입니다.

<!-- kind: run boundary: route -->

| 상황 | 모델 경로의 응답 | 시나리오 |
|---|---|---|
| 내부 신원의 테넌트가 정책의 테넌트와 다름 | 403 `Policy denied` | S1 `tenant-mismatch` |
| 서명한 뒤 내용이 바뀜 | 403 `Internal signature missing or invalid` | S1 `tampered` |
| 필요한 scope가 없음 | 403 `Policy denied` | S1 `missing-scope` |

정문을 지났다고 안쪽 구간이 서로를 그냥 믿지 않습니다. 구간마다 신원과 서명을 다시 확인합니다.
</details>

## 내가 할 일

1. 신원 모드를 고릅니다. 사용자를 대신해 일하면 `delegated`, 예약 작업처럼 사용자가 없으면 `independent`입니다.
2. Manifest `identity.requiredScopes`에 Agent가 쓰는 모델과 도구의 scope를 모두 적습니다.
3. 코드에 자격증명을 넣지 않습니다. 넣을 자리도 없습니다.
4. 403이 나면 관문을 위에서부터 확인합니다. 테넌트, 진입, 도구 목록, 실행 중 권한 순서입니다.

**내 PC에서 해 보기** 적합성 검사의 C4(테넌트 위조), C10(Manifest requiredScopes), C11(identity.mode)이 이 장의 관문을 실제로 확인합니다. 출력 11줄 가운데 세 줄입니다.

```bash
python scripts/agentctl.py conformance examples/agents/invoice-summary
```

<!-- kind: run boundary: local -->

```text
PASS  C4   platform-enforcement  Tenant spoof  403 on tenant spoof, adapter not executed
PASS  C10  platform-enforcement  Manifest requiredScopes  caller without a Manifest requiredScopes entry is denied (403) before the adapter runs
PASS  C11  platform-enforcement  Manifest identity.mode  delegated runs as the caller; independent runs as the Agent workload without the user principal
```

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| 테넌트·진입·도구 목록·실행 중 권한 관문, lease 발급과 소비 | 실행 | 로컬 mock, 적합성 C4·C8·C10·C11 |
| 내부 구간의 서명과 신원 재확인 | 실행 | 참조 구현 S1 |
| `tools.write`와 쓰기 승인 관문 | 실행(도구 경로만) | 참조 구현 S6a |
| 회사 IdP 연동, 토큰 교환 | 정의 | [Agent Identity](../identity-and-credentials.md) |

로컬 mock의 사용자는 `Bearer mock-user` 하나뿐이라 하준은 시뮬레이터에서만 재현됩니다.
</div>

## 규칙으로 정리

- 신원과 테넌트는 검증된 토큰에서만 정합니다. 요청 본문의 값으로 권한을 주지 않습니다(MUST NOT). 장면 ⑤
- 실행 중 권한은 사용자 권한 ∩ Agent 권한 ∩ 도구 허용 범위 ∩ 정책을 넘을 수 없습니다(MUST). 장면 ⑤
- 사람의 신원, Agent workload의 신원, 바깥 시스템에 위임받은 자격증명은 서로 다른 것으로 다룹니다.
- 자격증명 원문은 Runtime과 모델에 넘기지 않습니다. 단기, 호출 결합형, 내보낼 수 없는 lease만 씁니다(MUST).
- 토큰을 받은 그대로 다음 시스템에 넘기지 않습니다(token passthrough 금지). 대상(audience)이 정해진 토큰만 씁니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Identity](09-glossary.md#term-agent-identity) [scope](09-glossary.md#term-scope) [위임 모드](09-glossary.md#term-delegated) [identity context](09-glossary.md#term-identity-context) [Credential Broker](09-glossary.md#term-credential-broker) [Lease](09-glossary.md#term-lease) [테넌트](09-glossary.md#term-tenant)
</div>

## 한 문장으로

Agent가 할 수 있는 일은 부른 사람이 할 수 있는 일을 넘지 못합니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 같은 Agent인데 왜 서연은 되고 하준은 안 되나요?</summary>
Agent의 Manifest가 요구하는 권한 세 개를 서연은 모두 갖고 있고 하준은 하나만 갖고 있기 때문입니다. Agent는 부른 사람의 권한 안에서만 일합니다.
</details>

<details markdown="1"><summary>Q2. 403을 받았습니다. 어느 관문부터 확인하나요?</summary>
위에서부터입니다. 테넌트, 진입(requiredScopes), 도구 목록, 실행 중 권한 순서로 봅니다. 앞에서 막히면 뒤는 검사하지 않습니다.
</details>

<details markdown="1"><summary>Q3. 민준이 requiredScopes에 tools.read를 적지 않았습니다. tools.read가 없는 사용자가 부르면 어떻게 되나요?</summary>
진입 관문은 통과하고 코드가 실행되지만, 도구를 부르는 순간 실행 중 권한 관문에서 403이 납니다. 미리 적어 두면 코드가 실행되기 전에 막힙니다.
</details>
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- 토큰 교환과 위임: [IETF·OAuth](10-references.md#ref-identity)
- 도구 연결의 인가: [MCP](10-references.md#ref-mcp)
</div>

다음 장면은 ⑥입니다. 요약을 만들려는 순간 모델이 오류를 냅니다.
