# 핵심 용어 사전

> 온보딩 안내서에 나오는 용어를 한곳에 모았습니다. 규범적 정의는 [용어와 규범](../glossary.md)이 기준입니다.

<div class="goals" markdown="1">
**{{icon:book}} 이 사전을 쓰는 법**

- 각 페이지 위의 **핵심 용어** 칩을 누르면 이 사전의 해당 항목으로 옵니다.
- 항목마다 한 줄 정의, 예시나 주의점, 자세히 설명하는 페이지가 있습니다.
- 위에서부터 읽으면 기본 개념 → 구조 → 호출 경계 → 신원과 보안 → 실행 → 수명주기 순서입니다.
</div>

## 기본 개념

<div class="term-group">
<div class="term" id="term-agent">{{icon:agent}}<b>AI Agent <small>에이전트</small></b><p>모델을 이용해 스스로 판단하고, 도구와 지식을 써서 일을 처리하는 프로그램입니다.</p><p class="eg">예: 청구서를 조회해 요약하는 재무 Agent · <a href="01-why.md">왜 필요한가</a></p></div>
<div class="term" id="term-boundary">{{icon:shield}}<b>공통 경계 · 신뢰 경계 <small>boundary</small></b><p>누구를, 무엇을 믿을지 바뀌는 지점입니다. 플랫폼은 이 경계마다 검사를 둡니다.</p><p class="eg">예: 앱 → Agent Gateway, Runtime → Tool Gateway · <a href="04-trust.md">신뢰 경계</a></p></div>
<div class="term" id="term-contract">{{icon:code}}<b>계약 <small>contract</small></b><p>구성요소끼리 주고받는 형식과 규칙을 기계가 읽을 수 있게 정의한 것입니다. OpenAPI와 JSON Schema로 씁니다.</p><p class="eg">예: agent-manifest.schema.json, agent-gateway.openapi.json · <a href="08-reading-the-spec.md">규격 읽는 법</a></p></div>
<div class="term" id="term-tbd">{{icon:question}}<b>TBD <small>미정</small></b><p>회사 환경에 맞춰 정해야 하는 제품이나 수치입니다. 예제 값을 기본값으로 쓰면 안 됩니다.</p><p class="eg">예: IdP 제품, SLO 수치, 자격증명 TTL · <a href="08-reading-the-spec.md">규격 읽는 법</a></p></div>
<div class="term" id="term-tenant">{{icon:lock}}<b>Tenant <small>테넌트</small></b><p>데이터와 권한이 분리되는 단위입니다. 기본은 논리 격리이고, 위험도에 따라 물리 분리도 합니다.</p><p class="eg">예: 재무 사업부, 인사 사업부 · <a href="04-trust.md">신뢰 경계</a></p></div>
</div>

## 구조

<div class="term-group">
<div class="term" id="term-control-plane">{{icon:control}}<b>Shared Control Plane <small>공통 제어 평면</small></b><p>회사 전체가 함께 쓰는 통제 영역입니다. Registry, Policy, Identity 중개, Evaluation, Observability, Promotion을 맡습니다.</p><p class="eg">비유: 관제탑. 비행기를 조종하지 않고 허가와 기록을 맡습니다 · <a href="02-big-picture.md">전체 구조</a></p></div>
<div class="term" id="term-execution-plane">{{icon:runtime}}<b>Distributed Execution Plane <small>분산 실행 평면</small></b><p>Agent가 실제로 실행되는 여러 환경입니다. 개발자 PC, 사내 서버, 클라우드가 같은 계약을 따릅니다.</p><p class="eg">등록된 환경이라도 production 승인과는 별개입니다 · <a href="02-big-picture.md">전체 구조</a></p></div>
<div class="term" id="term-runtime">{{icon:runtime}}<b>Agent Runtime <small>런타임</small></b><p>Agent를 실행하는 곳입니다. framework adapter로 Agent를 부르고, 모델·도구·지식·상태·정책 서비스를 소비합니다.</p><p class="eg">보안·정책 권한을 스스로 바꿀 수 없습니다(MUST NOT) · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-adapter">{{icon:tools}}<b>Framework adapter <small>어댑터</small></b><p>LangGraph 같은 각 프레임워크를 공통 Runtime 계약에 연결하는 변환 계층입니다.</p><p class="eg">Manifest의 runtime.framework, runtime.adapter에 적습니다 · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
<div class="term" id="term-registry">{{icon:manifest}}<b>Registry <small>등록소</small></b><p>Agent·Tool·Model·Environment를 등록하는 곳입니다. 소스가 아니라 불변 revision, digest, Manifest, 평가 증거를 저장합니다.</p><p class="eg">상태: registered, eligible, production-approved, quarantined · <a href="06-lifecycle.md">production까지</a></p></div>
<div class="term" id="term-knowledge">{{icon:knowledge}}<b>Knowledge(RAG) Backend <small>지식 저장소</small></b><p>RAG Agent가 검색하는 저장소입니다. 공통 RAG 계약만 지키면 바꿔 낄 수 있습니다.</p><p class="eg">검색 시점에 ACL과 데이터 분류로 먼저 거릅니다 · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
</div>

