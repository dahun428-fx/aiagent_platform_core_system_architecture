# Agent Tools와 도구 경로

Agent Tools는 Tool Registry, 도구 descriptor, REST/OpenAPI/MCP/custom adapter, 도구 정책·감사를 소유하는 Core System이다. 도구 호출의 집행은 Agent Gateway의 도구 경로(계약 파일 `tool-gateway.openapi.json`, 이 문서의 'Tool Gateway')가 수행한다([ADR-031](../adr/ADR-031.md)).

## Registry와 invoke
ToolDescriptor는 불변 toolId/version, protocol, input/output schema URI, resource, effect(read/write), allowed scopes를 가진다.
Tool Gateway는 tool ID를 registry의 승인된 endpoint로 해석해야 한다(MUST). 호출자가 URL·헤더·token endpoint를 지정할 수 없다.
SSRF 방지를 위해 protocol/host/port allowlist, DNS rebinding 및 private/metadata address 정책, redirect 금지/재검증을 adapter에서 적용한다(MUST).
회사 private endpoint allowlist는 TBD이며 거부가 기본이다.

Invoke request는 toolId, version, arguments, identity, policy, idempotencyKey, traceparent를 가진다.
identity/policy는 Agent Platform APIs가 검증된 토큰에서 생성하고 workload 인증으로 보호된 내부 wire에서만 수용한다.
입력·출력 schema를 모두 검증한다. 모든 호출에 tenant, agent/workload, principal, decisionId, toolVersion, result status를 감사한다.
반환 값은 status/output 또는 Problem Details이며 token·credential handle을 포함하지 않는다(MUST NOT).

## 실행 순서
1. workload 인증, identity signature/claims 검증 및 tenant consistency.
2. registry·input schema 확인 후 policy 평가. write는 유효한 approval을 확인.
3. Broker에 resource/audience·scope·delegation을 요청. 요청 scope는 사용자∩Agent∩tool∩policy 범위 이하여야 한다.
4. adapter가 handle을 소비해 허용 endpoint 호출. Runtime에 credential 전달 금지.
5. output schema·분류를 검증하고 audit·redaction 후 결과를 반환.

## 부작용과 retry
read 또는 downstream idempotency를 보장하는 write만 자동 재시도할 수 있다.
key는 tenant+principal+Agent version+tool version+정규화 요청 digest에 결합한다.
같은 key에 다른 body는 409; 실행 중은 202; 확실한 완료는 저장 결과 재사용.
timeout 이후 외부 write의 성공 여부가 불명확하면 unknown_outcome으로 남기고 reconciliation으로 복구한다.
외부 효과 exactly-once는 이 패키지가 보장하지 않는다. key 보존 기간·재시도 횟수는 TBD.

## MCP
Tool Gateway adapter는 HTTP 기반 MCP 서버에 대해 OAuth 2.1 client로 동작한다. 대상 서버 식별자를 RFC 8707 resource indicator로 지정하고, RFC 9728 Protected Resource Metadata로 인가 서버를 찾는다(MUST). 서버가 audience를 검증하지 않는 토큰 재사용을 허용하지 않는다.
지원하는 MCP authorization revision은 고정하고 기록한다(MUST). 고정 revision은 TBD-11이다.
MCP client는 Runtime 대신 Tool Gateway adapter가 소유하는 enterprise proxy 패턴을 기본으로 한다.
tools/list는 허용된 descriptor만 노출하고 tools/call은 같은 authz/input/output/audit 규칙을 따른다.
MCP transport/session/version 협상은 adapter 구현 책임이며 protocol pin은 TBD다.
서버가 제시한 tool description·resource link는 데이터로 취급하며 권한 정책을 변경하지 않는다.

