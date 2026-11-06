# 주요 용어 정의

> 개발자 가이드에서 사용하는 용어의 권장 표기와 정의입니다. 규범적 정의는 [용어와 규범](../glossary.md)이 기준입니다.

<div class="goals" markdown="1">
**{{icon:book}} 표기 원칙**

- `Agent`, `Agent Platform APIs`, `Agent Gateway`, `Credential Broker`, `Manifest` 등 공식 명칭은 영문을 유지합니다.
- 일반 기술 개념은 한국어를 사용하고, 최초 등장 시 영문을 병기합니다. 예: 멱등성(Idempotency), 신뢰 경계(Trust Boundary).
- 설명문에서는 '프로덕션 환경', '프로덕션 승인'으로 표기하고, 코드·상태값(`production`, `production-approved`)은 원문을 유지합니다.
- 각 장 상단의 **주요 용어** 링크를 선택하면 이 문서의 해당 항목으로 이동합니다.
</div>

## 기본 개념

<div class="term-group">
<div class="term" id="term-agent">{{icon:agent}}<b>Agent <small>AI Agent</small></b><p>모델을 사용해 판단하고, 도구와 지식을 활용해 작업을 수행하는 프로그램입니다.</p><p class="eg">예: 청구서를 조회해 요약하는 재무 Agent · <a href="01-why.md">도입 배경과 설계 원칙</a></p></div>
<div class="term" id="term-boundary">{{icon:shield}}<b>신뢰 경계 <small>Trust Boundary</small></b><p>신뢰 수준이 달라지는 구성요소 간 지점입니다. 플랫폼은 각 신뢰 경계에서 검증을 수행합니다.</p><p class="eg">예: 클라이언트 → Agent Platform APIs, Runtime → Agent Gateway · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
<div class="term" id="term-contract">{{icon:code}}<b>기술 계약 <small>Contract</small></b><p>구성요소 간 입출력 형식과 규칙을 기계 판독 가능하게 정의한 것입니다. API 계약은 OpenAPI, 데이터 형식은 JSON Schema로 작성합니다.</p><p class="eg">예: agent-manifest.schema.json, agent-gateway.openapi.json · <a href="08-reading-the-spec.md">기술 표준 해석과 FAQ</a></p></div>
<div class="term" id="term-tbd">{{icon:question}}<b>TBD <small>To Be Determined</small></b><p>회사 환경에 따라 결정해야 하는 제품 또는 수치입니다. 예제 값을 기본값으로 사용할 수 없습니다.</p><p class="eg">예: IdP 제품, SLO 수치, 자격증명 TTL · <a href="08-reading-the-spec.md">기술 표준 해석과 FAQ</a></p></div>
<div class="term" id="term-tenant">{{icon:lock}}<b>테넌트 <small>Tenant</small></b><p>데이터와 권한이 분리되는 단위입니다. 논리 격리를 기본으로 하며, 위험도에 따라 물리 분리를 적용합니다.</p><p class="eg">예: 재무 사업부, 인사 사업부 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
</div>

## 아키텍처

