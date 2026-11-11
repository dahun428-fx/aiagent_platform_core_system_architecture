# impl — Core System 구현

[구현 로드맵](../docs/implementation-roadmap.md)의 조각을 실제 서비스로 만드는 코드다. 표준 패키지와 버전을 따로 매기며(`impl/VERSION`), 표준 패키지 ZIP과 checksums에는 포함하지 않는다.

## 지금까지의 조각: S0 걷는 뼈대, S0b 시나리오 화면, S1 권한 거부, S2 timeout, S3 오류 매핑·읽기 재시도, S4 보호 장치, S5 도구 경로·멱등성, S6a 쓰기·승인·unknown_outcome, S6b 동시 실행

Agent Gateway의 모델 경로와 도구 경로를 각각 별도 HTTP 서비스로 분리했다.

```
클라이언트 → Platform APIs + Runtime (참조 구현) ─┬→ Agent Gateway 모델 경로 → 가짜 모델
             impl/platform_api.py                 │   impl/gateway/model_route.py   impl/fakes/fake_model.py
                                                  └→ Agent Gateway 도구 경로 → 가짜 도구 (tool-search 읽기, tool-ticket 쓰기)
                                                      impl/gateway/tool_route.py    impl/fakes/fake_tool.py
                                                      └ PostgreSQL effect ledger (impl/gateway/ledger.py)
                                                      (도구 경로는 같은 DB를 쓰는 worker 2개: tool-route, tool-route-2)
```

모든 서비스는 127.0.0.1의 빈 포트에만 바인딩한다. Platform APIs에서 모델 경로로 가는 내부 구간에는 공유 비밀값으로 만든 HMAC 서명(`X-Internal-Signature`)을 붙이고, 모델 경로는 서명이 없거나 틀리면 403으로 거부한다. 서명 키는 `stack.py`가 실행마다 새로 만들어 환경 변수 `IMPL_INTERNAL_KEY`로 넘기며 파일에 남기지 않는다.

모델 경로는 서명이 맞아도 호출마다 identity·policy를 다시 검사한다(scope, tenant, 정책 만료, 데이터 분류에 따른 provider 제한).

Agent 호출마다 deadline이 있다. Platform APIs는 본문의 `execution.timeoutMs`와 앱이 보낸 `Request-Timeout-Ms` 헤더 중 짧은 쪽으로 deadline을 정하고, 모델 경로에 남은 시간을 `Request-Timeout-Ms`로 넘긴다. 모델 경로는 그 시간과 자체 상한(5초) 중 짧은 쪽만 upstream을 기다리고, 넘으면 upstream 연결을 끊고 504 `UPSTREAM_TIMEOUT`을 돌려준다([ADR-038](../adr/ADR-038.md)).

upstream 실패는 시간 초과 504, 연결 실패 503 `UPSTREAM_UNAVAILABLE`, 5xx·깨진 응답 502 `UPSTREAM_ERROR`로 나눈다. 모델 호출은 외부에 남는 효과가 없는 읽기 호출이라 모델 경로가 deadline 안에서 최대 3회(0.05초, 0.1초 간격) 시도한다. 4xx와 시간 초과는 다시 시도하지 않는다. Platform APIs는 다시 시도하지 않고 모델 경로의 502·503·504를 그대로 전한다. 오류 응답에는 upstream 주소나 원문 오류를 넣지 않는다.

모델 경로에는 보호 장치 두 가지가 있다. circuit breaker는 upstream 호출이 연속 3번 실패하면 열려서 1초 동안 upstream을 부르지 않고 바로 503(`Retry-After: 1`)을 준다. 1초가 지나면 시험 호출 하나만 보내서, 성공하면 닫고 실패하면 다시 연다. rate limit은 tenant·Agent마다 1초에 5번까지 받고, 넘으면 429 `RATE_LIMITED`와 `Retry-After`를 준다. Platform APIs는 이 `Retry-After`를 앱 응답까지 그대로 전한다. 수치는 로컬 시나리오용이며 운영 값은 TBD다.

