# 기술 표준 해석과 FAQ

> 개발자 가이드의 마지막 장입니다. 이후에는 기술 표준 문서를 직접 참조합니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [MUST / SHOULD / MAY](09-glossary.md#term-must) [TBD](09-glossary.md#term-tbd) [계약 버전](09-glossary.md#term-version) [MCP](09-glossary.md#term-mcp)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- 기술 표준 문장에 사용되는 표기 4가지를 해석할 수 있습니다.
- 버전 체계가 3가지로 분리된 이유를 설명할 수 있습니다.
- 주제별로 참조할 기술 표준 문서를 찾을 수 있습니다.
</div>

## 표기 체계

<div class="cards">
<div class="card">{{icon:shield}}<b>규범 수준</b><p><code>MUST</code> 필수 · <code>MUST NOT</code> 금지 · <code>SHOULD</code> 사유 문서화 시 예외 허용 · <code>MAY</code> 선택</p></div>
<div class="card">{{icon:question}}<b>미정 항목</b><p><code>TBD</code> 회사 환경에 따라 결정해야 하는 제품 또는 수치</p></div>
<div class="card">{{icon:clock}}<b>적용 단계</b><p><code>MVP</code> · <code>Follow-up</code> · <code>Optional</code> 구현 시점</p></div>
<div class="card">{{icon:code}}<b>계약 버전</b><p>예: <code>agent.platform/v1alpha1</code>, <code>/v1</code> 적용되는 계약의 버전</p></div>
</div>

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 잘못된 해석**

"MUST가 표기되어 있으므로 특정 제품을 사용해야 한다."
</div>
<div class="good" markdown="1">
**{{icon:check}} 올바른 해석**

"프로덕션 Agent 호출은 반드시 인증해야 한다(MUST)"는 요구사항이 있어도 IdP 제품은 TBD일 수 있습니다. MUST는 **충족해야 할 요구사항**이며, 제품 선택을 의미하지 않습니다.
</div>
</div>

## 버전 체계

<div class="cards">
<div class="card">{{icon:book}}<b>패키지 버전</b><p><code>0.1.0</code> 문서·예제·도구 패키지의 버전</p></div>
<div class="card">{{icon:manifest}}<b>Manifest 계약 버전</b><p><code>agent.platform/v1alpha1</code> Manifest 형식의 버전</p></div>
<div class="card">{{icon:gateway}}<b>HTTP API 경로 버전</b><p><code>/v1</code> Gateway API의 버전</p></div>
</div>

세 버전은 독립적으로 관리됩니다. 패키지 문서가 변경되어도 계약 버전은 유지될 수 있습니다. 계약을 변경할 때는 diff 검토, 변경 사유 기록, 마이그레이션 안내, 신규 released snapshot 승인이 필요하며, 테스트는 이전 snapshot과의 일치 여부를 검사합니다.

<div class="point" markdown="1">
**{{icon:warn}} 주의** snapshot만 덮어써서 테스트를 통과시켜서는 안 됩니다(MUST NOT).
</div>

## 기술 표준 및 참조 명세

| 주제 | 기술 표준 문서 |
|---|---|
| {{icon:map}} 10개 Core System의 책임과 제공 범위 | [Core Systems](../core-systems.md) |
| {{icon:map}} 구성요소의 책임과 신뢰 경계 | [아키텍처](../architecture.md) |
| {{icon:tools}} 도구 호출, MCP, 재시도 규칙 | [Agent Tools](../agent-tools.md) |
| {{icon:identity}} 사용자·Agent Identity, 위임, 자격증명 | [Agent Identity](../identity-and-credentials.md) |
| {{icon:shield}} 위협 모델과 보안 통제 | [보안 경계](../security.md) |
| {{icon:shield}} Guardrail 검사 서비스와 집행 지점 | [Guardrails](../guardrails.md) |
| {{icon:knowledge}} 단기·장기 Memory | [Memory](../memory.md) |
| {{icon:agents}} A2A Agent Card 발행·소비 | [Agent Card](../agent-card.md) |
| {{icon:clock}} 실행 상태, 승인, Durable 실행 | [Durable / HITL](../execution.md) |
| {{icon:eye}} 역할, 수명주기, 승인 요건 | [운영·평가](../operating-model.md) |
| {{icon:eye}} 실행 추적 규격과 지표 | [Observability](../observability.md) |
| {{icon:test}} 평가 3단계와 평가 항목 | [Evaluation](../evaluation.md) |
| {{icon:rocket}} Tuning 흐름과 규칙 | [Agent Tuning](../agent-tuning.md) |
| {{icon:cloud}} 실행 환경과 승격 | [배포 프로파일](../deployment.md) |
| {{icon:code}} 계약 버전과 호환성 | [계약 변경](../versioning.md) |
| {{icon:test}} CI 연동 | [CI 통합](../ci-integration.md) |
| {{icon:book}} 용어 | [주요 용어 정의](09-glossary.md), [용어와 규범](../glossary.md) |
| {{icon:book}} 외부 근거 자료 | [근거와 참고 자료](10-references.md) |
| {{icon:manifest}} API 계약과 JSON Schema 원본 | 포털 메뉴의 "계약 · 예제" |

## FAQ

<div class="check" markdown="1">
<details markdown="1"><summary>Agent를 플랫폼에 등록하려면 소스를 업로드해야 합니까?</summary>
업로드하지 않습니다. 소스는 팀 저장소에서 관리하며, Registry에는 불변 revision, artifact digest, Manifest, 평가 결과를 등록합니다.
</details>

<details markdown="1"><summary>LangGraph를 사용 중인 경우 프레임워크를 변경해야 합니까?</summary>
변경하지 않습니다. 공통 Runtime 계약과 framework adapter로 연결하며, Manifest의 <code>runtime.framework</code>와 <code>runtime.adapter</code>에 선언합니다.
</details>

<details markdown="1"><summary>외부 모델 API를 Agent 코드에서 직접 호출할 수 있습니까?</summary>
프로덕션 환경에서는 특정 공급사에 직접 결합하지 않고 Agent Gateway 모델 경로를 경유해야 합니다. 이를 통해 데이터 분류에 따른 외부 전송 통제와 공급사 교체 시 코드 변경 최소화가 가능합니다. 개발 단계부터 모델 경로 계약을 기준으로 구현하면 승격 시 변경 범위가 줄어듭니다.
</details>

<details markdown="1"><summary>Agent가 MCP 서버에 직접 연결할 수 있습니까?</summary>
기본 패턴은 Agent Gateway 도구 경로의 adapter가 MCP client를 소유하는 enterprise proxy 방식입니다. adapter는 OAuth 2.1 client로서 RFC 8707 resource indicator와 RFC 9728 Protected Resource Metadata를 사용합니다. MCP는 도구 프로토콜이며 회사 인가 정책을 대체하지 않습니다. <code>tools/list</code>는 허용된 도구만 노출하고, <code>tools/call</code>도 동일한 인가·입출력 검증·감사 규칙을 따릅니다.
</details>

<details markdown="1"><summary>도구 접근용 API 키는 어디에 저장합니까?</summary>
Agent 코드, Manifest, 환경 변수에 저장하지 않습니다. Credential Broker가 호출마다 단기 자격증명을 발급하며, 자격증명은 Agent Gateway 도구 경로의 adapter 내부에서만 사용됩니다.
</details>

<details markdown="1"><summary>등록한 Mac mini를 바로 서비스에 사용할 수 있습니까?</summary>
사용할 수 없습니다. 등록(registered)과 프로덕션 승인(production-approved)은 다르며, 프로덕션 환경에는 보안 검토, 평가 결과, 복구 검증, 위험도별 SLO 근거가 필요합니다.
</details>

<details markdown="1"><summary>예제의 TTL, 포트 등 수치를 그대로 사용할 수 있습니까?</summary>
사용할 수 없습니다. 예제의 주소, TTL, 호출 깊이, 평가 점수는 합성 값입니다. 회사 기준 수치는 <a href="../tbd-register.md">TBD 등록부</a>에서 결정합니다.
</details>

<details markdown="1"><summary>이 패키지로 프로덕션 환경을 바로 운영할 수 있습니까?</summary>
운영할 수 없습니다. 이 패키지는 구현 착수를 위한 기술 표준이며, 회사 IdP, 정책 엔진, 시크릿 관리, 실행 환경 연동과 운영 검증이 필요합니다. 착수 절차는 <a href="../ci-integration.md">CI 통합</a>을 참고하십시오.
</details>
</div>

<div class="summary" markdown="1">
**다음 단계**

- 회사 결정 사항: [TBD 등록부](../tbd-register.md)
- 패키지 제공 범위: [제공 범위와 한계](../release-scope.md)
- 용어 확인: [주요 용어 정의](09-glossary.md)
</div>

<nav class="pager"><a href="07-hands-on.md"><small>이전</small><b>로컬 환경 구성 및 호출 실습</b></a><a class="next" href="10-references.md"><small>다음</small><b>근거와 참고 자료</b></a></nav>