<div class="term-group">
<div class="term" id="term-core-systems">{{icon:map}}<b>Core Systems <small>Core Systems</small></b><p>플랫폼을 구성하는 10개 시스템입니다. AI Platform Applications, Agent Platform APIs, Agent Factory, Agent Runtime, Agent Tools, Agent Identity, Agent Observability, Agent Evaluation, Agent Gateway, Agent Tuning으로 구성됩니다.</p><p class="eg">기능 관점의 구분이며, 배치 관점은 공통 제어 평면·분산 실행 평면으로 구분합니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p></div>
<div class="term" id="term-applications">{{icon:laptop}}<b>AI Platform Applications <small>DevTools, Space</small></b><p>개발자·운영자가 사용하는 응용 계층입니다. DevTools(CLI·SDK·템플릿·mock)와 Space(Agent 카탈로그·추적·평가·승인 조회 공유 공간)로 구성됩니다.</p><p class="eg">Agent Platform APIs만 호출하며, Space 사용은 강제하지 않습니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p></div>
<div class="term" id="term-platform-apis">{{icon:gateway}}<b>Agent Platform APIs <small>Northbound API layer</small></b><p>플랫폼 기능을 노출하는 단일 API 계층이자 진입 경계입니다. Agent 호출, Registry 조회, Agent Card, 실행 상태, 승인, 평가 결과 API를 포함합니다.</p><p class="eg">Agent 호출 API의 계약 파일명은 agent-gateway.openapi.json입니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p></div>
<div class="term" id="term-factory">{{icon:manifest}}<b>Agent Factory <small>Agent Factory</small></b><p>Agent 생성, Manifest 선언, 로컬 검증, CI 게이트, Registry 등록으로 이어지는 개발 흐름을 담당하는 Core System입니다.</p><p class="eg">소스 업로드를 요구하지 않습니다 · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-tuning">{{icon:rocket}}<b>Agent Tuning <small>FastTrack</small></b><p>평가 결과와 실행 추적을 근거로 프롬프트·도구 구성·모델 선택·미세조정을 개선하는 Core System입니다. FastTrack은 평가 → 개선안 → 재평가 → 승격 후보 등록의 반복 흐름입니다.</p><p class="eg">프로덕션 승인 요건을 줄이지 않으며, 결과는 새 불변 버전으로 등록합니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p></div>
<div class="term" id="term-control-plane">{{icon:control}}<b>Shared Control Plane <small>공통 제어 평면</small></b><p>전사 공통으로 운영하는 제어 영역입니다. Registry, Policy, Identity 중개, Evaluation, Observability, Promotion을 제공합니다.</p><p class="eg">Agent를 직접 실행하지 않습니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p></div>
<div class="term" id="term-execution-plane">{{icon:runtime}}<b>Distributed Execution Plane <small>분산 실행 평면</small></b><p>Agent가 실행되는 이기종 환경의 집합입니다. 개발자 PC, 사내 서버, 클라우드가 동일한 계약을 따릅니다.</p><p class="eg">등록된 환경이라도 프로덕션 승인과는 별개입니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p></div>
<div class="term" id="term-runtime">{{icon:runtime}}<b>Agent Runtime <small>Runtime</small></b><p>framework adapter로 Agent를 실행하는 Core System입니다. 하위 구성요소로 Durable 실행·상태와 Memory를 포함합니다.</p><p class="eg">보안·정책 권한을 임의로 변경할 수 없습니다(MUST NOT) · <a href="11-runtime-memory.md">Agent Runtime과 Memory</a></p></div>
<div class="term" id="term-adapter">{{icon:tools}}<b>Framework adapter <small>Adapter</small></b><p>각 Agent 프레임워크를 공통 Runtime 계약에 연결하는 변환 계층입니다.</p><p class="eg">Manifest의 runtime.framework, runtime.adapter에 선언합니다 · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-registry">{{icon:manifest}}<b>Registry <small>Registry</small></b><p>Agent·Tool·Model·Environment를 등록하는 구성요소입니다. 소스가 아니라 불변 revision, artifact digest, Manifest, 평가 결과를 저장합니다.</p><p class="eg">상태: registered, eligible, production-approved, quarantined · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p></div>
<div class="term" id="term-knowledge">{{icon:knowledge}}<b>Knowledge(RAG) Backend <small>Knowledge Backend</small></b><p>RAG Agent가 검색하는 지식 저장소입니다. 공통 RAG 계약을 준수하면 교체할 수 있습니다.</p><p class="eg">검색 결과는 Guardrail ③ 집행 지점에서 검사합니다 · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-memory">{{icon:knowledge}}<b>Memory <small>Short-term / Long-term memory</small></b><p>Agent Runtime 하위 구성요소로, 대화·작업 사이에 정보를 유지합니다. 단기 Memory는 세션 범위, 장기 Memory는 세션을 넘어 유지됩니다.</p><p class="eg">tenant·주체·Agent 범위에 결합하며, 시크릿을 저장하지 않습니다 · <a href="11-runtime-memory.md">Agent Runtime과 Memory</a></p><p class="eg">피할 표현: Durable checkpoint와 동일시하는 표현</p></div>
<div class="term" id="term-memory-poisoning">{{icon:warn}}<b>Memory 오염 <small>Memory poisoning</small></b><p>잘못되거나 악의적인 정보가 장기 Memory에 저장되어 이후 세션의 동작에 영향을 주는 위험입니다.</p><p class="eg">장기 Memory 쓰기 전 검사와 비신뢰 취급으로 방지합니다 · <a href="11-runtime-memory.md">Agent Runtime과 Memory</a></p></div>
</div>

