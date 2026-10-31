# Agent Identity와 Credential Broker

Agent Identity는 user identity, Agent/workload identity, delegation context와 credential mediation의 논리 domain이다.
Credential Broker는 그 내부의 고신뢰 서비스다. token store/IdP/STS 제품은 TBD.

## 신원 계약과 인증
외부 bearer는 issuer·audience·signature·expiry·not-before·revocation 정책을 검증해야 한다(MUST).
client의 tenant/subject/role header는 신뢰하지 않는다. workload identity는 사용자 identity와 별도 기록한다.
delegated 모드는 principal과 non-empty delegation chain을 요구한다. independent는 workload 권한만 사용하고 사용자로 가장하지 않는다.
각 hop의 actor/subject/audience/scopes를 검증하고 유효 권한은 모든 grant의 교집합을 넘을 수 없다.
하위 Agent 호출 시 scope 축소·새 audience·parentInvocationId·depth/budget을 재검증한다.

## Broker API와 비노출
POST /v1/credential-leases는 내부 Tool Gateway workload만 호출한다.
요청에는 identity, toolId/version, resource, scopes, policyDecisionId, invocationId, approvalId(필요시)를 담는다.
Broker는 서명된 policy evidence를 권한 저장소에서 다시 확인한다. caller가 보낸 decisionId만으로 발급하지 않는다.
응답은 credentialRef, audience, scopes, expiresAt, nonExportable=true의 opaque lease다.
lease는 호출 tenant·workload·tool·invocation에 결합되어야 하며 단일 adapter 경계에서만 소비된다.
TTL은 단기여야 하고 grant/approval 만료보다 길 수 없다. 실제 수치는 TBD.
GET token endpoint를 Runtime/LLM에 제공하지 않는다. consume/revoke는 내부 adapter API로 보호한다.
lease 취소는 upstream grant/token 취소를 함께 시도하되 이미 나간 요청의 부작용은 rollback되지 않는다.

## RFC8693 mapping
이 API는 OAuth token endpoint와 동일한 wire 계약이 아니다.
adapter는 grant_type=urn:ietf:params:oauth:grant-type:token-exchange, subject_token, subject_token_type, resource 또는 audience, scope를 구성한다.
actor_token이 필요한 IdP는 workload actor를 별도 검증한다. token passthrough나 audience 없는 재사용은 금지한다.
unsupported exchange는 장기 공유 secret fallback 대신 거부한다. RFC9700 기반 audience 제한·sender constraint 지원을 검토한다.

## 장애와 감사
IdP/Broker/정책 조회 실패 시 credential 신규 발급은 fail closed한다.
refresh·revocation·key rotation·clock skew·cache TTL의 회사 정책은 TBD다.
로그에는 credentialRef의 비가역 correlation만 기록하고 bearer·refresh token·secret·raw credentialRef를 남기지 않는다.
실제 IdP·mTLS·KMS 연동은 제공하지 않는다. Python Broker는 정책·expiry·binding 거부를 보여주는 mock이다.

