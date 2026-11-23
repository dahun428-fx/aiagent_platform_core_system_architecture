# Agent Card와 Agent 간 통신

> 개발자 가이드 문서입니다. 규범은 [Agent Card](../agent-card.md) 기술 표준 문서와 A2A 1.0.0 명세가 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Card](09-glossary.md#term-agent-card) [A2A](09-glossary.md#term-a2a) [확장 Agent Card](09-glossary.md#term-extended-card) [JWS · JCS](09-glossary.md#term-jws) [Registry](09-glossary.md#term-registry)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- A2A Agent Card의 필수·선택 필드를 설명할 수 있습니다.
- 공개 카드와 인증된 확장 카드의 차이를 설명할 수 있습니다.
- Agent Card의 서명과 검증 절차를 설명할 수 있습니다.
- Registry가 Agent Card를 발행하는 규칙을 설명할 수 있습니다.
</div>

## 장면

재무팀의 출장 정산 Agent `expense-settlement`는 정산 중에 청구서 요약이 필요합니다. 민준이 이미 만든 `invoice-summary`를 부르면 됩니다. 그런데 다른 팀의 개발자는 그 Agent가 무엇을 할 수 있는지, 어디로 어떻게 인증해 불러야 하는지, 지금도 승인된 버전인지 알아야 합니다. 메신저로 물어본 주소는 다음 달이면 틀릴 수 있고, 누가 바꿔 놓았는지도 알 수 없습니다. 그래서 Registry가 승인된 Agent마다 명함 한 장을 만들어 서명해 둡니다. 이것이 Agent Card입니다.

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> 다른 팀의 Agent를 호출하려면 그 Agent가 무엇을 할 수 있고, 어디로 어떻게 인증해 호출하는지 알아야 합니다.

<span class="tag">{{icon:eye}} 현황</span> Agent 정보를 팀마다 문서나 메신저로 주고받으면 그 정보가 지금도 맞는지, 누가 고쳐 놓지는 않았는지 확인할 길이 없습니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> Registry가 Manifest와 등록 정보로 **A2A Agent Card**를 만들고 **조직 키로 서명**해 발행합니다. 호출하는 쪽은 서명을 검증한 카드만 믿습니다.
</div>

## Agent 간 통신의 두 계층

| 계층 | 기준 | 역할 |
|---|---|---|
| 발견(discovery) | A2A 1.0.0 Agent Card | Agent의 기능, 접속 인터페이스, 인증 방식을 알림 |
| 호출 | 공통 Agent 통신 계약(`cross-agent.schema.json`) | 상위 호출 ID, 축소된 권한 범위, 호출 깊이·예산 전달 |

호출까지 A2A 프로토콜로 할지는 선택입니다. Agent를 찾는 데 필요한 정보는 Agent Card 형식으로 발행합니다.

## Agent Card 필드 (A2A 1.0.0)

| 필드 | 필수 | 내용 |
|---|---|---|
| `name`, `description`, `version` | 필수 | Agent 이름, 목적, 버전 |
| `supportedInterfaces` | 필수 | 접속 인터페이스 목록. **첫 항목이 우선**입니다 |
| `capabilities` | 필수 | `streaming`, `pushNotifications`, `extensions`, `extendedAgentCard` |
| `defaultInputModes`, `defaultOutputModes` | 필수 | 입출력 미디어 유형 |
| `skills` | 필수 | Agent 기능 목록 |
| `provider` | 선택 | `organization`, `url` |
| `securitySchemes`, `securityRequirements` | 선택 | 인증 방식과 요구 조건 |
| `signatures` | 선택 | JWS 서명 |
| `documentationUrl`, `iconUrl` | 선택 | 문서·아이콘 |

<div class="cards">
<div class="card">{{icon:gateway}}<b>AgentInterface</b><p><code>url</code>(HTTP는 HTTPS, gRPC는 <code>host:port</code>), <code>protocolBinding</code>(<code>JSONRPC</code>·<code>GRPC</code>·<code>HTTP+JSON</code>), <code>protocolVersion</code>, 선택 <code>tenant</code>. <code>tenant</code>가 있으면 클라이언트는 모든 요청에 그 값을 그대로 넣습니다.</p></div>
<div class="card">{{icon:tools}}<b>AgentSkill</b><p>필수 <code>id</code>, <code>name</code>, <code>description</code>, <code>tags</code>. 선택 <code>examples</code>, <code>inputModes</code>, <code>outputModes</code>, skill별 <code>securityRequirements</code>.</p></div>
<div class="card">{{icon:lock}}<b>SecurityScheme</b><p>API key, HTTP auth, OAuth 2.0, OpenID Connect, mTLS 중 정확히 하나입니다. OAuth 2.0은 Implicit·Password flow를 지원하지 않습니다.</p></div>
</div>

<div class="point" markdown="1">
**{{icon:warn}} 명세 표기 차이** A2A 1.0.0 명세는 필드 표에서 `securityRequirements`, 본문 일부에서 `AgentCard.security`로 표기합니다. 구현은 규범 원본인 `spec/a2a.proto`의 정의를 따릅니다.
</div>

## 공개 카드와 확장 카드

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 공개 카드에 두지 않는 정보**

- 사내 Agent의 내부 URL
- 민감한 skill 설명
- 시크릿·토큰 등 정적 자격증명
</div>
<div class="good" markdown="1">
**{{icon:check}} 플랫폼의 공개 범위**

- 사내 Agent: 공개 `/.well-known/agent-card.json` 없음, 인증된 Registry 조회로만 제공
- 외부 공개 Agent: `https://{domain}/.well-known/agent-card.json`에 최소 정보
- 상세 정보: 인증된 확장 카드로만 제공
</div>
</div>

<ol class="flow">
<li data-say="누구나 볼 수 있는 공개 카드를 먼저 읽고, 더 자세한 확장 카드가 있는지 확인합니다.">{{icon:manifest}}<b>공개 카드 조회</b><span><code>capabilities.extendedAgentCard: true</code> 확인</span></li>
<li data-say="공개 카드에 적힌 방식으로 로그인해 토큰을 받습니다.">{{icon:lock}}<b>인증</b><span>공개 카드에 선언된 인증 방식으로 토큰 획득</span></li>
<li data-say="토큰을 들고 확장 카드를 요청합니다. 권한 수준에 따라 보여 주는 내용이 다릅니다.">{{icon:identity}}<b>GetExtendedAgentCard</b><span>인증 수준에 따라 다른 내용 반환</span></li>
<li data-say="이번 세션 동안은 공개 카드 대신 확장 카드를 사용합니다.">{{icon:check}}<b>카드 교체</b><span>세션 동안 공개 카드 대신 사용</span></li>
</ol>

확장 카드는 반드시 인증을 요구합니다(MUST). 확장 카드라도 새어 나가면 악용될 수 있는 정보는 넣지 않습니다(SHOULD NOT). 플랫폼은 요청한 쪽의 권한 교집합에 맞춰 확장 카드의 내용을 줄여서 보여 줍니다.

## 서명과 검증

<ol class="flow">
<li data-say="서명 부분을 뺀 카드 내용을 항상 같은 모양으로 정리(정규화)합니다. 글자 순서나 공백이 달라도 같은 내용이면 같은 결과가 나오게 하기 위해서입니다.">{{icon:manifest}}<b>정규화</b><span><code>signatures</code> 제외 후 JCS(RFC 8785) 정규화</span></li>
<li data-say="정리한 내용에 조직 키로 서명합니다. 내용이 한 글자만 바뀌어도 서명이 맞지 않게 됩니다.">{{icon:key}}<b>서명</b><span>JWS(RFC 7515), 보호 헤더 <code>alg</code>·<code>typ</code>·<code>kid</code>, 선택 <code>jku</code></span></li>
<li data-say="Registry가 서명된 카드를 내놓습니다.">{{icon:gateway}}<b>발행</b><span>Registry가 조직 키로 서명한 카드 제공</span></li>
<li data-say="받는 쪽은 키를 찾아 같은 방식으로 정리한 뒤 서명을 확인합니다. 맞을 때만 카드를 믿습니다." class="hi">{{icon:shield}}<b>검증</b><span>키 조회(kid·jku) → 정규화 → 서명 검증 후 신뢰</span></li>
</ol>

<div class="sim" data-sim="card"></div>

```json
{"alg": "ES256", "typ": "JOSE", "kid": "key-1", "jku": "https://example.com/agent/jwks.json"}
```

- 카드를 받는 쪽은 서명을 검증한 카드만 믿습니다(MUST). 키는 HTTPS로 받거나 신뢰하는 키 저장소에서 가져옵니다.
- 만료되거나 폐기된 키는 쓰지 않습니다(MUST NOT). 키를 교체하는 동안에는 서명을 여러 개 둘 수 있습니다.
- 서명이 유효해도 skill 설명 같은 카드 내용은 비신뢰 데이터입니다. 카드에 무엇이 적혀 있든 권한 정책은 바뀌지 않습니다.

## Registry의 발행 규칙

| 규칙 | 내용 |
|---|---|
| 생성 | Registry가 Manifest와 등록 정보에서 만듭니다. 사람이 직접 쓴 카드는 받지 않습니다 |
| 필드 대응 | `metadata.name`·`version` → `name`·`version`, 기능 선언 → `skills`, `identity.requiredScopes` → 보안 요구, 승인된 실행 환경 endpoint → `supportedInterfaces`, `metadata.owner.team` → `provider.organization` |
| 상태 연동 | `production-approved` 버전만 발행하고, `deprecated`·`quarantined`·`retired`로 바뀌면 카드를 갱신하거나 회수합니다(상태 정의: [수명주기와 프로덕션 승인](06-lifecycle.md)) |
| 캐시 | `Cache-Control`과 카드 `version` 또는 내용 해시 기반 `ETag`를 제공합니다 |
| 버전 | A2A 1.0.0을 기준으로 하고 `A2A-Version` 헤더를 씁니다 |
| 조회 API | A2A는 레지스트리 API를 표준으로 정하지 않으므로 Agent Platform APIs에 Registry 조회 API를 정의합니다 |

## 제공 범위

v0.1은 Agent Card를 발행하고 사용하는 규칙까지 정의합니다. 카드를 만들고 서명하는 구현, Registry 조회 API 계약, A2A 프로토콜 adapter는 후속 단계에서 제공합니다.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. 사내 전용 Agent의 Agent Card는 어디에서 조회하나요?</summary>
공개 <code>/.well-known/agent-card.json</code>에는 없고, Agent Platform APIs의 인증된 Registry 조회로만 볼 수 있습니다.
</details>

<details markdown="1"><summary>Q2. 서명을 검증하기 전에 카드를 어떻게 정규화하나요?</summary>
<code>signatures</code> 필드를 제외하고 JCS(RFC 8785)로 정규화합니다.
</details>

<details markdown="1"><summary>Q3. Agent Card는 어떤 상태의 Agent 버전에 발행되나요?</summary>
production-approved 상태의 버전에만 발행합니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- Agent를 찾을 때는 A2A 1.0.0 Agent Card를, 호출할 때는 공통 Agent 통신 계약을 따릅니다.
- 사내 Agent의 카드는 인증된 Registry 조회로만 볼 수 있고, 상세 정보는 확장 카드에만 둡니다.
- Registry가 카드를 JCS로 정규화한 뒤 JWS로 서명하고, 받는 쪽은 서명을 검증한 카드만 믿습니다.
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- A2A 1.0.0 명세, 발견 문서, 변경 사항: [A2A](10-references.md#ref-a2a)
- 서명·정규화 규격: [IETF·OAuth](10-references.md#ref-identity)
</div>

