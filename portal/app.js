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
  }
  const button = document.getElementById("menu");
  const sidebar = document.getElementById("sidebar");
  if (button && sidebar) button.addEventListener("click", () => {
    const open = sidebar.classList.toggle("open");
    button.setAttribute("aria-expanded", String(open));
  });
})();

