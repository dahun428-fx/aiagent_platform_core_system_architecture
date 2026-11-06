# Memory

Memory는 Agent Runtime의 하위 구성요소로, Agent가 대화와 작업 사이에 정보를 유지하는 기능이다. Durable 실행의 checkpoint(실행 재개용 상태)와 구분한다.

## 종류

| 종류 | 범위 | 예 |
|---|---|---|
| 단기 Memory | 하나의 세션·대화 | 현재 대화의 이전 메시지, 중간 결과 |
| 장기 Memory | 세션을 넘어 유지 | 사용자 선호, 이전 작업에서 추출한 사실 |

## 규칙

- 모든 Memory 항목은 tenant, 범위 주체(사용자 또는 Agent), Agent ID에 결합해야 한다(MUST). 조회와 저장은 이 범위 안에서만 허용한다.
- 장기 Memory의 쓰기는 Agent의 명시적 저장 동작 또는 정책이 허용한 추출 규칙으로만 수행한다(MUST).
- Memory 내용은 비신뢰 데이터로 취급한다(MUST). Memory에 저장된 지시문으로 권한을 획득할 수 없다.
- 장기 Memory 쓰기 전에 민감정보·간접 인젝션 검사를 적용해야 한다(SHOULD). 잘못되거나 악의적인 정보가 저장되어 이후 세션에 영향을 주는 Memory 오염(memory poisoning)을 방지하기 위함이다.
- Memory에는 시크릿, 토큰, 자격증명을 저장해서는 안 된다(MUST NOT).
- 데이터 분류는 저장 시점의 원본 분류를 상속한다(MUST). 사용자 삭제 요청과 보존 기간은 회사 정책(TBD-13)을 따른다.
- Memory 조회·저장은 실행 추적에 기록하되, 내용 원문은 기록하지 않는다(MUST NOT).

## 계약과 제공 범위

- Manifest의 `capabilities`에 Memory 사용 여부와 종류를 선언하는 확장은 후속 계약 버전에서 정의한다.
- v0.1은 Memory 저장소 제품과 API 구현을 제공하지 않는다. 저장소 제품은 TBD-13이다.

## 근거

- AWS Bedrock AgentCore는 Memory(단기 세션·장기 기억)를 독립 구성요소로 제공한다.
- Google Agent Engine Memory Bank는 장기 Memory를 특정 범위에 격리하고 memory poisoning을 위험으로 명시한다.
- OWASP Top 10 for Agentic Applications 2026은 메모리 관련 위험을 별도 범주로 다룬다.
- 출처 목록: [근거와 참고 자료](onboarding/10-references.md)
