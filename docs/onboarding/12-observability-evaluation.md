# Agent Observability

> 개발자 가이드 문서입니다. 규범은 [관측성](../observability.md) 기술 표준 문서가 기준입니다.

{{journey:8}}

<div class="sofar" markdown="1">
**지금까지** `invoice-summary`는 번호로 묻는 요청 A를 잘 처리했고, 숨은 지시문이 든 요청 D도 Guardrail이 막았습니다. 며칠 뒤 서연이 번호 대신 "한빛상사 10월 청구서 요약해 줘"라고 물었습니다(요청 B).
</div>

## 장면

서연이 민준에게 알립니다. "한빛상사 10월 금액이 틀려요. 9,800,000원이라는데 실제는 12,400,000원이에요." 민준이 가진 단서는 서연의 화면에 찍힌 호출 번호 하나입니다. 그 번호로 추적 기록을 열어 보니 구간 네 개가 모두 성공이고 유난히 느린 곳도 없습니다. 오류는 없는데 답은 틀렸습니다. 이 장에서는 이 기록으로 어디까지 알 수 있고 어디부터는 알 수 없는지를 봅니다.

<div class="point" markdown="1">
**{{icon:bulb}} Agent Observability가 없다면** 서연의 신고를 받고도 그 요청이 어디를 거쳤는지 찾을 방법이 없습니다.
</div>

## 무슨 일이 일어나나

<ol class="flow">
<li data-say="응답에 들어 있던 호출 번호나 추적 번호로 그 요청의 기록을 찾습니다.">{{icon:trace}}<b>1. 번호로 기록을 찾는다</b><span>invocationId · traceparent</span></li>
<li data-say="요청이 거친 구간(span)마다 걸린 시간과 성공 여부가 남아 있습니다.">{{icon:clock}}<b>2. 구간별 시간과 성공 여부를 본다</b><span>span 트리</span></li>
<li data-say="오류가 없으면 네트워크, 정책, 도구 고장은 아니라는 뜻입니다. 남은 가설만 추립니다." class="hi">{{icon:target}}<b>3. 오류가 없으면 범위를 좁힌다</b><span>남은 가설 둘</span></li>
<li data-say="기록에는 질문과 조회어의 원문이 없습니다. 개발 환경에서 같은 질문을 다시 실행해 원인을 확정합니다.">{{icon:code}}<b>4. 다시 실행해 원인을 확인한다</b><span>개발 환경</span></li>
</ol>

## 실물 보기

요청 B의 추적 기록입니다. 구간 하나를 span이라고 부릅니다.

<!-- kind: example -->

```text
invoke_agent invoice-summary          1,840ms  성공
├─ chat (조회어 만들기)                  320ms  성공
├─ execute_tool tool-erp-read           210ms  성공   결과 1건
└─ chat (요약 만들기)                  1,160ms  성공
```

- 네 줄의 추적 번호가 같아서 한 요청의 일로 묶여 보입니다.
- `결과 1건`: 도구가 청구서 하나를 돌려줬다는 것까지만 남습니다. 어느 청구서였는지는 없습니다.
- 고장은 첫째 `chat`에서 났습니다. 모델이 조회어를 "한빛상사"로만 만들어 월이 빠졌습니다. 그런데 모델은 오류 없이 답을 냈기 때문에 기록에는 성공으로만 보입니다.

내 PC의 로컬 mock이 요청 A 한 번에 실제로 남기는 감사 기록 다섯 줄입니다.

<!-- kind: run boundary: local -->

```json
{"component": "agent-gateway", "traceparent": "00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01", "tenantId": "tenant-demo", "invocationId": "inv-75c63e0874aa41ce91ba25039d6e8fe1"}
{"component": "runtime", "traceparent": "00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01", "invocationId": "inv-75c63e0874aa41ce91ba25039d6e8fe1"}
{"component": "credential-broker", "traceparent": "00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01", "decisionId": "policy-demo"}
{"component": "tool-gateway", "traceparent": "00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01", "toolId": "tool-search", "tenantId": "tenant-demo"}
{"component": "model-gateway", "traceparent": "00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01", "decisionId": "policy-demo", "provider": "self-hosted"}
```

