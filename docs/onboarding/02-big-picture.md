# 한 장으로 보는 전체 구조

> 온보딩 안내서입니다. 규범은 [아키텍처](../architecture.md) 정의 문서가 기준입니다.

<div class="terms" markdown="1">
<span class="label">핵심 용어</span> [Shared Control Plane](09-glossary.md#term-control-plane) [Distributed Execution Plane](09-glossary.md#term-execution-plane) [Agent Gateway](09-glossary.md#term-agent-gateway) [Model Gateway](09-glossary.md#term-model-gateway) [Tool Gateway](09-glossary.md#term-tool-gateway) [Credential Broker](09-glossary.md#term-credential-broker)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 이 페이지에서 배울 것**

- 통제와 실행을 두 평면으로 나누는 이유
- 구성요소 아홉 개가 각각 맡는 일
- Gateway가 세 개인 이유와 각자 지키는 방향
- 플랫폼을 정의하는 원칙 21개
</div>

## 들어가며

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 질문</span> 회사 전체를 통제하려면 모든 Agent를 한 곳에서 실행해야 할까요?

<span class="tag">{{icon:eye}} 관찰</span> Agent는 개발자 PC, Mac mini, 사내 서버, 클라우드처럼 제각각인 곳에서 돕니다. 한 곳으로 모으면 개발 속도가 떨어지고 장비도 낭비됩니다.

<span class="tag">{{icon:bulb}} 해결책</span> **통제는 한 곳에 모으고, 실행은 흩어 둡니다.** 어디서 돌든 같은 계약을 지키면 같은 규칙으로 통제됩니다.
</div>

## 두 개의 평면: 통제는 모으고, 실행은 흩는다

<div class="planes">
<div class="plane cp"><b class="title">{{icon:control}} Shared Control Plane</b><p>회사 전체가 하나를 함께 씁니다</p><ul><li>{{icon:manifest}} Registry</li><li>{{icon:shield}} Policy</li><li>{{icon:identity}} Identity 중개</li><li>{{icon:test}} Evaluation</li><li>{{icon:eye}} Observability</li><li>{{icon:rocket}} Promotion</li></ul></div>
<div class="bridge"><b>&#8596;</b>같은 계약<br>workload 신원</div>
<div class="plane"><b class="title">{{icon:runtime}} Distributed Execution Plane</b><p>Agent가 실제로 도는 곳</p><ul><li>{{icon:laptop}} 개발자 PC</li><li>{{icon:server}} Mac mini · 워크스테이션</li><li>{{icon:server}} 사내 서버</li><li>{{icon:cloud}} 클라우드</li></ul></div>
</div>

비유하면 항공 관제와 비슷합니다. 비행기(Agent)는 각 공항(실행 환경)에서 뜨고 내리지만, 비행 허가와 항로 규칙과 기록은 관제탑(Control Plane)이 맡습니다. 관제탑이 비행기를 직접 조종하지는 않습니다.

<div class="point" markdown="1">
**{{icon:warn}} 주의** 실행 환경이 **등록(registered)**됐다고 곧바로 **production 승인(production-approved)**이 되지는 않습니다. 개발자 PC도 등록할 수 있지만, 실제 업무 트래픽을 받으려면 별도의 승인 증거가 필요합니다.
</div>

## 구성요소 아홉 개

<div class="cards">
<div class="card">{{icon:gateway}}<b>Agent Gateway</b><p>앱이 Agent를 부를 때 들어오는 정문. 인증, Agent 찾기, 테넌트 권한 확인, 중복 요청 방지</p><span class="sub">비유: 건물 출입 게이트</span></div>
<div class="card">{{icon:runtime}}<b>Agent Runtime</b><p>Agent를 실제로 실행하는 곳. adapter로 Agent를 부르고 모델·도구·지식·상태·정책 서비스를 소비</p><span class="sub">비유: 작업장</span></div>
<div class="card">{{icon:model}}<b>Model Gateway</b><p>논리 모델 이름을 받아 데이터 분류·지역·비용·가용성 정책에 맞는 endpoint로 보냄</p><span class="sub">비유: 데이터 반출 검사대</span></div>
<div class="card">{{icon:tools}}<b>Agent Tools</b><p>도구 연동 영역 전체. Tool Registry, Tool Gateway, REST/OpenAPI/MCP adapter, 도구 정책과 감사</p><span class="sub">비유: 공구 창고</span></div>
<div class="card">{{icon:gateway}}<b>Tool Gateway</b><p>Agent Tools 안의 관문. 승인된 endpoint로만 보내고 입출력을 검사</p><span class="sub">비유: 공구 대여 창구</span></div>
<div class="card">{{icon:identity}}<b>Agent Identity</b><p>신원 영역 전체. 사용자 신원, Agent(workload) 신원, 위임 관계, 자격증명 중개</p><span class="sub">비유: 인사·보안팀</span></div>
<div class="card">{{icon:key}}<b>Credential Broker</b><p>Agent Identity 안의 고신뢰 서비스. 짧게 살고 범위가 좁은 자격증명을 발급. Runtime·LLM은 볼 수 없음</p><span class="sub">비유: 일회용 출입증 발급처</span></div>
<div class="card">{{icon:knowledge}}<b>Knowledge(RAG) Backend</b><p>검색 증강에 쓰는 지식 저장소. 공통 RAG 계약만 지키면 바꿔 낄 수 있음</p><span class="sub">비유: 사내 도서관</span></div>
<div class="card">{{icon:control}}<b>Shared Control Plane</b><p>Registry, Policy, Identity 중개, Evaluation, Observability, Promotion</p><span class="sub">비유: 관제탑</span></div>
</div>

<div class="point" markdown="1">
**{{icon:bulb}} 꼭 기억할 소속 관계** **Tool Gateway는 Agent Tools에**, **Credential Broker는 Agent Identity에** 속합니다. 논리적인 소속이라 물리적으로 합쳐 배포해도 되지만, 신원과 데이터 반출(egress)의 신뢰 경계는 합쳐도 지켜야 합니다(MUST).
</div>

실제 배치를 그린 C4 도식입니다.

![C4 Container: Shared Control Plane과 Distributed Execution Plane](../../diagrams/c4-container.svg)

## Gateway가 세 개인 이유

처음 보면 Gateway가 많아 보입니다. 각각 **지키는 방향**이 다릅니다.

<div class="lanes">
<div class="lane"><div>{{icon:user}} 사용자 · 업무 앱</div><i>&#8594;</i><div class="gate">{{icon:gateway}}<span>Agent Gateway<small>들어오는 길: 신원 위조, 권한 없는 접근, 중복 실행을 막음</small></span></div><i>&#8594;</i><div>{{icon:runtime}} Agent Runtime</div></div>
<div class="lane"><div>{{icon:runtime}} Agent Runtime</div><i>&#8594;</i><div class="gate">{{icon:model}}<span>Model Gateway<small>나가는 길: 기밀 데이터 외부 전송, 공급사 종속을 막음</small></span></div><i>&#8594;</i><div>{{icon:cloud}} 외부 · 자체 호스팅 모델</div></div>
<div class="lane"><div>{{icon:runtime}} Agent Runtime</div><i>&#8594;</i><div class="gate">{{icon:tools}}<span>Tool Gateway<small>나가는 길: 허가 안 된 호출, 자격증명 유출, 위조 결과를 막음</small></span></div><i>&#8594;</i><div>{{icon:server}} 사내 · 외부 도구</div></div>
</div>

호출을 통제하는 일과 모델 공급사를 추상화하는 일은 서로 다른 책임입니다. 세 Gateway 모두 **논리적인 책임 구분**이고, 특정 제품이나 프로세스 개수를 뜻하지 않습니다.

## 이 플랫폼을 정의하는 원칙

앞으로 읽을 내용을 원칙으로 모으면 다음과 같습니다. 각 원칙은 오른쪽 페이지에서 자세히 설명합니다.

| 영역 | 원칙 | 자세히 |
|---|---|---|
| {{icon:target}} 범위 | 전사가 함께 쓰는 하나의 공통 플랫폼이다. 팀마다 따로 만들지 않는다 | [왜 필요한가](01-why.md) |
| {{icon:cloud}} 인프라 | 온프레미스와 퍼블릭 클라우드를 함께 쓰는 Hybrid Cloud를 전제한다. 실행 자원은 특정 서빙 제품에 묶이지 않는다 | 이 페이지 |
| {{icon:control}} 구조 | 통제는 Shared Control Plane에 모으고, 실행은 Distributed Execution Plane에 분산한다 | 이 페이지 |
| {{icon:gateway}} 호출 경계 | Agent Gateway, Model Gateway, Tool Gateway는 서로 다른 경계를 지킨다 | 이 페이지 |
| {{icon:model}} 모델 | 외부 상용 LLM과 자체 호스팅 오픈소스 모델을 함께 쓰고, Model Gateway가 정책으로 경로를 고른다 | [요청 하나 따라가기](03-one-request.md) |
| {{icon:runtime}} 실행 | 공통 Runtime 계약과 framework adapter로 어떤 프레임워크든 실행한다 | [요청 하나 따라가기](03-one-request.md) |
| {{icon:tools}} 도구 | REST/OpenAPI, MCP, 사용자 정의 adapter를 Tool Gateway 뒤에서 지원한다 | [요청 하나 따라가기](03-one-request.md) |
| {{icon:identity}} 신원 | 사용자 신원과 Agent 신원을 함께 다루고, 자격증명은 Credential Broker가 짧게 발급한다 | [신뢰 경계](04-trust.md) |
| {{icon:lock}} 테넌트 | 기본은 논리 격리이고, 민감도와 위험에 따라 물리 분리를 선택한다 | [신뢰 경계](04-trust.md) |
| {{icon:shield}} 데이터 | 데이터 분류에 따라 접근과 이동(외부 모델 전송 포함)을 통제한다 | [신뢰 경계](04-trust.md) |
| {{icon:agent}} Agent 종류 | RAG, Tool, Workflow, Multi-Agent를 처음부터 공통 계약으로 지원한다 | [Agent와 Manifest](05-agents-and-manifest.md) |
| {{icon:knowledge}} 지식 | 공통 RAG 계약을 지키면 검색 저장소는 바꿔 낄 수 있다 | [Agent와 Manifest](05-agents-and-manifest.md) |
| {{icon:agents}} Agent 간 협업 | 공통 Agent 통신 계약을 쓰고, A2A 같은 특정 프로토콜은 선택이다 | [Agent와 Manifest](05-agents-and-manifest.md) |
| {{icon:laptop}} 개발 방식 | Local-First, CLI-First. 지금 쓰는 IDE·Git·CLI를 유지하고 중앙 소스 업로드를 강제하지 않는다 | [production까지](06-lifecycle.md) |
| {{icon:test}} 실험 | 실험은 로컬에서 하고, 공유가 필요하면 공용 실험·평가 기록소에 남긴다 | [production까지](06-lifecycle.md) |
| {{icon:approve}} 수명주기 | 자동 게이트를 통과하면 셀프서비스로 진행하고, 위험이 높을수록 사람 승인을 더한다 | [production까지](06-lifecycle.md) |
| {{icon:eye}} 품질 | 관측, 자동 평가, 품질 게이트를 배포 과정에 포함한다 | [production까지](06-lifecycle.md) |
| {{icon:clock}} 신뢰성 | 오래 걸리는 작업은 Durable 실행과 HITL 승인, 정책 통제로 다룬다 | [production까지](06-lifecycle.md) |
| {{icon:target}} 운영 목표 | SLO는 실행 환경과 업무 위험도에 따라 단계적으로 정한다 | [production까지](06-lifecycle.md) |
| {{icon:rocket}} 도입 방식 | 먼저 끝에서 끝까지 이어진 한 줄의 경로를 완성하고, 기능을 단계적으로 붙인다 | [production까지](06-lifecycle.md) |
| {{icon:code}} 계약 | 계약은 언어 중립(OpenAPI, JSON Schema)이고, 코드로 검증하며, 버전으로 관리한다 | [규격 읽는 법](08-reading-the-spec.md) |

<div class="check" markdown="1">
**{{icon:question}} 스스로 점검**

<details markdown="1"><summary>Q1. 개발자 PC를 실행 환경으로 등록하면 바로 업무 트래픽을 받을 수 있나요?</summary>
아닙니다. 등록(registered)과 production 승인(production-approved)은 다릅니다. 승인에는 보안·평가·복구 증거가 필요합니다.
</details>

<details markdown="1"><summary>Q2. Credential Broker는 어느 영역에 속하나요?</summary>
Agent Identity입니다. Tool Gateway는 Agent Tools에 속합니다.
</details>

<details markdown="1"><summary>Q3. Model Gateway가 막으려는 것은 무엇인가요?</summary>
데이터 분류에 맞지 않는 외부 모델 전송과, 특정 모델 공급사에 Agent 코드가 묶이는 것입니다.
</details>
</div>

<div class="summary" markdown="1">
**정리**

- 통제는 Shared Control Plane에, 실행은 Distributed Execution Plane에 둡니다.
- 구성요소는 아홉 개이고, Tool Gateway는 Agent Tools에, Credential Broker는 Agent Identity에 속합니다.
- 세 Gateway는 들어오는 길 하나와 나가는 길 둘을 각각 지킵니다.
</div>

<nav class="pager"><a href="01-why.md"><small>이전</small><b>왜 이 플랫폼이 필요한가</b></a><a class="next" href="03-one-request.md"><small>다음</small><b>요청 하나 따라가기</b></a></nav>
