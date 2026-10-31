# 아키텍처

## 구조
전사 Client/App은 Agent Gateway로 들어온다. Gateway는 인증·agent resolution·tenant authorization·idempotency를 책임진다.
Runtime은 orchestration consumer이며 Identity·Model·Tools·Knowledge·State·Policy를 소비한다.
Model Gateway는 모델 capability·분류·지역·비용/가용성 정책으로 endpoint를 선택한다.
Tool Gateway는 Agent Tools에 속하며 REST/OpenAPI/MCP egress를 중재한다.
Credential Broker는 Agent Identity에 속하며 승인된 Tool Gateway adapter에만 단기 credential을 전달하거나 비노출 handle을 발급한다.

## Shared Control Plane
Registry(Agent/Tool/Model/Environment), Policy, Identity mediation, Evaluation, Observability metadata, Promotion을 제공한다.
Registry는 source 자체가 아닌 불변 Git revision·artifact digest·Manifest·평가 증거를 저장해야 한다(MUST).
등록(registered), 시험 가능(eligible), production 승인(production-approved), 격리(quarantined)를 구분한다.
보안·정책 권한은 Runtime이 임의 변경할 수 없다(MUST NOT).

## Distributed Execution Plane
개발자 로컬, 워크스테이션/Mac mini 계열 자원, 사내·클라우드 실행 target은 회사 환경 TBD로 취급한다.
동일 Runtime 계약을 적용하되 registered만으로 production traffic을 받지 않는다.
물리 배치는 논리 분리를 합칠 수 있다. identity/egress trust boundary는 합쳐도 보존해야 한다(MUST).

## C4 계층과 시퀀스
[Context](../diagrams/c4-context.mmd), [Container](../diagrams/c4-container.mmd), [Runtime Component](../diagrams/c4-component.mmd).
[Invocation](../diagrams/invocation.mmd), [Model routing](../diagrams/model-routing.mmd), [Tool/Credential](../diagrams/tool-credential.mmd).
[Security boundaries](../diagrams/security-boundaries.mmd), [Deployment](../diagrams/deployment.mmd), [MVP](../diagrams/mvp.mmd).
포털은 각 그림의 로컬 SVG와 Mermaid 원문을 함께 제공한다.

## 데이터 책임
- tenant는 검증된 identity에서 파생한다. body의 tenant assertion은 비교용이며 권한의 근거가 아니다.
- 정책과 위임은 grant가 아니라 검증할 evidence다. 사용자 입력에 principal/roles를 넣어 승격할 수 없다.
- 검색 결과·tool output·model output은 비신뢰 데이터다. prompt instruction으로 권한을 획득할 수 없다.
- Gateway→Runtime→Model/Tool/RAG→하위 Agent에 traceparent를 전달한다. baggage에 PII·token을 넣지 않는다.

