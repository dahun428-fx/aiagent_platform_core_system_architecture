# 용어와 규범

MUST: 채택 시 필수. MUST NOT: 금지. SHOULD: 합당한 사유를 문서화하면 예외 가능. MAY: 선택.
Decided는 기준선의 결정 상태이며 회사 공식 배포 승인과 구분한다.
TBD는 회사별 결정이 없다는 뜻이며 예제 수치를 임의 기본값으로 승격하지 않는다.

Agent Gateway: client가 Agent를 호출하는 northbound ingress.
Model Gateway: 모델 provider/endpoint routing과 data egress 경계.
Agent Tools: Registry/Gateway/adapter/정책·감사를 포괄하는 capability.
Tool Gateway: 도구 호출의 controlled egress mediator.
Agent Identity: 사용자·workload·위임·credential mediation capability.
Credential Broker: audience·scope·expiry·binding이 제한된 credential mediation 서비스.
Runtime: 공통 계약을 실행하며 framework adapter를 통해 Agent를 호출하는 consumer.
HITL: Human-in-the-loop. Durable: process restart를 넘어 상태·효과를 복구하는 실행.
Registered: 등록 상태. Production-approved: production 통제가 검증된 승인 상태.