도구 경로는 승인된 도구만 실행한다. 등록된 도구(이름·버전)여야 하고, 정책의 `allowedResources`에 그 자원이 있어야 하고, 도구가 요구하는 scope(읽기 `tools.read`, 쓰기 `tools.write`)가 있어야 한다. 아니면 403이다. 실행 전에 Credential Broker로 이번 호출에만 쓰는 자격증명을 발급·소비한다.

쓰기 도구(`tool-ticket`)는 이 호출에 묶인 승인이 있어야 실행한다. tool-invoke의 `approvalId`로 승인 기록을 찾고, 같은 tenant, 같은 `invocationId`, 같은 요청(도구 이름·버전·인자의 digest, `subjectDigest`), 같은 정책 버전, 만료 전인지 본다. 승인이 없으면 403 `Write tool requires approval`, 맞지 않으면 403 `Approval is stale or not bound to this request`이고 도구는 부르지 않는다.

쓰기 도구에 요청을 보낸 뒤 답을 잃으면(시간 초과, 답 없이 연결 끊김, 이상한 답) 실제로 실행됐는지 알 수 없다. 이때는 오류 대신 `status: "unknown_outcome"`인 tool-result를 저장해 돌려주고, 자동으로 다시 실행하지 않는다. 같은 키로 다시 와도 저장된 `unknown_outcome`을 그대로 돌려준다. 보내기 전에 연결이 안 된 경우만 실행되지 않은 것이 확실하므로 503을 주고 다시 시도할 수 있게 한다.

같은 멱등성 키로 도구를 여러 번 불러도 실제 실행은 한 번이다. 키는 tenant·principal(없으면 workload)·Agent·도구·도구 버전·`Idempotency-Key`에 묶여 PostgreSQL 표 `tool_effects`에 한 줄로 남는다. 끝난 키로 다시 오면 실행하지 않고 저장된 결과(성공 또는 `unknown_outcome`)를 돌려주고, 같은 키에 다른 인자가 오면 409 `CONFLICT`, 아직 실행 중이면 202(`Retry-After: 1`)를 준다. 기록이 프로세스 밖에 있으므로 도구 경로를 재시작해도 남고, 같은 DB를 쓰는 worker가 여럿이어도 한 키는 한 번만 실행된다(`INSERT … ON CONFLICT DO NOTHING`으로 실행 권리를 원자적으로 가져감). 읽기 도구가 실패하거나 쓰기 도구가 보내기 전에 실패하면 줄을 지워 같은 키로 다시 시도할 수 있다.

실행 도중 worker가 죽으면 처리 중(pending) 줄이 남는다. 살아 있는 실행은 upstream을 5초보다 오래 기다리지 않으므로, 6초보다 오래된 pending은 실행하던 worker가 죽은 것으로 본다(DB 시계 기준). 그 키로 다음 요청이 오면 읽기 도구는 줄을 지우고 다시 실행하고, 쓰기 도구는 실행됐는지 모르므로 `unknown_outcome`으로 확정한다. 6초 전에는 202다.

## PostgreSQL

도구 경로에는 PostgreSQL이 필요하다. 둘 중 하나를 고른다.

- 설치된 PostgreSQL(`initdb`·`pg_ctl`이 PATH, `PGBIN`, 또는 흔한 설치 위치에 있음): 아무것도 하지 않아도 된다. `stack.py`가 실행마다 임시 DB를 만들고 끝나면 지운다. root로는 `initdb`가 돌지 않는다.
- Docker: `make db`로 띄우고 `IMPL_DATABASE_URL=postgresql://impl:impl@127.0.0.1:55432/impl make demo`처럼 주소를 함께 준다. 이미 있는 다른 PostgreSQL도 같은 환경 변수로 쓸 수 있다.

