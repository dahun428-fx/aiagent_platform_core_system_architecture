# Agent 수명주기와 프로덕션 승인

> 개발자 가이드 문서입니다. 규범은 [운영·평가](../operating-model.md), [배포 프로파일](../deployment.md), [Durable / HITL](../execution.md) 기술 표준 문서가 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Local-First](09-glossary.md#term-local-first) [Registry](09-glossary.md#term-registry) [Registered / Production-approved](09-glossary.md#term-approved) [배포 프로파일](09-glossary.md#term-profile) [Durable 실행](09-glossary.md#term-durable) [Contract-as-Code](09-glossary.md#term-contract-as-code)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- 로컬 실험부터 폐기까지 Agent 수명주기 7단계를 설명할 수 있습니다.
- 프로덕션 승인에 필요한 검증 근거 6가지를 나열할 수 있습니다.
- 배포 프로파일 3가지와 실행 상태 전이를 설명할 수 있습니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> 로컬 환경에서 동작이 확인된 Agent를 업무에 적용하기 위한 기준과 절차가 필요합니다.

<span class="tag">{{icon:eye}} 현황</span> 로컬 동작 확인과 업무 데이터 처리 적합성은 별개입니다. 반면 초기 단계부터 중앙 절차를 강제하면 실험 속도가 저하됩니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> **개발과 실험은 팀 자율로, 승격은 검증 근거로** 진행합니다. 단계별로 필요한 검증 근거가 정의되어 있습니다.
</div>

## 개발 방식 (Local-First, CLI-First)

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 강제하지 않는 사항 (MUST NOT)**

- 중앙 서버로의 소스 업로드
- 특정 Agent Studio 또는 IDE 사용
</div>
<div class="good" markdown="1">
**{{icon:check}} 플랫폼 제공 사항**

- 계약 기반 SDK, CLI, 템플릿
- 팀 Git 저장소와 기존 IDE·CLI 환경 유지
</div>
</div>

실험 단계의 중앙 등록은 선택 사항입니다. **공동 시험이나 프로덕션 승격**이 필요한 시점에 등록합니다.

## 수명주기 단계

<ol class="flow">
<li>{{icon:laptop}}<b>local experiment</b><span>로컬 개발 및 시험</span></li>
<li>{{icon:manifest}}<b>registered</b><span>불변 버전과 Manifest 등록</span></li>
<li>{{icon:test}}<b>validated</b><span>JSON Schema·API 계약 검증 통과</span></li>
<li>{{icon:approve}}<b>eligible</b><span>평가·검토 완료, 승격 후보</span></li>
<li class="hi">{{icon:rocket}}<b>production-approved</b><span>프로덕션 승인, 업무 트래픽 처리 가능</span></li>
<li>{{icon:clock}}<b>deprecated</b><span>신규 사용 중단 안내</span></li>
<li>{{icon:cross}}<b>retired</b><span>실행 종료</span></li>
</ol>

Registry는 이와 별도로 문제가 확인된 버전을 차단하는 **격리(quarantined)** 상태를 관리합니다.

## 프로덕션 승인 요건 (MUST)

<div class="cards">
<div class="card">{{icon:lock}}<b>불변 버전과 digest</b><p>승격 대상 산출물을 변경 불가능한 참조로 고정합니다.</p></div>
<div class="card">{{icon:test}}<b>계약 적합성 검증</b><p>Manifest의 JSON Schema 검증과 API 계약 검증을 통과합니다.</p></div>
<div class="card">{{icon:shield}}<b>보안 검토 기록</b><p>Identity, 위임, 데이터 이동에 대한 보안 검토를 완료합니다.</p></div>
<div class="card">{{icon:eye}}<b>평가 결과</b><p>데이터셋·Agent·Manifest·정책 버전, 지표, 통과 기준, traceId가 결합된 평가 결과입니다.</p></div>
<div class="card">{{icon:clock}}<b>롤백 검증 결과</b><p>문제 발생 시 이전 버전으로 복구할 수 있음을 검증합니다.</p></div>
<div class="card">{{icon:approve}}<b>위험도별 사람의 승인</b><p>위험도가 높을수록 사람의 승인 단계가 추가됩니다.</p></div>
</div>

<div class="point" markdown="1">
**{{icon:bulb}} 핵심 포인트** 셀프서비스가 기본입니다. 자동 검사를 통과하면 팀이 직접 진행하며, 위험도가 높은 경우에만 사람의 승인이 추가됩니다. 코드 외에도 런타임 이미지, 의존성, 도구 descriptor, 모델 라우팅 정책이 변경되면 재평가합니다.
</div>

## 배포 프로파일

<div class="cards">
<div class="card">{{icon:laptop}}<b>local</b><p>개발자 장비에서 계약 검증과 합성 데이터 실험을 수행합니다.</p><span class="sub">프로덕션 승인 대상 아님</span></div>
<div class="card">{{icon:server}}<b>shared-experiment</b><p>등록된 사내·클라우드 자원에서 통합 시험과 평가를 수행합니다.</p><span class="sub">테넌트 격리 · 사용량 한도 · 감사</span></div>
<div class="card">{{icon:cloud}}<b>production</b><p>승인된 hybrid 실행 환경에서 업무 트래픽을 처리합니다.</p><span class="sub">보안 · 평가 · 복구 · 위험도별 SLO 근거</span></div>
</div>

<div class="point" markdown="1">
**{{icon:warn}} 주의** 등록된 실행 환경은 프로덕션 승인 환경이 아닙니다. 개발자 PC나 Mac mini가 의도치 않게 프로덕션 환경으로 사용되는 것은 이 설계가 방지하려는 위험입니다. SLO는 실행 환경과 업무 위험도에 따라 단계적으로 정의합니다.
</div>

## 장시간 실행과 사람의 승인 (Durable, HITL)

workflow Agent는 장시간 실행되거나 중간에 사람의 승인을 대기할 수 있으므로 실행 상태를 관리합니다.

<ol class="flow">
<li>{{icon:check}}<b>accepted</b><span>요청 접수</span></li>
<li>{{icon:runtime}}<b>running</b><span>실행 중</span></li>
<li class="hi">{{icon:approve}}<b>waiting_approval</b><span>승인 대기</span></li>
<li>{{icon:runtime}}<b>running</b><span>승인 및 재인가 후 재개</span></li>
<li>{{icon:target}}<b>succeeded · failed</b><span>종료 상태는 덮어쓰지 않음</span></li>
</ol>

- 승인 대기 상태는 `rejected`, `expired`, `cancelled`로 종료될 수도 있습니다.
- 취소는 best effort이며, 이미 발생한 부작용을 롤백하지 않습니다.
- 재개 시 승인 대상 digest, 테넌트, 정책 버전, 만료, 취소 여부를 모두 재검증합니다.

Durable 실행 엔진(체크포인트 저장소, 큐, 스케줄러) 제품은 TBD이며, 이 패키지는 계약만 제공합니다.

## 초기 구현 범위: 종단 간 실행 경로

플랫폼은 전체 모듈을 동시에 구현하지 않습니다. 다음 종단 간 실행 경로를 먼저 완성한 뒤, 도구·RAG·Durable 실행·Multi-Agent·분산 실행 환경을 단계적으로 추가합니다.

<ol class="flow">
<li>{{icon:laptop}}<b>로컬 Agent</b><span>Manifest 검증</span></li>
<li>{{icon:gateway}}<b>Agent Gateway</b><span>인증 · Identity · 정책</span></li>
<li>{{icon:runtime}}<b>Runtime adapter</b><span>Agent 실행</span></li>
<li>{{icon:model}}<b>Model Gateway</b><span>외부 · 자체 호스팅 모델</span></li>
<li>{{icon:trace}}<b>실행 추적 · 평가</b><span>검증 근거 기록</span></li>
<li>{{icon:rocket}}<b>Registry · CI 게이트</b><span>승인된 실행 환경으로 승격</span></li>
</ol>

![Local-First MVP 흐름](../../diagrams/mvp.svg)

## CI 품질 게이트

계약 검증은 문서가 아닌 코드로 강제합니다(Contract-as-Code). CI에서 검사가 하나라도 실패하면 산출물 업로드와 승격을 차단합니다(MUST). 이 패키지는 `scripts/release.py`로 포털 생성, 계약·런타임 테스트, TypeScript 검사, 클라이언트 smoke 테스트, 브라우저 오프라인 검사를 실행합니다. 회사 CI 제품은 TBD입니다.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. registered 상태의 Agent는 업무 트래픽을 처리할 수 있습니까?</summary>
처리할 수 없습니다. 승인 요건을 충족해 production-approved 상태가 되어야 합니다.
</details>

<details markdown="1"><summary>Q2. 코드 변경 없이 모델 라우팅 정책만 변경되어도 재평가가 필요합니까?</summary>
필요합니다. 런타임 이미지, 의존성, 도구 descriptor, 모델 라우팅 정책의 변경도 재평가 대상입니다.
</details>

<details markdown="1"><summary>Q3. 승인 대기 중인 작업을 취소하면 이미 발송된 메일도 취소됩니까?</summary>
취소되지 않습니다. 취소는 best effort이며, 이미 발생한 부작용은 롤백하지 않습니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- 개발과 실험은 팀이 자율적으로 수행하고, 프로덕션 승격은 6가지 검증 근거로 판단합니다.
- 배포 프로파일은 local, shared-experiment, production 3가지이며, 등록과 승인은 구분됩니다.
- 종단 간 실행 경로를 먼저 완성하고, 기능은 단계적으로 추가합니다.
</div>

<nav class="pager"><a href="05-agents-and-manifest.md"><small>이전</small><b>Agent 유형과 Manifest 명세</b></a><a class="next" href="07-hands-on.md"><small>다음</small><b>로컬 환경 구성 및 호출 실습</b></a></nav>