- 다섯 줄의 `traceparent`가 같습니다. 정문, Runtime, Credential Broker, 도구 경로, 모델 경로가 한 요청의 일로 묶입니다.
- 어느 테넌트의 어느 호출이(`tenantId`, `invocationId`), 어떤 정책 결정으로(`decisionId`), 어떤 도구와 모델 쪽을(`toolId`, `provider`) 썼는지가 남습니다.
- 질문 문장, 조회어, 도구가 돌려준 내용은 어느 줄에도 없습니다. 기밀이 로그로 새는 길을 만들지 않으려고 일부러 남기지 않습니다.

그래서 추적 기록으로는 원인을 확정할 수 없고 **범위를 좁힐** 수 있습니다. 요청 B에서 기록이 지워 준 가설은 "네트워크, 정책, 도구 오류"이고, 남는 가설은 둘입니다. 조회가 엉뚱한 청구서를 가져왔거나, 조회는 맞았는데 요약이 금액을 틀렸거나입니다. 민준은 개발 환경에서 같은 질문을 다시 실행해 기대한 `INV-2048` 대신 `INV-2101`이 조회된 것을 보고, 조회어에 월이 빠진 것을 확인합니다.

## 직접 해 보기

<div class="sim" data-sim="trace"></div>

<ol class="mission">
<li>오류가 없는데 답이 틀렸습니다. 구간을 눌러 남은 속성을 본 뒤 다음에 할 일을 골라 보세요.</li>
<li>추적 번호 전달을 끊으면 기록이 어떻게 보이나요.</li>
</ol>

## 잘못되면

**하위 Agent를 부르면서 추적 번호를 넘기지 않으면** 기록이 두 동강 납니다. 출장 정산 Agent `expense-settlement`가 `invoice-summary`를 부르는 경우, 민준이 `traceparent`를 넘기지 않으면 하위 Agent의 구간은 새 번호로 기록됩니다. 신고를 받은 사람은 위쪽 한 줄만 보게 되고 그 아래에서 무슨 일이 있었는지 따라갈 수 없습니다. 직접 HTTP로 부르지 않고 플랫폼의 `ctx`로 부르면 번호는 자동으로 이어집니다.

**디버깅이 편하다고 프롬프트 원문을 로그에 남기면** 기밀이 로그로 새는 길이 생깁니다. 청구서 내용은 `confidential`인데 로그 저장소는 그만큼 엄격하게 보호되지 않는 경우가 많습니다. 그러면 청구서를 볼 권한이 없는 사람도 로그에서 청구서 내용을 보게 됩니다. 원문이 필요하면 개발 환경에서 합성 데이터로 다시 실행합니다.

<details class="more" markdown="1"><summary>더 보기: 지표만 볼 때, 호출 번호를 보여 주지 않을 때</summary>

**지표만 보고 추적을 보지 않으면** 요청 B 같은 고장은 보이지 않습니다. 오류율은 0%이고 평균 지연도 정상이기 때문입니다. 틀린 답은 지표가 아니라 사용자 신고와 평가([Agent Evaluation](18-agent-evaluation.md))로 잡습니다.

**호출 번호를 사용자에게 보여 주지 않으면** 서연의 신고를 받고도 수많은 요청 가운데 어느 것인지 찾지 못합니다. 앱은 응답의 `invocationId`를 화면이나 오류 메시지에 함께 보여 줍니다.
</details>

## 내가 할 일

1. 신고를 받으면 호출 번호로 추적 기록을 찾습니다.
2. 오류가 난 구간이나 가장 긴 구간을 먼저 봅니다.
3. 오류가 없으면 남은 가설을 적고, 같은 질문을 개발 환경에서 다시 실행합니다.
4. 원인을 찾았으면 틀린 요청을 평가 데이터셋의 행으로 추가합니다. 이 일은 다음 장에서 이어집니다.

**내 PC에서 해 보기** [Agent Tools](15-agent-tools.md)의 요청을 다시 보내고 응답의 `traceparent`를 확인합니다. 가운데 32자리가 추적 번호입니다.

<!-- kind: run boundary: local -->

```json
{"invocationId":"inv-9946215c02f347bd8ba5de71ca079905", "traceparent":"00-d0f1038087eb42d6b187b4c8ba5caa2a-ae9b01ef32f942d6-01"}
```