## 호출 경계

<div class="term-group">
<div class="term" id="term-agent-gateway">{{icon:gateway}}<b>Agent Gateway <small>들어오는 관문</small></b><p>앱이 Agent를 부를 때 들어오는 정문입니다. 인증, Agent 찾기, 테넌트 권한 확인, 중복 요청 방지를 맡습니다.</p><p class="eg">POST /v1/agents/{agentId}/invocations · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-model-gateway">{{icon:model}}<b>Model Gateway <small>모델 관문</small></b><p>논리 모델 이름을 받아 데이터 분류·지역·비용·가용성 정책에 맞는 실제 endpoint로 보냅니다.</p><p class="eg">confidential·restricted 데이터는 외부 경로를 거부합니다 · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-tool-gateway">{{icon:tools}}<b>Tool Gateway <small>도구 관문</small></b><p>Agent Tools에 속한 관문입니다. 도구 ID를 승인된 endpoint로 바꾸고 입출력과 정책을 검사합니다.</p><p class="eg">호출자가 URL·헤더·토큰 endpoint를 지정할 수 없습니다 · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-agent-tools">{{icon:tools}}<b>Agent Tools <small>도구 영역</small></b><p>Tool Registry, Tool Gateway, REST/OpenAPI/MCP adapter, 도구 정책과 감사를 포함하는 논리 영역입니다.</p><p class="eg">Tool Gateway는 이 영역에 속합니다 · <a href="02-big-picture.md">전체 구조</a></p></div>
<div class="term" id="term-mcp">{{icon:tools}}<b>MCP <small>Model Context Protocol</small></b><p>Agent가 도구를 쓰기 위한 프로토콜입니다. 이 플랫폼에서는 Tool Gateway의 adapter가 MCP client를 소유합니다.</p><p class="eg">MCP는 도구 프로토콜일 뿐 회사 권한 정책을 대신하지 않습니다 · <a href="08-reading-the-spec.md">자주 묻는 질문</a></p></div>
</div>

## 신원과 보안

<div class="term-group">
<div class="term" id="term-agent-identity">{{icon:identity}}<b>Agent Identity <small>신원 영역</small></b><p>사용자 신원, Agent(workload) 신원, 위임 관계, 자격증명 중개를 다루는 논리 영역입니다.</p><p class="eg">Credential Broker는 이 영역에 속합니다 · <a href="02-big-picture.md">전체 구조</a></p></div>
<div class="term" id="term-credential-broker">{{icon:key}}<b>Credential Broker <small>자격증명 중개</small></b><p>도구 호출에 필요한 짧게 살고 범위가 좁은 자격증명을 발급하는 고신뢰 서비스입니다.</p><p class="eg">Runtime과 LLM은 자격증명을 볼 수 없습니다 · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-lease">{{icon:key}}<b>Lease <small>임대 자격증명</small></b><p>Broker가 주는 불투명한 교환권입니다. 특정 테넌트·workload·도구·호출에 묶이고, adapter 안에서만 실제 자격증명으로 바뀝니다.</p><p class="eg">응답 필드: credentialRef, audience, scopes, expiresAt, nonExportable=true · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-identity-context">{{icon:identity}}<b>identity context <small>신원 정보</small></b><p>Gateway가 검증된 토큰에서 만들어 Runtime에 넘기는 신원 정보입니다. 요청 본문이 아니라 토큰이 근거입니다.</p><p class="eg">body의 tenantId는 비교용일 뿐 권한의 근거가 아닙니다 · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-delegated">{{icon:user}}<b>Delegated / Independent <small>위임 / 독립</small></b><p>Delegated는 사용자를 대신해 일하는 모드, Independent는 Agent 자신의 권한으로만 일하는 모드입니다.</p><p class="eg">Manifest의 identity.mode에 적습니다 · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
<div class="term" id="term-scope">{{icon:shield}}<b>권한 교집합 <small>scope intersection</small></b><p>유효 권한은 사용자 권한 ∩ Agent 권한 ∩ 도구 허용 범위 ∩ 정책입니다. 위임할수록 줄어들기만 합니다.</p><p class="eg">하위 Agent 호출 때마다 범위를 좁히고 다시 검증합니다 · <a href="04-trust.md">신뢰 경계</a></p></div>
<div class="term" id="term-injection">{{icon:warn}}<b>프롬프트 인젝션 <small>prompt injection</small></b><p>검색 결과나 도구 출력에 숨긴 지시문으로 Agent의 행동을 바꾸려는 공격입니다.</p><p class="eg">그래서 검색·도구·모델 결과는 비신뢰 데이터로 다룹니다 · <a href="04-trust.md">신뢰 경계</a></p></div>
<div class="term" id="term-fail-closed">{{icon:lock}}<b>fail closed <small>실패 시 닫힘</small></b><p>확인할 수 없으면 거부하는 원칙입니다. IdP·Broker·정책 조회가 실패하면 새 자격증명을 발급하지 않습니다.</p><p class="eg">반대말: fail open (확인할 수 없으면 허용) · <a href="04-trust.md">신뢰 경계</a></p></div>
<div class="term" id="term-classification">{{icon:shield}}<b>데이터 분류 <small>classification</small></b><p>데이터의 민감도 등급입니다. public, internal, confidential, restricted 네 가지가 있습니다.</p><p class="eg">분류가 모델 경로와 접근 권한을 정합니다 · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
</div>

