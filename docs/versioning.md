# 계약 버전·호환성·마이그레이션

패키지 0.1.0, Manifest apiVersion agent.platform/v1alpha1, HTTP /v1은 별도 축이다.
v1alpha1은 운영 안정성 보증이 아니다. 명시적 회사 채택 전 breaking 변경을 조용히 반영해서는 안 된다(MUST NOT).

## 변경 규칙
required 추가, enum 축소, type/format/pattern 변경, response 필드 제거, auth scope 변경은 breaking으로 검토한다.
optional request 추가도 closed schema를 쓰는 old server에 new client가 보내면 실패할 수 있다.
따라서 additive는 무조건 안전하지 않다. request/response 방향 및 실제 소비자 조합을 CI에서 검증한다.
새 API path/optional response 추가도 소비자 strictness와 보안 의미를 확인한다.

tests/test_contracts.py는 contracts/released/의 최신 snapshot(현재 0.2.0)과 현재 계약의 완전 동등성을 gate한다. 0.1.1은 0.1.0에 Manifest `capabilities.type`의 `message`를 추가한 것이다([ADR-037](../adr/ADR-037.md)). 0.2.0은 upstream 실패 구분, deadline 전달, 도구 경로 202를 추가한 것이다([ADR-038](../adr/ADR-038.md), 아래 표).
이는 보수적인 release freeze 검사이며 범용 semantic diff 도구는 아니다.
변경은 diff 검토·ADR·migration note·새 released snapshot을 승인한 뒤 baseline을 갱신한다.
임의로 snapshot만 덮어써 gate를 통과시키지 않는다(MUST NOT).

## 0.1.1 → 0.2.0 변경 요약

| 대상 | 변경 | 0.1.x 소비자 영향 |
|---|---|---|
| `problem.code` | `UPSTREAM_TIMEOUT`, `UPSTREAM_ERROR`, `RATE_LIMITED` 추가 | `code`를 닫힌 enum으로 검증하면 실패한다. 0.2.0 스키마로 갱신하거나 모르는 `code`는 상태 코드로 처리한다 |
| health 외 모든 operation | 502(`UPSTREAM_ERROR`), 504(`UPSTREAM_TIMEOUT`) 응답 추가 | 새 상태 코드를 5xx 일반 오류로 처리하면 동작은 같다 |
| health 외 모든 operation | 선택 요청 헤더 `Request-Timeout-Ms`(남은 시간, ms) 추가 | 보내지 않아도 된다. 보내지 않으면 받는 쪽 `timeoutMs`만 적용 |
| 429·503 응답 | 선택 응답 헤더 `Retry-After`(정수 초) 추가, 예시 `code`를 `RATE_LIMITED`·`UPSTREAM_UNAVAILABLE`로 수정 | 헤더를 무시해도 된다. 무시하면 자체 backoff를 쓴다 |
| `invokeTool` | 202 응답 추가: 같은 `Idempotency-Key` 요청이 실행 중, 본문 없음, `Retry-After` | 202를 성공으로 보고 본문을 읽으면 실패한다. `Retry-After` 뒤 같은 key로 다시 요청한다 |
| OpenAPI `info.version` | 0.1.0 → 0.2.0 | 없음 |

기존 응답·파라미터·오류 코드는 하나도 빠지거나 바뀌지 않았다(`test_0_2_0_only_adds_to_0_1_1`). 이 개정은 계약만 바꾼다. 참조 구현과 `impl/`가 새 응답을 보내는 시점은 [구현 로드맵](implementation-roadmap.md)의 S2~S4, S6b 조각이다.

## 마이그레이션
새 계약 버전을 병행 배포→소비자 적합성 테스트→등록된 소비자 전환→rollback drill→구버전 종료.
deprecation 기간·회사 toolchain·서명/태그 정책은 TBD.
OpenAPI 3.1.2 pin은 현재 validator로 실제 확인한 선택이며 최신 버전 주장과 무관하다.

