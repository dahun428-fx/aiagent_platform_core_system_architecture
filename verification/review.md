# 검토 및 수정 기록

코드·계약·문서 자체 검토이며 독립된 회사 보안 승인이나 production 인증은 아니다.

- Correctness: metaschema와 API examples 및 모든 fixture를 검증. URI format optional dependency 누락을 발견해 jsonschema[format-nongpl]로 수정.
- Trace: Broker가 고정 fixture trace를 쓰는 오류를 별도 실패 테스트로 재현 후 호출 trace를 전달하도록 수정.
- Offline: 검색 인덱스에 포함된 출처 URL을 network 호출로 오인하던 검사를 실행 JS와 데이터 JSON 검증으로 분리.
- Architecture: Agent Tools/Identity 소속, 계약/구현 경계, registry와 production-approved 구분을 점검.
- Security: 위조 tenant·scope 초과·lease binding/만료·approval replay·데이터 분류 route를 거부하는 테스트 실행.
- Presentation: 가로로 여러 노드를 가로지르는 C4 화살표를 우회 배치해 중간 노드가 호출자인 것처럼 보이는 문제를 수정.
- Dependencies: 시스템 Python의 macOS 탐지 오류를 피해 번들 Python 3.12.14에서 검증. Validator 호환성에 맞춰 jsonschema 4.24.0 pin. npm lock 및 감사 결과에 발견된 취약점 없음.
- Limitations: 실제 IdP/STS, network adapter, durable store, business evaluation은 미구현이며 회사 결정과 검증이 필요.

최종 통과 여부와 실제 실행 명령은 results.json, browser-results.json 및 archive-verification.json을 따른다.