## 호출 경계

<div class="term-group">
<div class="term" id="term-agent-gateway">{{icon:gateway}}<b>Agent Gateway <small>Egress gateway</small></b><p>Agent가 외부 모델·도구에 접근하는 반출 관문입니다. 모델 경로와 도구 경로로 구성되며, 모델 입출력·도구 호출·도구 결과 Guardrail의 집행 지점입니다.</p><p class="eg">앱의 진입은 Agent Platform APIs가 담당합니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p><p class="eg">피할 표현: 앱 진입 관문으로 설명하는 표현</p></div>
<div class="term" id="term-model-gateway">{{icon:model}}<b>모델 경로 <small>Model Gateway</small></b><p>Agent Gateway의 모델 경로입니다. 논리 모델 이름을 데이터 분류·지역·비용·가용성 정책에 맞는 endpoint로 라우팅합니다.</p><p class="eg">confidential·restricted 데이터의 외부 경로를 거부합니다 · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-tool-gateway">{{icon:tools}}<b>도구 경로 <small>Tool Gateway</small></b><p>Agent Gateway의 도구 경로입니다. 도구 ID를 Agent Tools의 승인된 endpoint로 해석하고 입출력 스키마와 정책을 검증합니다.</p><p class="eg">호출자는 URL·헤더·토큰 endpoint를 지정할 수 없습니다 · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-agent-tools">{{icon:tools}}<b>Agent Tools <small>Agent Tools</small></b><p>Tool Registry, 도구 descriptor, REST/OpenAPI/MCP adapter, 도구 정책과 감사를 포함하는 Core System입니다.</p><p class="eg">도구 호출의 집행은 Agent Gateway 도구 경로가 수행합니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p></div>
<div class="term" id="term-mcp">{{icon:tools}}<b>MCP <small>Model Context Protocol</small></b><p>Agent가 도구를 사용하기 위한 프로토콜입니다. 이 플랫폼에서는 Agent Gateway 도구 경로의 adapter가 MCP client를 소유합니다.</p><p class="eg">MCP는 회사 인가 정책을 대체하지 않습니다 · <a href="08-reading-the-spec.md">기술 표준 해석과 FAQ</a></p></div>
</div>

## Identity와 보안

