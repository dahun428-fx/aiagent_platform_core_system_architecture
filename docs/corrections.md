# 보고서 정정 및 누락 보완

원문 보고서는 sources/에 변경 없이 보존한다. 이 문서와 기준선이 원문의 오류를 명시적으로 대체한다.

| 발견 | 정정 / 보완 | 실제 산출물 |
|---|---|---|
| Q30 미응답으로 추론 | B를 명시적으로 답변한 Decided로 정정 | baseline-v0.1, ADR-030 |
| Tool Gateway 소속 모호 | Agent Tools = Registry + Gateway + protocol adapters + policy/audit | agent-tools.md |
| Credential Broker 누락 | Agent Identity 내부 단기 credential mediation, Runtime에 secret 비노출 | identity-and-credentials.md |
| ADR은 번호만 존재 | 30개 본문: 맥락·결정·대안·결과·제약·계약·보안·마이그레이션 | adr/ |
| 승인/재개 명세 누락 | 대상 digest·policy version·expiry에 승인 결합, 재개 시 재평가 | approval / execution schemas |
| 도구/RAG/Agent 간 계약 누락 | Tool·retrieval·cross-agent·runtime·evaluation 계약 추가 | contracts/ |
| 그림만 제안 | C4·시퀀스·보안 경계 Mermaid와 오프라인 SVG 제공 | diagrams/ |
| 파일 생성/실행 증거 없음 | 실행 가능한 local mock, contract tests, offline portal, ZIP 검증 | tests/ / verification/ |

OpenAPI 3.2.1 최신 여부는 원문 주장을 그대로 표준으로 채택하지 않는다.
이 패키지는 공식 3.1.2 명세와 실제 validator 적합성을 기준으로 3.1.2를 pin한다.
3.2 계열 채택은 회사 toolchain 호환성 검증 후 별도 변경한다.