`make scenarios`는 시나리오마다 추적 번호와, 같은 번호로 서비스별로 남은 감사 기록을 출력합니다. 로컬 mock 모델은 조회어를 만들지 않으므로 내 PC에서는 "월 누락"이 재현되지 않습니다. 민준이 다시 실행해 확인하는 대목은 이야기 속에서만 일어납니다.

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| 추적 번호 전파, 감사 기록 | 실행 | 로컬 mock의 응답, `make scenarios` |
| span 이름과 속성 규격 | 정의 | [관측성](../observability.md) |
| span 내보내기, 관측 백엔드, 추적 화면 | 정의 | 위 span 트리는 예시입니다 |
</div>

## 규칙으로 정리

| 구분 | 목적 | 예 |
|---|---|---|
| 관측성(Observability) | 시스템 동작 이해, 장애 분석 | 지연 시간, 오류율, 토큰 사용량 |
| 실행 추적(trace) | 요청 하나의 처리 경로 추적 | Agent 호출 → 모델 추론 → 도구 호출 span |
| 감사(audit) | 행위의 증적 보존 | 누가 어떤 정책 결정으로 어떤 도구를 호출했는지 |

- W3C Trace Context(`traceparent`, `tracestate`)를 모든 구간에 전파합니다(MUST). 장면 ⑧
- span 이름과 속성은 OpenTelemetry GenAI semantic conventions를 따릅니다(MUST). 이 규격은 Development 단계이므로 플랫폼은 쓰는 규격 버전을 고정하고 기록합니다(MUST).
- 프롬프트 원문, 모델 출력 원문, 토큰, 검색된 개인정보 원문은 기본으로 기록하지 않습니다. baggage에도 넣지 않습니다(MUST NOT). 장면 ⑧

| span | 이름 | 주요 속성 |
|---|---|---|
| Agent 호출 | `invoke_agent {gen_ai.agent.name}` | `gen_ai.agent.name`, `gen_ai.operation.name` |
| Agent 생성 | `create_agent` | `gen_ai.agent.name` |
| 모델 추론 | `{gen_ai.operation.name} {gen_ai.request.model}` | `gen_ai.provider.name`(필수), `gen_ai.request.model`, 토큰 사용량 |
| 플랫폼 고유 (SHOULD) | — | `platform.` 접두사: tenant 별칭, 정책 결정 ID, routeDecisionId, Guardrail 검사 ID |

기록 대상은 지연 시간, 오류, 모델 호출 수, 입력·출력 토큰, tenant·Agent별 비용 귀속, 도구 실패, 정책 거부, Guardrail 차단, 승인 대기입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [관측성](09-glossary.md#term-observability) [실행 추적 컨텍스트](09-glossary.md#term-trace) [span](09-glossary.md#term-span) [OpenTelemetry GenAI](09-glossary.md#term-otel-genai) [감사](09-glossary.md#term-audit)
</div>

## 한 문장으로

요청 하나가 어디를 거쳤고 어디서 얼마나 걸렸는지 번호 하나로 따라갑니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 도구가 1건을 돌려줬다는 기록으로 어떤 청구서를 가져왔는지 알 수 있나요?</summary>
알 수 없습니다. 추적 기록은 조회 인자와 결과의 원문을 남기지 않습니다. 개발 환경에서 같은 질문을 다시 실행해 확인합니다.
</details>

<details markdown="1"><summary>Q2. 요청 B의 기록은 네 구간 모두 성공입니다. 이 사실이 지워 주는 가설과 남기는 가설은 무엇인가요?</summary>
네트워크, 정책, 도구 고장은 지워집니다. "조회가 엉뚱한 청구서를 가져왔다"와 "요약이 금액을 틀렸다"가 남습니다.
</details>

<details markdown="1"><summary>Q3. 민준이 디버깅용으로 프롬프트 원문을 로그에 남기려 합니다. 무엇이 문제인가요?</summary>
기밀인 청구서 내용이 로그 저장소로 복사됩니다. 그러면 원본을 볼 권한이 없는 사람도 로그에서 그 내용을 보게 됩니다.
</details>
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- span 규격: [OpenTelemetry GenAI](10-references.md#ref-otel)
</div>

다음 장면은 ⑨입니다. 만점을 받고 승인된 버전이 왜 운영에서 틀렸는지를 시험지에서 찾습니다.