<div class="term-group">
<div class="term" id="term-guardrail">{{icon:shield}}<b>Guardrail <small>Guardrails</small></b><p>입력·출력·도구 결과·검색 결과·실행 동작이 정책을 벗어나지 않도록 검사하고 차단하는 통제입니다. 공통 검사 서비스와 네 집행 지점(모델 입출력, 도구 호출·결과, 검색 결과, 실행 제어)으로 구성됩니다.</p><p class="eg">검사 서비스는 판정만 반환하고 차단은 집행 지점이 결정합니다 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p><p class="eg">피할 표현: 단일 관문 검사로 충분하다는 표현</p></div>
<div class="term" id="term-agent-identity">{{icon:identity}}<b>Agent Identity <small>Agent Identity</small></b><p>사용자 Identity, Agent(workload) Identity, 위임 관계, 자격증명 중개를 다루는 논리 영역입니다.</p><p class="eg">Credential Broker가 이 영역에 속합니다 · <a href="02-big-picture.md">Core Systems 아키텍처</a></p><p class="eg">피할 표현: Manifest와 동일시하는 표현</p></div>
<div class="term" id="term-credential-broker">{{icon:key}}<b>Credential Broker <small>Credential Broker</small></b><p>대상(audience)·범위(scope)·만료가 제한된 단기 자격증명을 발급하는 고신뢰 서비스입니다.</p><p class="eg">Runtime과 LLM에는 자격증명을 노출하지 않습니다 · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-lease">{{icon:key}}<b>Lease <small>Credential lease</small></b><p>Credential Broker가 발급하는 불투명 참조입니다. 테넌트·workload·도구·호출에 결합되며, adapter 내부에서만 실제 자격증명으로 교환됩니다.</p><p class="eg">응답 필드: credentialRef, audience, scopes, expiresAt, nonExportable=true · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-identity-context">{{icon:identity}}<b>실행 주체 식별 정보 <small>identity context</small></b><p>Agent Platform APIs가 검증된 토큰에서 생성해 Runtime에 전달하는 Identity 정보입니다.</p><p class="eg">요청 본문의 tenantId는 비교에만 사용합니다 · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-delegated">{{icon:user}}<b>위임 모드 / 독립 모드 <small>Delegated / Independent</small></b><p>위임 모드는 사용자를 대신해 동작하고, 독립 모드는 Agent 자체 권한으로만 동작합니다.</p><p class="eg">Manifest의 identity.mode 값: delegated, independent · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-scope">{{icon:shield}}<b>권한 교집합 <small>Scope intersection</small></b><p>유효 권한은 사용자 권한 ∩ Agent 권한 ∩ 도구 허용 범위 ∩ 정책입니다. 위임 단계가 늘어날수록 축소만 가능합니다.</p><p class="eg">하위 Agent 호출마다 범위를 축소하고 재검증합니다 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
<div class="term" id="term-injection">{{icon:warn}}<b>프롬프트 인젝션 <small>Prompt injection</small></b><p>검색 결과나 도구 출력에 삽입한 지시문으로 Agent의 동작을 조작하려는 공격입니다.</p><p class="eg">검색·도구·모델 결과를 비신뢰 데이터로 처리하는 이유입니다 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
<div class="term" id="term-fail-closed">{{icon:lock}}<b>실패 시 거부 <small>fail closed</small></b><p>검증할 수 없으면 거부하는 원칙입니다. IdP·Credential Broker·정책 조회 실패 시 신규 자격증명을 발급하지 않습니다.</p><p class="eg">반대 개념: fail open · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
<div class="term" id="term-classification">{{icon:shield}}<b>데이터 분류 <small>Data classification</small></b><p>데이터의 민감도 등급입니다. public, internal, confidential, restricted 4단계입니다.</p><p class="eg">데이터 분류가 모델 경로와 접근 권한을 결정합니다 · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-secret">{{icon:key}}<b>시크릿 / 자격증명 <small>Secret / Credential</small></b><p>시크릿은 API 키·비밀번호 등 민감한 설정 값이고, 자격증명은 대상 시스템에 접근하기 위한 인증 정보입니다.</p><p class="eg">장기 시크릿은 코드·Manifest·로그에 두지 않으며, 자격증명은 Credential Broker가 단기로 발급합니다 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p><p class="eg">피할 표현: 두 개념을 &#x27;비밀값&#x27;으로 통칭하는 표현</p></div>
</div>

## 요청과 실행

