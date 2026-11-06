# 요구사항 기준선 v0.1

상태: Decided (아키텍처 결정). 회사의 공식 승인·production 배포 승인을 대신하지 않는다.
기준일: 2026-10-30 (Asia/Seoul). 버전: 0.1.0.

## 출처와 정정
두 첨부 Deep Research 보고서의 Q1–30 표 및 검증 결과를 기준으로 한다.
원 Q&A 원문은 대화 도구가 content-reference로만 반환하여 직접 대조하지 못했다.
따라서 아래 한국어는 질문 원문 인용이 아닌 결정의 규범적 정리다.
Q30은 검증 보고서 및 현재 사용자 지시에 따라 명시적 B 선택으로 정정한다.
회사 환경·제품·수치는 TBD이며 예제 fixture 수치는 합성 테스트 값이다.

| Q | 결정 | 규범 요구 | ADR | 구현/검증 추적 |
|---|---|---|---|---|
| Q1 | 전사 공통 플랫폼 | MUST: 전사 공통 AI Agent Platform을 구축한다. | [ADR-001](../../adr/ADR-001.md) | [산출물](../../docs/architecture.md) · tests/test_contracts.py |
| Q2 | 기술 표준의 독자 | MUST: 아키텍트, Agent/백엔드 개발자, DevOps/SRE, 보안·거버넌스 담당자를 대상으로 한다. | [ADR-002](../../adr/ADR-002.md) | [산출물](../../docs/operating-model.md) · tests/test_contracts.py |
| Q3 | Hybrid Cloud | MUST: Hybrid Cloud를 지원하고 회사의 현행 스택은 TBD로 둔다. | [ADR-003](../../adr/ADR-003.md) | [산출물](../../docs/deployment.md) · tests/test_contracts.py |
| Q4 | 복수 모델 소싱 | MUST: 외부 상용 LLM과 자체 호스팅 OSS 모델을 지원한다. | [ADR-004](../../adr/ADR-004.md) | [산출물](../../contracts/model-gateway.openapi.json) · tests/test_contracts.py |
| Q5 | 네 종류 Agent | MUST: RAG, tool-using, workflow, multi-Agent의 초기 계약을 지원한다. | [ADR-005](../../adr/ADR-005.md) | [산출물](../../examples/manifests/rag.json) · tests/test_contracts.py |
| Q6 | 공통 Runtime | MUST: 공통 Runtime Contract와 프레임워크 어댑터를 사용한다. | [ADR-006](../../adr/ADR-006.md) | [산출물](../../contracts/runtime.schema.json) · tests/test_contracts.py |
| Q7 | 테넌트 격리 | MUST: 논리 격리를 기본으로 위험에 따라 물리 격리를 선택한다. | [ADR-007](../../adr/ADR-007.md) | [산출물](../../contracts/identity.schema.json) · tests/test_contracts.py |
| Q8 | 사용자·Agent Identity | MUST: 사용자 및 Agent/workload 신원, 위임 및 독립 실행을 지원한다. | [ADR-008](../../adr/ADR-008.md) | [산출물](../../docs/identity-and-credentials.md) · tests/test_contracts.py |
| Q9 | Agent Tools | MUST: REST/OpenAPI, MCP, custom adapter를 지원한다. | [ADR-009](../../adr/ADR-009.md) | [산출물](../../docs/agent-tools.md) · tests/test_contracts.py |
| Q10 | 관측·평가 | MUST: 통합 관측, 자동 평가, 품질 gate를 적용한다. | [ADR-010](../../adr/ADR-010.md) | [산출물](../../contracts/evaluation.schema.json) · tests/test_contracts.py |
| Q11 | 셀프서비스 수명주기 | MUST: 자동 gate와 고위험 human approval을 결합한다. | [ADR-011](../../adr/ADR-011.md) | [산출물](../../contracts/approval.schema.json) · tests/test_contracts.py |
| Q12 | Gateway 분리 | MUST: Agent Gateway와 Model Gateway를 논리적으로 분리하고 정책 라우팅한다. Core Systems 명칭으로는 Agent Platform APIs(진입)와 Agent Gateway 모델 경로(반출)의 분리다([ADR-031](../../adr/ADR-031.md)). | [ADR-012](../../adr/ADR-012.md) | [산출물](../../docs/architecture.md) · tests/test_contracts.py |
| Q13 | 데이터 거버넌스 | MUST: 분류 기반 접근·데이터 이동 정책을 적용한다. | [ADR-013](../../adr/ADR-013.md) | [산출물](../../contracts/policy.schema.json) · tests/test_contracts.py |
| Q14 | Durable/HITL | MUST: checkpoint, retry, idempotency, HITL, policy 제어를 계약화한다. | [ADR-014](../../adr/ADR-014.md) | [산출물](../../docs/execution.md) · tests/test_contracts.py |
| Q15 | 중립 모델 서빙 | MUST: 벤더 중립 endpoint 계약을 채택한다. Backend.AI는 Out of Scope다. | [ADR-015](../../adr/ADR-015.md) | [산출물](../../docs/deployment.md) · tests/test_contracts.py |
| Q16 | 위험별 NFR | MUST: 환경·업무 위험별 단계적 SLO를 사용하고 수치는 TBD로 둔다. | [ADR-016](../../adr/ADR-016.md) | [산출물](../../docs/tbd-register.md) · tests/test_contracts.py |
| Q17 | 공통 제어·분산 실행 | MUST: Shared Control Plane + Distributed Execution Plane을 채택한다. | [ADR-017](../../adr/ADR-017.md) | [산출물](../../diagrams/c4-container.mmd) · tests/test_contracts.py |
| Q18 | Local-First/CLI-First | MUST: Contract-first SDK·CLI·템플릿을 제공하고 중앙 소스 업로드나 Agent Studio를 강제하지 않는다. | [ADR-018](../../adr/ADR-018.md) | [산출물](../../README.md) · tests/test_contracts.py |
| Q19 | 공통 RAG | MUST: 공통 RAG 계약과 교체 가능한 knowledge backend를 사용한다. | [ADR-019](../../adr/ADR-019.md) | [산출물](../../contracts/retrieval.schema.json) · tests/test_contracts.py |
| Q20 | Agent 간 통신 | MUST: 공통 Agent 통신 envelope와 adapter를 제공하고 A2A는 선택 사항이다. | [ADR-020](../../adr/ADR-020.md) | [산출물](../../contracts/cross-agent.schema.json) · tests/test_contracts.py |
| Q21 | 로컬 실험 | MUST: 로컬 실험과 공통 experiment/evaluation registry를 병행한다. | [ADR-021](../../adr/ADR-021.md) | [산출물](../../docs/operating-model.md) · tests/test_contracts.py |
| Q22 | 단계적 MVP | MUST: Local-First vertical MVP 이후 기능을 단계적으로 확장한다. | [ADR-022](../../adr/ADR-022.md) | [산출물](../../docs/implementation-plan.md) · tests/test_contracts.py |
| Q23 | 정적 포털 | MUST: 모듈형 정적 HTML 기술 표준 포털을 제공한다. | [ADR-023](../../adr/ADR-023.md) | [산출물](../../portal/index.html) · tests/test_contracts.py |
| Q24 | 언어 중립 계약 | MUST: 언어 중립 계약, Python 참조, TypeScript 핵심 예제를 제공한다. | [ADR-024](../../adr/ADR-024.md) | [산출물](../../examples/python/platform_ref.py) · tests/test_contracts.py |
| Q25 | 아키텍처 도식 | MUST: C4 계층, 주요 시퀀스, 배포/보안 경계, MVP 흐름을 제공한다. | [ADR-025](../../adr/ADR-025.md) | [산출물](../../docs/architecture.md) · tests/test_contracts.py |
| Q26 | Contract-as-Code | MUST: 자동 검증·버전 관리·호환성 검사를 적용한다. | [ADR-026](../../adr/ADR-026.md) | [산출물](../../docs/versioning.md) · tests/test_contracts.py |
| Q27 | 구현 착수 가능 | MUST: 실제 schema·API·예제·테스트를 포함하는 기술 표준 패키지를 완성한다. | [ADR-027](../../adr/ADR-027.md) | [산출물](../../docs/release-scope.md) · tests/test_contracts.py |
| Q28 | 배포 형식 | MUST: Git에 넣을 수 있는 소스, static HTML, offline ZIP을 제공한다. | [ADR-028](../../adr/ADR-028.md) | [산출물](../../README.md) · tests/test_contracts.py |
| Q29 | 한국어 표준 문서 | MUST: 한국어 중심, English technical terms, MUST/SHOULD/MAY, ADR을 사용한다. | [ADR-029](../../adr/ADR-029.md) | [산출물](../../docs/glossary.md) · tests/test_contracts.py |
| Q30 | 기준선 후 전체 제작 | MUST: B. 요구사항 기준선 검토 → 전체 패키지 제작. 명시적으로 답변한 확정 결정이다. | [ADR-030](../../adr/ADR-030.md) | [산출물](../../docs/corrections.md) · tests/test_contracts.py |

