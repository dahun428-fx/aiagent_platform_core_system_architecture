"""Emit generated portal files as JSON for native Write/Edit, or rebuild with --write."""
import html
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, unquote
import markdown

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "portal"
sources = [ROOT / "README.md", *sorted((ROOT / "docs").rglob("*.md"), key=Path.as_posix), *sorted((ROOT / "adr").glob("*.md"), key=Path.as_posix), *sorted((ROOT / "contracts").glob("*.json"), key=Path.as_posix), *sorted((ROOT / "examples/manifests").glob("*.json"), key=Path.as_posix), *sorted((ROOT / "sources").glob("*.md"), key=Path.as_posix)]
mapping = {p.resolve(): p.relative_to(ROOT).as_posix().replace("/", "--").replace(".md", ".html").replace(".json", ".html") for p in sources}


def link(p):
    return mapping.get((ROOT / p).resolve(), "../" + p)


navigation = [
    ("시작", [("README.md", "패키지 안내"), ("docs/requirements/baseline-v0.1.md", "요구사항 v0.1"), ("docs/corrections.md", "보고서 정정"), ("docs/release-scope.md", "제공 범위와 한계")]),
    ("설계", [("docs/architecture.md", "아키텍처"), ("docs/agent-tools.md", "Agent Tools"), ("docs/identity-and-credentials.md", "Agent Identity"), ("docs/security.md", "보안 경계"), ("docs/execution.md", "Durable / HITL")]),
    ("구현", [("docs/operating-model.md", "운영·평가"), ("docs/deployment.md", "배포 프로파일"), ("docs/versioning.md", "계약 변경"), ("docs/tbd-register.md", "TBD 등록부"), ("docs/verification.md", "검증 결과")])
]