<div class="term-group">
<div class="term" id="term-otel-genai">{{icon:eye}}<b>OTel GenAI 규격 <small>OpenTelemetry GenAI semantic conventions</small></b><p>생성형 AI와 Agent의 실행 추적 span 이름과 속성을 정의한 OpenTelemetry 규격입니다. Agent 호출 span은 invoke_agent {gen_ai.agent.name}입니다.</p><p class="eg">Development 단계 규격이므로 사용 버전을 고정합니다 · <a href="12-observability-evaluation.md">Agent Observability와 Agent Evaluation</a></p></div>
<div class="term" id="term-evaluation">{{icon:test}}<b>평가 3단계 <small>Evaluation stages</small></b><p>배포 전 평가, 실행 추적 분석, 운영 모니터링으로 구성된 Agent Evaluation의 단계입니다.</p><p class="eg">평가 결과는 Agent Tuning의 입력입니다 · <a href="12-observability-evaluation.md">Agent Observability와 Agent Evaluation</a></p></div>
<div class="term" id="term-red-teaming">{{icon:warn}}<b>Red teaming <small>Red teaming</small></b><p>공격 시나리오를 적용해 Agent의 안전성을 평가하는 방식입니다.</p><p class="eg">위험도 high Agent는 프로덕션 승인 전에 포함해야 합니다(MUST) · <a href="12-observability-evaluation.md">Agent Observability와 Agent Evaluation</a></p></div>
<div class="term" id="term-idempotency">{{icon:check}}<b>멱등성 키 <small>Idempotency-Key</small></b><p>동일 요청의 재전송이 중복 실행되지 않도록 식별하는 키입니다.</p><p class="eg">동일 키·동일 요청은 저장된 결과 반환, 동일 키·다른 요청은 409 · <a href="07-hands-on.md">로컬 환경 구성 및 호출 실습</a></p></div>
<div class="term" id="term-trace">{{icon:trace}}<b>실행 추적 컨텍스트 <small>traceparent (W3C Trace Context)</small></b><p>요청에 부여되는 추적 정보입니다. Agent Platform APIs → Runtime → Agent Gateway(모델·도구 경로)까지 전파해 종단 간으로 추적합니다.</p><p class="eg">baggage에 개인정보나 토큰을 포함하지 않습니다 · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-observability">{{icon:eye}}<b>관측성 <small>Observability</small></b><p>시스템 상태와 동작을 외부에서 파악할 수 있는 능력입니다. 실행 추적, 지표, 로그를 포함합니다.</p><p class="eg">실행 추적은 관측성의 한 요소이며, 감사(audit)는 행위 기록 목적이 다릅니다 · <a href="03-one-request.md">Agent 요청 처리 흐름</a></p></div>
<div class="term" id="term-route-decision">{{icon:model}}<b>라우팅 결정 ID <small>routeDecisionId</small></b><p>Agent Gateway 모델 경로가 선택한 라우팅 결과를 기록하는 식별자입니다.</p><p class="eg">예: route-self-hosted · <a href="07-hands-on.md">로컬 환경 구성 및 호출 실습</a></p></div>
<div class="term" id="term-problem">{{icon:warn}}<b>Problem Details <small>RFC 9457</small></b><p>HTTP API 오류를 기계 판독 가능하게 표현하는 표준 형식입니다. Content-Type은 application/problem+json입니다.</p><p class="eg">필드: type, title, status, detail, code, traceId · <a href="07-hands-on.md">로컬 환경 구성 및 호출 실습</a></p></div>
<div class="term" id="term-durable">{{icon:clock}}<b>Durable 실행 <small>Durable execution</small></b><p>프로세스 재시작 이후에도 상태를 복구해 실행을 이어가는 방식입니다. 장시간 workflow에 사용합니다.</p><p class="eg">실행 엔진 제품은 TBD이며, 이 패키지는 계약만 제공합니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p></div>
<div class="term" id="term-hitl">{{icon:approve}}<b>HITL <small>Human-in-the-loop</small></b><p>위험도가 높은 작업 전에 사람의 승인을 받는 단계입니다. 승인은 요청 digest, 정책 버전, 승인자, 만료에 결합됩니다.</p><p class="eg">단순 approved=true 플래그는 신뢰하지 않습니다 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
<div class="term" id="term-unknown">{{icon:warn}}<b>결과 불명 상태 <small>unknown_outcome</small></b><p>timeout 이후 외부 쓰기의 성공 여부를 알 수 없는 상태입니다. 자동 재실행하지 않고 대사(reconciliation)로 확인합니다.</p><p class="eg">외부 효과의 exactly-once는 보장하지 않습니다 · <a href="04-trust.md">신뢰 경계와 Guardrails</a></p></div>
</div>

