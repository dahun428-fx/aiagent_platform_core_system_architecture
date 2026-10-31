# 검증과 배포 패키지

## 재현
README의 의존성을 설치한 뒤 Python unittest, TypeScript typecheck와 client build를 수행한다.
scripts/release.py는 모든 검사 성공 시에만 checksums 및 ZIP을 만든다.
scripts/browser-check.cjs는 Playwright가 설치된 환경에서 file:// 및 network offline 동작을 검사한다.

## 검사 범위
- Draft 2020-12 metaschema와 모든 positive fixture, 네 Agent Manifest, 8개 negative Manifest
- 5개 OpenAPI 3.1.2 문서, 모든 보호 경로 security, request/response examples
- 이전 release snapshot 대비 계약 freeze와 baseline/ADR 추적성
- tenant/권한/분류/credential/승인/idempotency/trace/RAG ACL/Agent cycle 거부
- Python local HTTP 및 TypeScript client 실제 요청/응답
- 문서/포털 local link와 CDN/동적 network asset 미사용
- Playwright desktop/mobile·검색·그림·오프라인 로딩
- ZIP CRC 및 archive 내 manifest SHA256 일치

실제 결과는 [검증 결과](../verification/results.json)와 [브라우저 결과](../verification/browser-results.json)를 확인한다.
[생성·검증 요약](validation-results.md)을 확인한다. ZIP 검증 결과 verification/archive-verification.json은 ZIP 외부에 별도로 제공한다.
브라우저나 도구가 실행되지 않은 검사를 통과했다고 표시해서는 안 된다(MUST NOT).

