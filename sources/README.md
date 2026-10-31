# 출처와 증거 한계

참조 대화: 구조 심층 조사 / 6ae4235c-04d0-83ee-9457-885d69556f12.
read_thread가 반환한 두 첨부 Pasted text.txt를 변경 없이 보존했다.

- original-research.md: SHA256 fa5dffadd1aa2524f767347e81d2430a6b8446cc604e50831011d444d9418bc7
- verification-research.md: SHA256 635f7f72a03b2555f9b9b0a248fd540555636a907ceb308229ce1d9698e76d51

원 Q1–30의 질문·답변 원문 및 assistant 본문은 도구가 content-reference로만 반환했다.
이 패키지는 원문 Q&A를 보았다고 주장하지 않는다.
두 보고서의 Q1–29 일치 판정과 Q30 명시적 B 답변 정정을 근거로 기준선을 작성했다.
추가 원문이 확보되면 traceability를 재검토해야 한다(SHOULD).
원문의 검색 citation 식별자는 이 ZIP에서 해석되지 않는다. 최신 표준 여부의 증거로 취급하지 않는다.

## 직접 확인한 공식 명세 (2026-10-30)
- OpenAPI 3.1.2: https://spec.openapis.org/oas/v3.1.2.html
- OAuth Token Exchange RFC8693: https://www.rfc-editor.org/rfc/rfc8693.html
- OAuth Security BCP RFC9700: https://www.rfc-editor.org/rfc/rfc9700.html
- Problem Details RFC9457: https://www.rfc-editor.org/rfc/rfc9457.html
- JSON Schema 2020-12: https://json-schema.org/draft/2020-12/schema (메타 검증은 설치된 validator의 로컬 resource로 수행)
- W3C Trace Context: https://www.w3.org/TR/trace-context/

Credential Broker API는 RFC8693 token endpoint 자체가 아니라 플랫폼 내부 mediation 계약이다.
실제 token exchange adapter가 RFC8693 요청·응답으로 변환해야 한다.