## 확인 방법

```sh
make setup                     # 처음 한 번: .venv 생성 + requirements-dev.txt 설치(uv가 있으면 uv 사용)
make demo                      # 스택을 띄우고 브라우저에서 시나리오 화면(http://127.0.0.1:8700)을 연다
make scenarios                 # 같은 시나리오를 터미널 표로 실행한다
```

`make demo` 화면은 열리자마자 모든 시나리오를 실행하고, 시나리오마다 요청, 기대값과 실제값 비교, trace id, 가짜 upstream 호출 횟수, 같은 trace id로 남은 감사 기록을 보여 준다. `다시 실행` 버튼으로 하나만, `모두 실행`으로 전부 다시 돌린다. 오른쪽 위가 `초록 N개, 빨강 0개`이면 통과다. Ctrl-C로 화면 서버와 스택을 함께 끈다.

`make scenarios`는 출력 마지막 줄이 `초록 N개, 빨강 0개`이면 통과다. 각 시나리오의 trace id와, 같은 trace id로 남은 감사 기록이 서비스별로 출력된다.

- `make demo` 포트를 바꾸려면 `python impl/demo/server.py --port 8801`, 브라우저를 열지 않으려면 `--no-open`을 붙인다.
- `make stack`: 스택을 띄운 채로 두고 각 서비스 주소를 출력한다.
- `make test-impl`: 같은 시나리오 정의를 자동 테스트로 실행한다.
- 다른 인터프리터는 `PYTHON=... make scenarios`로 지정한다. Windows는 `python impl/scenarios/run.py`를 직접 실행한다.

## 시나리오 정의

`impl/scenarios/scenarios.json` 하나를 `make scenarios`, 자동 테스트, 시나리오 화면(`impl/demo/`)이 함께 읽는다. 시나리오를 추가하면 세 곳에 동시에 나타난다. 시나리오는 요청과 기대값(상태 코드, 걸린 시간 범위 `elapsedMs`(하한은 timeout보다 20ms 낮게 잡는다. Windows의 시계·타이머 단위가 약 15ms라 300ms timeout이 296ms로 재질 수 있다), 출력, 응답 필드, upstream 호출 횟수와 연결 끊김 횟수, 서비스별 감사 기록)을 담는다. `fault`에는 가짜 upstream에 심을 고장을 적는다(지연 `delayMs`, 상태 코드 `status`, 연결 끊기 `drop`, 깨진 응답 `garbage`, 처음 n번만 실패 `failTimes`). `noInternalAddress`는 응답에 내부 주소가 없는지, `headers`는 응답 헤더(예: `Retry-After`)를 본다. 여러 요청이 필요한 시나리오는 `steps`에 단계(고장 `fault`, 대기 `waitMs`, 반복 `repeat`, 마지막 응답의 기대값 `expect`)를 적는다. 단계에 `restart`(예: `"tool-route"`)를 적으면 그 서비스를 같은 포트로 다시 띄운다. `concurrent: n`은 같은 요청 n개를 동시에 보내고(`workers`가 있으면 돌아가며 나눠 보냄) 모든 응답이 `statusesIn` 안인지 본다. `background: true`는 답을 기다리지 않고 보낸 뒤 `settleMs`만큼 기다린다(실행 도중에 worker를 죽이는 시나리오용). 시나리오를 시작할 때마다 모델 경로의 circuit·rate limit 상태를 `/_reset`으로 되돌린다. `request.headers`로 추가 헤더(예: `Request-Timeout-Ms`)를 보낸다. `"target": "tool-route"`인 시나리오는 도구 경로에 tool-invoke를 직접 보내고(`toolId`·`version`·`arguments`·`idempotencyKey`로 fixture를 덮어씀, 키는 실행마다 새로 붙는 값과 합쳐짐, `grant`로 scope·자원을 더하고, `approval`이 있으면 이 요청에 맞는 승인을 만들어 붙임, `worker`로 보낼 worker를 고름. `approval` 안의 값은 승인에 덮어써서 만료·다른 요청을 흉내 냄), `"target": "model-route"`인 시나리오는 Platform을 건너뛰고 모델 경로에 직접 보내며, `sign`(서명 여부), `identity`·`policy`(예제 fixture에 덮어쓸 값), `afterSigning`(서명 뒤에 바꿀 값)으로 내부 구간을 흉내 낸다.

