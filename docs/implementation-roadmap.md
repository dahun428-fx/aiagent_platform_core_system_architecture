# 구현 로드맵

이 문서는 [Core Systems](core-systems.md)를 실제 서비스로 구현하는 순서와 각 조각의 완료 기준을 정의한다. 순서는 Agent Gateway → Agent Runtime → Agent Identity·Agent Observability → Agent Evaluation → Agent Tuning이다. 구현 단위는 1~3일 분량의 **조각(slice)** 이다. 각 조각은 명령 하나로 실행해 결과를 직접 확인할 수 있어야 한다.

첫 조각은 성공 경로 하나를 처음부터 끝까지 관통하는 걷는 뼈대(walking skeleton)다. 이후 조각은 실패 상황을 하나씩 추가한다.

## 출발점

현재 참조 구현(`examples/python/platform_ref.py`)은 계약을 실행해 보는 단일 프로세스 mock이다. 흐름과 거부 규칙은 계약과 맞지만, 운영에서 발생하는 실패 상황은 다루지 않는다. 구현 한계의 원문은 [제공 범위와 구현 한계](release-scope.md)를 따른다.

| 영역 | 현재 참조 구현 | 구현이 채울 부분 |
|---|---|---|
| 프로세스 경계 | Platform APIs·Runtime·모델 경로·도구 경로·Credential Broker가 한 프로세스의 클래스 | 서비스 간 네트워크 경계, 서로 다른 신뢰 영역 |
| 권한 | scope·tenant·만료·위임 체인 검사, 분류 하향 거부 | 실제 토큰 검증, 데이터 원천 분류, policy engine |
| 시간 제한 | 없음 | `timeoutMs` 적용, deadline 전파 |
| 오류·재시도 | Problem Details 형식 | upstream 실패 매핑, 재시도 예산, circuit breaker |
| 멱등성 | 메모리 dict | 재시작·다중 worker에 안전한 persistent effect ledger |
| 실행 | 동기 호출만, async는 501 | durable 상태 전이, checkpoint, 취소, 승인 대기 |
| Agent 격리 | in-process import | 프로세스·컨테이너 격리 |
| 관측 | 메모리 audit 목록 | OTel exporter, collector, 비용 지표 |
| 외부 연결 | 없음 | 모델 endpoint, REST·MCP tool server |

## 진행 방식

모든 조각은 5분 안에 직접 실행해 맞는지 판단할 수 있는 결과로 끝난다. 결과가 눈에 보이지 않는 기반 작업은 따로 모아 진행하지 않는다. 그 작업을 처음 필요로 하는 조각에 필요한 만큼만 넣는다.

**조각 조건**

- 크기는 1~3일, PR 하나다. 이보다 커지면 둘로 나눈다.
- 시나리오 정의 파일 하나를 자동 테스트, `make scenarios`(표 출력), 시나리오 실행 화면이 함께 읽는다.
- 고장 주입(지연, 5xx, 연결 끊김, 잘못된 응답)은 시나리오 정의의 `fault:` 필드로 지정한다. 화면과 CI가 같은 고장을 똑같이 재현한다.
- 판정은 "초록 N개, 빨강 0개" 한 줄로 끝난다. 이전 조각의 시나리오도 계속 통과해야 한다.

**조각 사이클**

1. 조각 목록의 "확인 방법"을 그 조각의 약속으로 삼는다.
2. 구현, 시나리오, 테스트를 PR 하나로 올린다. CI가 시나리오 결과표를 PR에 첨부한다.
3. 검토자는 결과표를 보고 병합하거나 수정을 요청한다. 변화가 큰 조각(S0, S0b, S5, S6a, S7a)은 로컬에서도 실행해 본다.
4. 피드백에 따라 다음 조각의 순서와 범위를 조정하고, 이 문서의 조각 목록을 갱신한다.

**코드 위치**

구현 코드는 이 저장소의 `impl/` 디렉터리에 둔다. 표준 패키지와 버전을 따로 매기며, 표준 패키지 ZIP과 checksums에는 포함하지 않는다. 계약이 안정되면 별도 저장소로 분리할지 다시 정한다.

## 1단계 Agent Gateway

Agent Gateway의 모델 경로와 도구 경로를 독립 HTTP 서비스로 만들고, 권한·timeout·오류·재시도를 조각마다 하나씩 입증한다. upstream은 모두 로컬의 가짜 서버라서 비밀정보가 필요 없다.

