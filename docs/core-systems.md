# Core Systems

AI Agent Platform은 10개 Core System으로 구성한다. 이 문서는 각 Core System의 책임, 하위 구성요소, 대응 계약, v0.1 제공 범위를 정의한다. 배치 관점의 분리는 [아키텍처](architecture.md)의 Shared Control Plane / Distributed Execution Plane을 따른다.

## 층 구조

| 층 | Core System | 연결 대상 |
|---|---|---|
| 응용 | AI Platform Applications (DevTools, Space) | 개발자·운영자 |
| API | Agent Platform APIs | External Applications and Solutions |
| 핵심 | Agent Factory, Agent Runtime, Agent Tools, Agent Identity, Agent Observability, Agent Evaluation | |
| 관문 | Agent Gateway, Agent Tuning (FastTrack) | External Tools and Models |
| 실행 인프라 | Distributed Execution Plane: 개발자 로컬, 워크스테이션·Mac mini 계열 자원, 사내·클라우드 실행 환경, 모델 endpoint | |

## 명칭 대응

이 문서부터 다음 명칭을 사용한다. 기존 계약 파일명과 코드 식별자는 호환성을 위해 유지한다(MUST). 파일명 변경은 [계약 변경](versioning.md) 절차를 따른다.

| 이전 문서의 명칭 | Core Systems 명칭 | 기존 계약·식별자 |
|---|---|---|
| Agent Gateway (northbound ingress) | **Agent Platform APIs**의 Agent 호출 API | `contracts/agent-gateway.openapi.json`, 감사 component `agent-gateway` |
| Model Gateway | **Agent Gateway**의 모델 경로(model route) | `contracts/model-gateway.openapi.json` |
| Tool Gateway (Agent Tools 소속) | **Agent Gateway**의 도구 경로(tool route). Tool Registry·도구 정책·감사는 Agent Tools가 소유한다 | `contracts/tool-gateway.openapi.json` |

진입 경계(Agent Platform APIs)와 모델 경로(Agent Gateway)는 논리적으로 분리해야 한다(MUST). 물리 배치는 합칠 수 있으나 신원·egress 신뢰 경계는 유지해야 한다(MUST).

## 1. AI Platform Applications

개발자와 운영자가 플랫폼을 사용하는 응용 계층이다.

- **DevTools**: CLI(`agentctl`), SDK, 템플릿, 로컬 mock, Manifest 검증 도구.
- **Space**: Agent 카탈로그 조회, 실행 추적·평가 결과 조회, 승인 요청 처리를 위한 공유 작업 공간.
- Applications는 Agent Platform APIs만 호출해야 한다(MUST). Applications 전용 비공개 경로를 두지 않는다.
- Space 사용은 선택이다. 개발은 Local-First/CLI-First로 수행하며, Space나 Agent Studio 사용을 강제해서는 안 된다(MUST NOT).
- v0.1 제공 범위: DevTools(CLI 검증, Python mock, TypeScript 클라이언트). Space는 화면 범위와 API 의존만 정의하며 구현은 제공하지 않는다.

## 2. Agent Platform APIs

플랫폼의 모든 외부 기능을 노출하는 단일 API 계층이자 진입 경계(northbound)다.

- 포함 API: Agent 호출(`agent-gateway.openapi.json`), Registry 조회·Agent Card 발행([Agent Card](agent-card.md)), 실행 상태·이벤트, 승인, 평가 결과 조회.
- 공통 규칙: OAuth 2.0 bearer 인증, 검증된 토큰에서 tenant·principal 파생, RFC 9457 Problem Details, W3C trace context, `/v1` 경로 버전, 멱등성 키.
- 인증·Agent 해석·테넌트 인가·멱등성 책임은 기존 Agent 호출 API 정의를 그대로 따른다.
- v0.1 제공 범위: Agent 호출과 health는 mock 구현, 나머지는 계약만 제공한다(501).

## 3. Agent Factory

Agent를 만들고, 선언하고, 검증하고, 등록하는 개발 흐름을 담당한다.

- 흐름: 템플릿으로 생성 → Manifest 선언 → 로컬 검증(`agentctl validate`) → CI 계약·평가 게이트 → Registry 등록(불변 revision·artifact digest).
- 템플릿은 Agent 유형(rag, tool, workflow, multi-agent)별로 제공한다(SHOULD).
- 소스는 개발자 저장소에 두며, Factory는 소스 업로드를 요구해서는 안 된다(MUST NOT).
- v0.1 제공 범위: Manifest 스키마, 양성·음성 fixture, `agentctl validate`, 4종 예제 Manifest. 템플릿 생성 명령은 후속 단계다.

## 4. Agent Runtime

Agent를 실행하는 구성요소다. 하위 구성요소는 framework adapter, Durable 실행·상태, Memory다.

- framework adapter, 실행 상태 전이는 [아키텍처](architecture.md), [Durable / HITL](execution.md)를 따른다.
- Memory는 [Memory](memory.md)를 따른다.
- 실행 제어 guardrail(권한 최소화, 고위험 작업 승인)의 집행 지점이다([Guardrails](guardrails.md)).

## 5. Agent Tools

도구 연동 영역이다. Tool Registry, 도구 descriptor, REST/OpenAPI/MCP/custom adapter, 도구 정책과 감사를 소유한다. 도구 호출의 집행은 Agent Gateway의 도구 경로가 수행한다. 규칙은 [Agent Tools](agent-tools.md)를 따른다.

## 6. Agent Identity

사용자 Identity, Agent(workload) Identity, 위임, 자격증명 중개 영역이다. Credential Broker를 포함한다. 규칙은 [Agent Identity](identity-and-credentials.md)를 따른다.

## 7. Agent Observability

실행 추적, 지표, 로그를 수집하는 영역이다. 규칙은 [Observability](observability.md)를 따른다.

## 8. Agent Evaluation

배포 전 평가, 실행 추적 기반 분석, 운영 모니터링을 담당한다. 규칙은 [Evaluation](evaluation.md)을 따른다.

## 9. Agent Gateway

Agent가 외부 모델과 도구에 접근하는 관문(egress)이다.

- **모델 경로**: 논리 모델 이름을 데이터 분류·지역·비용·가용성 정책에 맞는 endpoint로 라우팅한다. 규칙은 기존 Model Gateway 정의(`model-gateway.openapi.json`, [보안 경계](security.md))를 따른다.
- **도구 경로**: 도구 ID를 Agent Tools의 승인된 endpoint로 해석하고 Credential Broker의 lease로 호출한다. 규칙은 [Agent Tools](agent-tools.md)를 따른다.
- 모델 입출력·도구 호출·도구 결과 guardrail의 집행 지점이다([Guardrails](guardrails.md)).
- 토큰 사용량 한도와 비용 귀속(tenant·Agent 단위)을 기록해야 한다(SHOULD). 한도 수치는 TBD-07이다.

## 10. Agent Tuning (FastTrack)

평가 결과와 실행 추적을 근거로 Agent를 개선하는 영역이다. 규칙은 [Agent Tuning](agent-tuning.md)을 따른다.

## External 연결

- **External Applications and Solutions**는 Agent Platform APIs로만 접근한다(MUST).
- **External Tools and Models**는 Agent Gateway로만 접근한다(MUST). Agent Tuning이 외부 모델 튜닝 서비스를 사용할 때도 Agent Gateway의 모델 경로 정책(데이터 분류, egress)을 따른다(MUST).
