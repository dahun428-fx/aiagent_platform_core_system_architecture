"""Emit generated portal files as JSON for native Write/Edit, or rebuild with --write."""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
import markdown
from markdown.extensions.toc import TocExtension, slugify_unicode

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "portal"
sources = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"), key=Path.as_posix), *sorted((ROOT / "adr").glob("*.md"), key=Path.as_posix), *sorted((ROOT / "contracts").glob("*.json"), key=Path.as_posix), *sorted((ROOT / "examples/manifests").glob("*.json"), key=Path.as_posix), *sorted((ROOT / "sources").glob("*.md"), key=Path.as_posix)]
mapping = {p.resolve(): p.relative_to(ROOT).as_posix().replace("/", "--").replace(".md", ".html").replace(".json", ".html") for p in sources}


def link(p):
    if p.endswith(".html"):
        return p
    return mapping.get((ROOT / p).resolve(), "../" + p)


onboarding = [
    ("docs/onboarding/01-why.md", "왜 이 플랫폼이 필요한가", "5분", "팀마다 따로 풀던 신원·데이터·비밀값·추적 문제를 공통 경계에서 해결합니다"),
    ("docs/onboarding/02-big-picture.md", "한 장으로 보는 전체 구조", "10분", "통제는 모으고 실행은 흩는 두 평면과 구성요소 아홉 개"),
    ("docs/onboarding/03-one-request.md", "요청 하나 따라가기", "15분", "Agent Gateway에서 모델·도구 호출과 기록까지 한 요청의 길"),
    ("docs/onboarding/04-trust.md", "신뢰 경계: 무엇을 믿지 않는가", "10분", "요청 본문, 도구 결과, 비밀값, 승인 표시를 믿지 않는 이유"),
    ("docs/onboarding/05-agents-and-manifest.md", "네 종류 Agent와 Manifest", "10분", "RAG·Tool·Workflow·Multi-Agent와 Agent의 신분증"),
    ("docs/onboarding/06-lifecycle.md", "내 Agent가 production까지 가는 길", "10분", "로컬 실험에서 승인까지 일곱 단계와 필요한 증거"),
    ("docs/onboarding/07-hands-on.md", "30분 실습", "30분", "로컬 mock으로 Manifest 검증, 호출, 거부를 직접 확인"),
    ("docs/onboarding/08-reading-the-spec.md", "규격 읽는 법과 자주 묻는 질문", "10분", "MUST·TBD·버전 표시 읽는 법과 흔한 오해"),
]
navigation = [
    ("온보딩", [("index.html", "시작하기")] + [(p, t) for p, t, _, _ in onboarding]),
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
            href = mapping[resolved]
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
        body = markdown.markdown(text, extensions=["tables", "fenced_code", TocExtension(slugify=slugify_unicode, toc_depth="2")])
        body = rewrite_links(body, source)
        body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    out = mapping[source.resolve()]
    toc = ""
    sections = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', body)
    if len(sections) >= 3:
        toc = '<nav class="toc" aria-label="이 문서의 목차"><h2>이 문서에서</h2>' + "".join(f'<a href="#{i}">{re.sub(r"<[^>]+>", "", t)}</a>' for i, t in sections) + "</nav>"
    files["portal/" + out] = layout(title, body, out, relative, toc)
    index.append({"title": title, "href": out, "text": text})

home = """<h1>AI Agent Platform 온보딩</h1>
<p class="lead">전사 공통 AI Agent Platform을 처음 만나는 개발자를 위한 안내서입니다.<br>위에서부터 순서대로 읽으면 약 1시간 40분 안에 전체 그림을 잡고, 로컬에서 직접 돌려 볼 수 있습니다.</p>
<p class="actions"><a class="button" href="docs--onboarding--01-why.html">처음부터 읽기</a><a class="button secondary" href="docs--onboarding--07-hands-on.html">바로 실습하기</a></p>
<div class="notice"><strong>핵심 한 문장</strong><br>개발자는 지금 쓰는 도구와 프레임워크를 그대로 쓰고, 신원·정책·관측·평가·배포 통제는 플랫폼의 공통 경계에서 적용합니다.</div>
<h2>읽는 순서</h2><ol class="index-list path">"""
for p, title, minutes, detail in onboarding:
    home += f'<li><div><a href="{link(p)}">{title}</a><p>{detail}</p><p class="time">{minutes}</p></div></li>'
home += '</ol><h2>공통 제어, 분산 실행</h2><a href="diagrams.html"><img class="diagram" src="../diagrams/c4-container.svg" alt="C4 Container: Shared Control Plane과 Distributed Execution Plane"></a><p>구성요소별 설명은 <a href="docs--onboarding--02-big-picture.html">한 장으로 보는 전체 구조</a>에 있습니다.</p>'
home += """<h2>정의 문서로 바로 가기</h2><p>온보딩을 마쳤거나 특정 규칙을 찾는다면 정의 문서로 바로 가세요. 규범(MUST·SHOULD)은 정의 문서가 기준입니다.</p><ul>"""
for p, title, detail in [
    ("docs/architecture.md", "아키텍처", "구성요소의 책임과 신뢰 경계"),
    ("docs/security.md", "보안 경계", "위협과 필수 통제"),
    ("docs/operating-model.md", "운영·평가", "역할, 수명주기, 평가와 관측"),
    ("catalog.html", "계약 · 예제", "OpenAPI · JSON Schema · 4종 Agent Manifest · Python / TypeScript"),
    ("docs/tbd-register.md", "TBD 등록부", "회사 환경에 맞춰 정해야 하는 항목"),
]:
    home += f'<li><a href="{link(p)}">{title}</a> · {detail}</li>'
home += '</ul><p>회사 환경·제품·운영 수치는 TBD입니다. 이 패키지는 기술 표준과 로컬 mock 예제를 제공하며, production 배포 전 회사 통합과 운영 검증이 필요합니다.</p>'
files["portal/index.html"] = layout("온보딩 시작하기", home, "index.html")
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

