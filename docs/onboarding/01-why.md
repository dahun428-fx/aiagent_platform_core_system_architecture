# 플랫폼 도입 배경과 설계 원칙

> 개발자 가이드 문서입니다. 규범(MUST/SHOULD)은 링크된 기술 표준 문서가 기준이며, 이 가이드와 다를 경우 기술 표준 문서를 따릅니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [AI Agent](09-glossary.md#term-agent) [신뢰 경계](09-glossary.md#term-boundary) [기술 계약](09-glossary.md#term-contract) [TBD](09-glossary.md#term-tbd) [인증 / 인가](09-glossary.md#term-authn) [시크릿 / 자격증명](09-glossary.md#term-secret)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- 팀별 Agent 개발에서 반복되는 보안·운영 과제를 설명할 수 있습니다.
- 팀별 개발 환경과 전사 공통 통제의 책임 구분을 설명할 수 있습니다.
- 플랫폼의 제공 범위와 제공하지 않는 범위를 구분할 수 있습니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> Agent를 개발하는 팀이 늘어나면, 각 팀이 인증·데이터 반출·시크릿 관리·실행 추적을 개별적으로 구현하게 됩니다.

<span class="tag">{{icon:eye}} 현황</span> 팀마다 구현 방식과 보안 수준이 다르면 전사 보안 수준은 가장 약한 구현에 맞춰지고, 동일한 기능이 중복으로 개발됩니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> 이러한 통제를 **공통 제어·연계 지점**에서 일괄 적용합니다. Agent 개발은 각 팀의 방식대로 진행하고, 통제는 플랫폼이 담당합니다.
</div>

## 팀별 개발 시 반복되는 과제

<div class="cards">
<div class="card">{{icon:user}}<b>인증·인가</b><p>인증(Authentication, 호출 주체 확인)과 인가(Authorization, 접근 권한 판단)가 팀마다 다르게 구현됩니다.</p></div>
<div class="card">{{icon:cloud}}<b>데이터 반출 통제</b><p>기밀 데이터가 외부 모델로 전송되지 않는다는 보장이 없습니다.</p></div>
<div class="card">{{icon:key}}<b>시크릿·자격증명 관리</b><p>시크릿(Secret)과 ERP·메일·저장소 접근 자격증명(Credential)이 코드나 설정 파일에 남습니다.</p></div>
<div class="card">{{icon:trace}}<b>실행 추적</b><p>요청이 거친 구성요소와 수행한 작업을 종단 간으로 추적하기 어렵습니다.</p></div>
<div class="card">{{icon:test}}<b>품질 검증</b><p>업무 적용 여부를 판단할 공통 평가 기준이 없습니다.</p></div>
<div class="card">{{icon:warn}}<b>영향</b><p>개발 비용이 중복되고, 단일 팀의 보안 결함이 전사 위험으로 확대됩니다.</p></div>
</div>

## 핵심 설계 원칙

<div class="point" markdown="1">
**{{icon:bulb}} 핵심 설계 원칙** Agent 개발에는 팀별 도구와 프레임워크를 사용하며, 플랫폼은 공통 제어·연계 지점에서 인증·인가, 정책 적용, 관측성(Observability), 평가 및 배포 통제를 수행합니다.
</div>

소스 코드는 각 팀의 Git 저장소에서 관리하고, 개발은 각자의 IDE와 CLI에서 수행합니다. 플랫폼이 요구하는 것은 다음 네 가지 **기술 계약** 준수입니다.

<ol class="flow">
<li data-say="Agent를 만든 팀은 먼저 Manifest라는 선언 명세를 제출합니다. 이 Agent가 무엇이고, 어떤 도구와 권한이 필요한지 미리 적어 두는 단계입니다.">{{icon:manifest}}<b>Manifest 제출</b><span>Agent의 메타데이터, 런타임 설정, 권한 요구사항을 선언</span></li>
<li data-say="누가 Agent를 부르든 정문은 하나, Agent Platform APIs입니다. 여기서 호출한 사람이 누구인지와 호출할 권한이 있는지를 확인합니다.">{{icon:gateway}}<b>Agent Platform APIs 진입</b><span>Agent 호출은 Agent Platform APIs로 수행</span></li>
<li data-say="Agent가 모델이나 외부 도구를 쓰려면 반드시 Agent Gateway를 거칩니다. 나가는 문이 하나이므로 무엇이 밖으로 나가는지 통제할 수 있습니다.">{{icon:model}}<b>Agent Gateway 경유</b><span>외부 모델·도구 호출은 Agent Gateway를 통해 수행</span></li>
<li data-say="모든 구간에 같은 추적 번호(trace)가 따라다닙니다. 나중에 한 요청이 어디를 거쳐 어떻게 처리됐는지 처음부터 끝까지 이어서 볼 수 있습니다.">{{icon:trace}}<b>추적 컨텍스트 전파</b><span>trace 정보를 모든 구간에 전달</span></li>
</ol>

<div class="sim" data-sim="before-after"></div>

## 제공 범위

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 플랫폼이 제공하지 않는 것**

- 모든 Agent를 단일 중앙 서버에서 실행하는 구조
- 특정 프레임워크(LangGraph 등)의 강제
- 특정 IdP·CI·벡터 DB 제품의 지정
- 소스 코드 업로드가 필요한 Agent Studio
</div>
<div class="good" markdown="1">
**{{icon:check}} 플랫폼이 제공하는 것**

- 개발자 PC·사내 서버·클라우드에서 동일한 계약에 따른 실행
- 공통 Runtime 계약과 framework adapter 기반의 프레임워크 선택
- 회사 결정이 필요한 제품·수치의 **TBD** 분리
- 불변 버전 참조와 검증 근거의 중앙 등록
</div>
</div>

## 패키지 구성

<div class="cards">
<div class="card">{{icon:book}}<b>기술 표준 문서</b><p>아키텍처, 신뢰 경계, 운영 규칙을 정의한 한국어 문서</p></div>
<div class="card">{{icon:manifest}}<b>API 계약과 JSON Schema</b><p>OpenAPI와 JSON Schema로 작성된 기계 판독 가능한 계약</p></div>
<div class="card">{{icon:code}}<b>예제 구현</b><p>4종 Agent Manifest, Python mock, TypeScript 클라이언트, 테스트</p></div>
</div>

이 패키지는 구현 착수를 위한 기술 표준이며, 회사 IdP나 실제 실행 환경에 연결된 프로덕션 시스템이 아닙니다.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. 플랫폼을 사용하려면 개발 프레임워크를 변경해야 합니까?</summary>
아닙니다. 공통 Runtime 계약과 framework adapter로 연결하므로 프레임워크는 각 팀이 선택합니다.
</details>

<details markdown="1"><summary>Q2. 플랫폼의 공통 제어 지점이 담당하는 것은 실행입니까, 통제입니까?</summary>
통제입니다. 실행은 여러 환경에 분산되며, 인증·인가, 정책, 관측성, 평가, 배포 통제를 공통 지점에서 적용합니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- 팀별로 구현하던 인증·인가, 데이터 반출 통제, 시크릿 관리, 실행 추적, 품질 검증을 공통 지점에서 수행합니다.
- 개발 방식은 유지하고, Manifest 제출·Agent Platform APIs 진입·Agent Gateway 경유·추적 컨텍스트 전파라는 기술 계약을 준수합니다.
- 이 책임은 10개 Core System이 나눠 맡습니다. 구성은 다음 장에서 설명합니다.
- 결정되지 않은 제품과 수치는 TBD로 유지하며 임의로 정하지 않습니다.
</div>

<nav class="pager"><a class="next" href="02-big-picture.md"><small>다음</small><b>Core Systems 아키텍처</b></a></nav>
