# Changelog

패키지 버전, 계약 버전, 포함 기능, 검증 방법을 기록한다. 배포 ZIP은 `scripts/release.py`가 만들며, 생성 commit은 `verification/results.json`의 `source.commit`에 남는다. 아래 "배포 산출물"이 비어 있는 항목은 아직 해당 버전의 ZIP이 생성되지 않은 상태다.

| 패키지 | 계약 | 주요 내용 | 검증 | 배포 산출물 |
|---|---|---|---|---|
| 0.1.0 | 0.1.0 | 기준선 Q1–Q30, ADR-001~030, 계약 23 schema·5 OpenAPI, Python mock, TypeScript client, 오프라인 포털 | release.py(테스트·TypeScript·HTTP smoke·브라우저 오프라인·ZIP) | `dist/enterprise-ai-agent-platform-v0.1.zip` (2026-10-30 생성) |
| 0.1.1 (main) | 0.1.1 | 개발자 가이드 14장, Core Systems(ADR-031~037, Q31–Q37), 보안 결함 수정, 안전한 패키징, 내 Agent 연결 키트(adapter·로컬 Registry·적합성 11항목·템플릿 2종), Manifest scope·mode 집행 | CI: Python 테스트(Ubuntu·Windows), 포털 drift, TypeScript typecheck·build, Python↔TypeScript HTTP smoke | 미생성. Mac에서 `scripts/release.py` 실행 후 태그 `v0.1.1` → `dist/enterprise-ai-agent-platform-v0.1.1.zip` |

## 0.1.1

- 계약: Manifest `capabilities.type`에 `message` 추가(`contracts/released/0.1.1.json`).
- 실행: Manifest `identity.requiredScopes`·`identity.mode`를 실행에 반영. 호출자가 데이터 분류를 낮출 수 없음. 도구 재시도 digest를 인자·대상으로 한정.
- 개발 키트: `AgentAdapter`/`AgentContext`, 로컬 Registry(`--agents-dir`), `agentctl run`·`conformance`, `templates/agents/{message,tool}`.
- 배포: Git 추적 파일 기준 패키징, 민감 파일 포함 시 실패, POSIX 경로·LF 고정. 산출물 이름(ZIP, ZIP 최상위 폴더, sidecar, `verification/archive-verification-v<버전>.json`)을 `package.json` 버전에서 파생해 0.1.0 ZIP을 덮어쓰지 않음. 생성 전에 추적 파일 변경이 있으면 거부(`--allow-dirty`는 시험 실행용)하고, 생성 중 산출물 외 파일이 바뀌면 실패. source commit과 lockfile SHA256을 생성 전 상태로 기록.
- 문서: Core Systems 기술 표준 7종, 개발자 가이드 14장, 근거와 참고 자료.
- 한계: in-process adapter는 격리 경계가 아니며 `timeoutMs`가 적용되지 않음. Memory·Guardrails·Agent Card·Tuning은 목표 규칙.
