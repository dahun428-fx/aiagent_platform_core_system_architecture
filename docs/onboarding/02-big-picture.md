# 한 장으로 보는 전체 구조

> 온보딩 안내서입니다. 규범은 [아키텍처](../architecture.md) 원문이 기준입니다.

## 두 개의 평면: 통제는 모으고, 실행은 흩는다

이 플랫폼에서 가장 먼저 잡아야 할 그림은 **Shared Control Plane**과 **Distributed Execution Plane**의 구분입니다.

- **Shared Control Plane(공통 제어 평면)**: 회사 전체가 하나를 함께 씁니다. 어떤 Agent가 있는지(Registry), 누가 무엇을 해도 되는지(Policy, Identity), 품질이 어떤지(Evaluation), 무슨 일이 있었는지(Observability), production에 올려도 되는지(Promotion)를 관리합니다.
- **Distributed Execution Plane(분산 실행 평면)**: Agent가 실제로 도는 곳입니다. 개발자 PC, 워크스테이션이나 Mac mini 같은 장비, 사내 서버, 클라우드가 모두 해당합니다. 장소는 달라도 **같은 Runtime 계약**을 따릅니다.

비유하면 항공 관제와 비슷합니다. 비행기(Agent)는 각 공항(실행 환경)에서 뜨고 내리지만, 비행 허가와 항로 규칙과 기록은 관제(Control Plane)가 맡습니다. 관제탑이 비행기를 직접 조종하지는 않습니다.

여기서 중요한 규칙이 하나 있습니다. 실행 환경이 **등록(registered)**됐다고 해서 곧바로 **production 승인(production-approved)**이 되는 것은 아닙니다. 개발자 PC도 등록은 할 수 있지만 실제 업무 트래픽을 받으려면 별도의 승인 증거가 필요합니다.

## 구성요소 한눈에 보기

![C4 Container: Shared Control Plane과 Distributed Execution Plane](../../diagrams/c4-container.svg)

| 구성요소 | 한 줄 설명 | 비유 |
|---|---|---|
| **Agent Gateway** | 사용자나 업무 앱이 Agent를 부를 때 들어오는 정문. 인증, 어떤 Agent인지 찾기, 테넌트 권한 확인, 중복 요청 방지를 맡습니다. | 건물 출입 게이트 |
| **Agent Runtime** | Agent를 실제로 실행하는 곳. 프레임워크별 adapter로 Agent를 부르고, 모델·도구·지식·상태·정책 서비스를 소비합니다. | 작업장 |
| **Model Gateway** | 모델 호출의 관문. "일반 대화 모델" 같은 논리 이름을 받아 데이터 분류·지역·비용·가용성 정책에 맞는 실제 endpoint로 보냅니다. | 데이터 반출 검사대 |
| **Agent Tools** | 도구 연동 영역 전체. Tool Registry, Tool Gateway, REST/OpenAPI/MCP adapter, 도구 정책과 감사를 포함합니다. | 공구 창고와 대여 창구 |
| **Tool Gateway** | Agent Tools 안의 관문. Agent가 사내·외부 도구를 부를 때 반드시 거치며, 승인된 endpoint로만 보내고 입출력을 검사합니다. | 대여 창구 |
| **Agent Identity** | 신원 영역 전체. 사용자 신원, Agent(workload) 신원, 위임 관계, 자격증명 중개를 다룹니다. | 인사·보안팀 |
| **Credential Broker** | Agent Identity 안의 고신뢰 서비스. 도구 호출에 필요한 **짧게 살고 범위가 좁은** 자격증명을 발급합니다. Runtime이나 LLM은 그 자격증명을 볼 수 없습니다. | 일회용 출입증 발급처 |
| **Knowledge(RAG) Backend** | 검색 증강(RAG)에 쓰는 지식 저장소. 공통 RAG 계약만 지키면 어떤 검색 엔진·벡터 DB든 바꿔 낄 수 있습니다. | 사내 도서관 |
| **Shared Control Plane** | Registry(Agent·Tool·Model·Environment), Policy, Identity 중개, Evaluation, Observability, Promotion. | 관제탑 |

두 가지 소속 관계는 꼭 기억하세요. 처음 보는 사람이 가장 많이 헷갈리는 부분입니다.

- **Tool Gateway는 Agent Tools에 속합니다.**
- **Credential Broker는 Agent Identity에 속합니다.**

이것은 논리적인 소속입니다. 반드시 별도 서버로 배포하라는 뜻은 아닙니다. 물리적으로 합쳐 배포해도 되지만, 신원과 데이터 반출(egress)의 신뢰 경계는 합쳐도 지켜야 합니다(MUST).

## 왜 Gateway가 세 개나 있나

처음 보면 Gateway가 많아 보입니다. 각각 지키는 경계가 다릅니다.

| Gateway | 지키는 방향 | 막는 것 |
|---|---|---|
| Agent Gateway | 바깥 → Agent (들어오는 길) | 신원 위조, 권한 없는 테넌트 접근, 같은 요청의 중복 실행 |
| Model Gateway | Agent → 모델 (나가는 길) | 기밀 데이터의 외부 모델 전송, 특정 모델 공급사 종속 |
| Tool Gateway | Agent → 도구 (나가는 길) | 허가 안 된 시스템 호출, 자격증명 유출, 위조된 도구 결과 |

Agent Gateway와 Model Gateway를 나누는 이유는 호출을 통제하는 일과 모델 공급사를 추상화하는 일이 서로 다른 책임이기 때문입니다. 셋 모두 논리적인 책임 구분이고, 특정 제품이나 프로세스 개수를 뜻하지 않습니다.

## 용어 쉽게 풀기

