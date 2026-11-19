# Agent Factory와 Manifest

> 개발자 가이드 문서입니다. 규범은 [아키텍처](../architecture.md), [Core Systems](../core-systems.md) 기술 표준 문서와 계약 `agent-manifest.schema.json`이 기준입니다.

{{journey:2}}

<div class="sofar" markdown="1">
**지금까지** 서연이 "청구서 INV-2048 요약해 줘"를 보냈고, 정문이 서연을 확인한 뒤 `invoice-summary`라는 Agent를 찾았습니다. 이 Agent는 어떻게 거기 있게 됐을까요. 3주 전으로 돌아갑니다.
</div>

## 장면

3주 전 민준은 템플릿 폴더를 복사해 `invoice-summary`를 만들었습니다. 코드를 플랫폼에 올리지는 않았습니다. 대신 이 Agent가 무엇을 쓰고 무엇을 할 수 있는지 적은 신청서 한 장, 곧 Manifest를 채웠습니다. 첫 검증은 실패했습니다. 소스의 `revision`에 `main`이라고 적었기 때문입니다. 민준은 그 자리를 커밋 번호로 바꿨고, 검증을 통과한 버전이 목록(Registry)에 올랐습니다.

<div class="point" markdown="1">
**{{icon:bulb}} Agent Factory가 없다면** 플랫폼은 Agent가 어떤 도구를 쓰고 어떤 데이터를 다루는지 알 길이 없어, 통제하려면 팀마다 다른 코드를 일일이 읽어야 합니다.
</div>

## 무슨 일이 일어나나

<ol class="flow">
<li data-say="빈 화면에서 시작하지 않습니다. 동작하는 템플릿 폴더를 복사해 고칩니다.">{{icon:code}}<b>1. 틀을 복사한다</b><span>templates/agents/</span></li>
<li data-say="Manifest에 이 Agent의 이름과 버전, 쓰는 도구, 필요한 권한, 다루는 데이터의 등급을 적습니다.">{{icon:manifest}}<b>2. 신청서(Manifest)를 채운다</b><span>agent-manifest.json</span></li>
<li data-say="내 PC에서 agentctl validate가 형식을 검사합니다. 틀린 곳은 올리기 전에 잡힙니다." class="hi">{{icon:test}}<b>3. 검사가 틀린 곳을 잡는다</b><span>agentctl validate · conformance</span></li>
<li data-say="통과한 버전이 Registry에 오릅니다. 한번 오른 버전은 내용이 바뀌지 않습니다.">{{icon:control}}<b>4. 통과한 버전이 목록에 오른다</b><span>Registry · 불변 버전</span></li>
</ol>

## 실물 보기

`invoice-summary` Manifest에서 플랫폼의 동작을 정하는 세 블록입니다.

<!-- kind: example -->

```json
{
  "capabilities": {
    "type": "tool",
    "tools": ["tool-erp-read"],
    "knowledge": [],
    "agents": []
  },
  "identity": {
    "mode": "delegated",
    "requiredScopes": ["agents.invoke", "models.invoke", "tools.read"]
  },
  "governance": {
    "classification": "confidential",
    "risk": "medium",
    "policyProfile": "policy-finance",
    "evaluationProfile": "eval-finance"
  }
}
```

- `capabilities.tools`: 이 줄 때문에 `tool-erp-read`를 부를 수 있습니다. 여기 없는 도구는 코드가 불러도 실행 중에 거절됩니다.
- `identity.mode`: `delegated`는 부른 사람을 대신해 일한다는 뜻입니다. 서연의 권한 안에서만 움직입니다.
- `identity.requiredScopes`: 이 세 권한이 없는 사람이 부르면 코드를 실행하기 전에 돌려보냅니다.
- `governance.classification`: `confidential` 때문에 이 Agent의 모델 호출은 회사 안 모델로만 갑니다.
- `governance.risk`: `medium`은 프로덕션에 올릴 때 사람의 승인이 필요한 정도를 정합니다.

