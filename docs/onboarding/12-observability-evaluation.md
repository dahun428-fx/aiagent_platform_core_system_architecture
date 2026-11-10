# Agent Observability와 Agent Evaluation

> 개발자 가이드 문서입니다. 규범은 [Observability](../observability.md), [Evaluation](../evaluation.md) 기술 표준 문서가 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [관측성](09-glossary.md#term-observability) [실행 추적 컨텍스트](09-glossary.md#term-trace) [OTel GenAI](09-glossary.md#term-otel-genai) [평가 3단계](09-glossary.md#term-evaluation) [Red teaming](09-glossary.md#term-red-teaming) [감사](09-glossary.md#term-audit)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- 관측성, 실행 추적, 감사의 목적 차이를 설명할 수 있습니다.
- OpenTelemetry GenAI 규격의 Agent span 이름과 필수 속성을 설명할 수 있습니다.
- 평가 3단계(배포 전 평가, 실행 추적 분석, 운영 모니터링)를 구분할 수 있습니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> Agent의 응답이 잘못되었을 때, 원인이 모델·도구·검색·정책 중 어디에 있는지 확인할 수 있어야 합니다.

<span class="tag">{{icon:eye}} 현황</span> Agent 한 번의 실행에는 여러 모델 호출과 도구 호출이 포함됩니다. 구성요소마다 다른 형식으로 기록하면 하나의 실행으로 연결되지 않고, 품질 변화도 비교할 수 없습니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> 실행 추적은 **공개 표준 형식(OpenTelemetry GenAI)**으로 통일하고, 평가는 **배포 전·실행 후·운영 중 3단계**로 나눠 승격 판단의 근거로 사용합니다.
</div>

## 관측성, 실행 추적, 감사

| 구분 | 목적 | 예 |
|---|---|---|
| 관측성(Observability) | 시스템 동작 이해, 장애 분석 | 지연 시간, 오류율, 토큰 사용량 |
| 실행 추적(trace) | 요청 하나의 처리 경로 추적 | Agent 호출 → 모델 추론 → 도구 호출 span |
| 감사(audit) | 행위의 증적 보존 | 누가 어떤 정책 결정으로 어떤 도구를 호출했는지 |

## 실행 추적 규격

<ol class="flow">
<li data-say="요청이 들어오면 Agent Platform APIs가 추적 번호(traceparent)를 받거나 새로 만듭니다.">{{icon:gateway}}<b>Agent Platform APIs</b><span>traceparent 수신·생성</span></li>
<li data-say="Agent 호출 전체를 하나의 구간(span)으로 기록합니다.">{{icon:agent}}<b>invoke_agent</b><span>Agent 호출 span</span></li>
<li data-say="모델을 부를 때마다 어떤 모델로 무엇을 했는지 구간으로 기록합니다.">{{icon:model}}<b>모델 추론 span</b><span>operation + model</span></li>
<li data-say="도구를 부를 때마다 구간으로 기록합니다.">{{icon:tools}}<b>도구 호출 span</b><span>도구 경로</span></li>
<li data-say="하위 Agent를 부르면 같은 추적 번호를 넘겨 줍니다. 그래서 여러 Agent를 거친 요청도 하나의 이야기로 이어서 볼 수 있습니다.">{{icon:agents}}<b>하위 Agent</b><span>traceparent 전파</span></li>
</ol>

<div class="sim" data-sim="trace"></div>

- W3C Trace Context(`traceparent`, `tracestate`)를 모든 구간에 전파합니다(MUST).
- span 이름과 속성은 OpenTelemetry GenAI semantic conventions를 따릅니다(MUST).

| span | 이름 | 주요 속성 |
|---|---|---|
| Agent 호출 | `invoke_agent {gen_ai.agent.name}` | `gen_ai.agent.name`, `gen_ai.operation.name` |
| Agent 생성 | `create_agent` | `gen_ai.agent.name` |
| 모델 추론 | `{gen_ai.operation.name} {gen_ai.request.model}` | `gen_ai.provider.name`(필수), `gen_ai.request.model`, 토큰 사용량 |
| 플랫폼 고유 (SHOULD) | — | `platform.` 접두사: tenant 별칭, 정책 결정 ID, routeDecisionId, Guardrail 검사 ID |

<div class="point" markdown="1">
**{{icon:warn}} 규격 버전 고정** OpenTelemetry GenAI semantic conventions는 Development 단계 규격입니다. 플랫폼은 사용하는 규격 버전을 고정하고 기록하며(MUST), 버전 전환은 계약 변경 절차를 따릅니다.
</div>

<div class="compare" markdown="1">
<div class="good" markdown="1">
**{{icon:check}} 기록 대상**

지연 시간, 오류, 모델 호출 수, 입력·출력 토큰, tenant·Agent별 비용 귀속, 도구 실패, 정책 거부, Guardrail 차단, 승인 대기
</div>
<div class="bad" markdown="1">
**{{icon:cross}} 기본 기록 제외 대상**

프롬프트 원문, 모델 출력 원문, 토큰, 검색된 개인정보 원문. baggage에도 개인정보와 토큰을 넣지 않습니다
</div>
</div>

## 평가 3단계

<ol class="flow">
<li data-say="배포하기 전에 정해 둔 평가 데이터로 기준을 넘는지 확인합니다.">{{icon:test}}<b>배포 전 평가</b><span>CI·승격 전<br>평가 데이터셋으로 기준 충족 확인</span></li>
<li data-say="실행이 끝난 뒤 기록을 보며 어디서 왜 실패했는지 분석합니다.">{{icon:trace}}<b>실행 추적 분석</b><span>실행 후<br>처리 경로와 실패 원인 분석</span></li>
<li data-say="운영 중에는 품질 추세를 지켜보다가 나빠지는 순간을 잡아냅니다.">{{icon:eye}}<b>운영 모니터링</b><span>프로덕션 운영 중<br>추세와 회귀 감지</span></li>
<li data-say="평가 결과를 근거로 Agent를 개선하고, 새 버전은 다시 배포 전 평가를 거칩니다." class="hi">{{icon:rocket}}<b>Agent Tuning</b><span>평가 결과를 근거로 개선<br>새 버전은 다시 배포 전 평가</span></li>
</ol>

<div class="cards">
<div class="card">{{icon:target}}<b>품질</b><p>과제 완료, 응답 정확성, 근거성(RAG), 도구 사용 정확성</p></div>
<div class="card">{{icon:shield}}<b>안전성</b><p>프롬프트 인젝션 저항, 민감정보 노출, 유해 콘텐츠, 권한 외 도구 호출 시도. 공격 시나리오 기반 평가(red teaming)를 포함합니다</p></div>
<div class="card">{{icon:clock}}<b>운영</b><p>지연 시간, 비용, 오류율</p></div>
</div>

- 위험도 high Agent는 프로덕션 승인 전에 red teaming을 포함해야 합니다(MUST).
- 평가 결과는 `evaluation.schema.json`을 따르며 datasetVersion, agentVersion, manifestDigest, policyVersion, metric, gate, traceId를 포함합니다(MUST).
- 이 패키지의 deterministic fixture는 smoke regression이며, 업무 품질·안전성·통계적 유의성을 입증하지 않습니다.

## 제공 범위

v0.1은 trace context 전파, mock 감사 기록, 평가 결과 스키마와 smoke 평가 테스트를 제공합니다. OpenTelemetry exporter, 관측 백엔드, 평가 데이터셋과 기준 수치는 회사 결정(TBD)입니다.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. Agent 호출 span의 이름 규칙은 무엇입니까?</summary>
<code>invoke_agent {gen_ai.agent.name}</code>입니다.
</details>

<details markdown="1"><summary>Q2. 운영 모니터링에서 품질 저하가 감지되면 어떤 흐름으로 개선합니까?</summary>
평가 결과와 실행 추적을 근거로 Agent Tuning에서 개선안을 만들고, 새 불변 버전으로 배포 전 평가를 다시 통과한 뒤 승인 절차를 따릅니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- 관측성은 동작 이해, 실행 추적은 요청 경로 추적, 감사는 행위 증적을 목적으로 합니다.
- 실행 추적은 W3C Trace Context와 OpenTelemetry GenAI 규격(버전 고정)을 따릅니다.
- 평가는 배포 전 평가, 실행 추적 분석, 운영 모니터링의 3단계로 수행하며 Tuning의 입력이 됩니다.
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- span 규격: [OpenTelemetry GenAI](10-references.md#ref-otel)
- 평가 3단계와 red teaming: [클라우드 Agent 플랫폼](10-references.md#ref-industry)
</div>

<nav class="pager"><a href="04-trust.md"><small>이전</small><b>신뢰 경계와 Guardrails</b></a><a class="next" href="13-agent-card.md"><small>다음</small><b>Agent Card와 Agent 간 통신</b></a></nav>
