# 계약 버전·호환성·마이그레이션

패키지 0.1.0, Manifest apiVersion agent.platform/v1alpha1, HTTP /v1은 별도 축이다.
v1alpha1은 운영 안정성 보증이 아니다. 명시적 회사 채택 전 breaking 변경을 조용히 반영해서는 안 된다(MUST NOT).

## 변경 규칙
required 추가, enum 축소, type/format/pattern 변경, response 필드 제거, auth scope 변경은 breaking으로 검토한다.
optional request 추가도 closed schema를 쓰는 old server에 new client가 보내면 실패할 수 있다.
따라서 additive는 무조건 안전하지 않다. request/response 방향 및 실제 소비자 조합을 CI에서 검증한다.
새 API path/optional response 추가도 소비자 strictness와 보안 의미를 확인한다.

tests/test_contracts.py는 contracts/released/0.1.0.json과 현재 snapshot의 완전 동등성을 gate한다.
이는 보수적인 release freeze 검사이며 범용 semantic diff 도구는 아니다.
변경은 diff 검토·ADR·migration note·새 released snapshot을 승인한 뒤 baseline을 갱신한다.
임의로 snapshot만 덮어써 gate를 통과시키지 않는다(MUST NOT).

## 마이그레이션
새 계약 버전을 병행 배포→소비자 적합성 테스트→등록된 소비자 전환→rollback drill→구버전 종료.
deprecation 기간·회사 toolchain·서명/태그 정책은 TBD.
OpenAPI 3.1.2 pin은 현재 validator로 실제 확인한 선택이며 최신 버전 주장과 무관하다.