## 요청과 실행

<div class="term-group">
<div class="term" id="term-idempotency">{{icon:check}}<b>Idempotency-Key <small>중복 방지 키</small></b><p>같은 요청을 다시 보냈을 때 두 번 실행되지 않게 하는 키입니다.</p><p class="eg">같은 키·같은 요청은 저장된 결과, 같은 키·다른 요청은 409 · <a href="07-hands-on.md">30분 실습</a></p></div>
<div class="term" id="term-trace">{{icon:trace}}<b>traceparent <small>W3C Trace Context</small></b><p>요청 하나에 붙는 추적 정보입니다. Gateway → Runtime → 모델·도구까지 그대로 전달해 한 줄로 추적합니다.</p><p class="eg">baggage에 개인정보나 토큰을 넣지 않습니다 · <a href="03-one-request.md">요청 하나 따라가기</a></p></div>
<div class="term" id="term-route-decision">{{icon:model}}<b>routeDecisionId <small>경로 결정 ID</small></b><p>Model Gateway가 어떤 경로로 모델을 불렀는지 기록하는 ID입니다.</p><p class="eg">예: route-self-hosted · <a href="07-hands-on.md">30분 실습</a></p></div>
<div class="term" id="term-problem">{{icon:warn}}<b>Problem Details <small>RFC 9457</small></b><p>HTTP API 오류를 기계가 읽을 수 있게 표현하는 표준 형식입니다. Content-Type은 application/problem+json입니다.</p><p class="eg">필드: type, title, status, detail, code, traceId · <a href="07-hands-on.md">30분 실습</a></p></div>
<div class="term" id="term-durable">{{icon:clock}}<b>Durable 실행 <small>지속 실행</small></b><p>프로세스가 재시작돼도 상태를 이어서 실행할 수 있는 방식입니다. 오래 걸리는 workflow에 씁니다.</p><p class="eg">엔진 제품은 TBD, 이 패키지에는 계약만 있습니다 · <a href="06-lifecycle.md">production까지</a></p></div>
<div class="term" id="term-hitl">{{icon:approve}}<b>HITL <small>Human-in-the-loop</small></b><p>위험한 작업 전에 사람의 승인을 받는 단계입니다. 승인은 요청 digest, 정책 버전, 승인자, 만료에 묶입니다.</p><p class="eg">단순 approved=true는 믿지 않습니다 · <a href="04-trust.md">신뢰 경계</a></p></div>
<div class="term" id="term-unknown">{{icon:warn}}<b>unknown_outcome <small>결과 불명</small></b><p>timeout 뒤 외부 쓰기가 성공했는지 알 수 없는 상태입니다. 자동으로 다시 실행하지 않고 대사로 확인합니다.</p><p class="eg">외부 효과의 exactly-once는 보장하지 않습니다 · <a href="04-trust.md">신뢰 경계</a></p></div>
</div>