## v0.1 보강 결정 (2026-11-06)
Q1–Q30 이후 Core Systems 정합화를 위해 추가로 확정한 결정이다. 구현 상태는 [Core Systems 구현 상태](../core-systems.md#구현-상태)를 따른다.

| Q | 결정 | 기준선 | ADR | 추적 |
|---|---|---|---|---|
| Q31 | Core Systems 명칭과 경계 | MUST: 플랫폼은 AI Platform Applications, Agent Platform APIs, Agent Factory, Agent Runtime, Agent Tools, Agent Identity, Agent Observability, Agent Evaluation, Agent Gateway, Agent Tuning의 10개 Core System으로 구성한다. | [ADR-031](../../adr/ADR-031.md) | [Core Systems](../core-systems.md) |
| Q32 | Memory | MUST: Memory를 Agent Runtime 하위 구성요소로 둔다. | [ADR-032](../../adr/ADR-032.md) | [Memory](../memory.md) |
| Q33 | Guardrails | MUST: Guardrail은 공통 검사 서비스와 네 집행 지점(Agent Gateway 모델 경로의 모델 입출력, 도구 경로의 도구 호출·결과, RAG 검색 결과, Agent Runtime의 실행 제어)으로 구성한다. | [ADR-033](../../adr/ADR-033.md) | [Guardrails](../guardrails.md) |
| Q34 | Observability 규격 | MUST: 실행 추적은 W3C Trace Context로 전파하고, span 이름과 속성은 OpenTelemetry GenAI semantic conventions를 따른다. | [ADR-034](../../adr/ADR-034.md) | [Observability](../observability.md) |
| Q35 | Evaluation과 Agent Tuning | MUST: Evaluation은 배포 전 평가·실행 추적 분석·운영 모니터링 3단계로 수행하고, 위험도 high Agent는 red teaming을 포함한다. | [ADR-035](../../adr/ADR-035.md) | [Evaluation](../evaluation.md), [Agent Tuning](../agent-tuning.md) |
| Q37 | Agent Adapter와 로컬 적합성 | MUST: Agent는 AgentContext만 사용하는 adapter로 연결하고, 로컬 Registry와 9개 적합성 검사로 검증한다. | [ADR-037](../../adr/ADR-037.md) | [Core Systems](../core-systems.md) |
| Q36 | Agent Card | MUST: A2A 프로토콜을 채택하거나 Agent를 다른 팀·외부에 노출할 때, Registry가 Manifest와 등록 정보에서 A2A 1.0.0 Agent Card를 생성하고 조직 키로 JWS(JCS 정규화) 서명해 발행한다. | [ADR-036](../../adr/ADR-036.md) | [Agent Card](../agent-card.md) |

## 승인과 변경
기준선 변경은 영향받는 Q·ADR·계약·fixture·테스트를 같은 변경 단위로 수정해야 한다(MUST).
회사 적용 승인자·보안 승인자·업무 owner는 TBD. 변경 이력은 docs/versioning.md를 따른다.

