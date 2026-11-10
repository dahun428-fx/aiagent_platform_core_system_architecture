# Core Systems 아키텍처

> 개발자 가이드 문서입니다. 규범은 [Core Systems](../core-systems.md)와 [아키텍처](../architecture.md) 기술 표준 문서가 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Core Systems](09-glossary.md#term-core-systems) [Agent Platform APIs](09-glossary.md#term-platform-apis) [Agent Gateway](09-glossary.md#term-agent-gateway) [Agent Factory](09-glossary.md#term-factory) [Shared Control Plane](09-glossary.md#term-control-plane) [Distributed Execution Plane](09-glossary.md#term-execution-plane) [Registry](09-glossary.md#term-registry) [Agent Tools](09-glossary.md#term-agent-tools) [Agent Identity](09-glossary.md#term-agent-identity) [Credential Broker](09-glossary.md#term-credential-broker)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- AI Agent Platform을 구성하는 10개 Core System과 층 구조를 설명할 수 있습니다.
- Core System별 책임과 v0.1 제공 범위를 구분할 수 있습니다.
- 진입 경계(Agent Platform APIs)와 반출 경계(Agent Gateway)를 구분할 수 있습니다.
- 공통 제어 평면과 분산 실행 평면의 배치 관점을 설명할 수 있습니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> 인증, 실행, 도구 연동, 관측, 평가, 개선을 각 팀이 개별 구현하면 책임 경계가 팀마다 달라집니다.

<span class="tag">{{icon:eye}} 현황</span> Agent 플랫폼은 개발 도구부터 실행, 외부 모델·도구 연동, 품질 개선까지 여러 책임을 포함합니다. 책임을 나누는 기준이 없으면 같은 기능이 여러 곳에 중복되고 통제 지점이 흐려집니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> 플랫폼을 **10개 Core System**으로 나누고 층 구조로 배치합니다. 응용은 API 계층으로만 진입하고, 외부 모델·도구는 Agent Gateway로만 연결합니다.
</div>

## Core Systems 구조

<div class="stack">
<div class="s-app"><b>{{icon:laptop}} AI Platform Applications</b><small>DevTools(CLI · SDK · 템플릿) · Space(공유 작업 공간)</small><span class="st impl">DevTools 구현 · Space 정의</span></div>
<div class="s-api"><b>{{icon:gateway}} Agent Platform APIs</b><small>Agent 호출 · Registry 조회 · Agent Card · 실행 상태 · 승인 · 평가 결과</small><span class="st impl">호출 API mock 구현</span></div>
<div class="s-factory"><b>{{icon:manifest}} Agent Factory</b><small>생성 · Manifest 선언 · 검증 · 등록</small><span class="st impl">검증 도구 구현</span></div>
<div class="s-runtime"><b>{{icon:runtime}} Agent Runtime</b><small>framework adapter · Durable 실행 · Memory</small><span class="st impl">mock 구현</span></div>
<div class="s-tools"><b>{{icon:tools}} Agent Tools</b><small>Tool Registry · adapter · 도구 정책</small><span class="st impl">mock 구현</span></div>
<div class="s-identity"><b>{{icon:identity}} Agent Identity</b><small>사용자·workload Identity · Credential Broker</small><span class="st impl">mock 구현</span></div>
<div class="s-obs"><b>{{icon:eye}} Agent Observability</b><small>실행 추적 · 지표 · 로그</small><span class="st impl">trace 전파 구현</span></div>
<div class="s-eval"><b>{{icon:test}} Agent Evaluation</b><small>배포 전 평가 · 추적 분석 · 운영 모니터링</small><span class="st contract">계약</span></div>
<div class="s-gateway"><b>{{icon:gateway}} Agent Gateway</b><small>모델 경로 · 도구 경로 · Guardrail 집행</small><span class="st impl">mock 구현</span></div>
<div class="s-tuning"><b>{{icon:rocket}} Agent Tuning (FastTrack)</b><small>평가 기반 개선 흐름</small><span class="st">정의</span></div>
<div class="s-ext-app"><b>{{icon:user}} External Applications and Solutions</b><small>Agent Platform APIs로만 접근</small></div>
<div class="s-ext-tool"><b>{{icon:cloud}} External Tools and Models</b><small>Agent Gateway로만 접근</small></div>
<div class="s-infra"><b>{{icon:server}} 실행 인프라 (Distributed Execution Plane)</b><small>개발자 로컬 · Mac mini · 사내 서버 · 클라우드 · 모델 endpoint</small></div>
</div>

<div class="stack-legend"><span><span class="st impl">구현</span> 로컬 mock 또는 도구로 동작</span><span><span class="st contract">계약</span> 계약·규칙 정의, 구현은 후속</span><span><span class="st">정의</span> 책임·흐름 정의, 구현은 후속</span></div>

## Core System별 책임

<div class="cards">
<div class="card">{{icon:laptop}}<b>AI Platform Applications</b><p>개발자·운영자가 사용하는 응용 계층입니다. DevTools는 CLI·SDK·템플릿·mock, Space는 Agent 카탈로그·추적·평가·승인 조회를 위한 공유 작업 공간입니다. Space 사용은 강제하지 않습니다.</p><span class="sub">Agent Platform APIs만 호출</span></div>
<div class="card">{{icon:gateway}}<b>Agent Platform APIs</b><p>플랫폼 기능을 노출하는 단일 API 계층이자 진입 경계입니다. 인증, Agent 해석, 테넌트 인가, 멱등성을 처리합니다.</p><span class="sub">계약: agent-gateway.openapi.json 외</span></div>
<div class="card">{{icon:manifest}}<b>Agent Factory</b><p>Agent 생성, Manifest 선언, 로컬 검증, CI 게이트, Registry 등록으로 이어지는 개발 흐름을 담당합니다.</p><span class="sub">agentctl validate · Manifest 스키마</span></div>
<div class="card">{{icon:runtime}}<b>Agent Runtime</b><p>framework adapter로 Agent를 실행합니다. 하위 구성요소로 Durable 실행·상태와 Memory를 포함하며, 실행 제어 Guardrail의 집행 지점입니다.</p><span class="sub">Runtime 계약 · execution.schema</span></div>
<div class="card">{{icon:tools}}<b>Agent Tools</b><p>Tool Registry, 도구 descriptor, REST/OpenAPI/MCP adapter, 도구 정책과 감사를 소유합니다. 도구 호출의 집행은 Agent Gateway 도구 경로가 수행합니다.</p><span class="sub">tool-descriptor.schema</span></div>
<div class="card">{{icon:identity}}<b>Agent Identity</b><p>사용자 Identity, Agent(workload) Identity, 위임, 자격증명 중개를 담당합니다. Credential Broker를 포함합니다.</p><span class="sub">credential-broker.openapi</span></div>
<div class="card">{{icon:eye}}<b>Agent Observability</b><p>실행 추적·지표·로그를 수집합니다. span은 OpenTelemetry GenAI semantic conventions를 따릅니다.</p><span class="sub">W3C Trace Context · OTel GenAI</span></div>
<div class="card">{{icon:test}}<b>Agent Evaluation</b><p>배포 전 평가, 실행 추적 분석, 운영 모니터링으로 품질과 안전성을 측정하고 승격 판단 근거를 제공합니다.</p><span class="sub">evaluation.schema</span></div>
<div class="card">{{icon:gateway}}<b>Agent Gateway</b><p>외부 모델·도구로 나가는 반출(egress) 관문입니다. 모델 경로는 데이터 분류 기반 라우팅, 도구 경로는 승인된 endpoint와 단기 자격증명으로 호출합니다.</p><span class="sub">model-gateway · tool-gateway.openapi</span></div>
<div class="card">{{icon:rocket}}<b>Agent Tuning (FastTrack)</b><p>평가 결과와 실행 추적을 근거로 프롬프트·도구 구성·모델 선택·미세조정을 개선합니다. 결과는 새 불변 버전으로 다시 평가받습니다.</p><span class="sub">승인 요건은 생략하지 않음</span></div>
</div>

<div class="point" markdown="1">
**{{icon:bulb}} 계약 파일 대응** 계약 파일명은 호환성을 위해 유지합니다. `agent-gateway.openapi.json`은 Agent Platform APIs의 Agent 호출 API이고, `model-gateway.openapi.json`과 `tool-gateway.openapi.json`은 Agent Gateway의 모델 경로와 도구 경로입니다. 코드와 감사 기록의 component 이름(`agent-gateway`, `model-gateway`)도 그대로 사용합니다.
</div>

## 진입 경계와 반출 경계

<div class="lanes">
<div class="lane" data-say="업무 앱이 Agent를 부르는 길입니다. 정문인 Agent Platform APIs가 호출자 신원을 확인하고, 권한이 없거나 같은 요청이 중복되면 Agent Runtime에 닿기 전에 막습니다."><div>{{icon:user}} 업무 앱 · Applications</div><i>&#8594;</i><div class="gate">{{icon:gateway}}<span>Agent Platform APIs<small>진입: Identity 위조, 미인가 접근, 중복 실행 차단</small></span></div><i>&#8594;</i><div>{{icon:runtime}} Agent Runtime</div></div>
<div class="lane" data-say="Agent가 모델을 부르는 길입니다. Agent Gateway의 모델 경로가 데이터 분류를 보고, 밖으로 나가면 안 되는 데이터가 외부 모델로 가지 않게 막습니다."><div>{{icon:runtime}} Agent Runtime</div><i>&#8594;</i><div class="gate">{{icon:model}}<span>Agent Gateway · 모델 경로<small>반출: 분류 위반 외부 전송, 공급사 종속 차단</small></span></div><i>&#8594;</i><div>{{icon:cloud}} 외부 · 자체 호스팅 모델</div></div>
<div class="lane" data-say="Agent가 사내·외부 도구를 부르는 길입니다. Agent Gateway의 도구 경로가 승인된 도구인지 확인하고, 자격증명이 Agent에 노출되지 않게 대신 연결합니다."><div>{{icon:runtime}} Agent Runtime</div><i>&#8594;</i><div class="gate">{{icon:tools}}<span>Agent Gateway · 도구 경로<small>반출: 미승인 호출, 자격증명 유출, 비신뢰 결과 차단</small></span></div><i>&#8594;</i><div>{{icon:server}} 사내 · 외부 도구</div></div>
</div>

진입 경계와 모델 경로는 논리적으로 분리해야 합니다(MUST). 호출 통제와 모델 공급사 추상화는 서로 다른 책임이기 때문입니다. 논리적 분리이므로 물리적으로 통합 배포할 수 있으나, Identity와 데이터 반출의 신뢰 경계는 유지해야 합니다(MUST).

## 배치 관점: 공통 제어 평면과 분산 실행 평면

<div class="planes">
<div class="plane cp"><b class="title">{{icon:control}} Shared Control Plane</b><p>전사 공통으로 운영하는 제어 영역</p><ul><li>{{icon:manifest}} Registry</li><li>{{icon:shield}} Policy · Guardrail 검사</li><li>{{icon:identity}} Identity 중개</li><li>{{icon:test}} Evaluation</li><li>{{icon:eye}} Observability</li><li>{{icon:rocket}} Promotion</li></ul></div>
<div class="bridge"><b>&#8596;</b>공통 계약<br>workload identity</div>
<div class="plane"><b class="title">{{icon:runtime}} Distributed Execution Plane</b><p>Agent가 실행되는 환경</p><ul><li>{{icon:laptop}} 개발자 PC</li><li>{{icon:server}} Mac mini · 워크스테이션</li><li>{{icon:server}} 사내 서버</li><li>{{icon:cloud}} 클라우드</li></ul></div>
</div>

![C4 Container 도식](../../diagrams/c4-container.svg)

Core System은 기능 관점의 구분이고, 두 평면은 배치 관점의 구분입니다. 공통 제어 평면의 **Registry**는 Agent·도구·모델·실행 환경의 불변 revision, artifact digest, Manifest, 평가 결과를 저장하는 구성요소이며, 이후 장에서 계속 사용됩니다. 공통 제어 평면은 Agent를 직접 실행하지 않고 실행 허가·정책·기록을 담당하며, Agent Runtime과 Agent Gateway의 실행 인스턴스는 분산 실행 평면에 배치됩니다.

<div class="point" markdown="1">
**{{icon:warn}} 등록과 승인의 구분** 실행 환경의 **등록(registered)**은 **프로덕션 승인(production-approved)**과 다릅니다. 업무 트래픽을 처리하려면 별도의 승인 요건을 충족해야 합니다.
</div>

## 플랫폼 설계 원칙

| 영역 | 원칙 | 관련 문서 |
|---|---|---|
| {{icon:target}} 범위 | 전사 공통 플랫폼 하나를 10개 Core System으로 운영합니다 | 이 문서 |
| {{icon:cloud}} 인프라 | Hybrid Cloud를 전제하며, 실행 자원은 특정 서빙 제품에 종속되지 않습니다 | 이 문서 |
| {{icon:gateway}} 경계 | 진입은 Agent Platform APIs, 외부 모델·도구 접근은 Agent Gateway로 일원화합니다 | 이 문서 |
| {{icon:model}} 모델 | 외부 상용 LLM과 자체 호스팅 모델을 함께 사용하며, 모델 경로가 정책에 따라 선택합니다 | [요청 처리 흐름](03-one-request.md) |
| {{icon:manifest}} 개발 | Local-First, CLI-First로 개발하고, Agent Factory 흐름으로 선언·검증·등록합니다 | [Agent Factory](05-agents-and-manifest.md) |
| {{icon:runtime}} 실행 | 공통 Runtime 계약과 framework adapter로 프레임워크와 무관하게 실행합니다 | [Runtime과 Memory](11-runtime-memory.md) |
| {{icon:identity}} Identity | 사용자·Agent Identity를 함께 다루고, 자격증명은 Credential Broker가 단기로 발급합니다 | [신뢰 경계와 Guardrails](04-trust.md) |
| {{icon:shield}} Guardrail | 공통 검사 서비스와 네 집행 지점으로 입력·출력·도구·검색·실행을 통제합니다 | [신뢰 경계와 Guardrails](04-trust.md) |
| {{icon:eye}} 관측성 | OpenTelemetry GenAI 규격으로 실행 추적을 기록합니다 | [Observability와 Evaluation](12-observability-evaluation.md) |
| {{icon:test}} 평가 | 배포 전 평가·추적 분석·운영 모니터링 3단계로 품질과 안전성을 측정합니다 | [Observability와 Evaluation](12-observability-evaluation.md) |
| {{icon:agents}} Agent 간 통신 | 공통 통신 계약을 사용하고, Registry가 서명한 A2A Agent Card로 Agent를 발견합니다 | [Agent Card](13-agent-card.md) |
| {{icon:rocket}} 개선 | 평가 기반 Tuning 결과는 새 버전으로 다시 평가·승인받습니다 | [수명주기와 Tuning](06-lifecycle.md) |
| {{icon:code}} 계약 | API 계약과 JSON Schema는 언어 중립적이며, 코드로 검증하고 버전으로 관리합니다 | [기술 표준 해석](08-reading-the-spec.md) |

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. 업무 앱이 Agent를 호출할 때 처음 만나는 Core System은 무엇입니까?</summary>
Agent Platform APIs입니다. 인증, Agent 해석, 테넌트 인가, 멱등성 처리가 이 계층에서 수행됩니다.
</details>

<details markdown="1"><summary>Q2. Agent가 외부 모델이나 도구를 호출할 때 거치는 Core System은 무엇입니까?</summary>
Agent Gateway입니다. 모델은 모델 경로, 도구는 도구 경로를 거치며, 두 경로 모두 Guardrail 집행 지점입니다.
</details>

<details markdown="1"><summary>Q3. Tool Registry와 도구 정책은 어느 Core System이 소유합니까?</summary>
Agent Tools입니다. Agent Gateway의 도구 경로는 Agent Tools의 정의에 따라 호출을 집행합니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- 플랫폼은 Applications, Platform APIs, Factory, Runtime, Tools, Identity, Observability, Evaluation, Gateway, Tuning의 10개 Core System으로 구성됩니다.
- 진입은 Agent Platform APIs, 외부 모델·도구 접근은 Agent Gateway로 일원화합니다.
- Core System은 기능 관점, 공통 제어 평면·분산 실행 평면은 배치 관점의 구분입니다.
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- 업계 플랫폼의 구성요소 구분: [클라우드 Agent 플랫폼](10-references.md#ref-industry)
- 모델 관문(AI Gateway) 패턴: [AI Gateway](10-references.md#ref-gateway)
</div>

<nav class="pager"><a href="01-why.md"><small>이전</small><b>플랫폼 도입 배경과 설계 원칙</b></a><a class="next" href="03-one-request.md"><small>다음</small><b>Agent 요청 처리 흐름</b></a></nav>