| 용어 | 쉬운 뜻 |
|---|---|
| Manifest | Agent의 신분증. 이름, 버전, 소스 위치, 필요한 도구와 지식, 데이터 등급, 배포 프로파일을 적은 JSON 파일 |
| Tenant | 데이터와 권한이 분리되는 단위(예: 사업부). 기본은 논리 격리이고, 위험도에 따라 물리 분리도 합니다 |
| Delegated / Independent | 사용자를 대신해 일하는 모드 / Agent 자신의 권한으로만 일하는 모드 |
| Trace (traceparent) | 요청 하나에 붙는 추적 번호. Gateway → Runtime → 모델·도구까지 그대로 전달해서 한 줄로 추적합니다 |
| HITL | Human-in-the-loop. 위험한 작업 전에 사람의 승인을 받는 단계 |
| Durable 실행 | 프로세스가 재시작돼도 상태를 이어서 실행할 수 있는 방식 |
| TBD | 회사가 아직 정하지 않은 항목. 예제의 숫자를 기본값으로 쓰면 안 됩니다 |

전체 정의는 [용어와 규범](../glossary.md)에 있습니다.

## 이 플랫폼을 정의하는 원칙

앞으로 읽을 내용을 원칙으로 모으면 다음과 같습니다. 각 원칙은 뒤의 페이지에서 자세히 풀어 설명합니다.

| 영역 | 원칙 | 자세히 |
|---|---|---|
| 범위 | 전사가 함께 쓰는 하나의 공통 플랫폼이다. 팀마다 따로 만들지 않는다 | [왜 필요한가](01-why.md) |
| 인프라 | 온프레미스와 퍼블릭 클라우드를 함께 쓰는 Hybrid Cloud를 전제한다. 실행 자원은 특정 서빙 제품에 묶이지 않는다 | 이 페이지 |
| 구조 | 통제는 Shared Control Plane에 모으고, 실행은 Distributed Execution Plane에 분산한다 | 이 페이지 |
| 모델 | 외부 상용 LLM과 자체 호스팅 오픈소스 모델을 함께 쓰고, Model Gateway가 정책으로 경로를 고른다 | [요청 하나 따라가기](03-one-request.md) |
| 호출 경계 | Agent Gateway, Model Gateway, Tool Gateway는 서로 다른 경계를 지킨다 | 이 페이지 |
| 실행 | 공통 Runtime 계약과 framework adapter로 어떤 프레임워크든 실행한다 | [요청 하나 따라가기](03-one-request.md) |
| 도구 | REST/OpenAPI, MCP, 사용자 정의 adapter를 Tool Gateway 뒤에서 지원한다 | [요청 하나 따라가기](03-one-request.md) |
| 신원 | 사용자 신원과 Agent 신원을 함께 다루고, 자격증명은 Credential Broker가 짧게 발급한다 | [신뢰 경계](04-trust.md) |
| 테넌트 | 기본은 논리 격리이고, 민감도와 위험에 따라 물리 분리를 선택한다 | [신뢰 경계](04-trust.md) |
| 데이터 | 데이터 분류에 따라 접근과 이동(외부 모델 전송 포함)을 통제한다 | [신뢰 경계](04-trust.md) |
| Agent 종류 | RAG, Tool, Workflow, Multi-Agent를 처음부터 공통 계약으로 지원한다 | [네 종류 Agent와 Manifest](05-agents-and-manifest.md) |
| 지식 | 공통 RAG 계약을 지키면 검색 저장소는 바꿔 낄 수 있다 | [네 종류 Agent와 Manifest](05-agents-and-manifest.md) |
| Agent 간 협업 | 공통 Agent 통신 계약을 쓰고, A2A 같은 특정 프로토콜은 선택이다 | [네 종류 Agent와 Manifest](05-agents-and-manifest.md) |
| 개발 방식 | Local-First, CLI-First. 지금 쓰는 IDE·Git·CLI를 유지하고 중앙 소스 업로드를 강제하지 않는다 | [production까지 가는 길](06-lifecycle.md) |
| 실험 | 실험은 로컬에서 하고, 공유가 필요하면 공용 실험·평가 기록소에 남긴다 | [production까지 가는 길](06-lifecycle.md) |
| 수명주기 | 자동 게이트를 통과하면 셀프서비스로 진행하고, 위험이 높을수록 사람 승인을 더한다 | [production까지 가는 길](06-lifecycle.md) |
| 품질 | 관측, 자동 평가, 품질 게이트를 배포 과정에 포함한다 | [production까지 가는 길](06-lifecycle.md) |
| 신뢰성 | 오래 걸리는 작업은 Durable 실행과 HITL 승인, 정책 통제로 다룬다 | [production까지 가는 길](06-lifecycle.md) |
| 운영 목표 | SLO는 실행 환경과 업무 위험도에 따라 단계적으로 정한다 | [production까지 가는 길](06-lifecycle.md) |
| 도입 방식 | 먼저 끝에서 끝까지 이어진 한 줄의 경로를 완성하고, 기능을 단계적으로 붙인다 | [production까지 가는 길](06-lifecycle.md) |
| 계약 | 계약은 언어 중립(OpenAPI, JSON Schema)이고, 코드로 검증하며, 버전으로 관리한다 | [규격 읽는 법](08-reading-the-spec.md) |

## 더 읽을거리

- 신원과 Credential Broker: [Agent Identity](../identity-and-credentials.md)
- 도구와 Tool Gateway: [Agent Tools](../agent-tools.md)
- 모든 도식: [아키텍처 도식](../architecture.md)

이전: [왜 이 플랫폼이 필요한가](01-why.md) · 다음: [요청 하나 따라가기](03-one-request.md)
