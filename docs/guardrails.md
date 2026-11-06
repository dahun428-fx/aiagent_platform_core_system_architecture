# Guardrails

Guardrail은 Agent의 입력·출력·도구 결과·검색 결과·실행 동작이 정책을 벗어나지 않도록 검사하고 차단하는 통제다. 공통 검사 서비스 하나와 네 개의 집행 지점으로 구성한다.

## 구성

- **공통 검사 서비스**: Shared Control Plane에 두며 프롬프트 인젝션, 민감정보(PII), 유해 콘텐츠, 출력 형식, 근거성 검사를 제공한다. 검사 결과(판정, 정책 버전, 검사 ID)만 반환한다.
- **집행 지점(Policy Enforcement Point)**: 검사 결과에 따라 차단·수정·통과를 결정한다. 검사 서비스는 차단을 수행하지 않는다.

| 집행 지점 | 검사 대상 | 집행 Core System |
|---|---|---|
| ① 모델 입력·출력 | 프롬프트 인젝션, PII, 유해 콘텐츠, 출력 형식 | Agent Gateway 모델 경로 |
| ② 도구 호출·결과 | 호출 인자 검증, 도구 결과의 간접 인젝션·민감정보 | Agent Gateway 도구 경로 |
| ③ 검색 결과 | 검색 문서의 간접 인젝션, ACL·분류 필터, 근거성 | Knowledge(RAG) 단계 |
| ④ 실행 제어 | 권한 최소화, 고위험 작업의 사람 승인 | Agent Runtime |

## 규칙

- 네 집행 지점은 모두 적용해야 한다(MUST). 하나의 지점으로 다른 지점을 대체할 수 없다.
- ①은 사용자 메시지뿐 아니라 모델에 전달되는 도구 결과·검색 문서·Memory 내용도 검사 대상에 포함해야 한다(MUST).
- 검사 서비스 장애 시 집행 지점은 위험도에 따라 차단(fail closed)해야 한다(MUST). 저위험 경로의 통과 허용 여부는 회사 정책 TBD-03이다.
- 검사 결과(판정, 정책 버전, 검사 ID)는 실행 추적에 기록하고, 검사 대상 원문은 기록하지 않는다(MUST NOT).
- 검사 모드는 "검사만(기록)"과 "검사 후 차단"을 구분한다. 프로덕션 환경의 ①②③은 "검사 후 차단"이어야 한다(MUST).
- 인코딩(예: Base64)으로 우회하는 입력을 고려해 정규화 후 검사해야 한다(SHOULD).
- 검사 제품은 adapter로 연결하며 특정 제품을 강제하지 않는다. 제품 선정은 TBD이다.
- Guardrail은 위험 감소 통제이며 완전한 방어를 보장하지 않는다. 권한 교집합, 자격증명 비노출, 사람 승인과 함께 적용한다.

## 근거

- NVIDIA NeMo Guardrails는 input, retrieval, dialog, execution(도구 호출·결과), output rail을 처리 단계별로 구분한다.
- Kong AI Gateway는 모델 요청·응답에 프롬프트 가드와 PII 제거를 적용하지만, AI Prompt Guard는 `user` 역할 메시지만 검사한다. 관문 단일 검사로는 간접 인젝션을 놓칠 수 있다는 근거다.
- AWS Bedrock Guardrails의 `ApplyGuardrail`은 모델 호출 없이 독립 호출할 수 있다.
- Azure Prompt Shields는 사용자 입력과 도구 응답 지점을 검사하며, API 자체는 차단하지 않는다.
- Google Model Armor는 프롬프트와 응답을 검사하고, 차단은 Policy Enforcement Point의 책임으로 둔다.
- OWASP LLM01:2025는 입출력 필터링, 코드 수준 권한 제어, 고위험 작업의 사람 승인을 함께 권고한다.
- 출처 목록: [근거와 참고 자료](onboarding/10-references.md)
