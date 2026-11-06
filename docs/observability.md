# Observability

Agent Observability는 실행 추적(trace), 지표(metric), 로그를 수집해 Agent의 동작을 파악하게 하는 Core System이다. 감사(audit) 기록과 목적이 다르다. 감사는 행위의 증적을, Observability는 동작 이해와 장애 분석을 목적으로 한다.

## 실행 추적

- W3C Trace Context(`traceparent`, `tracestate`)를 Agent Platform APIs → Agent Runtime → Agent Gateway(모델·도구 경로) → Knowledge → 하위 Agent까지 전파해야 한다(MUST).
- span 이름과 속성은 OpenTelemetry GenAI semantic conventions를 따른다(MUST).
  - Agent 호출: `invoke_agent {gen_ai.agent.name}`
  - Agent 생성: `create_agent`
  - 모델 추론: `{gen_ai.operation.name} {gen_ai.request.model}`, `gen_ai.provider.name` 필수
- GenAI semantic conventions는 Development 단계 규격이다. 플랫폼은 사용하는 규격 버전을 고정하고 기록해야 한다(MUST). 버전 전환은 [계약 변경](versioning.md) 절차를 따른다. 고정 버전은 TBD-12이다.
- 플랫폼 고유 속성(tenant 별칭, policy decision ID, route decision ID, guardrail 검사 ID)은 `platform.` 접두사로 기록한다(SHOULD).

## 지표

다음 지표를 측정해야 한다(SHOULD).

| 분류 | 지표 |
|---|---|
| 성능 | 지연 시간, 오류율, timeout |
| 사용량 | 모델 호출 수, 입력·출력 토큰, tenant·Agent별 비용 귀속 |
| 도구 | 도구 호출 실패, unknown outcome |
| 통제 | 정책 거부, guardrail 차단, 승인 대기 |

## 기록 금지

- 프롬프트 원문, 모델 출력 원문, 토큰, 검색된 개인정보 원문은 기본적으로 기록하지 않는다(MUST NOT). 원문 기록이 필요한 평가 목적은 별도 승인과 보존 정책(TBD-12)을 따른다.
- baggage에 개인정보나 토큰을 넣지 않는다(MUST NOT).

## 제공 범위

v0.1은 trace context 전파와 mock 감사 기록을 제공한다. OpenTelemetry exporter 연동과 백엔드 제품은 TBD-12이다.

## 근거

- OpenTelemetry GenAI semantic conventions: agent span(`invoke_agent`, `create_agent`)과 inference span 규격.
- W3C Trace Context.
- Microsoft Foundry는 평가, 추적, 모니터링을 구분하고 Agent 실행·모델·도구·토큰·지연·실패를 추적한다.
- 출처 목록: [근거와 참고 자료](onboarding/10-references.md)