민준이 처음 검증했을 때와 고친 뒤의 터미널 출력입니다.

<!-- kind: run boundary: local -->

```text
$ python scripts/agentctl.py validate examples/negative/mutable-revision.json
[
  {
    "file": "examples/negative/mutable-revision.json",
    "valid": false,
    "error": "Invalid or unreadable Agent Manifest"
  }
]

$ python scripts/agentctl.py validate examples/agents/invoice-summary/agent-manifest.json
[
  {
    "file": "examples/agents/invoice-summary/agent-manifest.json",
    "valid": true
  }
]
```

- CLI는 실패 이유를 말해 주지 않습니다. 이유는 이렇습니다. `main`은 브랜치 이름이라 내일이면 다른 코드를 가리킵니다. `revision`은 40자 커밋 번호여야 등록한 코드와 실행되는 코드가 같다고 말할 수 있습니다.
- `valid: true`는 형식이 맞다는 뜻입니다. 업무에 써도 된다는 승인은 아닙니다.

<details class="more" markdown="1"><summary>더 보기: Manifest 전문과 블록별 의미</summary>

로컬 예제 `examples/agents/invoice-summary/agent-manifest.json` 전문입니다. 로컬에서는 도구 이름이 대역 `tool-search`입니다.

<!-- kind: run boundary: local -->

