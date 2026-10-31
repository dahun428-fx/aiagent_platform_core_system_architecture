# 실행·Durable·HITL

## 상태 전이
accepted → running → succeeded | failed | waiting_approval | cancel_requested.
waiting_approval → running(유효 승인 및 재인가) | rejected | expired | cancelled.
cancel_requested → cancelled 또는 이미 commit된 succeeded/failed.
terminal 상태는 실행 결과를 덮어쓰지 않는다(MUST). cancellation은 best effort이며 부작용 rollback 보장이 아니다.

## Contract
execution.schema.json은 invocationId, revision, state, checkpointRef, pendingEffectId를 정의한다.
revision 기반 compare-and-swap으로 동시 재개·중복 worker를 방지한다.
checkpoint는 tenant scoped storage에 암호화하고 manifest digest·adapter version·policy version에 결합한다.
checkpointRef와 event payload에는 secret을 넣지 않는다. 저장·복구·보존 수치는 TBD.
retry 예산·backoff·deadline은 policy에서 결정한다. write의 unknown_outcome은 자동 재실행하지 않는다.
events는 단조 sequence와 invocationId로 중복 제거하고 polling cursor 이후의 이벤트를 요청한다.

## Approval
approval은 tenant·invocationId·subjectDigest·policyVersion·reviewer·expiry·decision에 결합한다.
subjectDigest는 승인 대상 canonical request + tool/model/Agent version + destination을 포함해야 한다.
단순 approved=true를 신뢰해서는 안 된다. 재개 시 digest·tenant·policy version·expiry·revocation을 모두 다시 확인한다.
승인자 역할과 요청자 분리 수준은 위험 정책 TBD. 승인 이벤트는 append-only audit로 기록한다.
정책 변경·요청 변경·승인 만료·취소 후 재승인은 새 evidence를 요구한다.

## 참조 범위
Python 예제는 sync flow, 메모리 idempotency, approval verifier와 fail-closed 정책을 실행한다.
process restart를 견디는 checkpoint store, queue, scheduler, transactional outbox, 실제 workflow resume는 구현하지 않는다.
durable HTTP 경로는 계약만 제공하며 mock에서는 501이다. production durable engine 선정은 TBD.

