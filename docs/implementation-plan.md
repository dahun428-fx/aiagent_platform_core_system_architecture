# 전사 AI Agent Platform Implementation Plan

> 실행 방식: 현재 세션에서 순차 구현한다. 기존 확정 질문과 두 보고서를 기준으로 하며 새 회사 제품·수치를 선정하지 않는다.

**Goal:** 구현 착수 가능한 v0.1 기술 표준과 검증 가능한 로컬 예제를 실제 파일로 제공한다.
**Architecture:** 공통 Control Plane과 분산 Execution Plane. Agent Tools 아래 Tool Gateway, Agent Identity 아래 Credential Broker.
**Tech Stack:** JSON Schema 2020-12, OpenAPI 3.1.2 JSON, Python, TypeScript, HTML/CSS/JS.
**Spec:** requirements/baseline-v0.1.md 및 원문 보고서 sources/.

## 제약과 검토 초점
- 회사 환경, 제품, SLO·용량·비용·보존 기간은 TBD.
- Q30은 Decided이며 원본 Q&A 대화 본문은 참조 시스템에서 반환되지 않아 두 보고서의 공통 기준선을 사용한다.
- 위조 tenant/권한, 과도한 credential audience, 승인 재사용, idempotency 충돌, 오프라인 링크를 중점 검증한다.
- 실제 IdP·secret store·durable engine·exporter 통합은 회사 결정 후 구현한다. 참조 구현을 production 보안 구현으로 오인하지 않게 한다.

## 순차 작업
- [x] 1. sources 보존, Q30 정정, baseline 30행과 ADR 30건 생성. Q→ADR→파일 링크 점검.
- [x] 2. C4·배포·MVP·호출·모델·도구/credential·보안 경계 제작. 논리 책임과 trust boundary 교차 점검.
- [x] 3. Manifest 및 공통/기능 schema, API 5종, positive 4종·negative fixtures 제작. metaschema·OpenAPI·예제 검증.
- [x] 4. 보안 거부·재시도·trace·모델 정책·평가 테스트 작성 후 실행 실패 확인. Python local HTTP mock 및 TypeScript client 구현 후 재실행.
- [x] 5. 정적 페이지·검색·SVG 렌더링 제작. file:// 링크와 브라우저 오프라인 동작 검증.
- [x] 6. 계약 호환성·전체 검증·SHA256·ZIP 생성 및 압축 해제 내용 검증. 실제 결과와 제한 사항 기록.

## 검증 명령
설치 및 실행은 README의 명령을 사용한다. 모든 테스트와 타입 검사가 성공한 경우에만 release 검증 결과를 성공으로 기록한다.

