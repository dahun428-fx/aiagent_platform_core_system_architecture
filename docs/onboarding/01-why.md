# 왜 이 플랫폼이 필요한가

> 온보딩 안내서입니다. 규범(MUST/SHOULD)은 링크된 정의 문서가 기준이며, 안내서와 다르면 정의 문서가 맞습니다.

<div class="terms" markdown="1">
<span class="label">핵심 용어</span> [AI Agent](09-glossary.md#term-agent) [공통 경계](09-glossary.md#term-boundary) [계약](09-glossary.md#term-contract) [TBD](09-glossary.md#term-tbd)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 이 페이지에서 배울 것**

- 팀마다 Agent를 따로 만들 때 생기는 문제 다섯 가지
- 이 플랫폼이 그 문제를 푸는 방식을 한 문장으로 말하기
- 이 플랫폼이 하는 일과 하지 않는 일 구분하기
</div>

## 들어가며

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 질문</span> Agent를 잘 만드는 팀이 이미 있는데, 왜 회사 공통 플랫폼이 필요할까요?

<span class="tag">{{icon:eye}} 관찰</span> Agent가 늘어날수록 팀마다 같은 고민을 다시 풉니다. 누가 불렀는지, 데이터가 밖으로 나가는지, 비밀값은 어디 두는지, 무슨 일이 있었는지. 답이 팀마다 다르면 회사 전체의 보안 수준은 가장 약한 팀에 맞춰집니다.

<span class="tag">{{icon:bulb}} 해결책</span> 이 고민들을 **공통 경계에서 한 번에** 풉니다. 개발은 각 팀이 하던 대로 하고, 통제만 플랫폼이 맡습니다.
</div>

## 팀마다 따로 만들면 생기는 다섯 가지 문제

<div class="cards">
<div class="card">{{icon:user}}<b>누가 불렀나</b><p>호출한 사람과 권한을 팀마다 다르게 확인합니다.</p></div>
<div class="card">{{icon:cloud}}<b>데이터가 나가나</b><p>기밀 문서가 외부 모델로 전송되지 않는다는 보장이 없습니다.</p></div>
<div class="card">{{icon:key}}<b>비밀값은 어디에</b><p>ERP·메일·저장소 토큰이 코드나 설정 파일에 남습니다.</p></div>
<div class="card">{{icon:trace}}<b>무슨 일이 있었나</b><p>요청이 어디를 거쳐 무엇을 했는지 끝까지 추적하기 어렵습니다.</p></div>
<div class="card">{{icon:test}}<b>써도 되나</b><p>실제 업무에 쓸 만큼 품질이 검증됐는지 판단 기준이 없습니다.</p></div>
<div class="card">{{icon:warn}}<b>결과</b><p>비용은 겹치고, 한 팀의 실수가 회사 전체의 위험이 됩니다.</p></div>
</div>

## 이 플랫폼이 하는 방식

<div class="point" markdown="1">
**{{icon:bulb}} 핵심 포인트** 개발자는 지금 쓰는 도구와 프레임워크를 그대로 쓰고, 신원·정책·관측·평가·배포 통제는 플랫폼의 공통 경계에서 적용합니다.
</div>

소스 코드는 지금처럼 각 팀의 Git 저장소에 있고, 개발도 각자의 IDE와 CLI에서 합니다. 플랫폼이 요구하는 것은 네 가지 **약속(계약)**입니다.

<ol class="flow">
<li>{{icon:manifest}}<b>신분증을 낸다</b><span>Agent가 무엇이고 무엇이 필요한지 Manifest에 적는다</span></li>
<li>{{icon:model}}<b>모델은 관문으로</b><span>모델은 Model Gateway를 통해 부른다</span></li>
<li>{{icon:tools}}<b>도구도 관문으로</b><span>사내 도구는 Tool Gateway를 통해 부른다</span></li>
<li>{{icon:trace}}<b>추적을 잇는다</b><span>trace 정보를 끊지 않고 전달한다</span></li>
</ol>

## 하는 일과 하지 않는 일

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 이 플랫폼이 아닌 것**

- 모든 Agent를 중앙 서버 한 곳에서 실행하는 시스템
- 특정 프레임워크(LangGraph 등)를 강제하는 SDK
- 특정 IdP·CI·벡터 DB 제품을 정해 둔 패키지
- 소스 코드를 중앙에 올려야 쓰는 Agent Studio
</div>
<div class="good" markdown="1">
**{{icon:check}} 이 플랫폼인 것**

- 개발자 PC·사내 서버·클라우드 어디서든 같은 계약으로 실행
- 공통 Runtime 계약과 adapter로 프레임워크는 팀이 선택
- 회사가 정할 제품과 수치는 **TBD**로 분리
- 중앙에는 불변 버전 참조와 검증 증거만 등록
</div>
</div>

## 이 패키지에 들어 있는 것

<div class="cards">
<div class="card">{{icon:book}}<b>정의 문서</b><p>구조, 신뢰 경계, 운영 규칙을 정의한 한국어 문서</p></div>
<div class="card">{{icon:manifest}}<b>계약 파일</b><p>OpenAPI와 JSON Schema로 된 기계가 읽는 계약</p></div>
<div class="card">{{icon:code}}<b>실행 예제</b><p>4종 Agent Manifest, Python mock, TypeScript 클라이언트, 테스트</p></div>
</div>

실제 회사 IdP나 운영 환경에 연결된 production 시스템은 아닙니다. 구현을 시작하기 위한 기술 표준입니다.

<div class="check" markdown="1">
**{{icon:question}} 스스로 점검**

<details markdown="1"><summary>Q1. 이 플랫폼을 쓰려면 개발 프레임워크를 바꿔야 하나요?</summary>
아닙니다. 공통 Runtime 계약과 framework adapter로 연결하므로 프레임워크는 팀이 고릅니다.
</details>

<details markdown="1"><summary>Q2. 플랫폼의 중앙에서 하는 일은 실행인가요, 통제인가요?</summary>
통제입니다. 실행은 여러 환경에 분산되고, 신원·정책·관측·평가·배포 통제를 공통 경계에서 적용합니다.
</details>
</div>

<div class="summary" markdown="1">
**정리**

- 팀마다 따로 풀던 신원·데이터·비밀값·추적·품질 문제를 공통 경계에서 해결합니다.
- 개발 방식은 그대로 두고, Manifest·Model Gateway·Tool Gateway·trace라는 약속만 지킵니다.
- 정해지지 않은 제품과 수치는 TBD로 남겨 두고 임의로 정하지 않습니다.
</div>

<nav class="pager"><a class="next" href="02-big-picture.md"><small>다음</small><b>한 장으로 보는 전체 구조</b></a></nav>
