# 보안 경계와 위협 모델

| 경계 / 위협 | 필수 통제 | 검증 증거 | 잔여 구현 |
|---|---|---|---|
| Client→Agent Gateway: identity/tenant 위조 | 검증 token에서 신원 파생, body 비교, deny by default | spoof/missing auth tests | 실제 JWKS·issuer·audience·revocation TBD |
| Runtime→Tools: confused deputy·prompt injection | 논리 tool ID, scope 교집합, output 비신뢰, 정책 재검증 | scope/tenant/write denial | adapter egress allowlist TBD |
| Tools→Broker: credential 유출 | audience 제한, expiry·binding, 비노출 handle | lease binding/expiry tests | STS·mTLS·KMS TBD |
| Registry/Control Plane: 공급망 오염 | immutable digest, owner review, signed artifact, provenance | Manifest schema + promotion gate | 서명 인프라 TBD |
| RAG→model: ACL 누출 | 검색 시 ACL·분류 filter, citation 후에도 output 검사 | retrieval tenant/ACL tests | 회사 검색 backend TBD |
| Model Gateway→external: 분류 우회 | confidential/restricted 외부 route deny, 안전 route 없으면 실패 | routing tests | 지역·국경 정책 TBD |
| Agent→Agent: 권한 확산·cycle | scope 축소, audience 재검증, depth/budget/cycle 제어 | cross-agent tests | adapter/A2A version TBD |
| Retry/resume: 승인 replay·중복 write | digest/expiry/policy 확인, request key 충돌, unknown outcome | replay/idempotency tests | persistent effect ledger TBD |
| Trace/audit: 정보 유출 | allowlist metadata, token/PII redaction, 접근통제 | redaction tests | exporter·retention TBD |
| 제어-plane 장애 | 신규 권한/승격 fail closed, 캐시된 권한은 승인된 TTL 범위 | mock fail-closed tests | 장애·복구 drill TBD |

## 배포 전 기준
TLS·workload 인증·network policy·secret rotation·audit tamper resistance는 MUST다.
모든 tenant scoped lookup에는 tenant 조건이 포함되어야 한다. invocation ID만으로 poll/cancel/events를 허용하지 않는다.
raw prompt/output 로깅은 기본 비활성화한다. 민감정보 평가·삭제·보존 절차는 회사 정책 TBD다.
CORS·rate limiting·body size·timeout·egress quotas는 위험별 policy로 적용한다. 수치는 TBD.
Python 예제는 합성 bearer가 고정 매핑된 로컬 mock이며 JWT 검증 제품이 아니다.