def layout(title, body, current="", source=None):
    nav = '<a href="index.html" class="brand">AGENT PLATFORM<small>TECHNICAL STANDARD / v0.1</small></a>'
    for group, entries in navigation:
        nav += "<h2>" + group + "</h2>"
        for p, label in entries:
            href = link(p)
            active = ' aria-current="page"' if href == current else ""
            nav += f'<a href="{href}"{active}>{label}</a>'
    nav += '<h2>Reference</h2><a href="catalog.html">계약 · Fixture · ADR</a><a href="diagrams.html">아키텍처 도식 9종</a>'
    source_link = f'<p class="file-link">원본 파일: <a href="../{html.escape(source)}">{html.escape(source)}</a></p>' if source else ""
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self' file:; script-src 'self' file:; style-src 'self' file:; img-src 'self' file: data:; connect-src 'none'; object-src 'none'; base-uri 'none'">
<title>{html.escape(title)} · Agent Platform</title><link rel="stylesheet" href="styles.css">
<script defer src="search-index.js"></script><script defer src="app.js"></script></head>
<body><a class="skip" href="#main">본문으로 이동</a><aside id="sidebar" class="sidebar"><nav aria-label="주 탐색">{nav}</nav></aside>
<div class="layout"><header><button class="menu" id="menu" aria-controls="sidebar" aria-expanded="false">메뉴</button><span>전사 공통 AI Agent Platform</span><span class="version">BASELINE 0.1</span>
<div class="search"><label for="search">문서·계약·ADR 검색</label><input id="search" type="search" placeholder="문서·계약·ADR 검색" autocomplete="off"><div id="results" class="search-results" role="status" aria-live="polite" hidden></div></div></header>
<main id="main" class="content" tabindex="-1">{body}{source_link}</main><footer>2026-10-30 · 한국어 기술 표준 · 회사 환경 / 제품 / 운영 수치 TBD · 로컬 오프라인 열람 지원</footer></div></body></html>"""


def rewrite_links(body, source):
    def replace(m):
        target = html.unescape(m.group(1))
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
        return 'href="' + html.escape(href) + '"'
    return re.sub(r'href="([^"]+)"', replace, body)


files = {}
index = []
for source in sources:
    text = source.read_text(encoding="utf-8")
    relative = source.relative_to(ROOT).as_posix()
    title = re.search(r"^# (.+)", text, re.M).group(1) if source.suffix == ".md" else source.name
    if source.suffix == ".json" or relative.startswith("sources/") and source.name != "README.md":
        body = "<h1>" + html.escape(title) + "</h1><pre><code>" + html.escape(text) + "</code></pre>"
    else:
        body = markdown.markdown(text, extensions=["tables", "fenced_code"])
        body = rewrite_links(body, source)
        body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    out = mapping[source.resolve()]
    files["portal/" + out] = layout(title, body, out, relative)
    index.append({"title": title, "href": out, "text": text})

home = """<p class="eyebrow">IMPLEMENTATION STANDARD · 0.1</p>
<h1>전사 AI Agent Platform<br>구현을 시작하는 공통 기준</h1>
<p class="lead">확정된 30개 결정에서 실행 가능한 계약과 참조 예제까지.<br>Local-First 개발과 전사 거버넌스를 같은 구조 안에 연결합니다.</p>
<div class="notice"><strong>Q30 기록 정정 반영</strong><br>“B. 요구사항 기준선 검토 → 전체 패키지 제작”을 명시적 확정 결정으로 기록했습니다. Tool Gateway는 Agent Tools, Credential Broker는 Agent Identity에 속합니다.</div>
<h2>표준 읽기</h2><ol class="index-list">"""
entries = [
    ("docs/requirements/baseline-v0.1.md", "요구사항 기준선", "Q1–30 · ADR 추적 · 출처와 정정"),
    ("docs/architecture.md", "구조와 신뢰 경계", "C4 · 호출 흐름 · Agent Tools · Agent Identity"),
    ("catalog.html", "계약과 참조 예제", "OpenAPI · JSON Schema · 4종 Agent · Python / TypeScript"),
    ("docs/verification.md", "검증과 구현 인계", "실행 결과 · Contract Tests · TBD · 배포 패키지")
]
for n, (p, title, detail) in enumerate(entries, 1):
    href = p if p.endswith(".html") else link(p)
    home += f'<li><span class="number">0{n}</span><div><a href="{href}">{title}</a><p>{detail}</p></div></li>'
home += '</ol><h2>공통 제어, 분산 실행</h2><a href="diagrams.html"><img class="diagram" src="../diagrams/c4-container.svg" alt="C4 Container: Shared Control Plane과 Distributed Execution Plane"></a><p>회사 환경·제품·운영 수치는 TBD입니다. 이 패키지는 기술 표준과 로컬 mock 예제를 제공하며, production 배포 전 회사 통합과 운영 검증이 필요합니다.</p>'
files["portal/index.html"] = layout("구현 착수 기술 표준", home)
catalog = "<h1>계약 · Fixture · ADR</h1><p>Machine-readable 원본과 읽기용 페이지를 함께 제공합니다. 예제는 합성 데이터입니다.</p>"
for prefix, label in [("contracts/", "API / JSON Schema"), ("examples/manifests/", "4종 Agent Manifest"), ("adr/", "Architecture Decision Records"), ("sources/", "Deep Research 출처")]:
    catalog += "<h2>" + label + "</h2><ul>"
    for p in sources:
        if p.relative_to(ROOT).as_posix().startswith(prefix):
            catalog += f'<li><a href="{mapping[p.resolve()]}">{html.escape(p.relative_to(ROOT).as_posix())}</a></li>'
    catalog += "</ul>"
catalog += '<h2>실행 예제와 테스트</h2><ul><li><a href="../examples/python/platform_ref.py">Python local reference</a></li><li><a href="../examples/python/client.py">Python HTTP client</a></li><li><a href="../examples/typescript/client.ts">TypeScript client</a></li><li><a href="../tests/test_contracts.py">Contract tests</a></li><li><a href="../tests/test_runtime.py">Runtime / security tests</a></li></ul>'
files["portal/catalog.html"] = layout("계약과 ADR", catalog)
diagrams = "<h1>아키텍처 도식</h1><p>SVG는 네트워크나 Mermaid runtime 없이 열립니다. 동일 논리 흐름의 Mermaid 원문을 함께 제공합니다.</p>"
for svg in sorted((ROOT / "diagrams").glob("*.svg"), key=Path.as_posix):
    diagrams += f'<h2>{html.escape(svg.stem)}</h2><img class="diagram" src="../diagrams/{svg.name}" alt="{html.escape(svg.stem)} 아키텍처 도식"><p><a href="../diagrams/{svg.stem}.mmd">Mermaid 원문</a> · <a href="../diagrams/{svg.name}">SVG 원본</a></p>'
files["portal/diagrams.html"] = layout("아키텍처 도식", diagrams)
files["portal/search-index.js"] = "window.PLATFORM_SEARCH = " + json.dumps(index, ensure_ascii=False).replace("</", "<\\/") + ";\n"
if "--write" in sys.argv:
    for p, content in files.items():
        (ROOT / p).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / p).write_text(content, encoding="utf-8")
    print(f"Built {len(files)} offline portal files")
else:
    print(json.dumps(files, ensure_ascii=False))

