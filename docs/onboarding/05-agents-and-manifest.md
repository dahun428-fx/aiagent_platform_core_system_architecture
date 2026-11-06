# Agent Factory와 Manifest 명세

> 개발자 가이드 문서입니다. 규범은 [Agent Manifest JSON Schema](../../contracts/agent-manifest.schema.json)가 기준입니다.

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Factory](09-glossary.md#term-factory) [Manifest](09-glossary.md#term-manifest) [RAG](09-glossary.md#term-rag) [불변 버전](09-glossary.md#term-immutable) [Delegated / Independent](09-glossary.md#term-delegated) [데이터 분류](09-glossary.md#term-classification) [Framework adapter](09-glossary.md#term-adapter) [Registry](09-glossary.md#term-registry) [Durable 실행](09-glossary.md#term-durable) [HITL](09-glossary.md#term-hitl)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 학습 목표**

- Agent Factory의 개발 흐름(생성·선언·검증·등록)을 설명할 수 있습니다.
- 플랫폼이 지원하는 Agent 유형 4가지를 구분할 수 있습니다.
- Manifest의 블록별 의미와 검증 규칙을 설명할 수 있습니다.
- 검증에 실패하는 Manifest의 대표 사례를 식별할 수 있습니다.
</div>

## 배경

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 문제 정의</span> 플랫폼은 Agent 소스 코드를 해석하지 않으므로, 통제와 호출에 필요한 정보를 다른 방식으로 확보해야 합니다.

<span class="tag">{{icon:eye}} 현황</span> 팀마다 프레임워크와 언어가 다르므로, 코드 분석 방식으로는 전사 공통 통제를 적용할 수 없습니다.

<span class="tag">{{icon:bulb}} 설계 방향</span> 각 Agent는 **Agent 선언 명세(Manifest)**를 제출합니다. Manifest는 플랫폼이 Agent를 통제·호출하는 데 필요한 메타데이터, 실행 설정, 권한 요구사항을 선언하며, 플랫폼은 이 선언을 기준으로 동작합니다.
</div>

## Agent Factory 개발 흐름

Agent Factory는 Agent를 만들고, 선언하고, 검증하고, 등록하는 개발 흐름을 담당하는 Core System입니다. 소스는 개발자 저장소에 두며, Factory는 소스 업로드를 요구하지 않습니다(MUST NOT).

<ol class="flow">
<li>{{icon:code}}<b>생성</b><span>Agent 유형별 템플릿<br>(후속 단계)</span></li>
<li>{{icon:manifest}}<b>선언</b><span>Manifest 작성</span></li>
<li>{{icon:test}}<b>로컬 검증</b><span><code>agentctl validate</code></span></li>
<li>{{icon:shield}}<b>CI 게이트</b><span>계약·보안·평가 검증</span></li>
<li class="hi">{{icon:control}}<b>Registry 등록</b><span>불변 revision · artifact digest</span></li>
</ol>

<div class="cards">
<div class="card">{{icon:code}}<b>CLI</b><p><code>scripts/agentctl.py validate</code>로 Manifest를 JSON Schema 기준으로 검증합니다.</p><span class="sub">구현</span></div>
<div class="card">{{icon:manifest}}<b>스키마와 fixture</b><p>Manifest JSON Schema, 4종 예제 Manifest, 검증 실패용 fixture를 제공합니다.</p><span class="sub">구현</span></div>
<div class="card">{{icon:laptop}}<b>템플릿</b><p>Agent 유형별 프로젝트 템플릿과 생성 명령을 제공합니다.</p><span class="sub">후속 단계</span></div>
</div>

Factory의 도구는 AI Platform Applications의 DevTools로 제공됩니다.

## Agent 유형

<div class="cards">
<div class="card">{{icon:knowledge}}<b>rag</b><p>사내 문서를 검색하고 근거를 포함해 응답합니다.</p><span class="sub">Knowledge Backend · Agent Gateway 모델 경로</span></div>
<div class="card">{{icon:tools}}<b>tool</b><p>사내·외부 시스템 API를 호출해 작업을 수행합니다.</p><span class="sub">Agent Gateway 도구 경로 · Credential Broker</span></div>
<div class="card">{{icon:workflow}}<b>workflow</b><p>여러 단계를 순차적으로 처리하며, 장시간 실행과 사람의 승인을 포함할 수 있습니다.</p><span class="sub">Durable 실행 · HITL</span></div>
<div class="card">{{icon:agents}}<b>multi-agent</b><p>하위 Agent에 작업을 위임합니다.</p><span class="sub">공통 Agent 통신 계약</span></div>
</div>

4가지 유형은 모두 **계약 수준에서** 지원합니다. 예제 Manifest가 4종 제공된다는 것이 4종의 프로덕션 실행 엔진 구현을 의미하지는 않습니다. 예를 들어 durable 실행은 계약만 제공되며, 로컬 mock은 501을 반환합니다.

<div class="point" markdown="1">
**{{icon:knowledge}} RAG 검색 규칙** 공통 RAG 계약을 준수하면 지식 저장소를 교체할 수 있습니다. 검색 시에는 **사용자 권한(ACL)과 데이터 분류로 먼저 필터링해야** 하며, 접근 권한이 없는 문서는 검색 결과에 포함되지 않아야 합니다.
</div>

<div class="point" markdown="1">
**{{icon:agents}} Agent 간 호출** 공통 Agent 통신 계약(`cross-agent.schema.json`)을 사용합니다. 상위 호출 ID, 축소된 권한 범위, 호출 깊이와 예산이 함께 전달됩니다. 프레임워크 고유의 협업 방식은 adapter로 연결합니다. A2A 프로토콜로 호출하는 것은 선택이며, 발견 정보를 발행할 때는 A2A Agent Card 형식을 사용합니다([Agent Card와 Agent 간 통신](13-agent-card.md)).
</div>

## Manifest 명세

Manifest는 플랫폼이 Agent를 통제하고 호출하는 데 필요한 정보만 선언하는 JSON 문서입니다. 프레임워크 내부 구현은 포함하지 않습니다. Manifest는 인증 수단이 아니며, 실행 주체의 Identity나 자격증명과 구분됩니다.

<ol class="flow">
<li>{{icon:identity}}<b>메타데이터</b><span>apiVersion · kind<br>metadata</span></li>
<li>{{icon:code}}<b>소스 참조</b><span>source</span></li>
<li>{{icon:runtime}}<b>런타임 설정</b><span>runtime</span></li>
<li>{{icon:tools}}<b>기능 및 의존 리소스</b><span>capabilities</span></li>
<li>{{icon:user}}<b>실행 주체와 권한 모드</b><span>identity</span></li>
<li>{{icon:shield}}<b>데이터 분류·위험도·정책</b><span>governance</span></li>
<li>{{icon:cloud}}<b>배포 설정과 입출력 계약</b><span>deployment · contracts</span></li>
</ol>

이 패키지의 tool Agent 예제(`examples/manifests/tool.json`)입니다.

```json
{
  "apiVersion": "agent.platform/v1alpha1",
  "kind": "Agent",
  "metadata": {
    "id": "agent-tool",
    "name": "합성 tool Agent",
    "version": "0.1.0",
    "owner": {"team": "TBD"}
  },
  "source": {
    "repository": "https://example.invalid/agents/demo.git",
    "revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "artifactDigest": "sha256:bbbb…"
  },
  "runtime": {
    "framework": "custom",
    "adapter": "adapter-reference",
    "entrypoint": "platform_ref:Runtime",
    "executionMode": "sync"
  },
  "capabilities": {
    "type": "tool",
    "tools": ["tool-search"],
    "knowledge": [],
    "agents": []
  },
  "identity": {"mode": "delegated", "requiredScopes": ["agents.invoke"]},
  "governance": {
    "classification": "internal",
    "risk": "low",
    "policyProfile": "policy-demo",
    "evaluationProfile": "eval-demo"
  },
  "deployment": {"profile": "local", "environmentRef": "environment-demo"},
  "contracts": {
    "inputSchema": "https://agent.example.invalid/contracts/invocation.schema.json",
    "outputSchema": "https://agent.example.invalid/contracts/result.schema.json"
  }
}
```

| 블록 | 의미 | 검증 규칙 및 주의 사항 |
|---|---|---|
| `apiVersion`, `kind` | 계약 버전과 리소스 유형 | 현재 `agent.platform/v1alpha1`입니다. alpha 버전이므로 운영 안정성을 보증하지 않습니다 |
| `metadata` | ID, 이름, 버전, 소유 팀 | 소유 팀이 없으면 검증에 실패합니다 |
| `source` | 소스 참조 | 소스를 업로드하지 않고 **저장소 위치, 불변 revision, artifact digest**를 선언합니다 |
| `runtime` | 런타임 설정 | `executionMode`는 `sync`, `async`, `durable` 중 하나입니다 |
| `capabilities` | 기능 및 의존 리소스 | `type`은 4가지 유형 중 하나이며, 도구·지식·하위 Agent를 **논리 ID**로 선언합니다 |
| `identity` | 실행 주체와 권한 모드 | `delegated`(사용자 위임) 또는 `independent`(Agent 자체 권한)이며, 필요 scope를 선언합니다 |
| `governance` | 데이터 분류·위험도·정책 | 분류 `public`·`internal`·`confidential`·`restricted`, 위험도 `low`·`medium`·`high`, 정책·평가 프로파일 |
| `deployment` | 배포 설정 | 프로파일 `local`, `shared-experiment`, `production` |
| `contracts` | 입출력 계약 | 입력·출력 JSON Schema URI |

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 검증 실패: 가변 참조**

```json
"revision": "main"
```

브랜치 이름은 시점에 따라 다른 커밋을 가리킵니다.
</div>
<div class="good" markdown="1">
**{{icon:check}} 검증 통과: 불변 참조**

```json
"revision": "aaaaaaaa…(40자 커밋 해시)",
"artifactDigest": "sha256:…"
```

항상 동일한 코드와 산출물을 가리킵니다.
</div>
</div>

## 검증 실패 사례

`examples/negative/`에는 검증 실패를 확인하기 위한 Manifest가 포함되어 있습니다.

| 파일 | 실패 원인 |
|---|---|
| {{icon:user}} `missing-owner.json` | 소유 팀 누락 |
| {{icon:manifest}} `invalid-version.json` | 버전 형식 오류 |
| {{icon:code}} `mutable-revision.json` | `main` 등 가변 revision 사용 |
| {{icon:key}} `unexpected-secret.json` | 정의되지 않은 필드에 시크릿 포함 |
| {{icon:runtime}} `unsupported-mode.json` | 지원하지 않는 실행 모드 |
| {{icon:shield}} `invalid-classification.json` | 정의되지 않은 데이터 분류 |
| {{icon:map}} `malformed-uri.json` | URI 형식 오류 |
| {{icon:tools}} `empty-tools.json` | tool 유형 Agent의 도구 목록 누락 |

검증 실행 방법은 [로컬 환경 구성 및 호출 실습](07-hands-on.md)을 참고하십시오.

<div class="check" markdown="1">
**{{icon:question}} 이해도 점검**

<details markdown="1"><summary>Q1. Manifest에 API 키를 포함할 수 있습니까?</summary>
포함할 수 없습니다. 스키마가 정의되지 않은 필드를 허용하지 않으므로 검증에 실패합니다. 접근 자격증명은 Credential Broker가 호출 시점에 발급합니다.
</details>

<details markdown="1"><summary>Q2. 사용자를 대신해 동작하는 Agent의 identity.mode 값은 무엇입니까?</summary>
<code>delegated</code>입니다. Agent 자체 권한으로만 동작하면 <code>independent</code>입니다.
</details>
</div>

<div class="summary" markdown="1">
**요약**

- 플랫폼은 rag, tool, workflow, multi-agent 4가지 유형을 공통 계약 수준에서 지원합니다.
- Manifest는 메타데이터, 소스 참조, 런타임 설정, 기능·의존 리소스, 권한 모드, 데이터 분류·정책, 배포 설정을 선언하는 Agent 선언 명세입니다.
- 소스는 불변 revision과 digest로 참조하며, 시크릿은 Manifest에 포함할 수 없습니다.
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- Agent Factory 명칭과 구축 패턴: [클라우드 Agent 플랫폼](10-references.md#ref-industry)
</div>

<nav class="pager"><a href="03-one-request.md"><small>이전</small><b>Agent 요청 처리 흐름</b></a><a class="next" href="11-runtime-memory.md"><small>다음</small><b>Agent Runtime과 Memory</b></a></nav>
