# impl — Core System 구현

[구현 로드맵](../docs/implementation-roadmap.md)의 조각을 실제 서비스로 만드는 코드다. 표준 패키지와 버전을 따로 매기며(`impl/VERSION`), 표준 패키지 ZIP과 checksums에는 포함하지 않는다.

## 지금까지의 조각: S0 걷는 뼈대, S0b 시나리오 화면

Agent Gateway 모델 경로를 별도 HTTP 서비스로 분리했다. 요청은 세 프로세스를 거친다.

```
클라이언트 → Platform APIs + Runtime (참조 구현) → Agent Gateway 모델 경로 → 가짜 모델
             impl/platform_api.py                  impl/gateway/model_route.py   impl/fakes/fake_model.py
```

모든 서비스는 127.0.0.1의 빈 포트에만 바인딩하고, 비밀정보 없이 동작한다.

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

`impl/scenarios/scenarios.json` 하나를 `make scenarios`, 자동 테스트, 시나리오 화면(`impl/demo/`)이 함께 읽는다. 시나리오를 추가하면 세 곳에 동시에 나타난다. 시나리오는 요청과 기대값(상태 코드, 출력, upstream 호출 횟수, 서비스별 감사 기록)을 담는다.

## 아직 하지 않은 것

- 모델 경로는 요청 본문의 identity·policy를 그대로 검사한다. 내부 구간 서명은 S1에서 추가한다.
- upstream timeout은 고정 5초이고, 실패는 모두 503 `UPSTREAM_UNAVAILABLE`이다. timeout·오류 구분은 C1·S2·S3에서 다룬다.
- 도구 경로·Credential Broker·멱등성은 아직 참조 구현의 in-process 코드다.
- `/_audit`, `/_stats`, `/_reset`과 시나리오 화면의 `/api/*`는 로컬 확인용 엔드포인트다. 운영 배포에 두지 않는다.
