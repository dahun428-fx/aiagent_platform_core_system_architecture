# 규격 문서 읽는 법과 자주 묻는 질문

> 온보딩 안내서의 마지막 페이지입니다. 여기부터는 정의 문서를 직접 읽게 됩니다.

<div class="terms" markdown="1">
<span class="label">핵심 용어</span> [MUST / SHOULD / MAY](09-glossary.md#term-must) [TBD](09-glossary.md#term-tbd) [계약 버전](09-glossary.md#term-version) [MCP](09-glossary.md#term-mcp)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 이 페이지에서 배울 것**

- 규격 문장에 붙는 표시 네 가지 읽는 법
- 버전이 세 개로 나뉘는 이유
- 궁금한 것이 생겼을 때 열어 볼 정의 문서
- 처음 온 개발자가 자주 묻는 질문 일곱 가지
</div>

## 규격 문서의 표시

<div class="cards">
<div class="card">{{icon:shield}}<b>규범 수준</b><p><code>MUST</code> 필수 · <code>MUST NOT</code> 금지 · <code>SHOULD</code> 사유를 문서화하면 예외 가능 · <code>MAY</code> 선택</p></div>
<div class="card">{{icon:question}}<b>미정</b><p><code>TBD</code> 회사 환경에 맞춰 정해야 하는 제품이나 수치</p></div>
<div class="card">{{icon:clock}}<b>적용 단계</b><p><code>MVP</code> · <code>Follow-up</code> · <code>Optional</code> 언제 구현하는가</p></div>
<div class="card">{{icon:code}}<b>계약 버전</b><p>예: <code>agent.platform/v1alpha1</code>, <code>/v1</code> 어떤 버전의 계약인가</p></div>
</div>

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 흔한 오해**

"MUST가 붙었으니 특정 제품을 써야 한다."
</div>
<div class="good" markdown="1">
**{{icon:check}} 바른 해석**

"production Agent 호출은 반드시 인증해야 한다(MUST)"여도, 어떤 IdP를 쓸지는 여전히 TBD일 수 있습니다. MUST는 **지켜야 할 성질**이지 제품 선택이 아닙니다.
</div>
</div>

## 버전이 세 개인 이유

<div class="cards">
<div class="card">{{icon:book}}<b>패키지 버전</b><p><code>0.1.0</code> 문서·예제·도구 묶음의 버전</p></div>
<div class="card">{{icon:manifest}}<b>Manifest 계약 버전</b><p><code>agent.platform/v1alpha1</code> Manifest 형식의 버전</p></div>
<div class="card">{{icon:gateway}}<b>HTTP API 경로 버전</b><p><code>/v1</code> Gateway API의 버전</p></div>
</div>

셋은 따로 움직입니다. 패키지 문서를 고쳐도 계약 버전은 그대로일 수 있습니다. 계약을 바꿀 때는 diff 검토, 변경 사유 기록, 마이그레이션 안내, 새 released snapshot 승인이 필요하고, 테스트가 이전 snapshot과 다른지 검사합니다.

<div class="point" markdown="1">
**{{icon:warn}} 주의** snapshot만 덮어써서 테스트를 통과시키면 안 됩니다(MUST NOT).
</div>

## 무엇이 어디에 정의되어 있나

| 알고 싶은 것 | 정의 문서 |
|---|---|
| {{icon:map}} 구성요소의 책임과 신뢰 경계 | [아키텍처](../architecture.md) |
| {{icon:tools}} 도구 호출, MCP, 재시도 규칙 | [Agent Tools](../agent-tools.md) |
| {{icon:identity}} 사용자·Agent 신원, 위임, 자격증명 | [Agent Identity](../identity-and-credentials.md) |
| {{icon:shield}} 위협과 통제 | [보안 경계](../security.md) |
| {{icon:clock}} 실행 상태, 승인, durable | [Durable / HITL](../execution.md) |
| {{icon:eye}} 역할, 수명주기, 평가와 관측 | [운영·평가](../operating-model.md) |
| {{icon:cloud}} 실행 환경과 승격 | [배포 프로파일](../deployment.md) |
| {{icon:code}} 계약 버전과 호환성 | [계약 변경](../versioning.md) |
| {{icon:test}} CI 연결 | [CI 통합](../ci-integration.md) |
| {{icon:book}} 용어 | [핵심 용어 사전](09-glossary.md) |
| {{icon:manifest}} API와 스키마 원본 | 포털 메뉴의 "계약 · 예제" |

## 자주 묻는 질문

<div class="check" markdown="1">
<details markdown="1"><summary>내 Agent를 플랫폼에 올리려면 소스를 어디에 업로드하나요?</summary>
업로드하지 않습니다. 소스는 팀 저장소에 두고, Registry에는 불변 revision, artifact digest, Manifest, 평가 증거를 등록합니다.
</details>

<details markdown="1"><summary>LangGraph를 쓰고 있는데 바꿔야 하나요?</summary>
아닙니다. 공통 Runtime 계약과 framework adapter로 연결합니다. Manifest의 <code>runtime.framework</code>와 <code>runtime.adapter</code>에 적으면 됩니다.
</details>

<details markdown="1"><summary>외부 모델을 코드에서 바로 불러도 되나요?</summary>
production에서는 특정 공급사에 직접 묶지 않고 Model Gateway를 거쳐야 합니다. 그래야 데이터 분류에 따라 외부 전송을 막고, 공급사를 바꿔도 Agent 코드를 고칠 필요가 없습니다. 처음부터 Model Gateway 계약에 맞춰 개발해 두면 승격할 때 고칠 것이 줄어듭니다.
</details>

<details markdown="1"><summary>MCP 서버를 Agent가 직접 붙어 쓰면 안 되나요?</summary>
기본 패턴은 Tool Gateway의 adapter가 MCP client를 소유하는 enterprise proxy입니다. MCP는 도구 프로토콜일 뿐 회사 권한 정책을 대신하지 않습니다. <code>tools/list</code>에는 허용된 도구만 보이고, <code>tools/call</code>도 같은 권한·입출력·감사 규칙을 따릅니다.
</details>

<details markdown="1"><summary>도구 API 키는 어디에 넣나요?</summary>
Agent 코드, Manifest, 환경 변수 어디에도 넣지 않습니다. Credential Broker가 호출마다 짧은 수명의 자격증명을 발급하고, Tool Gateway의 adapter 안에서만 씁니다.
</details>

<details markdown="1"><summary>개발용 Mac mini를 등록했는데 바로 서비스에 쓰면 되나요?</summary>
안 됩니다. 등록(registered)과 production 승인(production-approved)은 다릅니다. production에는 보안, 평가, 복구, 위험별 SLO 증거가 필요합니다.
</details>

<details markdown="1"><summary>예제에 TTL이나 포트 같은 숫자가 있는데 그대로 쓰면 되나요?</summary>
안 됩니다. 예제의 주소, TTL, 깊이, 평가 점수는 합성 값입니다. 회사 수치는 <a href="../tbd-register.md">TBD 등록부</a>에서 정해집니다.
</details>

<details markdown="1"><summary>이 패키지로 바로 production을 운영할 수 있나요?</summary>
아닙니다. 이 패키지는 구현을 시작하기 위한 기술 표준입니다. 회사 IdP, 정책 엔진, 비밀 관리, 실행 환경을 연결하고 운영 검증을 거쳐야 합니다. 시작 순서는 <a href="../ci-integration.md">CI 통합</a>에 있습니다.
</details>
</div>

<div class="summary" markdown="1">
**온보딩을 마쳤다면**

- 회사가 정해야 할 것: [TBD 등록부](../tbd-register.md)
- 이 패키지의 범위: [제공 범위와 한계](../release-scope.md)
- 헷갈리는 용어: [핵심 용어 사전](09-glossary.md)
</div>

<nav class="pager"><a href="07-hands-on.md"><small>이전</small><b>30분 실습</b></a><a class="next" href="09-glossary.md"><small>다음</small><b>핵심 용어 사전</b></a></nav>
