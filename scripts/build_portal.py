"""Emit generated portal files as JSON for native Write/Edit, or rebuild with --write."""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
import markdown
from markdown.extensions.toc import TocExtension, slugify_unicode
from portal_icons import expand as expand_icons, svg as icon_svg

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "portal"
sources = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"), key=Path.as_posix), *sorted((ROOT / "adr").glob("*.md"), key=Path.as_posix), *sorted((ROOT / "contracts").glob("*.json"), key=Path.as_posix), *sorted((ROOT / "examples/manifests").glob("*.json"), key=Path.as_posix), *sorted((ROOT / "sources").glob("*.md"), key=Path.as_posix)]
mapping = {p.resolve(): p.relative_to(ROOT).as_posix().replace("/", "--").replace(".md", ".html").replace(".json", ".html") for p in sources}


def link(p):
    if p.endswith(".html"):
        return p
    return mapping.get((ROOT / p).resolve(), "../" + p)


onboarding = [
    ("docs/onboarding/01-why.md", "플랫폼 도입 배경과 설계 원칙", "5분", "팀별 Agent 개발 환경과 전사 공통 보안·운영 통제의 책임 구분", "target"),
    ("docs/onboarding/02-big-picture.md", "Core Systems 아키텍처", "15분", "10개 Core System의 층 구조, 책임, 진입·반출 경계와 배치 관점", "map"),
    ("docs/onboarding/03-one-request.md", "Agent 요청 처리 흐름", "15분", "Agent Platform APIs 진입부터 Agent Gateway를 통한 모델·도구 호출, 실행 추적까지", "trace"),
    ("docs/onboarding/05-agents-and-manifest.md", "Agent Factory와 Manifest 명세", "10분", "생성·선언·검증·등록 흐름, Agent 유형과 Manifest 검증 규칙", "manifest"),
    ("docs/onboarding/11-runtime-memory.md", "Agent Runtime과 Memory", "10분", "framework adapter, Durable 실행, 단기·장기 Memory의 범위와 규칙", "runtime"),
    ("docs/onboarding/04-trust.md", "신뢰 경계와 Guardrails", "15분", "신뢰하지 않는 입력, Guardrail의 공통 검사 서비스와 네 집행 지점", "shield"),
    ("docs/onboarding/12-observability-evaluation.md", "Agent Observability와 Agent Evaluation", "10분", "OpenTelemetry GenAI 실행 추적과 평가 3단계", "eye"),
    ("docs/onboarding/13-agent-card.md", "Agent Card와 Agent 간 통신", "10분", "A2A 1.0.0 Agent Card의 필드, 확장 카드, 서명과 Registry 발행 규칙", "agents"),
    ("docs/onboarding/06-lifecycle.md", "Agent 수명주기·Tuning과 프로덕션 승인", "10분", "등록·검증·평가·승인 단계, 승인 요건, Agent Tuning 개선 흐름", "rocket"),
    ("docs/onboarding/07-hands-on.md", "로컬 환경 구성 및 호출 실습", "30분", "로컬 mock 환경에서 Manifest 검증, Agent 호출 및 오류 응답 확인", "code"),
    ("docs/onboarding/14-connect-your-agent.md", "내 Agent 연결과 적합성 검증", "30분", "템플릿으로 adapter와 Manifest를 작성해 새 Agent ID로 호출하고 적합성 9항목 통과", "agent"),
    ("docs/onboarding/08-reading-the-spec.md", "기술 표준 해석과 FAQ", "10분", "MUST·SHOULD·MAY, TBD 및 버전 표기의 의미", "question"),
    ("docs/onboarding/10-references.md", "근거와 참고 자료", "참조용", "클라우드 Agent 플랫폼, OpenTelemetry, MCP, A2A, IETF, OWASP 등 외부 근거", "book"),
    ("docs/onboarding/09-glossary.md", "주요 용어 정의", "참조용", "Core Systems, 실행 모델 및 기술 계약의 주요 용어", "book"),
]
navigation = [
    ("개발자 가이드", [("index.html", "가이드 개요")] + [(p, t) for p, t, _, _, _ in onboarding]),
    ("설계 정의", [("docs/core-systems.md", "Core Systems"), ("docs/architecture.md", "아키텍처"), ("docs/agent-tools.md", "Agent Tools"), ("docs/identity-and-credentials.md", "Agent Identity"), ("docs/security.md", "보안 경계"), ("docs/guardrails.md", "Guardrails"), ("docs/memory.md", "Memory"), ("docs/agent-card.md", "Agent Card"), ("docs/execution.md", "Durable / HITL")]),
    ("운영 정의", [("docs/operating-model.md", "운영·평가"), ("docs/observability.md", "Observability"), ("docs/evaluation.md", "Evaluation"), ("docs/agent-tuning.md", "Agent Tuning"), ("docs/deployment.md", "배포 프로파일"), ("docs/versioning.md", "계약 변경"), ("docs/ci-integration.md", "CI 통합"), ("docs/glossary.md", "용어와 규범")]),
    ("레퍼런스", [("catalog.html", "계약 · 예제"), ("diagrams.html", "아키텍처 도식 9종"), ("docs/tbd-register.md", "TBD 등록부"), ("docs/release-scope.md", "제공 범위와 한계")]),
    ("결정 기록", [("records.html", "결정 기록과 이력")]),
]