| 순서 | 조각 | 만드는 것 | 확인 방법 |
|---|---|---|---|
| 1 | S0 걷는 뼈대 | Gateway 모델 경로와 가짜 모델만 HTTP로 분리한다. Platform APIs·Runtime은 참조 구현을 그대로 쓴다. 시나리오 정의 파일 1개와 `make scenarios`를 만든다 | `make scenarios` → "정상 호출"이 초록, trace id와 감사 기록 출력 |
| 2 | S0b 시나리오 화면 | 정적 HTML 한 장: 시나리오 목록, 실행 버튼, 기대값과 실제값 비교, trace id, 가짜 upstream 호출 횟수 | `make demo` → 브라우저에서 같은 시나리오가 초록 |
| 3 | S1 권한 거부 | 호출마다 identity·policy를 다시 검사한다. 내부 구간에 공유 비밀값 기반 최소 서명을 넣어 요청 본문의 identity를 그대로 믿지 않는다 | scope 없음·tenant 불일치·서명 없음 → 403, 모델 호출 0회. 분류를 `public`으로 낮춰도 서버 분류 유지: self-hosted가 있으면 200, external만 있으면 503 |
| 4 | C1 계약 개정 0.2.0 | 502·504 응답, `UPSTREAM_TIMEOUT`·`UPSTREAM_ERROR`·`RATE_LIMITED` 코드, `Retry-After` 헤더, deadline 전달 헤더, 도구 경로 202 응답. ADR, migration note, 새 snapshot | 계약 변경 요약표 확인, 기존 테스트가 0.2.0 기준으로 초록 |
| 5 | S2 timeout | deadline을 전파하고 `timeoutMs`와 남은 시간 중 짧은 쪽을 적용한다. 초과하면 upstream 연결을 끊는다 | `timeoutMs`=500에서 지연 주입 → 500~650ms 안에 504, upstream 연결 종료 표시 |
| 6 | S3 오류·읽기 재시도 | upstream 실패를 Problem Details로 매핑한다. 읽기 호출만 최대 3회 backoff 재시도한다 | 5xx·연결 거부·깨진 응답 → 502·503·502. 일시 장애 → 시도 2회 후 200. 계속 실패 → 3회 후 502. 응답에 내부 주소 없음 |
| 7 | S4 보호 장치 | upstream별 circuit breaker, tenant·Agent별 rate limit | 연속 실패 → circuit open, 즉시 503 → half-open 카운트다운 후 자동 회복. 한도 초과 → 429와 `Retry-After` |
| 8 | S5 도구 경로·멱등성 | 가짜 REST tool server, 승인된 도구만 허용. 여기서 PostgreSQL을 도입한다. idempotency key는 tenant·principal·Agent version·tool version·요청 digest에 결합한다 | 같은 key 재요청 → `make restart-gateway` → 재요청. 도구 실행 1회. 다른 본문 409, 미승인 도구 403 |
| 9 | S6a 쓰기·승인·unknown_outcome | 쓰기 전에 로컬 승인 검증(tenant·invocationId·subjectDigest·policyVersion·만료). `pending`을 기록하고, 응답을 잃으면 `unknown_outcome`으로 두며 자동 재실행하지 않는다 | 승인 없는 쓰기 403. 응답 끊김 → `unknown_outcome`, 재실행 0회. 같은 key 재요청은 저장된 `unknown_outcome`을 그대로 반환 |
| 10 | S6b 동시 실행 | worker 2개, effect ledger 기반 중복 실행 방지 | 동시 20회 실행 → 실제 실행 1회, 나머지는 202 또는 저장된 결과. 최종 판정은 CI 반복 테스트 |
| 11 | S7a MCP | 인증 없는 로컬 MCP tool server를 거쳐 도구를 호출한다 | S1·S3·S5 시나리오를 MCP 도구로 다시 실행해 같은 결과 |
| 12 | S7b SDK 분리 | Agent용 SDK를 독립 패키지로 분리한다 | `make agent-demo` 성공. agent-demo가 SDK만 import |
| 13 | S7c 계약 타입 생성 | 스키마에서 타입을 생성하고 드리프트를 검사한다. `release-scope.md`를 갱신한다 | 스키마를 일부러 바꾸면 CI가 빨강 |

