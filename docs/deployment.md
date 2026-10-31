# 배포 프로파일과 환경 승격

| 프로파일 | 실행 위치 | 허용 목적 | production 전제 |
|---|---|---|---|
| local | 개발자 장비 | 계약 검증·합성 데이터 실험 | production 승인 아님 |
| shared-experiment | 등록된 사내/클라우드 자원 TBD | 통합·평가 | tenant 격리·quota·감사 |
| production | 승인된 hybrid target TBD | 실제 업무 traffic | 보안·평가·복구·위험별 SLO 증거 |

Shared Control Plane은 등록·정책·신원·평가·관측을 통제한다.
분산 target은 workload identity와 outbound trust channel로 연결한다.
실제 ingress/egress·망분리·방화벽·private connectivity·배치 수량은 TBD.
HA, queue, DB, object store, secret store, scheduler 제품은 TBD. Backend.AI는 Out of Scope.
Model serving은 외부 API/자체 호스팅 endpoint adapter를 사용하며 내부 GPU scheduler는 향후 TBD.
등록된 환경은 즉시 production-approved가 되지 않는다.
Control Plane 단절 시 신규 권한·승격을 중단하고, 실행 중 작업 처리 방식은 승인된 policy snapshot과 만료를 따른다.