## 아직 하지 않은 것

- 내부 구간 서명에 만료 시각이나 nonce가 없어, 가로챈 요청을 그대로 다시 보내면 통과한다. 3단계(Identity)에서 워크로드 토큰으로 바꾼다.
- 재시도 backoff에 jitter가 없고 재시도 예산이 호출마다 따로다. circuit breaker가 연속 실패를 끊어 주지만, 열리기 전까지는 인스턴스마다 재시도가 겹칠 수 있다.
- circuit과 rate limit 상태는 프로세스 메모리에만 있다. 모델 경로를 여러 개 띄우면 한도가 그 수만큼 늘고 circuit도 따로 열린다. 수평 확장 때 공유 저장소로 옮긴다.
- circuit 기준(연속 3번, 1초)과 한도(1초 5번)는 코드 상수다. 운영 값은 upstream·tenant별 설정으로 받는다(TBD).
- timeout은 소켓 동작(연결, 읽기 한 번)마다 걸린다. 조금씩 흘려 보내는 upstream은 deadline을 넘길 수 있다. 실제 upstream을 붙일 때 전체 시간 상한을 둔다.
- Platform APIs는 잘못된 `Request-Timeout-Ms` 값을 422로 거부하지 않고 무시한다(본문의 `timeoutMs`는 적용). 모델 경로는 422로 거부한다.
- pending을 죽은 것으로 보는 6초는 도구 경로의 upstream 상한(5초)에 묶인 코드 상수다. 상한을 설정으로 받게 되면 함께 옮긴다.
- worker가 죽은 뒤 다음 요청이 올 때까지 pending은 그대로다. 요청 없이 정리하는 작업(sweeper)은 없다.
- Platform·Runtime은 첫 번째 worker(tool-route)만 부른다. worker 사이 부하 분산은 없다.
- `unknown_outcome`을 실제 결과로 확정하는 reconciliation은 2단계(Runtime)에서 한다. 지금은 같은 키로 와도 계속 `unknown_outcome`이다.
- 승인 기록은 로컬 확인용 `/_approvals`로 바로 넣는다. 승인자 권한(reviewer role) 검사와 승인 API(`submitApproval`)는 아직 없다.
- Platform·Runtime은 아직 쓰기 도구를 부르지 않는다(Agent 템플릿은 읽기 도구만 쓴다). Runtime이 `unknown_outcome`을 어떻게 다룰지는 2단계에서 정한다.
- 쓰기 도구가 4xx로 거절해도 `unknown_outcome`으로 둔다(보수적으로). 실제 도구를 붙일 때 확실한 거절은 오류로 나눈다.
- 등록된 도구 목록이 코드(예제 fixture)에 고정돼 있다. Agent Factory의 도구 Registry가 생기면 거기서 읽는다.
- tool-invoke 계약에 Agent 버전이 없어 멱등성 키를 Agent id로 묶는다.
- Credential Broker는 도구 경로 프로세스 안에 있다(참조 구현에서 발급 규칙만 등록된 도구로 넓힘). 별도 서비스 분리는 후속 조각이다.
- ledger는 호출마다 DB 연결을 새로 연다. 호출이 많아지면 연결 풀로 바꾼다.
- `/_audit`, `/_stats`, `/_reset`(가짜 모델·도구와 모델 경로)과 시나리오 화면의 `/api/*`는 로컬 확인용 엔드포인트다. 운영 배포에 두지 않는다.