## Agent와 수명주기

<div class="term-group">
<div class="term" id="term-agent-card">{{icon:manifest}}<b>Agent Card <small>A2A Agent Card</small></b><p>A2A 프로토콜에서 Agent의 이름, 기능(skill), 접속 인터페이스, 인증 방식을 설명하는 메타데이터 문서입니다. 플랫폼에서는 Registry가 생성하고 서명합니다.</p><p class="eg">production-approved 버전에만 발행합니다 · <a href="13-agent-card.md">Agent Card와 Agent 간 통신</a></p></div>
<div class="term" id="term-a2a">{{icon:agents}}<b>A2A <small>Agent2Agent Protocol</small></b><p>Agent 간 발견과 통신을 위한 공개 프로토콜입니다. 이 플랫폼은 1.0.0 기준의 Agent Card로 발견을 통일하고, 호출은 공통 Agent 통신 계약을 사용합니다.</p><p class="eg">A2A 프로토콜 호출은 선택 사항입니다 · <a href="13-agent-card.md">Agent Card와 Agent 간 통신</a></p></div>
<div class="term" id="term-extended-card">{{icon:lock}}<b>확장 Agent Card <small>Extended Agent Card</small></b><p>인증된 클라이언트에게만 제공하는 상세 Agent Card입니다. capabilities.extendedAgentCard가 true일 때 GetExtendedAgentCard로 조회합니다.</p><p class="eg">인증 수준에 따라 다른 내용을 반환할 수 있습니다 · <a href="13-agent-card.md">Agent Card와 Agent 간 통신</a></p></div>
<div class="term" id="term-jws">{{icon:key}}<b>JWS · JCS <small>RFC 7515 · RFC 8785</small></b><p>JWS는 JSON 데이터 서명 형식, JCS는 서명 전 JSON 정규화 방식입니다. Agent Card는 signatures 필드를 제외하고 JCS로 정규화한 뒤 JWS로 서명합니다.</p><p class="eg">보호 헤더: alg, typ, kid, 선택 jku · <a href="13-agent-card.md">Agent Card와 Agent 간 통신</a></p></div>
<div class="term" id="term-manifest">{{icon:manifest}}<b>Manifest <small>Agent 선언 명세</small></b><p>플랫폼이 Agent를 통제·호출하는 데 필요한 메타데이터, 실행 설정, 권한 요구사항을 선언하는 JSON 문서입니다.</p><p class="eg">블록: metadata, source, runtime, capabilities, identity, governance, deployment, contracts · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p><p class="eg">피할 표현: &#x27;Agent의 신분증&#x27; 등 Identity·Credential과 혼동되는 표현</p></div>
<div class="term" id="term-rag">{{icon:knowledge}}<b>RAG <small>Retrieval-Augmented Generation</small></b><p>사내 문서를 검색해 근거와 함께 응답을 생성하는 방식이며, 플랫폼의 Agent 유형 중 하나입니다.</p><p class="eg">다른 유형: tool, workflow, multi-agent · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-immutable">{{icon:lock}}<b>불변 버전 <small>Immutable version</small></b><p>항상 동일한 코드와 산출물을 가리키는 버전 참조입니다. 커밋 해시와 artifact digest로 고정합니다.</p><p class="eg">main 등 브랜치 이름은 검증에 실패합니다 · <a href="05-agents-and-manifest.md">Agent Factory와 Manifest 명세</a></p></div>
<div class="term" id="term-local-first">{{icon:laptop}}<b>Local-First · CLI-First <small>Local-First / CLI-First</small></b><p>기존 IDE·Git·CLI로 개발하고 로컬에서 실험하는 개발 방식입니다. 중앙 소스 업로드를 강제하지 않습니다.</p><p class="eg">플랫폼은 계약 기반 SDK, CLI, 템플릿을 제공합니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p></div>
<div class="term" id="term-approved">{{icon:rocket}}<b>등록 / 프로덕션 승인 <small>Registered / Production-approved</small></b><p>등록은 Registry에 기록된 상태이며, 프로덕션 승인은 프로덕션 통제가 검증되어 업무 트래픽을 처리할 수 있는 상태입니다.</p><p class="eg">등록만으로는 프로덕션 트래픽을 처리하지 않습니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p><p class="eg">피할 표현: 등록을 배포나 실행 허가로 표현하는 것</p></div>
<div class="term" id="term-profile">{{icon:cloud}}<b>배포 프로파일 <small>Deployment profile</small></b><p>Agent의 실행 위치와 목적에 따른 구분입니다. local, shared-experiment, production 3가지입니다.</p><p class="eg">Manifest의 deployment.profile에 선언합니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p></div>
<div class="term" id="term-evidence">{{icon:test}}<b>승인 검증 근거 <small>Promotion evidence</small></b><p>프로덕션 승인에 필요한 검증 결과입니다. 불변 digest, 계약 적합성, 보안 검토 기록, 평가 결과, 롤백 검증 결과, 위험도별 승인을 포함합니다.</p><p class="eg">항목을 구체적으로 명시합니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p><p class="eg">피할 표현: &#x27;증거&#x27;만으로 뭉뚱그리는 표현</p></div>
<div class="term" id="term-contract-as-code">{{icon:test}}<b>Contract-as-Code <small>Contract-as-Code</small></b><p>기술 계약을 문서로만 두지 않고 테스트로 강제하는 방식입니다. CI 검사가 실패하면 승격을 차단합니다.</p><p class="eg">예: scripts/release.py · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p></div>
<div class="term" id="term-mock">{{icon:code}}<b>mock <small>Mock implementation</small></b><p>실제 시스템의 동작을 모사하는 구현입니다. 이 패키지의 Python mock은 loopback에서만 동작하며 합성 토큰만 허용합니다.</p><p class="eg">실제 IdP·모델·도구 서버에는 연결하지 않습니다 · <a href="07-hands-on.md">로컬 환경 구성 및 호출 실습</a></p></div>
</div>