## Agent와 수명주기

<div class="term-group">
<div class="term" id="term-manifest">{{icon:manifest}}<b>Manifest <small>Agent 신분증</small></b><p>플랫폼이 Agent를 통제하고 호출하는 데 필요한 정보만 적은 JSON입니다.</p><p class="eg">블록: metadata, source, runtime, capabilities, identity, governance, deployment, contracts · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
<div class="term" id="term-rag">{{icon:knowledge}}<b>RAG <small>검색 증강 생성</small></b><p>사내 문서를 검색해 근거를 붙여 답하는 방식입니다. 네 종류 Agent 중 하나입니다.</p><p class="eg">나머지: tool, workflow, multi-agent · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
<div class="term" id="term-immutable">{{icon:lock}}<b>불변 버전 <small>immutable version</small></b><p>언제 봐도 같은 코드를 가리키는 버전입니다. 커밋 해시와 artifact digest로 고정합니다.</p><p class="eg">main 같은 브랜치 이름은 거부됩니다 · <a href="05-agents-and-manifest.md">Agent와 Manifest</a></p></div>
<div class="term" id="term-local-first">{{icon:laptop}}<b>Local-First · CLI-First <small>로컬 우선</small></b><p>지금 쓰는 IDE·Git·CLI로 개발하고 로컬에서 실험하는 방식입니다. 중앙 소스 업로드를 강제하지 않습니다.</p><p class="eg">플랫폼은 계약 기반 SDK, CLI, 템플릿을 제공합니다 · <a href="06-lifecycle.md">production까지</a></p></div>
<div class="term" id="term-approved">{{icon:rocket}}<b>Registered / Production-approved <small>등록 / 운영 승인</small></b><p>Registered는 Registry에 등록된 상태, Production-approved는 production 통제가 검증되어 업무 트래픽을 받아도 되는 상태입니다.</p><p class="eg">등록만으로는 production 트래픽을 받지 않습니다 · <a href="06-lifecycle.md">production까지</a></p></div>
<div class="term" id="term-profile">{{icon:cloud}}<b>배포 프로파일 <small>deployment profile</small></b><p>Agent를 어디서 무엇을 위해 실행하는지 나눈 구분입니다. local, shared-experiment, production 세 가지입니다.</p><p class="eg">Manifest의 deployment.profile에 적습니다 · <a href="06-lifecycle.md">production까지</a></p></div>
<div class="term" id="term-contract-as-code">{{icon:test}}<b>Contract-as-Code <small>코드로 검증하는 계약</small></b><p>계약을 문서로만 두지 않고 테스트로 강제하는 방식입니다. CI에서 하나라도 실패하면 승격을 막습니다.</p><p class="eg">예: scripts/release.py · <a href="06-lifecycle.md">production까지</a></p></div>
<div class="term" id="term-mock">{{icon:code}}<b>mock <small>모의 구현</small></b><p>실제 시스템 대신 동작을 흉내 내는 구현입니다. 이 패키지의 Python mock은 로컬에서만 돌고 합성 토큰만 받습니다.</p><p class="eg">실제 IdP·모델·도구 서버에는 연결하지 않습니다 · <a href="07-hands-on.md">30분 실습</a></p></div>
</div>

## 규격 표시

<div class="term-group">
<div class="term" id="term-must">{{icon:shield}}<b>MUST / SHOULD / MAY <small>규범 수준</small></b><p>MUST는 필수, MUST NOT은 금지, SHOULD는 사유를 문서화하면 예외 가능, MAY는 선택입니다.</p><p class="eg">MUST는 지켜야 할 성질이지 특정 제품 선택이 아닙니다 · <a href="08-reading-the-spec.md">규격 읽는 법</a></p></div>
<div class="term" id="term-version">{{icon:code}}<b>계약 버전 <small>version</small></b><p>패키지 버전(0.1.0), Manifest 계약 버전(agent.platform/v1alpha1), HTTP 경로 버전(/v1)은 따로 움직입니다.</p><p class="eg">v1alpha1은 운영 안정성 보증이 아닙니다 · <a href="08-reading-the-spec.md">규격 읽는 법</a></p></div>
</div>

<nav class="pager"><a href="08-reading-the-spec.md"><small>이전</small><b>규격 읽는 법과 자주 묻는 질문</b></a><a class="next" href="01-why.md"><small>처음으로</small><b>왜 이 플랫폼이 필요한가</b></a></nav>
