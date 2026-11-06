# 전사 공통 AI Agent Platform — v0.1

구현 착수를 위한 기술 표준 패키지. [오프라인 포털](portal/index.html)을 브라우저에서 열면 전체 문서·계약·ADR을 탐색할 수 있다.

## 시작
처음이라면 [개발자 가이드](docs/onboarding/01-why.md)의 학습 경로를 따른다. 포털 첫 화면도 같은 순서로 안내한다.

1. docs/core-systems.md에서 10개 Core System과 구현 상태를 확인한다.
2. docs/architecture.md, docs/agent-tools.md, docs/identity-and-credentials.md, docs/guardrails.md로 책임·신뢰 경계를 확인한다.
3. 결정 근거는 docs/requirements/baseline-v0.1.md(Q1–Q36)와 adr/에서 확인한다.
4. contracts/의 OpenAPI 3.1.2 JSON과 JSON Schema 2020-12를 소비한다.
5. 예제를 실행하고 tests/로 계약 적합성을 확인한다.
6. docs/tbd-register.md의 회사별 결정을 완료하고 production 통합·부하·보안 검증을 수행한다.

버전별 포함 기능과 검증 방법은 [CHANGELOG](CHANGELOG.md)를 따른다.

## 빠른 시작 (최소 경로)
Python 3.11+만으로 첫 호출과 실패 응답까지 확인한다. 상세 설명과 문제 해결은 [로컬 환경 구성 및 호출 실습](docs/onboarding/07-hands-on.md)을 따른다.

```sh
git clone https://github.com/dahun428-fx/aiagent_platform_core_system_architecture.git
cd aiagent_platform_core_system_architecture
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests
.venv/bin/python examples/python/platform_ref.py   # 터미널 1
.venv/bin/python examples/python/client.py         # 터미널 2: "status": "succeeded"
```

검증 환경: macOS·Linux(Python 3.11+), Windows 11(Python 3.12, PowerShell). Windows는 `.venv\Scripts\python`을 사용한다.

## 로컬 검증
Python 3.11+와 Node.js 22+, TypeScript compiler가 필요하다. 최초 개발 의존성 설치에는 네트워크가 필요하다.
포털 열람에는 설치·서버·인터넷이 필요 없다. 완전 오프라인 재검증용 dependency wheel/npm bundle은 포함하지 않는다.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/agentctl.py validate examples/manifests/*.json
npm install
npx playwright install chromium
npm run typecheck
npm run build:client
.venv/bin/python examples/python/platform_ref.py
```

별도 터미널:
```sh
node examples/typescript/dist/demo.js
```

서버는 loopback에만 바인딩하며 합성 mock token만 받는다. 회사 IdP·실제 secret·외부 모델에 접속하지 않는다.
Python SDK 호출 예제: `python3 examples/python/client.py`.
전체 검증·체크섬·ZIP: `.venv/bin/python scripts/release.py`.
포털 재생성만 수행: `.venv/bin/python scripts/build_portal.py --write`.
결과는 verification/, 배포 ZIP은 dist/에 생성된다.
실행 검증 요약은 docs/validation-results.md에서 확인한다.

## 구성
- docs/ · adr/: 한국어 규범 문서, baseline 30항목, ADR 30건
- contracts/: Manifest·identity·policy·runtime·tool·credential·RAG·approval·evaluation·cross-Agent 및 API 5종
- examples/: 4종 Manifest, Python mock vertical slice, TypeScript HTTP client
- tests/: schema·API·권한·idempotency·승인·모델 정책·평가·포털 정합성
- portal/ · diagrams/: file:// 정적 HTML, 로컬 검색, Mermaid source와 SVG
- sources/: 두 Deep Research 원문 및 출처 한계
- verification/ · dist/: 실제 실행 결과·SHA256·ZIP

회사 제품, topology별 주소·수량, NFR·비용·용량·보존 수치는 모두 TBD.
127.0.0.1:8765, fixture의 TTL·depth·평가값은 합성 예제 값이며 회사 표준 수치가 아니다.

이 저장소의 main이 최신 표준이다. `dist/`의 ZIP과 `checksums.sha256`은 `scripts/release.py`를 실행한 시점의 스냅샷이며, 생성 commit은 `verification/results.json`과 `verification/archive-verification-v<버전>.json`의 `source.commit`에 기록된다. commit이 HEAD와 다르면 ZIP은 과거 스냅샷이다. ZIP 이름은 `package.json` 버전을 따르며(`dist/enterprise-ai-agent-platform-v<버전>.zip`), `release.py`는 추적 파일에 커밋하지 않은 변경이 있으면 실행을 거부한다.
production 구현과 검증의 잔여 범위는 docs/release-scope.md에 명시한다.

