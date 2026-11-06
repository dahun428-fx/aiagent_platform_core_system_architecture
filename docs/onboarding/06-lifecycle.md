# 내 Agent가 production까지 가는 길

> 온보딩 안내서입니다. 규범은 [운영·평가](../operating-model.md), [배포 프로파일](../deployment.md), [Durable / HITL](../execution.md) 원문이 기준입니다.

## 개발은 지금처럼 한다 (Local-First, CLI-First)

이 플랫폼은 개발 방식을 바꾸라고 하지 않습니다. 소스는 팀의 Git 저장소에 두고, 평소 쓰는 IDE와 CLI로 개발하고, 로컬에서 실험합니다. 중앙 소스 업로드나 Agent Studio 사용은 강제하지 않습니다(MUST NOT). 플랫폼은 그 대신 계약 기반 SDK, CLI, 템플릿을 제공합니다.

실험 단계에서 중앙에 등록하는 것은 선택입니다. 등록이 필요해지는 것은 **다른 사람과 같이 시험하거나 production에 올릴 때**입니다.

![Local-First MVP 흐름](../../diagrams/mvp.svg)

## 수명주기: 일곱 단계

```text
local experiment → registered → validated → eligible → production-approved → deprecated → retired
```

| 단계 | 뜻 |
|---|---|
| local experiment | 내 PC에서 만들고 시험하는 중 |
| registered | Registry에 불변 버전(Git revision, artifact digest)과 Manifest가 등록됨 |
| validated | 스키마·API 계약 검증을 통과함 |
| eligible | 평가와 검토를 거쳐 승격 후보가 됨 |
| production-approved | production 통제가 검증되어 실제 업무 트래픽을 받아도 됨 |
| deprecated | 새로 쓰지 말라고 안내하는 중 |
| retired | 더 이상 실행하지 않음 |

Registry에는 이와 별도로 문제가 생긴 버전을 막아 두는 **격리(quarantined)** 상태도 있습니다.

## production에 오르려면 필요한 증거

production 승격에는 다음이 모두 필요합니다(MUST).

1. **불변 버전과 digest**: 무엇을 올리는지 바뀌지 않게 고정
2. **스키마·API 적합성**: Manifest와 계약 검증 통과
3. **보안 검토**: 신원, 위임, 데이터 이동 검토
4. **평가 결과**: 데이터셋 버전, Agent 버전, Manifest digest, 정책 버전, 지표, 통과 기준, traceId가 묶인 결과
5. **롤백 증거**: 문제가 생기면 되돌릴 수 있다는 증거
6. **위험도별 사람 승인**: 위험이 높을수록 사람의 승인이 필요

코드만이 아니라 런타임 이미지, 의존성, 도구 설명, 모델 routing 정책이 바뀌어도 다시 평가합니다.

평가는 셀프서비스가 기본입니다. 자동 검사를 통과하면 스스로 진행하고, 위험이 높은 경우에만 사람 승인이 들어갑니다.

## 어디서 실행하나: 배포 프로파일 세 가지

| 프로파일 | 어디서 | 무엇을 위해 | 조건 |
|---|---|---|---|
| `local` | 개발자 장비 | 계약 검증, 합성 데이터 실험 | production 승인 아님 |
| `shared-experiment` | 등록된 사내·클라우드 자원 | 통합 시험, 평가 | 테넌트 격리, 사용량 한도, 감사 |
| `production` | 승인된 hybrid 실행 환경 | 실제 업무 트래픽 | 보안·평가·복구·위험별 SLO 증거 |

다시 강조하면 **등록된 환경이 곧 production 승인 환경은 아닙니다.** 개발자 PC나 Mac mini를 실수로 production처럼 쓰게 되는 것이 이 설계가 경계하는 위험 중 하나입니다.

## 오래 걸리는 일과 사람 승인 (Durable, HITL)

workflow Agent는 몇 분, 몇 시간이 걸리거나 중간에 사람 승인을 기다릴 수 있습니다. 그래서 실행에는 상태가 있습니다.

```text
accepted → running → succeeded | failed | waiting_approval | cancel_requested
waiting_approval → running(승인 및 재인가) | rejected | expired | cancelled
cancel_requested → cancelled 또는 이미 끝난 succeeded/failed
```

- 끝난 상태(terminal)는 덮어쓰지 않습니다.
- 취소는 최선의 노력(best effort)이고, 이미 일어난 부작용을 되돌려 주지는 않습니다.
- 승인을 받고 재개할 때는 승인 대상 digest, 테넌트, 정책 버전, 만료, 취소 여부를 모두 다시 확인합니다.

durable 실행 엔진(체크포인트 저장소, 큐, 스케줄러) 제품은 아직 정하지 않았습니다(TBD). 이 패키지에는 계약만 있습니다.

## 처음 만드는 것: 한 줄로 이어진 경로

플랫폼은 모든 모듈을 한꺼번에 만들지 않습니다. 먼저 아래 경로 하나를 끝에서 끝까지 실제로 동작하게 만들고, 도구·RAG·durable 실행·Multi-Agent·분산 실행 환경을 그 위에 단계적으로 붙입니다.

```text
로컬 Agent → Manifest 검증 → 인증된 Agent Gateway 호출 → 신원·정책 확인
→ Runtime adapter → Model Gateway → 외부 또는 자체 호스팅 모델
→ trace 기록 → 평가 결과 → Registry 기록 → CI 품질 게이트 → 승인된 실행 환경
```

## 품질 게이트는 CI에서

계약 검증은 문서가 아니라 코드로 강제합니다(Contract-as-Code). CI에서 검사가 하나라도 실패하면 결과물 업로드와 승격을 막습니다(MUST). 이 패키지는 `scripts/release.py` 하나로 포털 생성, 계약·런타임 테스트, TypeScript 검사, 클라이언트 smoke 테스트, 브라우저 오프라인 검사를 돌립니다. 회사 CI 제품은 TBD입니다.

## 더 읽을거리

- 수명주기와 평가 원문: [운영·평가](../operating-model.md)
- 배포 프로파일 원문: [배포 프로파일](../deployment.md)
- 상태 전이와 승인 원문: [Durable / HITL](../execution.md)
- CI 연결 방법: [CI 통합](../ci-integration.md)

이전: [네 종류 Agent와 Manifest](05-agents-and-manifest.md) · 다음: [30분 실습](07-hands-on.md)
