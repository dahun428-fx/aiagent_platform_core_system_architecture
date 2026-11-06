# 운영·셀프서비스·평가

## 역할
Agent owner는 소스·Manifest·평가 dataset·runbook을 소유한다.
Platform owner는 계약·Registry·Agent Platform APIs·Agent Gateway·공통 운영을 소유한다.
Security는 Identity·delegation·data movement·risk policy를 검토한다.
SRE는 실행 target의 가용성·복구 증거를 관리한다. 실제 담당 팀·RACI·연락망은 TBD.

## 수명주기
local experiment → registered → validated → eligible → production-approved → deprecated → retired. 어느 단계에서든 문제가 확인되면 quarantined로 격리한다. 이 목록이 수명주기 상태의 단일 정의다.
실험의 중앙 등록은 선택 가능하나 production 승격에는 immutable version/digest, schema/API conformance,
보안 검토, evaluation result, rollback 증거, 위험별 human approval이 필수다(MUST).
중앙 소스 업로드나 Agent Studio를 강제해서는 안 된다(MUST NOT).
런타임 이미지·의존성·tool descriptor·model routing policy 변경도 재평가 대상으로 포함한다.

## 평가와 관측
평가 결과는 `evaluation.schema.json`에 따라 datasetVersion, agentVersion, manifestDigest, policyVersion, metric, score, threshold, passed, traceId를 포함한다.
deterministic fixture는 smoke regression이며 업무 품질·안전성·통계 유의성을 입증하지 않는다.
회사 metric 목표·threshold·평가 데이터·심사 기준은 TBD.
traceparent/tracestate는 검증 후 hop에 전달하고 span에는 tenant 별칭(`platform.` 접두사), invocation, adapter, policy decision, error category를 기록한다.
prompt·token·retrieved raw PII는 기록하지 않는다. 실제 OpenTelemetry exporter 연동과 retention은 TBD.
한도·latency·cost·tool failures·policy deny·approval backlog·unknown outcomes를 운영 지표로 측정해야 한다(SHOULD).

