# 네 종류 Agent와 Manifest

> 온보딩 안내서입니다. 규범은 [Agent Manifest 스키마](../../contracts/agent-manifest.schema.json)가 기준입니다.

<div class="terms" markdown="1">
<span class="label">핵심 용어</span> [Manifest](09-glossary.md#term-manifest) [RAG](09-glossary.md#term-rag) [불변 버전](09-glossary.md#term-immutable) [Delegated / Independent](09-glossary.md#term-delegated) [데이터 분류](09-glossary.md#term-classification) [Adapter](09-glossary.md#term-adapter)
</div>

<div class="goals" markdown="1">
**{{icon:target}} 이 페이지에서 배울 것**

- 플랫폼이 처음부터 지원하는 네 종류 Agent
- Manifest의 블록별 의미
- 검증에 실패하는 Manifest의 대표 사례 여덟 가지
</div>

## 들어가며

<div class="opener" markdown="1">
<span class="tag">{{icon:question}} 질문</span> 플랫폼은 Agent 코드를 열어 보지 않는데, 어떻게 Agent를 통제할까요?

<span class="tag">{{icon:eye}} 관찰</span> 프레임워크도 언어도 팀마다 다릅니다. 코드를 직접 해석하는 방식으로는 전사 공통 통제를 할 수 없습니다.

<span class="tag">{{icon:bulb}} 해결책</span> Agent마다 **Manifest라는 신분증**을 냅니다. 플랫폼이 통제하고 호출하는 데 필요한 것만 적고, 플랫폼은 그것만 봅니다.
</div>

## 네 종류 Agent

<div class="cards">
<div class="card">{{icon:knowledge}}<b>rag</b><p>사내 문서를 검색해 근거를 붙여 답합니다.</p><span class="sub">Knowledge Backend · Model Gateway</span></div>
<div class="card">{{icon:tools}}<b>tool</b><p>사내·외부 시스템의 API를 불러 일을 처리합니다.</p><span class="sub">Tool Gateway · Credential Broker</span></div>
<div class="card">{{icon:workflow}}<b>workflow</b><p>여러 단계를 순서대로, 때로는 오래 걸려 처리합니다. 중간에 사람 승인이 들어갈 수 있습니다.</p><span class="sub">Durable 실행 · HITL</span></div>
<div class="card">{{icon:agents}}<b>multi-agent</b><p>다른 Agent에게 일을 나눠 맡깁니다.</p><span class="sub">공통 Agent 통신 계약</span></div>
</div>

네 종류 모두 **계약 수준**에서 처음부터 지원합니다. 예제 Manifest가 네 개 있다고 네 종류의 production 엔진이 완성된 것은 아닙니다. 예를 들어 durable 실행은 계약만 있고, 로컬 mock에서는 501을 돌려줍니다.

<div class="point" markdown="1">
**{{icon:knowledge}} RAG의 규칙** 공통 RAG 계약만 지키면 지식 저장소는 바꿔 낄 수 있습니다. 대신 검색할 때 **사용자 권한(ACL)과 데이터 분류로 먼저 걸러야** 합니다. 볼 권한이 없는 문서는 검색 결과에 아예 나오지 않아야 합니다.
</div>

<div class="point" markdown="1">
**{{icon:agents}} Agent끼리 부를 때** 공통 통신 계약(`cross-agent.schema.json`)을 씁니다. 부모 호출 ID, 줄어든 권한 범위, 호출 깊이와 예산이 함께 전달됩니다. 프레임워크 고유의 협업 방식은 adapter로 연결하고, A2A 같은 특정 프로토콜은 선택입니다.
</div>

## Manifest: Agent의 신분증

Manifest는 "이 Agent를 통제하고 호출하는 데 플랫폼이 알아야 할 것"만 적은 JSON입니다. 프레임워크 내부 구현은 적지 않습니다.

<ol class="flow">
<li>{{icon:identity}}<b>누구인가</b><span>apiVersion · kind<br>metadata</span></li>
<li>{{icon:code}}<b>어디 있나</b><span>source</span></li>
<li>{{icon:runtime}}<b>어떻게 도나</b><span>runtime</span></li>
<li>{{icon:tools}}<b>무엇을 쓰나</b><span>capabilities</span></li>
<li>{{icon:user}}<b>누구 권한인가</b><span>identity</span></li>
<li>{{icon:shield}}<b>얼마나 민감한가</b><span>governance</span></li>
<li>{{icon:cloud}}<b>어디 배포하나</b><span>deployment · contracts</span></li>
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

| 블록 | 뜻 | 알아 둘 점 |
|---|---|---|
| `apiVersion`, `kind` | 어떤 계약 버전의 무엇인가 | 현재는 `agent.platform/v1alpha1`. alpha라서 운영 안정성 보증이 아닙니다 |
| `metadata` | ID, 이름, 버전, 소유 팀 | 소유 팀이 없으면 검증에 실패합니다 |
| `source` | 소스가 어디 있는가 | 소스를 올리지 않고 **위치와 불변 revision, artifact digest**만 적습니다 |
| `runtime` | 어떻게 실행하는가 | `executionMode`는 `sync`, `async`, `durable` 중 하나 |
| `capabilities` | 무엇을 쓰는가 | `type`은 네 종류 중 하나. 도구·지식·하위 Agent를 **논리 ID**로 적습니다 |
| `identity` | 누구의 권한으로 일하는가 | `delegated`(사용자 대신) 또는 `independent`(Agent 자신의 권한) |
| `governance` | 얼마나 민감하고 위험한가 | 분류 `public`·`internal`·`confidential`·`restricted`, 위험 `low`·`medium`·`high` |
| `deployment` | 어디에 배포하는가 | `local`, `shared-experiment`, `production` |
| `contracts` | 입출력 형식 | 입력·출력 스키마 URI |

<div class="compare" markdown="1">
<div class="bad" markdown="1">
**{{icon:cross}} 거부되는 source**

```json
"revision": "main"
```

브랜치 이름은 내일 다른 코드를 가리킬 수 있습니다.
</div>
<div class="good" markdown="1">
**{{icon:check}} 통과하는 source**

```json
"revision": "aaaaaaaa…(40자 커밋 해시)",
"artifactDigest": "sha256:…"
```

언제 봐도 같은 코드를 가리킵니다.
</div>
</div>

## 검증에 실패하는 Manifest

`examples/negative/`에는 일부러 틀리게 만든 Manifest가 있습니다. 무엇이 왜 거부되는지 보면 규칙이 빨리 익혀집니다.

| 파일 | 거부되는 이유 |
|---|---|
| {{icon:user}} `missing-owner.json` | 소유 팀이 없다 |
| {{icon:manifest}} `invalid-version.json` | 버전 형식이 틀렸다 |
| {{icon:code}} `mutable-revision.json` | 소스 revision이 `main`처럼 바뀔 수 있는 값이다 |
| {{icon:key}} `unexpected-secret.json` | 허용되지 않은 필드에 비밀값을 넣었다 |
| {{icon:runtime}} `unsupported-mode.json` | 지원하지 않는 실행 모드다 |
| {{icon:shield}} `invalid-classification.json` | 정의되지 않은 데이터 분류다 |
| {{icon:map}} `malformed-uri.json` | URI 형식이 틀렸다 |
| {{icon:tools}} `empty-tools.json` | 도구 Agent인데 도구 목록이 비어 있다 |

직접 검증해 보는 방법은 [30분 실습](07-hands-on.md)에 있습니다.

<div class="check" markdown="1">
**{{icon:question}} 스스로 점검**

<details markdown="1"><summary>Q1. Manifest에 API 키를 넣어 두면 편하지 않을까요?</summary>
넣을 수 없습니다. 스키마가 정의되지 않은 필드를 허용하지 않아서 검증에 실패합니다. 자격증명은 Credential Broker가 호출마다 발급합니다.
</details>

<details markdown="1"><summary>Q2. 사용자를 대신해 일하는 Agent의 identity.mode는 무엇인가요?</summary>
<code>delegated</code>입니다. Agent 자신의 권한으로만 일하면 <code>independent</code>입니다.
</details>
</div>

<div class="summary" markdown="1">
**정리**

- 플랫폼은 rag, tool, workflow, multi-agent 네 종류를 공통 계약으로 지원합니다.
- Manifest는 누구인가·어디 있나·어떻게 도나·무엇을 쓰나·누구 권한인가·얼마나 민감한가·어디 배포하나를 적은 신분증입니다.
- 소스는 불변 revision과 digest로 가리키고, 비밀값은 Manifest에 들어갈 수 없습니다.
</div>

<nav class="pager"><a href="04-trust.md"><small>이전</small><b>신뢰 경계</b></a><a class="next" href="06-lifecycle.md"><small>다음</small><b>내 Agent가 production까지 가는 길</b></a></nav>
