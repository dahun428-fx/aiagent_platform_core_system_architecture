# 용어와 규범

MUST: 채택 시 필수. MUST NOT: 금지. SHOULD: 합당한 사유를 문서화하면 예외 가능. MAY: 선택.
Decided는 기준선의 결정 상태이며 회사 공식 배포 승인과 구분한다.
TBD는 회사별 결정이 없다는 뜻이며 예제 수치를 임의 기본값으로 승격하지 않는다.

Agent Platform APIs: client가 Agent를 호출하는 northbound ingress를 포함한 플랫폼 API 계층. 계약 파일 `agent-gateway.openapi.json`은 이 계층의 Agent 호출 API다.
Agent Gateway: 외부 모델·도구로 나가는 egress 관문. 모델 경로(이전 명칭 Model Gateway)와 도구 경로(이전 명칭 Tool Gateway)로 구성한다.
Model Gateway: Agent Gateway의 모델 경로. 모델 provider/endpoint routing과 data egress 경계.
Agent Tools: Registry/Gateway/adapter/정책·감사를 포괄하는 capability.
Tool Gateway: Agent Gateway의 도구 경로. 도구 호출의 controlled egress mediator이며 Tool Registry·정책은 Agent Tools가 소유한다.
Memory: Agent Runtime 하위의 단기·장기 정보 유지 기능. Durable checkpoint와 구분한다.
Guardrail: 공통 검사 서비스와 네 집행 지점으로 구성한 입력·출력·도구·검색·실행 통제.
Agent Card: A2A 1.0.0의 Agent 메타데이터 문서. Registry가 발행하고 서명한다.
Agent Identity: 사용자·workload·위임·credential mediation capability.
Credential Broker: audience·scope·expiry·binding이 제한된 credential mediation 서비스.
Runtime: 공통 계약을 실행하며 framework adapter를 통해 Agent를 호출하는 consumer.
HITL: Human-in-the-loop. Durable: process restart를 넘어 상태·효과를 복구하는 실행.
Registered: 등록 상태. Production-approved: production 통제가 검증된 승인 상태.

