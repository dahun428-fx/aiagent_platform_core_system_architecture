# 규격 문서 읽는 법과 자주 묻는 질문

> 온보딩 안내서의 마지막 페이지입니다. 여기부터는 원문 규격을 직접 읽게 됩니다.

## 규격 문서의 네 가지 표시

원문 규격에는 문장마다 네 종류의 표시가 섞여 있습니다. 각각 다른 것을 말하므로 구분해서 읽어야 합니다.

| 표시 | 값 | 뜻 |
|---|---|---|
| 규범 수준 | MUST, MUST NOT, SHOULD, MAY | 필수, 금지, 사유를 문서화하면 예외 가능, 선택 |
| 결정 상태 | Decided, Recommended, TBD, Optional | 기준선에서 결정됨, 권장, 회사 결정 대기, 선택 기능 |
| 적용 단계 | MVP, Follow-up, Optional | 언제 구현하는가 |
| 계약 버전 | 예: `agent.platform/v1alpha1`, `/v1` | 어떤 버전의 계약인가 |

가장 많이 헷갈리는 부분은 이것입니다. **MUST는 "특정 제품을 써야 한다"는 뜻이 아닙니다.** "production Agent 호출은 반드시 인증해야 한다(MUST)"는 문장이 있어도, 어떤 IdP를 쓸지는 여전히 TBD일 수 있습니다.

또 **Decided는 기준선의 결정 상태**입니다. 회사가 공식으로 배포를 승인했다는 뜻과는 다릅니다.

## 버전이 세 개인 이유

- 패키지 버전: `0.1.0`
- Manifest 계약 버전: `agent.platform/v1alpha1`
- HTTP API 경로 버전: `/v1`

셋은 따로 움직입니다. 패키지 문서를 고쳐도 계약 버전은 그대로일 수 있습니다. 계약을 바꿀 때는 diff 검토, ADR, 마이그레이션 안내, 새 released snapshot 승인이 필요하고, 테스트가 이전 snapshot과 다른지 검사합니다. snapshot만 덮어써서 테스트를 통과시키면 안 됩니다(MUST NOT).

## ADR 읽는 법

ADR(Architecture Decision Record)은 결정 하나에 문서 하나입니다. 30개 질문마다 ADR이 하나씩 있습니다. "왜 이렇게 정했지?"가 궁금할 때 해당 ADR을 열면 Context(맥락), Decision(결정), Alternatives considered(검토한 대안), Consequences(결과)가 있습니다. 전체 목록은 포털 메뉴의 "계약 · Fixture · ADR"에서 볼 수 있습니다.

처음이라면 이 순서로 읽기를 권합니다.

1. [ADR-017 공통 제어·분산 실행](../../adr/ADR-017.md)
2. [ADR-018 Local-First/CLI-First](../../adr/ADR-018.md)
3. [ADR-012 Gateway 분리](../../adr/ADR-012.md)
4. [ADR-009 Agent Tools](../../adr/ADR-009.md)
5. [ADR-008 사용자·Agent Identity](../../adr/ADR-008.md)
6. [ADR-006 공통 Runtime](../../adr/ADR-006.md)

## 자주 묻는 질문

**Q. 내 Agent를 플랫폼에 올리려면 소스를 어디에 업로드하나요?**
업로드하지 않습니다. 소스는 팀 저장소에 두고, Registry에는 불변 revision, artifact digest, Manifest, 평가 증거를 등록합니다.

**Q. LangGraph를 쓰고 있는데 바꿔야 하나요?**
아닙니다. 공통 Runtime 계약과 framework adapter로 연결합니다. Manifest의 `runtime.framework`와 `runtime.adapter`에 적으면 됩니다.

**Q. OpenAI나 Claude 같은 외부 모델을 코드에서 바로 불러도 되나요?**
production에서는 특정 공급사에 직접 묶지 않고 Model Gateway를 거쳐야 합니다. 그래야 데이터 분류에 따라 외부 전송을 막고, 공급사를 바꿔도 Agent 코드를 고칠 필요가 없습니다. 처음부터 Model Gateway 계약에 맞춰 개발해 두면 승격할 때 고칠 것이 줄어듭니다.

**Q. MCP 서버를 Agent가 직접 붙어 쓰면 안 되나요?**
기본 패턴은 Tool Gateway의 adapter가 MCP client를 소유하는 enterprise proxy입니다. MCP는 도구 프로토콜일 뿐 회사 권한 정책을 대신하지 않습니다. `tools/list`에는 허용된 도구만 보이고, `tools/call`도 같은 권한·입출력·감사 규칙을 따릅니다.

**Q. 도구 API 키는 어디에 넣나요?**
Agent 코드, Manifest, 환경 변수 어디에도 넣지 않습니다. Credential Broker가 호출마다 짧은 수명의 자격증명을 발급하고, Tool Gateway의 adapter 안에서만 씁니다.

**Q. 개발용 Mac mini를 등록했는데 바로 서비스에 쓰면 되나요?**
안 됩니다. 등록(registered)과 production 승인(production-approved)은 다릅니다. production에는 보안, 평가, 복구, 위험별 SLO 증거가 필요합니다.

**Q. 예제에 TTL이나 포트 같은 숫자가 있는데 그대로 쓰면 되나요?**
안 됩니다. 예제의 주소, TTL, 깊이, 평가 점수는 합성 값입니다. 회사 수치는 [TBD 등록부](../tbd-register.md)에서 결정을 기다리고 있습니다.

**Q. 이 패키지로 바로 production을 운영할 수 있나요?**
아닙니다. 이 패키지는 구현을 시작하기 위한 기술 표준입니다. 회사 IdP, 정책 엔진, 비밀 관리, 실행 환경을 연결하고 운영 검증을 거쳐야 합니다. 시작 순서는 [CI 통합과 착수 인계](../ci-integration.md)에 있습니다.

## 다음에 읽을 것

- 전체 결정 30개: [요구사항 기준선 v0.1](../requirements/baseline-v0.1.md)
- 회사가 정해야 할 것: [TBD 등록부](../tbd-register.md)
- 검증된 정정 사항: [보고서 정정](../corrections.md)
- 원본 연구: [Deep Research 출처](../../sources/README.md)

이전: [30분 실습](07-hands-on.md) · 처음으로: [왜 이 플랫폼이 필요한가](01-why.md)
