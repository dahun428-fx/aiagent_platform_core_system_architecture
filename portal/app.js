(() => {
  const input = document.getElementById("search");
  const results = document.getElementById("results");
  const data = window.PLATFORM_SEARCH || [];
  if (input && results) {
    input.addEventListener("input", () => {
      const q = input.value.trim().toLocaleLowerCase();
      results.replaceChildren();
      results.hidden = !q;
      if (!q) return;
      const words = q.split(/\s+/);
      const hits = data.filter(x => words.every(w => (x.title + " " + x.text).toLocaleLowerCase().includes(w))).slice(0, 12);
      const status = document.createElement("p");
      status.textContent = hits.length ? hits.length + "개 결과 (최대 12개 표시)" : "검색 결과가 없습니다. 다른 용어로 검색해 보세요.";
      results.append(status);
      for (const hit of hits) {
        const a = document.createElement("a");
        a.href = hit.href;
        a.textContent = hit.title;
        results.append(a);
      }
    });
    input.addEventListener("keydown", e => { if (e.key === "Escape") { results.hidden = true; input.blur(); } });
    document.addEventListener("keydown", e => {
      if (e.key === "/" && !e.ctrlKey && !e.metaKey && !e.altKey && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
        e.preventDefault();
        input.focus();
      }
    });
    document.addEventListener("click", e => { if (!e.target.closest(".search")) results.hidden = true; });
    input.addEventListener("focus", () => { if (input.value.trim()) results.hidden = false; });
  }
  const button = document.getElementById("menu");
  const sidebar = document.getElementById("sidebar");
  if (button && sidebar) button.addEventListener("click", () => {
    const open = sidebar.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
})();

// Term help: mark the first mention of each glossary term in the page, show its definition on demand,
// and offer a searchable term panel (button or "?" key) on every page.
(() => {
  const terms = window.PLATFORM_TERMS || [];
  const doc = document.querySelector(".doc");
  if (!terms.length || !doc) return;
  const byId = new Map(terms.map(t => [t.id, t]));
  const make = (tag, cls, text) => { const el = document.createElement(tag); if (cls) el.className = cls; if (text) el.textContent = text; return el; };

  const pop = make("div", "gloss-pop");
  pop.setAttribute("role", "tooltip");
  pop.id = "gloss-pop";
  pop.hidden = true;
  document.body.append(pop);
  let anchor = null;
  function fill(box, term) {
    box.replaceChildren();
    const head = make("p", "gloss-name", term.name);
    if (term.alt) head.append(make("small", "", term.alt));
    const link = make("a", "gloss-more", "용어 사전에서 보기");
    link.href = term.href;
    box.append(head, make("p", "gloss-def", term.def), link);
  }
  function show(el) {
    const term = byId.get(el.dataset.term);
    if (!term) return;
    fill(pop, term);
    pop.hidden = false;
    anchor = el;
    el.setAttribute("aria-describedby", "gloss-pop");
    const r = el.getBoundingClientRect();
    const w = Math.min(360, innerWidth - 24);
    pop.style.width = w + "px";
    pop.style.left = Math.max(12, Math.min(r.left + scrollX, scrollX + innerWidth - w - 12)) + "px";
    const below = r.bottom + 8 + pop.offsetHeight < innerHeight;
    pop.style.top = (below ? r.bottom + scrollY + 8 : r.top + scrollY - pop.offsetHeight - 8) + "px";
  }
  function hide() { if (anchor) anchor.removeAttribute("aria-describedby"); pop.hidden = true; anchor = null; }

  // The glossary page itself and code samples are left as they are.
  if (!location.pathname.endsWith("09-glossary.html")) {
    const entries = [];
    for (const t of terms) for (const k of t.keys) entries.push([k, t.id]);
    entries.sort((a, b) => b[0].length - a[0].length);
    const esc = s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp("(?<![A-Za-z0-9_-])(" + entries.map(e => esc(e[0])).join("|") + ")(?![A-Za-z0-9_])", "g");
    const keyToId = new Map(entries);
    const used = new Set();
    const walker = document.createTreeWalker(doc, NodeFilter.SHOW_TEXT, {
      acceptNode: n => n.parentElement.closest("pre, code, a, h1, h2, h3, h4, b, strong, .stack, .flow, .lanes, .planes, .gloss, .refs, script, style")
        ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    for (const node of nodes) {
      const text = node.nodeValue;
      pattern.lastIndex = 0;
      let m, last = 0;
      const frag = document.createDocumentFragment();
      while ((m = pattern.exec(text))) {
        const id = keyToId.get(m[1]);
        if (used.has(id)) continue;
        used.add(id);
        frag.append(text.slice(last, m.index));
        const mark = make("span", "gloss", m[1]);
        mark.dataset.term = id;
        mark.tabIndex = 0;
        mark.setAttribute("role", "button");
        frag.append(mark);
        last = m.index + m[1].length;
      }
      if (last) { frag.append(text.slice(last)); node.replaceWith(frag); }
    }
    doc.addEventListener("mouseover", e => { const g = e.target.closest(".gloss"); if (g) show(g); });
    doc.addEventListener("mouseout", e => { const g = e.target.closest(".gloss"); if (g && !pop.contains(e.relatedTarget)) setTimeout(() => { if (!pop.matches(":hover") && document.activeElement !== g) hide(); }, 150); });
    pop.addEventListener("mouseleave", () => { if (document.activeElement !== anchor) hide(); });
    doc.addEventListener("focusin", e => { const g = e.target.closest(".gloss"); if (g) show(g); });
    doc.addEventListener("focusout", e => { if (e.target.closest(".gloss") && !pop.contains(e.relatedTarget)) setTimeout(() => { if (!pop.contains(document.activeElement)) hide(); }, 0); });
    doc.addEventListener("click", e => { const g = e.target.closest(".gloss"); if (g) { e.preventDefault(); anchor === g && !pop.hidden ? hide() : show(g); } });
  }

  // Term panel
  const open = make("button", "gloss-open", "용어");
  open.type = "button";
  open.setAttribute("aria-haspopup", "dialog");
  open.title = "용어 찾기 (?)";
  const panel = make("div", "gloss-panel");
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-label", "용어 찾기");
  panel.hidden = true;
  const field = make("input");
  field.type = "search";
  field.placeholder = "용어 검색 (예: 멱등성, Manifest, egress)";
  field.setAttribute("aria-label", "용어 검색");
  const close = make("button", "gloss-close", "닫기");
  close.type = "button";
  const list = make("div", "gloss-list");
  const top = make("div", "gloss-top");
  top.append(field, close);
  panel.append(top, list);
  document.body.append(open, panel);
  function render() {
    const q = field.value.trim().toLocaleLowerCase();
    const hits = terms.filter(t => !q || (t.name + " " + t.alt + " " + t.keys.join(" ") + " " + t.def).toLocaleLowerCase().includes(q));
    list.replaceChildren();
    if (!hits.length) list.append(make("p", "gloss-empty", "일치하는 용어가 없습니다. 상단의 문서·계약 검색을 사용해 보세요."));
    for (const t of hits) { const item = make("div", "gloss-item"); fill(item, t); list.append(item); }
  }
  function toggle(show) {
    panel.hidden = !show;
    open.setAttribute("aria-expanded", String(show));
    if (show) { render(); field.focus(); field.select(); } else open.focus();
  }
  open.addEventListener("click", () => toggle(panel.hidden));
  close.addEventListener("click", () => toggle(false));
  field.addEventListener("input", render);
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") { if (!panel.hidden) toggle(false); hide(); return; }
    if (e.key === "?" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) { e.preventDefault(); toggle(panel.hidden); }
  });
})();

