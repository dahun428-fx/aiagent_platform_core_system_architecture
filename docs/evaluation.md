# Evaluation

Agent Evaluation은 Agent의 품질과 안전성을 측정하고 승격 판단의 근거를 제공하는 Core System이다.

## 평가 3단계

| 단계 | 시점 | 목적 | 입력 |
|---|---|---|---|
| 배포 전 평가 | CI·승격 전 | 품질·안전성 기준 충족 확인 | 평가 데이터셋, 평가 프로파일 |
| 실행 추적 분석 | 실행 후 | 개별 실행의 처리 경로와 실패 원인 분석 | 실행 추적, 감사 기록 |
| 운영 모니터링 | 프로덕션 운영 중 | 품질·안전성·비용 추세와 회귀 감지 | 운영 지표, 표본 평가 |

## 평가 항목

- **품질**: 과제 완료, 응답 정확성, 근거성(RAG), 도구 사용 정확성.
- **안전성**: 프롬프트 인젝션 저항, 민감정보 노출, 유해 콘텐츠, 권한 외 도구 호출 시도.
- **운영**: 지연 시간, 비용, 오류율.
- 안전성 평가에는 공격 시나리오 기반 평가(red teaming)를 포함해야 한다(SHOULD). 위험도 high Agent는 프로덕션 승인 전에 포함해야 한다(MUST).

## 평가 결과

- 평가 결과는 `evaluation.schema.json`을 따르며 datasetVersion, agentVersion, manifestDigest, policyVersion, metric, score, threshold, passed, traceId를 포함해야 한다(MUST).
- 평가 결과는 Registry에 Agent 버전과 함께 저장하고, 프로덕션 승인 요건으로 사용한다([운영·평가](operating-model.md)).
- 지표 목표, threshold, 평가 데이터셋, 심사 기준은 TBD-12이다.
- 이 패키지의 deterministic fixture는 smoke regression이며 업무 품질·안전성·통계적 유의성을 입증하지 않는다.

## Agent Tuning과의 관계

평가 결과와 실행 추적은 [Agent Tuning](agent-tuning.md)의 입력이다. Tuning으로 만든 변경은 다시 배포 전 평가를 통과해야 한다(MUST).

## 근거

- Microsoft Foundry는 배포 전 평가, 실행 추적, 운영 모니터링을 구분하고 내장 evaluator와 red teaming을 제공한다.
- OWASP Top 10 for Agentic Applications 2026은 Agent 고유 위험의 평가 대상을 제시한다.
- 출처 목록: [근거와 참고 자료](onboarding/10-references.md)