모든 조각에서 응답·감사 기록·오류에 같은 trace id가 남는지 함께 확인한다.

**1단계 범위 밖**

- 실제 모델·SaaS 호출과 실제 자격증명
- A2A 경로
- OTel exporter (3단계)
- 모델 경로 멱등성
- `unknown_outcome` reconciliation (2단계)
- MCP OAuth 요구사항 (3단계 Credential Broker 이후)

S1의 내부 서명은 임시 장치이며 3단계 토큰 검증으로 대체한다. 이 한계는 `release-scope.md`에 적는다.

## 2단계 Agent Runtime

Agent를 플랫폼 프로세스 밖에서 격리 실행하고, 실행 상태를 저장소에 두어 재시작·취소·승인 대기를 견디게 한다. Runtime의 모든 모델·도구 호출은 1단계 Gateway로만 나간다.

조각 후보(1단계 종료 시 확정):

1. R1 별도 프로세스 실행: 무한 루프 Agent가 `timeoutMs`에 종료되고 `failed`로 기록된다.
2. R2 비동기 호출: `getInvocation`·`listEvents`로 상태와 이벤트가 순서대로 쌓인다.
3. R3 취소: `cancelInvocation` 후 terminal 상태가 덮어쓰이지 않는다.
4. R4 재시작 복구: Runtime 재시작 후 checkpoint에서 재개하고, 확정된 쓰기는 다시 실행하지 않는다. 상태 전이는 `revision` 기반 compare-and-swap으로 보호한다.
5. R5 승인 대기: `waiting_approval`에서 `submitApproval`로 재개한다. 재사용·다른 요청·만료 승인은 거부한다.
6. R6 네트워크 차단: Agent가 Gateway를 거치지 않고 외부에 접속하면 차단된다.
7. R7 reconciliation: `unknown_outcome`을 확인 절차로 확정한다.

상태 전이는 [실행·Durable·HITL](execution.md)을 따른다. Session Store와 Artifact Store는 인터페이스와 단순 구현만 둔다. Memory는 이 단계 범위 밖이다.

## 3단계 Agent Identity·Agent Observability

합성 identity를 실제 토큰 검증으로 바꾸고, span을 실제 collector로 내보낸다. 사내 IdP가 정해지기 전에는 로컬 OIDC 발급자로 검증한다.

조각 후보(2단계 종료 시 확정):

1. I1 토큰 검증: 위조·만료·다른 audience 토큰, 본문 tenant 조작 → 401/403. tenant·principal은 토큰에서만 파생한다.
2. I2 workload identity와 위임: delegated 호출은 토큰 교환(RFC 8693)으로 위임 체인을 표현한다.
3. I3 Credential Broker: secret store의 실제 자격증명을 Gateway 안에서만 주입한다. Agent 쪽 메모리·로그·span에 자격증명이 없음을 자동 검사한다. token passthrough는 금지한다.
4. O1 trace 내보내기: 한 요청의 전 경로(Platform APIs → Runtime → Gateway → upstream)가 collector에서 하나의 trace로 조회된다. GenAI semantic conventions 버전을 고정한다.
5. O2 지표와 비용: 지연, 오류율, timeout, 토큰, tenant·Agent별 비용, 정책 거부, 승인 대기, `unknown_outcome`.

감사 기록은 trace와 분리된 저장소에 추가 전용으로 남긴다. 프롬프트·모델 출력 원문과 토큰은 기본으로 기록하지 않는다. 사내 IdP와의 실제 연동은 TBD-01 결정 후 진행한다.

## 4단계 Agent Evaluation

3단계에서 모인 trace를 평가 데이터로 바꾸고, 기준에 못 미치는 Agent revision의 등록·승격을 막는다.

조각 후보: E1 trace를 평가 사례로 저장 → E2 코드 grader와 승격 게이트 → E3 모델 grader와 사람 검토.

- grader는 코드 기반(도구 선택·정책 준수·스키마), 모델 기반(답변 품질), 사람 검토를 섞는다.
- 측정 축은 목표 달성, 도구 사용 적절성, 안전, 비용·지연이다.
- 완료 기준: 도구 설명을 일부러 망가뜨린 revision이 게이트에서 막히고, 실패 사례가 도구 오류·정책 거부·답변 품질로 분류된다.
- 의미 있는 dataset을 만들려면 첫 업무 사례(TBD-04)가 필요하다.

