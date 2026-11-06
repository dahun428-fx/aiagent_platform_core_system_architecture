# 제공 범위와 구현 한계

## 이 패키지가 제공하는 것
요구사항 v0.1, 36개 규범 ADR(보강 결정 ADR-031~036 포함), 아키텍처 원문/시각화, 기능별 machine-readable 계약,
4종 Agent Manifest와 양성/음성 fixture, 실행 가능한 Python 로컬 HTTP mock,
TypeScript client/typecheck, 계약/보안/통합 smoke tests, 모듈형 오프라인 HTML과 검증/ZIP 도구를 제공한다.

## 실제 실행과 설계의 경계
Python mock은 Agent Platform APIs(Agent 호출 API)→Runtime→Agent Gateway 모델 경로 및 도구 경로→Credential Broker의 동기 흐름을 실행한다. 출력과 감사 기록의 `agent-gateway`, `model-gateway`, `tool-gateway`는 legacy component 이름이다.
mock 한계: 데이터 분류는 정책 값보다 낮출 수 없지만 실제 데이터 원천 분류는 없다. retrieval helper는 `agents.invoke` scope로 인가하고, 위임 체인의 마지막이 상위 Agent인지 검증하지 않으며, 멱등성 메모리는 크기 제한이 없다.
RAG ACL filtering·cross-Agent envelope validation·approval verifier는 deterministic helper로 검증한다.
실제 외부 상용/자체호스팅 모델, REST/MCP tool server, IdP/STS, workflow engine, vector DB, OTel collector에는 연결하지 않는다.
HTTP API 문서는 목표 인터페이스다. mock은 Agent invoke / health만 구현하며 나머지는 명시적으로 501을 반환한다.
4종 Manifest가 있다는 사실은 4종 production engine의 구현 완료를 뜻하지 않는다.
메모리 idempotency는 재시작/다중 worker에 안전하지 않다.
mock lease는 외부 credential이 아니며 실전 cryptography·federation·persistency를 제공하지 않는다.
프로덕션 TLS, quota, audit store, queue, retry ledger, approval service, artifact signature는 회사 결정 후 구현해야 한다.

## 검증 주장
verification/results.json의 각 검사는 실행된 도구·exit code·출력을 기록한다.
표준 검증은 machine-readable 문법·fixture·예제·명시된 거부 동작의 범위이며 production 보안 인증이 아니다.
브라우저 오프라인 검증과 ZIP 무결성은 별도 결과에 기록한다.
의존성은 requirements-dev.txt/package.json으로 고정하며 최초 설치에는 인터넷이 필요하다.

