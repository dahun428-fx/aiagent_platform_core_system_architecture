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
    ("docs/onboarding/02-big-picture.md", "플랫폼 아키텍처와 주요 구성요소", "10분", "Shared Control Plane과 Distributed Execution Plane의 구성 및 책임", "map"),
    ("docs/onboarding/03-one-request.md", "Agent 요청 처리 흐름", "15분", "Agent Gateway 진입부터 모델·도구 호출, 실행 추적까지의 처리 흐름", "trace"),
    ("docs/onboarding/04-trust.md", "신뢰 경계와 보안 통제", "10분", "요청 입력, 도구 응답, 자격증명 및 승인 정보의 검증 원칙", "shield"),
    ("docs/onboarding/05-agents-and-manifest.md", "Agent 유형과 Manifest 명세", "10분", "RAG·Tool·Workflow·Multi-Agent 유형과 Manifest 구성 및 검증 규칙", "manifest"),
    ("docs/onboarding/06-lifecycle.md", "Agent 수명주기와 프로덕션 승인", "10분", "등록·검증·평가·승인 단계와 프로덕션 승인 요건", "rocket"),
    ("docs/onboarding/07-hands-on.md", "로컬 환경 구성 및 호출 실습", "30분", "로컬 mock 환경에서 Manifest 검증, Agent 호출 및 오류 응답 확인", "code"),
    ("docs/onboarding/08-reading-the-spec.md", "기술 표준 해석과 FAQ", "10분", "MUST·SHOULD·MAY, TBD 및 버전 표기의 의미", "question"),
    ("docs/onboarding/09-glossary.md", "주요 용어 정의", "참조용", "플랫폼 구성요소, 실행 모델 및 기술 계약의 주요 용어", "book"),
]
navigation = [
    ("개발자 가이드", [("index.html", "가이드 개요")] + [(p, t) for p, t, _, _, _ in onboarding]),
    ("설계 정의", [("docs/architecture.md", "아키텍처"), ("docs/agent-tools.md", "Agent Tools"), ("docs/identity-and-credentials.md", "Agent Identity"), ("docs/security.md", "보안 경계"), ("docs/execution.md", "Durable / HITL")]),
    ("운영 정의", [("docs/operating-model.md", "운영·평가"), ("docs/deployment.md", "배포 프로파일"), ("docs/versioning.md", "계약 변경"), ("docs/ci-integration.md", "CI 통합"), ("docs/glossary.md", "용어와 규범")]),
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
<script defer src="search-index.js"></script><script defer src="app.js"></script></head>
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

home = """<h1>AI Agent Platform 개발자 가이드</h1>
<p class="lead">전사 공통 AI Agent Platform의 아키텍처, 보안 모델, Agent 개발 및 승인 절차를 설명합니다.<br>학습 경로에 따라 주요 기술 계약을 이해하고, 로컬 mock 환경에서 Manifest 검증과 Agent 호출을 실습할 수 있습니다.</p>
<p class="actions"><a class="button" href="docs--onboarding--01-why.html">가이드 시작</a><a class="button secondary" href="docs--onboarding--07-hands-on.html">로컬 실습 시작</a></p>
<div class="notice"><strong>핵심 설계 원칙</strong><br>Agent 개발에는 팀별 도구와 프레임워크를 사용하며, 플랫폼은 공통 제어·연계 지점에서 인증·인가, 정책 적용, 관측성, 평가 및 배포 통제를 수행합니다.</div>
<h2>학습 경로</h2><ol class="index-list path">"""
for p, title, minutes, detail, icon in onboarding:
    home += f'<li><div>{icon_svg(icon, "icon tile-icon")}<a href="{link(p)}">{title}</a><p>{detail}</p><p class="time">예상 소요 시간 {minutes}</p></div></li>' if minutes != "참조용" else f'<li><div>{icon_svg(icon, "icon tile-icon")}<a href="{link(p)}">{title}</a><p>{detail}</p><p class="time">참조용</p></div></li>'
home += '</ol><h2>공통 제어 평면과 분산 실행 평면</h2><a href="diagrams.html"><img class="diagram" src="../diagrams/c4-container.svg" alt="C4 Container: Shared Control Plane과 Distributed Execution Plane"></a><p>구성요소별 설명은 <a href="docs--onboarding--02-big-picture.html">플랫폼 아키텍처와 주요 구성요소</a>를 참고하십시오.</p>'
home += """<h2>기술 표준 및 참조 명세</h2><p>특정 규칙이나 계약을 확인하려면 기술 표준 문서를 참조합니다. 규범(MUST·SHOULD)은 기술 표준 문서가 기준입니다.</p><ul>"""
for p, title, detail in [
    ("docs/architecture.md", "아키텍처", "구성요소의 책임과 신뢰 경계"),
    ("docs/security.md", "보안 경계", "위협과 필수 통제"),
    ("docs/operating-model.md", "운영·평가", "역할, 수명주기, 평가와 관측"),
    ("catalog.html", "계약 · 예제", "OpenAPI · JSON Schema · 4종 Agent Manifest · Python / TypeScript"),
    ("docs/tbd-register.md", "TBD 등록부", "회사 환경에 맞춰 정해야 하는 항목"),
]:
    home += f'<li><a href="{link(p)}">{title}</a> · {detail}</li>'
home += '</ul><p>회사 환경·제품·운영 수치는 TBD입니다. 이 패키지는 기술 표준과 로컬 mock 예제를 제공하며, production 배포 전 회사 통합과 운영 검증이 필요합니다.</p>'
files["portal/index.html"] = layout("개발자 가이드 개요", home, "index.html")
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
if "--write" in sys.argv:
    for p, content in files.items():
        (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / p).write_text(content, encoding="utf-8")
    print(f"Built {len(files)} offline portal files")
else:
    print(json.dumps(files, ensure_ascii=False))

