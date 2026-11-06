# Agent Tuning (FastTrack)

Agent Tuning은 평가 결과와 실행 추적을 근거로 Agent를 개선하는 Core System이다. FastTrack은 평가 → 개선안 → 재평가 → 승격 후보 등록을 하나의 반복 경로로 묶은 개선 흐름이다.

## 개선 대상

| 대상 | 예 | 산출물 |
|---|---|---|
| 프롬프트·지시문 | 시스템 지시문, few-shot 예시 | 새 Agent 버전(소스 revision) |
| 도구·검색 구성 | 도구 선택, 검색 파라미터 | 새 Agent 버전 또는 Manifest 변경 |
| 모델 선택 | 논리 모델 capability 변경 | Manifest 변경 |
| 모델 미세조정(fine-tuning) | 평가 데이터 기반 모델 조정 | 새 모델 endpoint 등록 |

## FastTrack 흐름

1. 평가 결과·실행 추적에서 개선 대상을 선정한다.
2. 개선안을 개발자 저장소에 새 revision으로 작성한다(Local-First).
3. 배포 전 평가를 실행하고 기존 버전과 비교한다.
4. 기준을 충족하면 Registry에 승격 후보(eligible)로 등록한다.
5. 프로덕션 승인은 [운영·평가](operating-model.md)의 승인 요건을 그대로 따른다.

## 규칙

- Tuning은 승인 절차를 생략해서는 안 된다(MUST NOT). FastTrack은 평가와 등록을 자동화하는 경로이며, 프로덕션 승인 요건을 줄이지 않는다.
- Tuning 결과는 항상 새 불변 버전으로 등록한다(MUST). 기존 버전을 덮어쓰지 않는다.
- 미세조정에 사용하는 데이터는 데이터 분류와 egress 정책을 따른다(MUST). 외부 튜닝 서비스는 Agent Gateway 모델 경로 정책을 적용한다.
- 미세조정으로 만든 모델은 Agent Gateway 모델 경로에 새 endpoint로 등록한 뒤 사용한다(MUST).
- 실행 추적 원문을 학습 데이터로 쓰려면 별도 승인과 보존 정책(TBD-12)이 필요하다.

## 제공 범위

v0.1은 개선 흐름과 규칙을 정의한다. 자동 개선안 생성, 미세조정 파이프라인, 튜닝 인프라 제품은 제공하지 않으며 후속 단계로 구현한다.
