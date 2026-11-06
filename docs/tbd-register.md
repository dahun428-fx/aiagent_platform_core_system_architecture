# TBD 등록부

회사 현황이나 채택 제품을 추정하지 않는다. 예제의 주소·TTL·depth·test score는 합성값이다.

| ID | 우선순위 | 회사 결정 사항 | 책임 역할 | 종료 증거 |
|---|---|---|---|---|
| TBD-01 | P0 | IdP·issuer·audience·workload identity·delegation·STS 지원 | Security | token 검증·교환·취소 통합 테스트 |
| TBD-02 | P0 | tenant 모델·분류체계·지역/국경·egress allowlist | Security/Data | deny/allow matrix |
| TBD-03 | P0 | policy engine·secret/KMS·approval workflow·TTL | Security/Platform | rotation·replay·expiry 검증 |
| TBD-04 | P0 | 첫 업무·owner·위험 등급·production target | Business/SRE | promotion evidence |
| TBD-05 | P0 | 회사 OpenAPI lint/codegen/Gateway 지원 버전 | Platform | 3.1.2 호환성 spike |
| TBD-06 | P1 | CI·Registry·artifact signing·SBOM 제품 | DevOps | 공급망·승격 gate |
| TBD-07 | P1 | SLO·RTO·RPO·latency·quota·비용·용량 수치 | SRE/Business | 측정 baseline·부하/복구 보고서 |
| TBD-08 | P1 | checkpoint/queue/outbox/durable engine | Platform | restart·failover·unknown effect 복구 |
| TBD-09 | P1 | RAG backend·ACL·corpus·retention·삭제 | Data | ACL·검색 품질·삭제 검증 |
| TBD-10 | P1 | 모델 endpoint·지역·fallback·budget | ML/Security | 분류 기반 routing 검증 |
| TBD-11 | P1 | tool endpoint·schema·MCP transport/version | Tools owner | adapter conformance·SSRF 검증 |
| TBD-12 | P1 | 평가 dataset·threshold·관측 exporter·보존 | Quality/SRE | regression·redaction·접근통제 |
| TBD-13 | P2 | A2A protocol adapter 구현·GPU scheduler·Space 구현 제품·Memory 저장소·Guardrail 검사 제품·Tuning 인프라 | Platform | 별도 ADR/적합성 |