## 표기 규칙

<div class="term-group">
<div class="term" id="term-must">{{icon:shield}}<b>규범 수준 <small>MUST / SHOULD / MAY</small></b><p>MUST는 필수, MUST NOT은 금지, SHOULD는 사유 문서화 시 예외 허용, MAY는 선택입니다.</p><p class="eg">MUST는 충족해야 할 요구사항이며, 특정 제품 선택을 의미하지 않습니다 · <a href="08-reading-the-spec.md">기술 표준 해석과 FAQ</a></p></div>
<div class="term" id="term-version">{{icon:code}}<b>계약 버전 <small>Contract version</small></b><p>패키지 버전(0.1.0), Manifest 계약 버전(agent.platform/v1alpha1), HTTP 경로 버전(/v1)은 독립적으로 관리됩니다.</p><p class="eg">v1alpha1은 운영 안정성을 보증하지 않습니다 · <a href="08-reading-the-spec.md">기술 표준 해석과 FAQ</a></p></div>
<div class="term" id="term-production">{{icon:cloud}}<b>프로덕션 <small>production</small></b><p>업무 트래픽을 처리하는 실행 환경입니다. 설명문에서는 &#x27;프로덕션 환경&#x27;, &#x27;프로덕션 승인&#x27;으로 표기합니다.</p><p class="eg">코드·상태값 production, production-approved는 원문을 유지합니다 · <a href="06-lifecycle.md">Agent 수명주기·Tuning과 프로덕션 승인</a></p><p class="eg">피할 표현: &#x27;운영&#x27;과 혼용하는 표현</p></div>
</div>

<nav class="pager"><a href="10-references.md"><small>이전</small><b>근거와 참고 자료</b></a><a class="next" href="01-why.md"><small>처음으로</small><b>플랫폼 도입 배경과 설계 원칙</b></a></nav>