## 5단계 Agent Tuning

평가에서 찾은 실패를 고치는 루프를 닫는다. 비용이 적은 방법부터 적용한다.

1. 프롬프트·도구 설명 개선안을 만들고 golden dataset으로 재평가한다.
2. 모델 경로의 라우팅 정책을 평가 결과로 조정한다.
3. 필요할 때만 trace로 학습 데이터를 만들어 모델을 튜닝하고, 결과 모델을 모델 경로에 새 버전으로 등록해 평가 게이트를 다시 통과시킨다.

개선안은 평가 점수를 올릴 때만 승격하고, 모든 변경에 근거 trace와 평가 결과를 연결한다.

## 공통 완료 정의

각 조각과 단계는 다음이 모두 참일 때 끝난다.

1. 확인 방법의 모든 항목이 CI 자동 테스트로 통과한다. 손으로만 확인한 항목은 완료로 치지 않는다.
2. 이전 조각의 테스트가 계속 통과한다.
3. 계약을 바꾸면 [계약 변경](versioning.md) 절차대로 스키마·ADR·테스트를 같은 변경에서 갱신한다.
4. `release-scope.md`의 구현 한계에서 해소된 항목을 지우고 남은 한계를 사실대로 적는다.
5. 로컬에서 `make demo` 또는 `make scenarios`로 재현된다.
6. 단계가 끝나면 태그를 붙인다.

## 기술 결정

| # | 질문 | 결정 | 이유 |
|---|---|---|---|
| D1 | 구현 언어 | Python | 기존 계약 검증·참조 구현·테스트를 재사용한다. 측정상 병목이면 Gateway만 교체한다 |
| D2 | 코드 위치 | 이 저장소의 `impl/` | 계약과 구현을 한 PR에서 바꾼다. 1단계 종료 후 분리 여부를 다시 정한다 |
| D3 | 1단계 모델 | 가짜 모델 서버(stub) | 비밀정보 없이 고장을 재현한다. 상용 API는 Credential Broker 이후 |
| D4 | 상태 저장소 | PostgreSQL | 다중 worker 동시성을 검증하려면 서버형 DB가 필요하다. S5에서 도입한다 |
| D5 | 로컬 실행 | 컨테이너 compose | 개발자 노트북에서 바로 실행된다 |
| C1 | 계약 개정 | 0.2.0으로 개정 | timeout과 upstream 오류를 구분하고 deadline을 전달하려면 계약 변경이 필요하다 |

아직 정하지 않은 결정:

| # | 질문 | 추천안 | 필요 시점 |
|---|---|---|---|
| D6 | policy engine | 1단계는 코드 내장과 인터페이스, 3단계 전에 OPA 또는 Cedar 중 선택(TBD-03) | 3단계 전 |
| D7 | durable 실행 | 자체 상태머신과 DB로 시작, 장기 실행이 늘면 workflow engine 검토(TBD-08) | 2단계 전 |
| D8 | 첫 실제 업무 사례 | 1~3단계는 없이 진행, 4단계 dataset 전에 필요(TBD-04) | 4단계 전 |

## 위험과 대응

| 위험 | 영향 | 대응 |
|---|---|---|
| Gateway가 모든 호출의 단일 통과점 | 지연·장애 집중 | 처음부터 무상태 수평 확장 구조. 정책 판단 지연을 측정한다. 부하 목표는 TBD-07 결정 후 정한다 |
| 참조 구현과 실제 구현의 동작 차이 | 문서와 코드 불일치 | 같은 시나리오 정의를 두 구현에 모두 실행한다 |
| 쓰기 도구 중복 실행 | 외부 시스템 피해 | effect ledger, `unknown_outcome`, 자동 재실행 금지를 S6a·S6b에서 먼저 입증한다 |
| 회사 결정(TBD) 대기 | 일정 지연 | IdP·policy·secret store는 표준 인터페이스 뒤에 로컬 구현으로 진행하고 나중에 교체한다 |
| GenAI semantic conventions 변경 | span 재작업 | 사용 버전을 고정하고 매핑을 한 곳에 모은다 |
| 참조 구현을 production으로 오인 | 보안 사고 | 조각마다 `release-scope.md`의 남은 한계를 갱신한다 |
