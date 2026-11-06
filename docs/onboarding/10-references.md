# 근거와 참고 자료

> 개발자 가이드와 기술 표준이 근거로 삼은 외부 자료입니다. 각 항목은 해당 자료에서 확인한 내용과, 이 플랫폼에서 반영한 위치를 함께 적습니다. 외부 명세는 개정될 수 있으므로 구현 전에 최신 버전을 다시 확인하십시오.

<div class="goals" markdown="1">
**{{icon:book}} 이 문서를 읽는 법**

- 자료는 영역별로 묶었습니다. 각 장 끝의 **근거와 참고 자료** 상자에서 해당 영역으로 이동합니다.
- **확인한 내용**은 1차 자료에서 확인한 사실이고, **플랫폼 반영**은 그 사실을 근거로 기술 표준에 정한 규칙입니다.
- 2차 자료(해설 글, 업체 비교)는 1차 자료를 확인하지 못한 경우에만 쓰고 그 사실을 표시합니다.
</div>

<div class="ref-group" id="ref-industry" markdown="1">

## 클라우드 Agent 플랫폼

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| AWS Bedrock AgentCore ([FAQ](https://aws.amazon.com/pt/bedrock/agentcore/faqs), [InfoQ 출시 기사](https://infoq.com/news/2025/07/amazon-bedrock-agentcore-launch)) | Runtime, Gateway(기존 API를 Agent용 도구로 변환), Identity(OAuth 2.0, IdP 연동), Memory(단기·장기), Observability를 개별 구성요소로 제공하며 모델에 종속되지 않음 | Core Systems 구분, Memory를 Runtime 하위 구성요소로 정의, Agent Gateway 도구 경로 |
| Microsoft Foundry ([Agent Factory: observability best practices](https://azure.microsoft.com/en-us/blog/agent-factory-top-5-agent-observability-best-practices-for-reliable-ai/), [평가·모니터링·추적 GA](https://techcommunity.microsoft.com/t5/microsoft-foundry-blog/generally-available-evaluations-monitoring-and-tracing-in/ba-p/4502760)) | Agent 구축 방법을 "Agent Factory" 시리즈로 정리. 평가(배포 전)·추적·모니터링을 구분하고 내장 evaluator와 red teaming을 제공 | Agent Factory 명칭, 평가 3단계, red teaming |
| Google Agent Engine ([Memory Bank 개요](https://docs.cloud.google.com/agent-builder/agent-engine/memory-bank/overview)) | 장기 Memory를 사용자 등 특정 범위에 격리. Memory 오염(memory poisoning)을 위험으로 명시하고 IAM 조건으로 범위별 접근을 제한 | Memory 범위 결합, 쓰기 전 검사, 비신뢰 취급 |

</div>

<div class="ref-group" id="ref-gateway" markdown="1">

## AI Gateway

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [Kong AI Gateway](https://developer.konghq.com/ai-gateway/) | 모델 요청·응답에 프롬프트 가드, PII 제거, 응답 검사, 토큰 기반 사용량 제한, 클라우드 guardrail 연동을 적용. AI Prompt Guard는 `user` 역할 메시지만 검사([AI Prompt Guard](https://developer.konghq.com/ai-gateway/policies/ai-prompt-guard/)) | Agent Gateway 모델 경로의 입출력 검사·사용량 기록, 도구 결과·검색 문서를 별도 지점에서 검사 |
| AI Gateway 비교 자료(2차 자료: [Kong](https://konghq.com/performance-comparison/ai-gateway-alternatives), [Maxim](https://www.getmaxim.ai/articles/top-5-envoy-ai-gateway-alternatives-for-llm-routing.md)) | 애플리케이션과 모델 공급사 사이에서 인증, 라우팅, 캐시, 비용 추적, 사용량 제한을 수행하는 관문 패턴 | 모델 경로의 책임 범위. Envoy AI Gateway 공식 문서는 확인하지 못함 |

</div>

<div class="ref-group" id="ref-guardrails" markdown="1">

## Guardrails

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [NVIDIA NeMo Guardrails rail types](https://docs.nvidia.com/nemo/guardrails/about-nemo-guardrails-library/rail-types) | input(모델 호출 전), retrieval(검색 결과), dialog, execution(도구 호출·인자·결과), output(모델 응답 후) rail을 처리 단계별로 구분 | 네 집행 지점 구성 |
| [AWS Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html), [ApplyGuardrail API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ApplyGuardrail.html) | 모델 호출 시 적용하거나 모델 호출 없이 독립 호출 가능. 콘텐츠·프롬프트 공격·민감정보·근거성 검사 | 공통 검사 서비스를 독립 API로 두는 구조 |
| [Azure Prompt Shields](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection) | 사용자 입력과 도구 응답 지점(Agent, Preview)에서 직접·간접 프롬프트 공격 검사. API 자체는 차단하지 않음 | 도구 결과 검사, 검사와 차단의 책임 분리 |
| [Google Model Armor](https://docs.cloud.google.com/security-command-center/docs/model-armor-overview) | 프롬프트와 응답 검사. 차단은 Policy Enforcement Point의 책임. Base64 등 인코딩 내용은 해석하지 않음 | 집행 지점의 차단 책임, 정규화 후 검사 |
| [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | 입출력 필터링, 코드 수준 권한 제어, 고위험 작업의 사람 승인, 외부 콘텐츠 분리를 권고. 완전한 방어 방법은 없다고 명시 | Runtime 실행 제어 지점, 다층 통제 |

</div>

<div class="ref-group" id="ref-otel" markdown="1">

## OpenTelemetry GenAI

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [GenAI agent spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans) | Agent 호출 span `invoke_agent {gen_ai.agent.name}`, 생성 span `create_agent`. 기본 GenAI span 규격을 확장 | Agent Observability span 규격 |
| [GenAI spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans) | 추론 span 이름 `{gen_ai.operation.name} {gen_ai.request.model}`, `gen_ai.provider.name` 필수. 규격 상태는 Development | span 규격, 버전 고정 규칙 |
| [W3C Trace Context](https://www.w3.org/TR/trace-context/) | `traceparent`, `tracestate` 헤더 표준 | 전 구간 trace context 전파 |

</div>

<div class="ref-group" id="ref-mcp" markdown="1">

## MCP

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [MCP Authorization (2026-07-28)](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization), [(2025-06-18)](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization) | MCP 서버는 OAuth 2.1 resource server, 클라이언트는 RFC 8707 resource indicator 사용, RFC 9728 Protected Resource Metadata로 인가 서버 발견, 서버는 audience 검증 | Agent Gateway 도구 경로의 MCP 인가 프로파일, revision 고정 |
| [MCP Security Best Practices](https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices) | MCP 서버에 발급되지 않은 토큰 수용 금지, 로컬 서버 실행 전 동의, URL 검증, 최소 scope | 토큰 passthrough 금지, 도구 경로의 입력 검증 |

</div>

<div class="ref-group" id="ref-a2a" markdown="1">

## A2A

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [A2A 1.0.0 Specification](https://a2a-protocol.org/latest/specification/) | AgentCard 필드, AgentInterface의 `tenant`, 인증된 확장 카드(GetExtendedAgentCard), JWS 서명과 JCS 정규화, HTTPS 필수. 규범 원본은 `spec/a2a.proto` | [Agent Card](13-agent-card.md) 필드·서명·확장 카드 규칙 |
| [A2A Agent Discovery](https://a2a-protocol.org/latest/topics/agent-discovery/) | `/.well-known/agent-card.json`(RFC 8615), 레지스트리 API는 표준으로 정하지 않음, 민감 정보가 있는 카드는 인증·인가로 보호, 정적 시크릿 대신 대역 외 동적 자격증명 권장 | 사내 Agent의 공개 카드 금지, Registry 조회 API 정의 |
| [What's new in A2A v1.0](https://a2a-protocol.org/latest/whats-new-v1/) | 0.3 대비 `url`·`preferredTransport`·`additionalInterfaces` 등이 `supportedInterfaces`로 통합, 열거값 표기 변경, Implicit·Password OAuth flow 제거 | A2A 1.0.0 기준 고정 |

</div>

<div class="ref-group" id="ref-identity" markdown="1">

## IETF·OAuth

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [RFC 8693 OAuth Token Exchange](https://www.rfc-editor.org/rfc/rfc8693.html), [RFC 9700 OAuth Security BCP](https://www.rfc-editor.org/rfc/rfc9700.html) | 위임·대리 시나리오의 토큰 교환, OAuth 보안 권고 | Credential Broker의 토큰 교환 매핑 |
| [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) | HTTP API 오류의 기계 판독 형식 | Agent Platform APIs 오류 형식 |
| RFC 7515 JWS, RFC 8785 JCS | JSON 서명과 정규화 | Agent Card 서명 |
| Agent 인증 IETF 초안(2차 자료: [AIMS 해설](https://dev.to/iamdevbox/ietf-aims-how-ai-agents-authenticate-with-spiffe-and-oauth-20-2g0i), [On-Behalf-Of](https://workos.com/blog/oauth-on-behalf-of-ai-agents), [draft-lundholm-kaif-00](https://mirror.apps.cam.ac.uk/pub/doc/internet-drafts/draft-lundholm-kaif-00.xml)) | SPIFFE·OAuth·토큰 교환을 조합한 Agent 인증 초안이 진행 중이며 표준으로 확정되지 않음 | 안정 규격(RFC 8693, SPIFFE)만 채택하고 초안은 계약에 고정하지 않음 |

</div>

<div class="ref-group" id="ref-security" markdown="1">

## 보안 프레임워크

| 자료 | 확인한 내용 | 플랫폼 반영 |
|---|---|---|
| [OWASP Top 10 for Agentic Applications 2026](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026) | 자율 Agent의 주요 보안 위험 10개 범주(ASI01~ASI10). 공식 페이지에서는 표지와 설명만 확인했으며 항목별 본문은 확인하지 못함 | 위협 모델 보강 대상. 항목별 대응표는 본문 확인 후 작성 |
| [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) | 프롬프트 인젝션 완화 권고 | Guardrails, 신뢰하지 않는 입력 규칙 |

</div>

<nav class="pager"><a href="08-reading-the-spec.md"><small>이전</small><b>기술 표준 해석과 FAQ</b></a><a class="next" href="09-glossary.md"><small>다음</small><b>주요 용어 정의</b></a></nav>
