# Agent 요청 처리 흐름

> 개발자 가이드 문서입니다. 규범은 [아키텍처](../architecture.md), [Agent Tools](../agent-tools.md), [Agent Identity](../identity-and-credentials.md) 기술 표준 문서가 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [멱등성 키](09-glossary.md#term-idempotency) [identity context](09-glossary.md#term-identity-context) [Lease](09-glossary.md#term-lease) [routeDecisionId](09-glossary.md#term-route-decision) [traceparent](09-glossary.md#term-trace) [Problem Details](09-glossary.md#term-problem)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- Agent 호출 요청의 5단계 처리 흐름을 설명할 수 있습니다.
- 단계별 검증 대상과 신뢰하지 않는 입력을 구분할 수 있습니다.
- 도구 호출 시 자격증명이 Runtime과 LLM에 노출되지 않는 구조를 설명할 수 있습니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> 사용자가 "청구서 INV-2048 요약"을 요청했을 때, 응답 생성까지 어떤 구성요소가 어떤 검증을 수행하는지 정의해야 합니다.

<span class="tag">{{icon:eye}} 현황</span> 예시 Agent는 사내 ERP에서 청구서를 조회(도구 호출)하고 모델로 요약합니다. 데이터 분류는 `confidential`입니다. 하나의 요청에 인증·인가, 도구 권한, 데이터 반출 통제가 모두 관여합니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> 각 Gateway가 **자신의 경계에서 하나의 책임**을 수행합니다. 한 지점의 통제가 실패해도 다른 지점에서 차단할 수 있습니다.
</div>

## 처리 단계

<ol class="flow">
<li>{{icon:gateway}}<b>1. 진입</b><span>Agent Gateway<br>인증 · 해석 · 인가 · 멱등성</span></li>
<li>{{icon:runtime}}<b>2. 실행</b><span>Agent Runtime<br>adapter 기반 Agent 실행</span></li>
<li>{{icon:tools}}<b>3. 도구 호출</b><span>Tool Gateway + Broker<br>단기 자격증명</span></li>
<li>{{icon:model}}<b>4. 모델 호출</b><span>Model Gateway<br>분류 기반 라우팅</span></li>
<li>{{icon:trace}}<b>5. 기록</b><span>Observability<br>종단 간 실행 추적</span></li>
</ol>

## 1단계. Agent Gateway 진입

클라이언트는 Agent Gateway에 HTTP 요청을 전송합니다.

```text
POST /v1/agents/{agentId}/invocations
Authorization: Bearer <회사 IdP가 발급한 access token>
traceparent: 00-<trace-id>-<span-id>-01
Idempotency-Key: <재전송 요청을 식별하는 키>
```

```json
{
  "input": {"type": "message", "content": "청구서 INV-2048 요약해 줘"},
  "context": {"tenantId": "finance", "dataClassification": "confidential"},
  "execution": {"mode": "sync", "timeoutMs": 30000}
}
```

<div class="cards">
<div class="card">{{icon:lock}}<b>인증</b><p>access token의 발급자, 대상(audience), 서명, 만료를 검증합니다.</p></div>
<div class="card">{{icon:manifest}}<b>Agent 해석</b><p>Registry에서 Git revision과 artifact digest로 고정된 불변 버전을 조회합니다.</p></div>
<div class="card">{{icon:user}}<b>테넌트 인가</b><p>호출 주체가 해당 테넌트의 Agent를 호출할 권한이 있는지 판단합니다.</p></div>
<div class="card">{{icon:check}}<b>멱등성 처리</b><p>동일 키에 다른 요청이 오면 거부하고, 동일 요청이면 저장된 결과를 반환합니다.</p></div>
</div>

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 신뢰하지 않는 값**

요청 본문의 `tenantId`, `"role": "admin"` 등. 요청 본문의 값으로는 권한이 부여되지 않습니다.
</div>
<div class="good" markdown="1">
**{{icon:check}} 신뢰하는 값**

검증된 토큰에서 도출한 Identity와 테넌트. 요청 본문의 값은 토큰 값과의 **비교에만** 사용합니다.
</div>
</div>

## 2단계. Agent Runtime 실행

Agent Gateway는 Agent 버전, **검증된 실행 주체 식별 정보(identity context)**, **정책 컨텍스트(policy context)**를 Runtime에 전달합니다.

Runtime은 Manifest에 선언된 framework adapter로 Agent를 실행합니다. LangGraph 기반 Agent와 자체 구현 Agent는 Runtime에 동일한 계약으로 노출되므로, 프레임워크를 교체해도 플랫폼 측 변경은 필요하지 않습니다.

<div class="point" markdown="1">
**{{icon:bulb}} 핵심 포인트** Runtime은 보안·정책 권한을 임의로 변경할 수 없습니다(MUST NOT). 전달받은 권한 범위 안에서만 동작합니다.
</div>

## 3단계. Tool Gateway를 통한 도구 호출

Agent가 ERP에서 청구서를 조회하는 단계입니다. 각 구간이 보유하는 정보를 확인하십시오.

<ol class="flow">
<li>{{icon:runtime}}<b>Runtime</b><span>도구 ID · 버전 · 인자<br><strong>자격증명 없음</strong></span></li>
<li>{{icon:gateway}}<b>Tool Gateway</b><span>승인된 endpoint 해석<br>입력 스키마 · 정책 · 승인</span></li>
<li class="hi">{{icon:key}}<b>Credential Broker</b><span>정책 근거 재검증 후<br>호출에 결합된 lease</span></li>
<li>{{icon:tools}}<b>Tool adapter</b><span>신뢰 경계 내부에서<br>lease를 자격증명으로 교환</span></li>
<li>{{icon:server}}<b>ERP</b><span>출력 스키마·분류 검증 후<br>Runtime에 반환</span></li>
</ol>

1. Runtime은 Tool Gateway에 **도구 ID, 버전, 인자**만 전달합니다. URL이나 토큰은 전달할 수 없습니다.
2. Tool Gateway는 Tool Registry에서 **승인된 endpoint**를 해석하고 입력 스키마와 정책을 검증합니다. 쓰기(write) 작업은 유효한 승인 여부도 확인합니다.
3. Credential Broker에 요청하는 범위는 **사용자 권한 ∩ Agent 권한 ∩ 도구 허용 범위 ∩ 정책**을 초과할 수 없습니다.
4. Credential Broker는 토큰 원문 대신 **단기·호출 결합형 불투명 lease**를 발급합니다.
5. 결과는 출력 스키마와 데이터 분류 검증, 감사 기록, 민감 정보 제거를 거쳐 반환됩니다. 결과에는 토큰과 lease가 포함되지 않습니다.

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 허용하지 않는 구조**

```text
Runtime → 저장된 API 키 조회 → LLM·도구 코드 → ERP
```

LLM이 자격증명에 접근하면 프롬프트 인젝션으로 유출될 수 있습니다.
</div>
<div class="good" markdown="1">
**{{icon:check}} 표준 구조**

```text
Runtime → Tool Gateway → Credential Broker
→ 단기 lease → adapter → ERP
```

LLM은 자격증명에 접근하지 않으므로 유출 경로가 없습니다.
</div>
</div>

시퀀스 도식입니다.

![Tool 호출과 Credential 발급 순서](../../diagrams/tool-credential.svg)

## 4단계. Model Gateway를 통한 모델 호출

Agent는 특정 공급사의 모델을 직접 호출하지 않고, Model Gateway에 **논리 모델 이름**과 **정책 컨텍스트**를 전달합니다.

<div class="lanes">
<div class="lane"><div>{{icon:shield}} <code>public</code> · <code>internal</code></div><i>&#8594;</i><div class="gate">{{icon:model}}<span>Model Gateway<small>정책 허용 시</small></span></div><i>&#8594;</i><div>{{icon:cloud}} 외부 또는 자체 호스팅 모델</div></div>
<div class="lane"><div>{{icon:lock}} <code>confidential</code> · <code>restricted</code></div><i>&#8594;</i><div class="gate">{{icon:model}}<span>Model Gateway<small>외부 경로 거부</small></span></div><i>&#8594;</i><div>{{icon:server}} 자체 호스팅 모델</div></div>
<div class="lane"><div>{{icon:warn}} 허용 경로 없음</div><i>&#8594;</i><div class="gate">{{icon:model}}<span>Model Gateway<small>우회 없음</small></span></div><i>&#8594;</i><div>{{icon:cross}} 요청 실패</div></div>
</div>

예시 데이터는 `confidential`이므로 자체 호스팅 모델로 라우팅됩니다. 응답에는 라우팅 결정을 기록한 `routeDecisionId`가 포함됩니다.

![모델 routing 순서](../../diagrams/model-routing.svg)

## 5단계. 실행 추적과 응답

요청의 `traceparent`는 Agent Gateway → Runtime → Tool Gateway → Model Gateway의 모든 구간에 전파됩니다. 이를 통해 요청 하나의 처리 경로를 종단 간으로 추적할 수 있습니다.

<div class="compare" markdown="1">
<div class="good" markdown="1">
**{{icon:check}} 기록 대상**

테넌트 별칭, 호출 ID, adapter, 정책 결정, 오류 분류
</div>
<div class="bad" markdown="1">
**{{icon:cross}} 기록 제외 대상**

프롬프트 원문, 토큰, 검색된 개인정보 원문
</div>
</div>

다음은 이 패키지의 로컬 mock을 실행한 실제 응답입니다.

```json
{
  "invocationId": "inv-79b4fa3420244ae4bccb3b4a3473dea6",
  "agentVersion": "0.1.0",
  "status": "succeeded",
  "output": {"type": "message", "content": "mock:hello"},
  "traceparent": "00-1b0f13dcfd2f426a87937b2bb6d7f852-ac2cb29d6d8f4c46-01",
  "routeDecisionId": "route-self-hosted",
  "usage": {"inputTokens": 1, "outputTokens": 1}
}
```

오류는 RFC 9457 Problem Details(`application/problem+json`) 형식으로 반환됩니다.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. 요청 본문에 다른 팀의 tenantId를 지정하면 해당 팀 데이터에 접근할 수 있습니까?</summary>
접근할 수 없습니다. 테넌트는 검증된 토큰에서 도출하며, 요청 본문의 값은 비교에만 사용합니다. 두 값이 다르면 요청을 거부합니다.
</details>

<details markdown="1"><summary>Q2. Runtime이 Tool Gateway에 전달하는 정보는 무엇입니까?</summary>
도구 ID, 버전, 인자입니다. URL과 토큰은 전달하지 않으며, endpoint와 자격증명은 Tool Gateway와 Credential Broker가 결정합니다.
</details>

<details markdown="1"><summary>Q3. confidential 데이터 요청 시 자체 호스팅 모델을 사용할 수 없으면 어떻게 처리됩니까?</summary>
요청이 실패합니다. 허용된 경로가 없을 때 외부 모델로 우회하지 않습니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- 진입 → 실행 → 도구 호출 → 모델 호출 → 기록의 각 단계에서 담당 구성요소가 하나의 책임을 수행합니다.
- Identity는 토큰에서만 도출하며, 자격증명은 Runtime과 LLM에 노출하지 않습니다.
- 데이터 분류가 모델 경로를 결정하며, 허용 경로가 없으면 요청이 실패합니다.
</div>

<nav class="pager"><a href="02-big-picture.md"><small>이전</small><b>플랫폼 아키텍처와 주요 구성요소</b></a><a class="next" href="04-trust.md"><small>다음</small><b>신뢰 경계와 보안 통제</b></a></nav>
