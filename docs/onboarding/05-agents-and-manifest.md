# 네 종류 Agent와 Manifest

> 온보딩 안내서입니다. 규범은 [Agent Manifest 스키마](../../contracts/agent-manifest.schema.json)가 기준입니다.

## 플랫폼이 처음부터 지원하는 네 가지 Agent

| 종류 | 무엇을 하나 | 주로 쓰는 플랫폼 구성요소 |
|---|---|---|
| `rag` | 사내 문서를 검색해 근거를 붙여 답한다 | Knowledge(RAG) Backend, Model Gateway |
| `tool` | 사내·외부 시스템의 API를 불러 일을 처리한다 | Tool Gateway, Credential Broker |
| `workflow` | 여러 단계를 순서대로, 때로는 오래 걸려 처리한다. 중간에 사람 승인이 들어갈 수 있다 | Durable 실행, HITL 승인 |
| `multi-agent` | 다른 Agent에게 일을 나눠 맡긴다 | 공통 Agent 간 통신 계약 |

네 종류 모두 **계약 수준**에서 처음부터 지원합니다. 다만 Manifest 예제가 네 개 있다고 해서 네 종류의 production 엔진이 완성됐다는 뜻은 아닙니다. 예를 들어 durable 실행은 계약만 있고, 로컬 mock에서는 501을 돌려줍니다.

### RAG는 검색 엔진을 강제하지 않는다

공통 RAG 계약만 지키면 지식 저장소는 바꿔 낄 수 있습니다. 회사가 하나의 벡터 DB나 검색 엔진을 강제하지 않습니다. 대신 검색할 때 **사용자 권한(ACL)과 데이터 분류로 먼저 걸러야** 합니다. 볼 권한이 없는 문서는 검색 결과에 아예 나오지 않아야 합니다.

### Agent끼리 부를 때

다른 Agent를 부를 때는 공통 통신 계약(`cross-agent.schema.json`)을 씁니다. 부모 호출 ID, 줄어든 권한 범위, 호출 깊이와 예산이 함께 전달됩니다. 프레임워크 고유의 협업 방식은 adapter로 연결하고, A2A 같은 특정 프로토콜은 선택 사항입니다.

## Manifest: Agent의 신분증

플랫폼은 Agent의 코드를 들여다보지 않습니다. 대신 **Manifest**라는 JSON 파일로 Agent를 이해합니다. Manifest는 "이 Agent를 통제하고 호출하는 데 플랫폼이 알아야 할 것"만 적습니다. 프레임워크 내부 구현은 적지 않습니다.

이 패키지에 들어 있는 tool Agent 예제(`examples/manifests/tool.json`)를 부분별로 읽어 보겠습니다.

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
| `source` | 소스가 어디 있는가 | 소스를 올리는 게 아니라 **위치와 불변 revision, artifact digest**만 적습니다. 브랜치 이름처럼 바뀌는 값은 거부됩니다 |
| `runtime` | 어떻게 실행하는가 | `executionMode`는 `sync`, `async`, `durable` 중 하나 |
| `capabilities` | 무엇을 쓰는가 | `type`은 네 종류 중 하나. 도구·지식·하위 Agent를 **논리 ID**로 적습니다 |
| `identity` | 누구의 권한으로 일하는가 | `delegated`(사용자 대신) 또는 `independent`(Agent 자신의 권한) |
| `governance` | 얼마나 민감하고 위험한가 | 분류는 `public`·`internal`·`confidential`·`restricted`, 위험은 `low`·`medium`·`high` |
| `deployment` | 어디에 배포하는가 | `local`, `shared-experiment`, `production` |
| `contracts` | 입출력 형식 | 입력·출력 스키마 URI |

## 검증에 실패하는 Manifest

`examples/negative/`에는 일부러 틀리게 만든 Manifest가 있습니다. 무엇이 왜 거부되는지 보면 규칙이 빨리 익혀집니다.

| 파일 | 거부되는 이유 |
|---|---|
| `missing-owner.json` | 소유 팀이 없다 |
| `invalid-version.json` | 버전 형식이 틀렸다 |
| `mutable-revision.json` | 소스 revision이 바뀔 수 있는 값이다 |
| `unexpected-secret.json` | 허용되지 않은 필드에 비밀값을 넣었다 |
| `unsupported-mode.json` | 지원하지 않는 실행 모드다 |
| `invalid-classification.json` | 정의되지 않은 데이터 분류다 |
| `malformed-uri.json` | URI 형식이 틀렸다 |
| `empty-tools.json` | 도구 Agent인데 도구 목록이 비어 있다 |

직접 검증해 보는 방법은 [30분 실습](07-hands-on.md)에 있습니다.

## 더 읽을거리

- Manifest 스키마 원문: [agent-manifest.schema.json](../../contracts/agent-manifest.schema.json)
- 4종 예제 Manifest: [RAG](../../examples/manifests/rag.json), [Tool](../../examples/manifests/tool.json), [Workflow](../../examples/manifests/workflow.json), [Multi-Agent](../../examples/manifests/multi-agent.json)
- Agent 간 통신 계약: [cross-agent.schema.json](../../contracts/cross-agent.schema.json)
- 계약 버전 규칙: [계약 변경](../versioning.md)

이전: [신뢰 경계](04-trust.md) · 다음: [내 Agent가 production까지 가는 길](06-lifecycle.md)