def layout(title, body, current="", source=None, toc=""):
    nav = '<a href="index.html" class="brand">Agent Platform<small>Technical Standard v0.1</small></a>'
    for group, entries in navigation:
        nav += "<h2>" + group + "</h2>"
        for p, label in entries:
            href = link(p)
            active = ' aria-current="page"' if href == current else ""
            nav += f'<a href="{href}"{active}>{label}</a>'
    source_link = f'<p class="file-link">원본 파일: <a href="../{html.escape(source)}">{html.escape(source)}</a></p>' if source else ""
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self' file:; script-src 'self' file:; style-src 'self' file:; img-src 'self' file: data:; connect-src 'none'; object-src 'none'; base-uri 'none'">
<title>{html.escape(title)} · Agent Platform</title><link rel="stylesheet" href="styles.css">
<script defer src="search-index.js"></script><script defer src="glossary-index.js"></script><script defer src="app.js"></script><script defer src="interactive.js"></script></head>
<body><a class="skip" href="#main">본문으로 이동</a><aside id="sidebar" class="sidebar"><nav aria-label="주 탐색">{nav}</nav></aside>
<div class="layout"><header><button class="menu" id="menu" aria-controls="sidebar" aria-expanded="false">메뉴</button><span>전사 공통 AI Agent Platform</span><span class="version">v0.1</span>
<div class="search"><label for="search">문서·계약 검색</label><input id="search" type="search" placeholder="문서·계약 검색  ( / )" autocomplete="off"><div id="results" class="search-results" role="status" aria-live="polite" hidden></div></div></header>
<main id="main" class="content{" has-toc" if toc else ""}" tabindex="-1"><article class="doc">{body}{source_link}</article>{toc}</main><footer>AI Agent Platform 기술 표준 v0.1 · 회사 환경 / 제품 / 운영 수치 TBD · 로컬 오프라인 열람 지원</footer></div></body></html>"""


def rewrite_links(body, source):
    def replace(m):
        target = html.unescape(m.group(2))
        parts = urlsplit(target)
        if parts.scheme or target.startswith("#"):
            return m.group(0)
        resolved = (source.parent / unquote(parts.path)).resolve()
        if resolved in mapping:
            href = mapping[resolved] + ("#" + parts.fragment if parts.fragment else "")
            # Generated Markdown heading IDs are not stable across languages. Link to module top.
        else:
            try:
                href = "../" + resolved.relative_to(ROOT).as_posix()
            except ValueError:
                href = "#"
        return m.group(1) + '="' + html.escape(href) + '"'
    return re.sub(r'\b(href|src)="([^"]+)"', replace, body)


files = {}
index = []
for source in sources:
    text = source.read_text(encoding="utf-8")
    relative = source.relative_to(ROOT).as_posix()
    title = re.search(r"^# (.+)", text, re.M).group(1) if source.suffix == ".md" else source.name
    if source.suffix == ".json" or relative.startswith("sources/") and source.name != "README.md":
        body = "<h1>" + html.escape(title) + "</h1><pre><code>" + html.escape(text) + "</code></pre>"
    else:
        body = markdown.markdown(text, extensions=["tables", "fenced_code", "md_in_html", TocExtension(slugify=slugify_unicode, toc_depth="2")])
        body = rewrite_links(body, source)
        body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
        body = expand_icons(body)
    out = mapping[source.resolve()]
    toc = ""
    sections = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    if len(sections) >= 3:
        toc = '<nav class="toc" aria-label="이 문서의 목차"><h2>이 문서에서</h2>' + "".join(f'<a href="#{i}">{re.sub(r"<[^>]+>", "", t)}</a>' for i, t in sections) + "</nav>"
    files["portal/" + out] = layout(title, body, out, relative, toc)
    index.append({"title": title, "href": out, "text": text})

G = "docs--onboarding--"
home = f"""<h1>AI Agent Platform 개발자 가이드</h1>
<p class="lead thesis">팀은 원하는 프레임워크와 도구로 Agent를 만들고, 플랫폼은 그 Agent를 <b>등록·실행·통제·관측·평가</b>하는 공통 계층을 제공합니다. 아래 10개 Core System이 그 공통 계층이며, 이 가이드는 각 Core System의 책임과 Agent가 이 구조 위에서 실행되는 방식을 정의합니다.</p>
<div class="stack home-stack" aria-label="AI Agent Platform Core Systems 구성도">
<a href="{G}07-hands-on.html" class="s-app"><b>{{{{icon:laptop}}}} AI Platform Applications</b><small>DevTools(CLI · SDK · 템플릿) · Space(공유 작업 공간)</small></a>
<a href="{G}03-one-request.html" class="s-api"><b>{{{{icon:gateway}}}} Agent Platform APIs</b><small>모든 진입의 단일 관문: 인증 · 테넌트 인가 · Agent 해석 · 멱등성</small></a>
<a href="{G}05-agents-and-manifest.html" class="s-factory"><b>{{{{icon:manifest}}}} Agent Factory</b><small>생성 · Manifest 선언 · 검증 · 등록</small></a>
<a href="{G}11-runtime-memory.html" class="s-runtime"><b>{{{{icon:runtime}}}} Agent Runtime</b><small>framework adapter · Durable 실행 · Memory</small></a>
<a href="{G}04-trust.html" class="s-tools"><b>{{{{icon:tools}}}} Agent Tools</b><small>Tool Registry · 도구 정책</small></a>
<a href="{G}04-trust.html" class="s-identity"><b>{{{{icon:identity}}}} Agent Identity</b><small>사용자·workload Identity · Credential Broker</small></a>
<a href="{G}12-observability-evaluation.html" class="s-obs"><b>{{{{icon:eye}}}} Agent Observability</b><small>실행 추적 · 지표 · 로그</small></a>
<a href="{G}12-observability-evaluation.html" class="s-eval"><b>{{{{icon:test}}}} Agent Evaluation</b><small>배포 전 평가 · 운영 모니터링</small></a>
<a href="{G}04-trust.html" class="s-gateway"><b>{{{{icon:gateway}}}} Agent Gateway</b><small>모든 반출의 단일 관문: 모델 경로 · 도구 경로 · Guardrail 집행</small></a>
<a href="{G}06-lifecycle.html" class="s-tuning"><b>{{{{icon:rocket}}}} Agent Tuning</b><small>평가 기반 개선</small></a>
<a href="{G}02-big-picture.html" class="s-ext-app"><b>{{{{icon:user}}}} External Applications and Solutions</b><small>Agent Platform APIs로만 접근</small></a>
<a href="{G}02-big-picture.html" class="s-ext-tool"><b>{{{{icon:cloud}}}} External Tools and Models</b><small>Agent Gateway로만 접근</small></a>
<a href="{G}02-big-picture.html" class="s-infra"><b>{{{{icon:server}}}} 실행 인프라 (Distributed Execution Plane)</b><small>개발자 로컬 · Mac mini · 사내 서버 · 클라우드 · 모델 endpoint</small></a>
</div>
<p class="caption">블록을 선택하면 해당 Core System을 설명하는 장으로 이동합니다. 전체 설명은 <a href="{G}02-big-picture.html">Core Systems 아키텍처</a>에 있습니다. 본문에서 점선으로 표시된 용어를 선택하면 정의가 바로 표시되며, 화면 오른쪽 아래 <b>용어</b> 버튼(단축키 <kbd>?</kbd>)으로 어느 페이지에서나 용어를 검색할 수 있습니다.</p>
<h2>이 구조가 보장하는 네 가지</h2>
<div class="cards">
<div class="card">{{{{icon:control}}}}<b>개발 방식은 자유, 통제는 공통</b><p>Agent 개발에는 팀별 프레임워크와 도구를 사용합니다. 인증·인가, 정책, 관측, 평가, 배포 통제는 모든 Agent에 플랫폼이 동일하게 적용합니다.</p><span class="sub"><a href="{G}01-why.html">도입 배경과 설계 원칙</a></span></div>
<div class="card">{{{{icon:gateway}}}}<b>들어오고 나가는 길은 두 관문뿐</b><p>외부 앱은 Agent Platform APIs로만 들어오고, Agent는 Agent Gateway를 거쳐서만 모델과 도구를 호출합니다. 경계가 두 곳이므로 통제와 기록이 빠지지 않습니다.</p><span class="sub"><a href="{G}03-one-request.html">Agent 요청 처리 흐름</a></span></div>
<div class="card">{{{{icon:manifest}}}}<b>Manifest에 선언한 만큼만 실행</b><p>Agent는 Manifest에 선언한 도구·scope·신원 모드로만 실행됩니다. 실제 권한은 호출자·Agent·정책의 교집합이고, 자격증명은 Agent에 노출되지 않습니다.</p><span class="sub"><a href="{G}05-agents-and-manifest.html">Agent Factory와 Manifest</a></span></div>
<div class="card">{{{{icon:test}}}}<b>평가를 통과해야 프로덕션</b><p>실행은 모두 추적되고, 평가 결과가 프로덕션 승인의 근거가 됩니다. 개선(Tuning)한 Agent도 새 버전으로 다시 평가받습니다.</p><span class="sub"><a href="{G}06-lifecycle.html">수명주기와 프로덕션 승인</a></span></div>
</div>
<p class="actions"><a class="button" href="{G}01-why.html">가이드 시작</a><a class="button secondary" href="{G}07-hands-on.html">로컬 실습 시작</a><a class="button secondary" href="{G}14-connect-your-agent.html">내 Agent 연결</a></p>
<h2>학습 경로</h2><ol class="index-list path">"""
for p, title, minutes, detail, icon in onboarding:
    home += f'<li><div>{icon_svg(icon, "icon tile-icon")}<a href="{link(p)}">{title}</a><p>{detail}</p><p class="time">예상 소요 시간 {minutes}</p></div></li>' if minutes != "참조용" else f'<li><div>{icon_svg(icon, "icon tile-icon")}<a href="{link(p)}">{title}</a><p>{detail}</p><p class="time">참조용</p></div></li>'
home += '</ol>'
home += """<h2>기술 표준 및 참조 명세</h2><p>특정 규칙이나 계약을 확인하려면 기술 표준 문서를 참조합니다. 규범(MUST·SHOULD)은 기술 표준 문서가 기준입니다.</p><ul>"""
for p, title, detail in [
    ("docs/core-systems.md", "Core Systems", "10개 Core System의 책임과 제공 범위"),
    ("docs/architecture.md", "아키텍처", "구성요소의 책임과 신뢰 경계"),
    ("docs/security.md", "보안 경계", "위협과 필수 통제"),
    ("docs/operating-model.md", "운영·평가", "역할, 수명주기, 평가와 관측"),
    ("catalog.html", "계약 · 예제", "OpenAPI · JSON Schema · 4종 Agent Manifest · Python / TypeScript"),
    ("docs/tbd-register.md", "TBD 등록부", "회사 환경에 맞춰 정해야 하는 항목"),
]:
    home += f'<li><a href="{link(p)}">{title}</a> · {detail}</li>'
home += '</ul><p>회사 환경·제품·운영 수치는 TBD입니다. 이 패키지는 기술 표준과 로컬 mock 예제를 제공하며, production 배포 전 회사 통합과 운영 검증이 필요합니다.</p>'
files["portal/index.html"] = layout("개발자 가이드 개요", expand_icons(home), "index.html")
catalog = "<h1>계약 · 예제</h1><p>Machine-readable 원본과 읽기용 페이지를 함께 제공합니다. 예제는 합성 데이터입니다.</p>"
for prefix, label in [("contracts/", "API / JSON Schema"), ("examples/manifests/", "4종 Agent Manifest")]:
    catalog += "<h2>" + label + "</h2><ul>"
    for p in sources:
        if p.relative_to(ROOT).as_posix().startswith(prefix):
            catalog += f'<li><a href="{mapping[p.resolve()]}">{html.escape(p.relative_to(ROOT).as_posix())}</a></li>'
    catalog += "</ul>"
catalog += '<h2>실행 예제와 테스트</h2><ul><li><a href="../examples/python/platform_ref.py">Python local reference</a></li><li><a href="../examples/python/client.py">Python HTTP client</a></li><li><a href="../examples/typescript/client.ts">TypeScript client</a></li><li><a href="../tests/test_contracts.py">Contract tests</a></li><li><a href="../tests/test_runtime.py">Runtime / security tests</a></li></ul>'
files["portal/catalog.html"] = layout("계약과 예제", catalog, "catalog.html")
records = "<h1>결정 기록과 이력</h1><p>이 표준이 어떤 결정과 검토를 거쳐 정의되었는지 남긴 기록입니다. 플랫폼을 이해하고 사용하는 데는 필요하지 않으며, 온보딩과 정의 문서만으로 충분합니다.</p><h2>기준선과 검토</h2><ul>"
for p, title in [("README.md", "패키지 안내"), ("docs/requirements/baseline-v0.1.md", "요구사항 기준선 v0.1"), ("docs/corrections.md", "보고서 정정"), ("docs/verification.md", "검증 결과"), ("docs/validation-results.md", "실행 검증 요약"), ("docs/implementation-plan.md", "구현 계획")]:
    records += f'<li><a href="{link(p)}">{title}</a></li>'
records += "</ul>"
for prefix, label in [("adr/", "Architecture Decision Records"), ("sources/", "Deep Research 출처")]:
    records += "<h2>" + label + "</h2><ul>"
    for p in sources:
        if p.relative_to(ROOT).as_posix().startswith(prefix):
            records += f'<li><a href="{mapping[p.resolve()]}">{html.escape(p.relative_to(ROOT).as_posix())}</a></li>'
    records += "</ul>"
files["portal/records.html"] = layout("결정 기록과 이력", records, "records.html")
diagrams = "<h1>아키텍처 도식</h1><p>SVG는 네트워크나 Mermaid runtime 없이 열립니다. 동일 논리 흐름의 Mermaid 원문을 함께 제공합니다.</p>"
for svg in sorted((ROOT / "diagrams").glob("*.svg"), key=Path.as_posix):
    diagrams += f'<h2>{html.escape(svg.stem)}</h2><img class="diagram" src="../diagrams/{svg.name}" alt="{html.escape(svg.stem)} 아키텍처 도식"><p><a href="../diagrams/{svg.stem}.mmd">Mermaid 원문</a> · <a href="../diagrams/{svg.name}">SVG 원본</a></p>'
files["portal/diagrams.html"] = layout("아키텍처 도식", diagrams, "diagrams.html")
files["portal/search-index.js"] = "window.PLATFORM_SEARCH = " + json.dumps(index, ensure_ascii=False).replace("</", "<\\/") + ";\n"
# Glossary terms for in-page term help (popover on first mention, searchable term panel).
GLOSSARY = ROOT / "docs/onboarding/09-glossary.md"
GLOSSARY_HREF = link("docs/onboarding/09-glossary.md")
# Keys too generic to mark in running text.
GENERIC_KEYS = {"Agent", "AI Agent", "Runtime", "Adapter", "Space", "DevTools", "Contract", "mock", "Mock implementation",
                "production", "Core Systems", "Agent Tools", "Agent Factory", "Agent Identity", "Credential Broker", "Registry",
                "Guardrails", "AgentContext", "Red teaming", "Contract-as-Code", "등록", "승인", "배포", "deployment"}


def glossary_terms():
    terms = []
    pattern = r'<div class="term" id="(term-[^"]+)">.*?<b>(.*?) <small>(.*?)</small></b><p>(.*?)</p>'
    for term_id, name, alt, definition in re.findall(pattern, GLOSSARY.read_text(encoding="utf-8")):
        name, alt = html.unescape(re.sub(r"<[^>]+>", "", name)).strip(), html.unescape(re.sub(r"<[^>]+>", "", alt)).strip()
        keys = [k.strip() for k in re.split(r" / | · ", name)]
        keys += [k.strip() for k in re.split(r" / |, | · ", alt.split(" · 계약")[0])
                 if re.fullmatch(r"[A-Za-z][A-Za-z0-9 ()\-]{2,}", k.strip())]
        keys = sorted({k for k in keys if len(k) >= 2 and k not in GENERIC_KEYS}, key=lambda k: (-len(k), k))
        terms.append({"id": term_id, "name": name, "alt": alt if alt != name else "", "keys": keys,
                      "def": html.unescape(re.sub(r"<[^>]+>", "", definition)).strip(), "href": GLOSSARY_HREF + "#" + term_id})
    return terms


files["portal/glossary-index.js"] = "window.PLATFORM_TERMS = " + json.dumps(glossary_terms(), ensure_ascii=False).replace("</", "<" + chr(92) + "/") + ";\n"
if "--write" in sys.argv:
    for p, content in files.items():
        (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / p).write_text(content, encoding="utf-8", newline="\n")
    print(f"Built {len(files)} offline portal files")
else:
    print(json.dumps(files, ensure_ascii=False))

