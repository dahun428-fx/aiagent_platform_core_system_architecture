# 실제 생성·검증 결과

기준일: 2026-10-30 / Asia/Seoul. 패키지 0.1.0.
회사 제품·환경·운영 수치는 TBD로 유지했다.

## 생성 산출물
- 요구사항 v0.1: Q1–30 결정 표와 Q→ADR→산출물 추적.
- ADR 30건: 각 문서에 Context, Decision, Alternatives, Consequences, Constraints, Contracts, Security, Migration.
- 계약: JSON Schema 23종, OpenAPI 3.1.2 5종.
- Fixture: 4종 Agent Manifest, 8개 음성 Manifest, 공통/기능별 양성 예제.
- 도식: C4 context/container/component, invocation/model/tool-credential sequence, security boundaries, deployment, MVP 총 9종. Mermaid와 오프라인 SVG.
- 예제: Python 공통 Runtime 및 local Gateway/Model/Tool/Broker mock, CLI Manifest 검증, Python/TypeScript HTTP client.
- 포털: 모듈별 HTML, 로컬 검색·탐색, 모바일 메뉴, 외부 network asset 미사용.
- 배포: source + static HTML + fixtures + tests + 실행 로그 + SHA256 manifest + ZIP.

## 실행 결과를 확인하는 법
[전체 실행 기록](../verification/results.json)의 status가 passed이고 모든 exitCode가 0이어야 한다.
Contract/Runtime/CLI 단위 테스트의 정확한 개수와 실행 로그, TypeScript typecheck·build 결과,
Python 및 TypeScript 클라이언트가 반환한 실제 HTTP response를 기록한다.
[브라우저 결과](../verification/browser-results.json)는 Chromium file:// + offline 모드에서 10개 검사를 수행한다.
ZIP 외부의 verification/archive-verification-v<버전>.json은 ZIP CRC·모든 파일의 SHA256·entry count·압축 내 HTML 링크를 확인한다.
ZIP 자체의 SHA256은 dist/enterprise-ai-agent-platform-v<버전>.zip.sha256에 제공한다. 산출물 이름은 package.json 버전에서 파생하며, 0.1.0 산출물(enterprise-ai-agent-platform-v0.1.zip, archive-verification.json)은 그대로 보존한다.

## 발견·수정한 문제
- Q30을 추론으로 기록한 원문 오류를 Decided로 정정.
- Tool Gateway/Agent Tools, Credential Broker/Agent Identity의 소속과 보안 경계를 보완.
- URI format 검사 의존성 누락 및 validator 버전 충돌을 해결.
- Broker의 고정 trace 사용을 재현한 테스트 후 실제 호출 trace 전달로 수정.
- 로컬 검색 데이터의 출처 URL을 network 호출로 오인한 테스트를 수정.
- C4 SVG에서 가로 연결이 중간 노드 호출처럼 보이던 선 배치를 수정.

## 판단 범위
실제로 검증한 것은 표준 계약, 합성 fixture, 로컬 mock과 정적 포털이다.
실제 회사 서비스 통합·production durable 실행·기업용 보안 인증·업무 품질 평가·부하/복구 검증은 완료했다고 주장하지 않는다.
원 Q&A 본문은 reference 도구가 반환하지 않아 두 첨부 보고서로 기준선을 재구성했다.

