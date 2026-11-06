# Agent Card

Agent Card는 A2A(Agent2Agent) 프로토콜에서 Agent를 설명하는 공개 메타데이터 문서다. 플랫폼은 Registry의 Agent 정보를 A2A Agent Card로 발행해 다른 Agent와 시스템이 Agent를 발견하고 호출 방법을 알 수 있게 한다. Agent 간 호출 자체는 공통 Agent 통신 계약(`cross-agent.schema.json`)을 따르며, A2A 프로토콜 채택은 선택이다([ADR-020](../adr/ADR-020.md)). 이 문서의 규칙은 A2A를 채택하거나 Agent를 다른 팀·외부에 노출해 발견 정보를 발행하는 경우에 적용한다([ADR-036](../adr/ADR-036.md)).

## 기준 버전

- A2A 1.0.0을 기준으로 한다(MUST). 규범 원본은 A2A의 `spec/a2a.proto`이다.
- 요청에는 `A2A-Version` 헤더를 사용하고, 지원하지 않는 버전은 VersionNotSupportedError로 처리한다.

## 필드

| 필드 | 필수 | 내용 |
|---|---|---|
| `name`, `description`, `version` | 필수 | Agent 이름, 목적, 버전 |
| `supportedInterfaces` | 필수 | `url`, `protocolBinding`(`JSONRPC`·`GRPC`·`HTTP+JSON`), `protocolVersion`, 선택 `tenant`. 첫 항목이 우선 |
| `capabilities` | 필수 | `streaming`, `pushNotifications`, `extensions`, `extendedAgentCard` |
| `defaultInputModes`, `defaultOutputModes` | 필수 | 입출력 미디어 유형 |
| `skills` | 필수 | `id`, `name`, `description`, `tags`, 선택 `examples`·`inputModes`·`outputModes`·`securityRequirements` |
| `provider` | 선택 | `organization`, `url` |
| `securitySchemes`, `securityRequirements` | 선택 | API key, HTTP auth, OAuth 2.0, OpenID Connect, mTLS 중 하나 |
| `signatures` | 선택 | JWS 서명 |
| `documentationUrl`, `iconUrl` | 선택 | 문서·아이콘 |

A2A 1.0.0 명세는 필드 표에서 `securityRequirements`, 본문 일부에서 `AgentCard.security`로 표기한다. 구현은 `a2a.proto`의 정의를 따른다(MUST).

## Manifest와의 대응

| Agent Card | 플랫폼 원천 |
|---|---|
| `name`, `version` | Manifest `metadata.name`, `metadata.version` |
| `description` | Registry 등록 설명 |
| `skills` | Manifest `capabilities.type`과 도구·지식 선언, Registry의 skill 설명 |
| `supportedInterfaces[].url` | 승인된 실행 환경의 Agent Platform APIs endpoint |
| `supportedInterfaces[].tenant` | tenant 라우팅 값 |
| `securitySchemes`, `securityRequirements` | 회사 IdP 설정과 Manifest `identity.requiredScopes` |
| `provider.organization` | Manifest `metadata.owner.team` |

## 발행 규칙

- Agent Card는 Registry가 Manifest와 등록 정보에서 생성한다(MUST). 수동 작성 카드는 받지 않는다.
- production-approved 상태의 버전만 카드를 발행한다(MUST). deprecated·quarantined·retired로 전환하면 카드를 갱신하거나 회수한다(MUST).
- Registry는 조직 키로 카드를 JWS(RFC 7515) 서명해야 한다(MUST). 서명 대상은 JCS(RFC 8785)로 정규화하고 `signatures` 필드를 제외한다. 보호 헤더에는 `alg`, `typ`(`JOSE`), `kid`를 넣고 `jku`로 JWKS 위치를 제공할 수 있다.
- 키 교체 기간에는 서명을 여러 개 둘 수 있다. 만료·폐기된 키로 서명하거나 검증해서는 안 된다(MUST NOT).
- 응답에는 `Cache-Control`과 카드 `version` 또는 내용 해시 기반 `ETag`를 포함한다(SHOULD).

## 공개 범위

- 사내 Agent는 공개 `/.well-known/agent-card.json`을 두지 않는다(MUST NOT). Agent Platform APIs의 인증된 Registry 조회로만 제공한다.
- 외부에 공개하는 Agent만 `https://{domain}/.well-known/agent-card.json`에 최소 정보의 공개 카드를 둔다.
- 내부 skill과 상세 정보는 인증된 확장 카드(`capabilities.extendedAgentCard: true`, GetExtendedAgentCard)로만 제공하며, 권한 교집합에 따라 내용을 제한한다(MUST).
- Agent Card와 확장 카드에 시크릿·토큰을 넣어서는 안 된다(MUST NOT). 인증에는 대역 외 동적 자격증명을 사용한다.

## 소비 규칙

- 다른 Agent의 카드는 서명을 검증한 뒤에만 신뢰한다(MUST). 키는 HTTPS로 받거나 신뢰 키 저장소를 사용한다.
- 카드 내용(skill 설명 등)은 비신뢰 데이터로 취급한다(MUST). 카드 내용으로 권한 정책을 변경할 수 없다.
- 인가는 A2A가 정하지 않으므로 플랫폼의 권한 교집합·위임 규칙을 적용한다([Agent Identity](identity-and-credentials.md)).

## Registry 조회 API

A2A는 큐레이션 레지스트리 API를 표준으로 정하지 않는다. Agent 목록·조회는 기존 Agent 호출 API의 `listAgents`(`GET /v1/agents`), `getAgent`(`GET /v1/agents/{agentId}`)를 사용한다. Agent Card 조회와 검색은 후속 계약 버전에서 추가한다.

## 근거

- A2A 1.0.0 명세(Agent Card, 발견, 확장 카드, 서명), Agent discovery 문서, v1.0 변경 사항.
- 출처 목록: [근거와 참고 자료](onboarding/10-references.md)