```json
{
  "apiVersion": "agent.platform/v1alpha1",
  "kind": "Agent",
  "metadata": {"id": "invoice-summary", "name": "Invoice summary Agent", "version": "0.1.0", "owner": {"team": "finance"}},
  "source": {
    "repository": "https://example.invalid/agents/invoice-summary.git",
    "revision": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "artifactDigest": "sha256:bbbb…"
  },
  "runtime": {"framework": "custom", "adapter": "python-inprocess-v1", "entrypoint": "agent:create", "executionMode": "sync"},
  "capabilities": {"type": "tool", "tools": ["tool-search"], "knowledge": [], "agents": []},
  "identity": {"mode": "delegated", "requiredScopes": ["agents.invoke", "models.invoke", "tools.read"]},
  "governance": {"classification": "confidential", "risk": "medium", "policyProfile": "policy-demo", "evaluationProfile": "eval-demo"},
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
| `source` | 소스 참조 | 소스를 올리지 않고 **저장소 위치, 불변 revision, artifact digest**를 선언합니다 |
| `runtime` | 런타임 설정 | `executionMode`는 `sync`, `async`, `durable` 중 하나입니다 |
| `capabilities` | 기능 및 의존 리소스 | 도구·지식·하위 Agent를 **논리 ID**로 선언합니다 |
| `identity` | 실행 주체와 권한 모드 | `delegated`(사용자 위임) 또는 `independent`(Agent 자체 권한)이며, 필요 scope를 선언합니다 |
| `governance` | 데이터 분류·위험도·정책 | 분류 `public`·`internal`·`confidential`·`restricted`, 위험도 `low`·`medium`·`high`, 정책·평가 프로파일 |
| `deployment` | 배포 설정 | 프로파일 `local`, `shared-experiment`, `production` |
| `contracts` | 입출력 계약 | 입력·출력 JSON Schema URI |
</details>

<details class="more" markdown="1"><summary>더 보기: Agent 유형 다섯 가지</summary>

| `capabilities.type` | 하는 일 | 이 가이드의 예 |
|---|---|---|
| `tool` | 사내·외부 시스템의 API를 불러 일합니다 | `invoice-summary` |
| `workflow` | 여러 단계를 차례로 처리하고 사람 승인을 기다릴 수 있습니다. 실행 모드는 `durable`이어야 합니다 | `invoice-mailer` |
| `rag` | 사내 문서를 검색해 근거와 함께 답합니다 | `policy-search`. "출장비 한도가 얼마야"에 규정 문서를 찾아 답함 |
| `multi-agent` | 하위 Agent에게 일을 맡깁니다 | `expense-settlement`. 출장 정산 중에 `invoice-summary`를 부름 |
| `message` | 도구 없이 모델과 대화만 합니다 | `templates/agents/message` |

유형은 모두 **계약 수준에서** 지원합니다. 로컬 mock이 실행하는 것은 `sync` 모드뿐이고 `durable` 실행은 501을 돌려줍니다.

`rag` 유형은 검색할 때 사용자 권한(ACL)과 데이터 분류로 **먼저** 걸러야 합니다. 볼 수 없는 문서는 검색 결과에 들어가지 않습니다. `multi-agent` 유형이 하위 Agent를 부를 때는 공통 계약(`cross-agent.schema.json`)으로 상위 호출 번호, 줄어든 권한 범위, 호출 깊이와 예산을 함께 넘깁니다([Agent Card와 Agent 간 통신](13-agent-card.md)).
</details>

## 직접 해 보기

<div class="sim" data-sim="manifest-lint"></div>

<ol class="mission">
<li><code>revision</code>을 <code>main</code>으로 바꾸고 검증해 보세요.</li>
<li>도구 목록을 비워 보세요. 이것은 등록에 실패한 것인가요, 등록한 뒤에 거절된 것인가요.</li>
<li>모두 끄고 통과하는 Manifest를 확인하세요.</li>
</ol>

## 잘못되면

**민준이 `revision`에 브랜치 이름을 적으면** 검증에서 실패합니다. 플랫폼은 "등록한 그 코드"가 실행된다는 것을 보장해야 하는데, `main`은 내일이면 다른 커밋을 가리킵니다. 커밋 SHA 40자와 산출물 digest를 적습니다.

**민준이 편하게 하려고 Manifest에 ERP의 API 키를 적으면** 검증에서 실패합니다. Manifest 스키마는 정의되지 않은 필드를 받지 않고, 자격증명을 적을 자리가 없습니다. 접근 자격증명은 호출할 때마다 Credential Broker가 발급합니다([Agent Identity](16-agent-identity.md)).

<details class="more" markdown="1"><summary>더 보기: 도구 목록을 비울 때, 그리고 나머지 다섯 가지</summary>

**유일한 도구를 지워 `capabilities.tools`가 비면** `tool` 유형은 도구가 하나 이상 있어야 하므로 검증에서 실패합니다(`empty-tools`). 이것은 **등록 전** 실패입니다. Manifest는 유효한데 코드가 적지 않은 도구를 부르는 **실행 중** 403과는 다른 실패입니다([Agent Tools](15-agent-tools.md)).

`examples/negative/`에는 검증 실패를 확인하는 Manifest 8종이 있습니다.

| 파일 | 실패 원인 |
|---|---|
| `mutable-revision.json` | `main` 등 가변 revision |
| `unexpected-secret.json` | 정의되지 않은 필드에 시크릿 |
| `empty-tools.json` | tool 유형인데 도구 목록이 빔 |
| `missing-owner.json` | 소유 팀 누락 |
| `invalid-version.json` | 버전을 `latest`로 적음 |
| `unsupported-mode.json` | 지원하지 않는 실행 모드 |
| `invalid-classification.json` | 정의되지 않은 데이터 분류 |
| `malformed-uri.json` | URI 형식 오류 |
</details>

## 내가 할 일

1. 템플릿 폴더를 복사합니다. 도구를 쓰면 `templates/agents/tool`, 대화만 하면 `templates/agents/message`입니다.
2. Manifest의 ID, 소유 팀, 도구, 권한, 데이터 분류를 내 Agent에 맞게 고칩니다.
3. `agentctl validate`로 형식을 검사합니다.
4. `agentctl conformance`로 플랫폼 규칙 11항목을 검사합니다.
5. `agentctl run`으로 띄워 호출해 봅니다.

**내 PC에서 해 보기** 저장소 루트에서 실행합니다. 따라 하는 전체 절차는 [내 Agent 연결과 적합성 검증](14-connect-your-agent.md)에 있습니다.

```bash
python scripts/agentctl.py validate examples/agents/invoice-summary/agent-manifest.json
python scripts/agentctl.py conformance examples/agents/invoice-summary
python scripts/agentctl.py run --port 8765 --agents-dir examples/agents
```

<div class="scope" markdown="1">
**제공 범위 (v0.1)**

| 항목 | 등급 | 확인하는 곳 |
|---|---|---|
| Manifest 스키마 검증, 실패 fixture 8종, 템플릿 2종, 적합성 11항목 | 실행 | `scripts/agentctl.py`, `examples/negative/`, `templates/agents/` |
| 로컬 Registry(폴더를 읽어 등록) | 실행 | `agentctl run --agents-dir` |
| CI 게이트, 전사 Registry 서비스 | 정의 | [Core Systems](../core-systems.md) |
</div>

## 규칙으로 정리

- 소스는 개발자의 저장소에 둡니다. Factory는 소스 업로드를 요구하지 않습니다(MUST NOT). 장면 ②
- Manifest는 플랫폼이 Agent를 통제하고 호출하는 데 필요한 정보만 선언합니다. 인증 수단이 아니며 자격증명을 담지 않습니다(MUST NOT). 장면 ②
- 소스는 불변 revision과 artifact digest로 참조합니다(MUST). 등록된 버전은 바뀌지 않습니다.
- 등록은 "존재를 알렸다"는 뜻이고 프로덕션 승인이 아닙니다([수명주기와 프로덕션 승인](06-lifecycle.md)).
- Factory의 도구는 AI Platform Applications의 DevTools로 제공됩니다([AI Platform Applications](20-applications.md)).

<div class="terms" markdown="1">
<span class="label">주요 용어</span> [Agent Factory](09-glossary.md#term-factory) [Manifest](09-glossary.md#term-manifest) [Registry](09-glossary.md#term-registry) [불변 버전](09-glossary.md#term-immutable) [위임 모드](09-glossary.md#term-delegated) [데이터 분류](09-glossary.md#term-classification) [적합성 검증](09-glossary.md#term-conformance) [RAG](09-glossary.md#term-rag)
</div>

## 한 문장으로

Agent를 만들어 올리는 곳이고, 무엇을 쓰고 무엇을 할 수 있는지 적은 신청서를 먼저 검사합니다.

<div class="check" markdown="1">
**{{icon:question}} 이해 점검**

<details markdown="1"><summary>Q1. 민준이 도구 목록을 비운 Manifest를 검증했습니다. 등록에 실패한 것인가요, 등록한 뒤에 거절된 것인가요?</summary>
등록에 실패한 것입니다. tool 유형은 도구가 하나 이상 있어야 해서 검증 단계에서 멈춥니다. 등록한 뒤에 거절되는 것은 유효한 Manifest에 없는 도구를 코드가 부를 때입니다.
</details>

<details markdown="1"><summary>Q2. Manifest에 API 키를 적으면 어떻게 되나요?</summary>
검증에 실패합니다. 스키마가 정의되지 않은 필드를 받지 않습니다. 자격증명은 Credential Broker가 호출 시점에 발급합니다.
</details>

<details markdown="1"><summary>Q3. agentctl validate가 valid: true를 돌려줬습니다. 이제 업무에 써도 되나요?</summary>
아닙니다. 형식이 맞다는 뜻일 뿐입니다. 적합성 검사, 평가, 프로덕션 승인을 거쳐야 업무 요청을 받습니다.
</details>
</div>

<div class="refs" markdown="1">
**{{icon:book}} 근거와 참고 자료**

- Agent 선언과 Registry를 두는 플랫폼 사례: [클라우드 Agent 플랫폼](10-references.md#ref-industry)
</div>

다음 장면은 ③입니다. 등록된 `invoice-summary`의 코드가 실제로 어떻게 실행되는지를 봅니다.
