// Interactive guide: step players for every flow diagram, path walkthroughs for lanes and the
// Core Systems diagram, and small simulators that apply the same rules as the reference mock.
// Everything runs offline in the page; nothing is sent anywhere.
(() => {
  const h = (tag, props = {}, ...kids) => {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(props)) {
      if (k === "class") el.className = v;
      else if (k === "text") el.textContent = v;
      else if (k.startsWith("on")) el.addEventListener(k.slice(2), v);
      else if (v !== false && v != null) el.setAttribute(k, v === true ? "" : v);
    }
    for (const kid of kids.flat()) if (kid != null) el.append(kid);
    return el;
  };
  const btn = (text, onclick, cls = "") => h("button", { type: "button", class: "ix-btn " + cls, onclick, text });
  const wait = ms => new Promise(r => setTimeout(r, ms));
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const pace = ms => (reduce ? 0 : ms);
  const labelOf = el => (el.querySelector("b")?.textContent || el.textContent).trim();

  // ---------- Step player for every .flow ----------
  document.querySelectorAll(".content .flow").forEach(flow => {
    const steps = [...flow.children].filter(li => li.tagName === "LI");
    if (steps.length < 2) return;
    let idx = -1, timer = null;
    const count = h("span", { class: "ix-count", "aria-hidden": "true" });
    const caption = h("div", { class: "ix-caption", "aria-live": "polite", hidden: true });
    const play = btn("▶ 단계별로 보기", () => (timer ? stop() : start()), "primary");
    const prev = btn("이전", () => { stop(); go(Math.max(0, idx - 1)); });
    const next = btn("다음", () => { stop(); go(Math.min(steps.length - 1, idx + 1)); });
    prev.disabled = next.disabled = true;
    const bar = h("div", { class: "ix-bar" }, play, prev, next, count);
    flow.before(bar);
    flow.after(caption);
    flow.classList.add("ix-flow");
    function go(i) {
      idx = i;
      steps.forEach((s, n) => { s.classList.toggle("on", n === i); s.classList.toggle("done", n < i); });
      const say = steps[i].dataset.say || steps[i].textContent.trim();
      const label = labelOf(steps[i]);
      caption.replaceChildren(h("b", { text: /^\d+\./.test(label) ? label : `${i + 1}. ${label}` }), h("p", { text: say }));
      caption.hidden = false;
      count.textContent = `${i + 1} / ${steps.length}`;
      prev.disabled = i === 0;
      next.disabled = i === steps.length - 1;
    }
    function start() {
      if (idx >= steps.length - 1 || idx < 0) go(0);
      play.textContent = "❚❚ 멈춤";
      timer = setInterval(() => { if (idx >= steps.length - 1) stop(); else go(idx + 1); }, 4200);
    }
    function stop() { clearInterval(timer); timer = null; play.textContent = idx >= steps.length - 1 ? "↺ 처음부터" : "▶ 이어서 보기"; }
    steps.forEach((s, n) => {
      s.tabIndex = 0;
      s.addEventListener("click", () => { stop(); go(n); });
      s.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); stop(); go(n); } });
    });
  });

  // ---------- Path walkthrough for every .lanes ----------
  document.querySelectorAll(".content .lanes").forEach(lanes => {
    const rows = [...lanes.querySelectorAll(":scope > .lane")];
    const caption = h("div", { class: "ix-caption", "aria-live": "polite", hidden: true });
    let running = false;
    async function show(row) {
      rows.forEach(r => r.classList.toggle("on", r === row));
      row.classList.remove("run");
      void row.offsetWidth;
      row.classList.add("run");
      const gate = row.querySelector(".gate span")?.firstChild?.textContent?.trim() || labelOf(row);
      caption.replaceChildren(h("b", { text: gate }), h("p", { text: row.dataset.say || row.textContent.trim() }));
      caption.hidden = false;
    }
    const play = btn("▶ 경로 따라가기", async () => {
      if (running) return;
      running = true;
      for (const r of rows) { show(r); await wait(pace(3600)); }
      running = false;
    }, "primary");
    lanes.before(h("div", { class: "ix-bar" }, play, h("span", { class: "ix-hint", text: "각 줄을 선택하면 그 경로만 볼 수 있습니다." })));
    lanes.after(caption);
    lanes.classList.add("ix-lanes");
    rows.forEach(r => { r.tabIndex = 0; r.addEventListener("click", () => show(r)); r.addEventListener("keydown", e => { if (e.key === "Enter") show(r); }); });
  });

  // ---------- Core Systems diagram: highlight the systems a path goes through ----------
  const PATHS = [
    ["Agent 호출", ["s-ext-app", "s-api", "s-identity", "s-runtime", "s-obs", "s-infra"],
      "업무 앱의 요청이 Agent Platform APIs로 들어옵니다. Agent Identity로 호출자를 확인한 뒤 Agent Runtime이 실행 인프라에서 Agent를 실행하고, 전 과정이 Agent Observability에 기록됩니다."],
    ["모델 호출", ["s-runtime", "s-gateway", "s-ext-tool", "s-obs"],
      "실행 중인 Agent가 모델을 부르면 Agent Gateway의 모델 경로가 데이터 분류에 맞는 모델로만 보냅니다. 외부 모델도 이 경로를 거쳐서만 호출됩니다."],
    ["도구 호출", ["s-runtime", "s-gateway", "s-tools", "s-identity", "s-ext-tool", "s-obs"],
      "Agent가 도구를 부르면 Agent Gateway의 도구 경로가 Agent Tools에 등록·승인된 도구인지 확인하고, Agent Identity의 Credential Broker가 그 호출 한 번용 사용권을 발급합니다."],
    ["개발·등록", ["s-app", "s-api", "s-factory", "s-eval"],
      "개발자는 DevTools로 Agent를 만들고 Agent Factory에서 Manifest를 검증해 등록합니다. 프로덕션 승인 전에는 Agent Evaluation의 평가를 거칩니다."],
    ["평가·개선", ["s-obs", "s-eval", "s-tuning", "s-factory"],
      "실행 기록(Observability)과 평가 결과(Evaluation)를 근거로 Agent Tuning이 개선안을 만들고, 새 버전은 Agent Factory를 거쳐 다시 평가받습니다."],
  ];
  document.querySelectorAll(".content .stack:not(.build)").forEach(stack => {
    const caption = h("div", { class: "ix-caption", "aria-live": "polite", hidden: true });
    const buttons = [];
    function pick(i) {
      const on = buttons[i].getAttribute("aria-pressed") !== "true";
      buttons.forEach((b, n) => b.setAttribute("aria-pressed", String(on && n === i)));
      stack.classList.toggle("ix-path", on);
      [...stack.children].forEach(el => el.classList.toggle("lit", on && PATHS[i][1].some(c => el.classList.contains(c))));
      caption.hidden = !on;
      if (on) caption.replaceChildren(h("b", { text: PATHS[i][0] + " 경로" }), h("p", { text: PATHS[i][2] }));
    }
    PATHS.forEach(([name], i) => buttons.push(btn(name, () => pick(i))));
    buttons.forEach(b => b.setAttribute("aria-pressed", "false"));
    stack.before(h("div", { class: "ix-bar" }, h("span", { class: "ix-hint", text: "경로 보기:" }), buttons));
    stack.after(caption);
  });

  // ---------- Simulators ----------
  function frame(el, title, intro) {
    el.classList.add("ix-sim");
    const body = h("div", { class: "ix-sim-body" });
    el.replaceChildren(h("p", { class: "ix-sim-title" }, h("span", { class: "ix-tag", text: "직접 해 보기" }), title), h("p", { class: "ix-sim-intro", text: intro }), body);
    return body;
  }
  const check = (label, name) => h("label", { class: "ix-check" }, h("input", { type: "checkbox", name }), label);
  const result = () => h("div", { class: "ix-result", "aria-live": "polite" });
  function verdict(box, ok, head, text) {
    box.className = "ix-result " + (ok === true ? "ok" : ok === false ? "bad" : "info");
    box.replaceChildren(h("b", { text: head }), ...[].concat(text).map(t => h("p", { text: t })));
  }
  function stages(names) {
    const wrap = h("ol", { class: "ix-stages" }, names.map(n => h("li", { text: n })));
    return { wrap, items: [...wrap.children], reset() { this.items.forEach(li => li.className = ""); } };
  }

  const S = window.PLATFORM_SCENARIO || {};
  const select = (name, opts) => h("select", { name }, opts.map(([v, t]) => h("option", { value: v, text: t })));
  const field = (label, control) => h("label", { class: "ix-field" }, label, control);
  const on = box => box.querySelector("input").checked;
  const pressed = (bs, i) => bs.forEach((b, n) => b.setAttribute("aria-pressed", String(n === i)));

  const SIMS = {
    // Chapter 3: a request through the five stages, with switches that break it at the right stage.
    request(el) {
      const body = frame(el, "요청 하나 보내 보기", "아래 조건을 켜고 '요청 보내기'를 누르면, 요청이 어느 단계에서 왜 멈추는지 볼 수 있습니다. 조건을 모두 끄면 정상 처리됩니다.");
      const RULES = [
        ["noToken", "토큰 없이 호출", 0, "401 Unauthorized", "호출자가 누구인지 확인할 수 없어 Agent Platform APIs에서 돌려보냅니다."],
        ["spoof", "요청 본문에 다른 테넌트 ID 넣기", 0, "403 Forbidden", "테넌트는 검증된 토큰에서만 정합니다. 본문으로 다른 테넌트를 지정할 수 없습니다."],
        ["scope", "하준처럼 Agent가 요구하는 권한이 없는 사용자", 0, "403 Forbidden", "Manifest의 requiredScopes를 호출자가 모두 갖고 있지 않아 Agent를 실행하지 않습니다."],
        ["conflict", "같은 멱등성 키로 다른 내용 보내기", 0, "409 Conflict", "같은 요청 번호로 내용이 다른 요청이 와서 거부합니다. 실수나 재전송 공격을 막습니다."],
        ["undeclared", "Manifest에 선언하지 않은 도구 호출", 2, "403 Forbidden", "Agent는 실행됐지만, 선언하지 않은 도구는 도구 경로가 거부합니다."],
        ["restricted", "제한(restricted) 데이터인데 외부 모델만 사용 가능", 3, "503 Service Unavailable", "제한 데이터는 외부 모델로 보낼 수 없고 다른 모델도 없어, 우회하지 않고 실패시킵니다(fail closed)."],
      ];
      const st = stages(["진입 · Agent Platform APIs", "실행 · Agent Runtime", "도구 경로", "모델 경로", "기록 · 응답"]);
      const boxes = RULES.map(r => check(r[1], r[0]));
      const out = result();
      const run = btn("요청 보내기", async () => {
        run.disabled = true;
        st.reset();
        verdict(out, null, "처리 중", "요청이 단계를 지나가고 있습니다.");
        const on = RULES.filter((r, i) => boxes[i].querySelector("input").checked);
        const fail = on.sort((a, b) => a[2] - b[2])[0];
        for (let i = 0; i < st.items.length; i++) {
          st.items[i].className = "on";
          await wait(pace(650));
          if (fail && fail[2] === i) {
            st.items[i].className = "bad";
            verdict(out, false, `${fail[3]} · ${st.items[i].textContent}에서 멈춤`,
              fail[4] + (i === 0 ? " Agent 코드는 한 번도 실행되지 않았습니다." : ""));
            run.disabled = false;
            return;
          }
          st.items[i].className = "ok";
        }
        verdict(out, true, "200 OK · 정상 처리", "모든 단계를 통과했습니다. 같은 추적 번호로 전 과정이 기록됐고, 결과가 호출자에게 돌아갑니다.");
        run.disabled = false;
      }, "primary");
      body.append(h("div", { class: "ix-controls" }, boxes), st.wrap, h("div", { class: "ix-actions" }, run), out);
    },

    // Chapter 3: model route choice by data classification.
    routing(el) {
      const body = frame(el, "데이터 분류에 따라 모델 고르기", "데이터 분류와 쓸 수 있는 모델을 바꿔 보세요. 호출자가 분류를 더 낮게 적어도 플랫폼은 낮추지 않습니다.");
      const LEVELS = ["public", "internal", "confidential", "restricted"];
      const KO = { public: "공개", internal: "사내", confidential: "기밀", restricted: "제한" };
      const sel = (name, opts) => h("select", { name }, opts.map(([v, t]) => h("option", { value: v, text: t })));
      const server = sel("server", LEVELS.map(l => [l, `${KO[l]} (${l})`]));
      server.value = "confidential";
      const caller = sel("caller", [["same", "플랫폼 분류와 같게"], ["public", "공개(public)로 낮춰 적기"], ["restricted", "제한(restricted)으로 높여 적기"]]);
      const ext = check("외부 모델 사용 가능", "ext");
      const self = check("자체 호스팅 모델 사용 가능", "self");
      ext.querySelector("input").checked = self.querySelector("input").checked = true;
      const out = result();
      function update() {
        const s = LEVELS.indexOf(server.value);
        const c = caller.value === "same" ? s : LEVELS.indexOf(caller.value);
        const eff = LEVELS[Math.max(s, c)];
        const canExt = eff === "public" || eff === "internal";
        const routes = [];
        if (self.querySelector("input").checked) routes.push("자체 호스팅 모델");
        if (canExt && ext.querySelector("input").checked) routes.push("외부 모델");
        const note = c < s ? " 호출자가 낮춰 적은 값은 무시했습니다." : c > s ? " 호출자가 높여 적은 값은 받아들였습니다." : "";
        if (!routes.length) verdict(out, false, `적용 분류: ${KO[eff]} · 503 요청 실패`, `보낼 수 있는 모델이 없습니다. ${canExt ? "" : "외부 모델은 이 분류에서 금지됩니다. "}다른 길로 돌아가지 않고 실패시킵니다.${note}`);
        else verdict(out, true, `적용 분류: ${KO[eff]} · ${routes.join(" 또는 ")}로 전송`, `${canExt ? "정책이 허용하면 외부 모델도 쓸 수 있습니다." : "외부 모델로 가는 길은 막고 회사 안 모델만 씁니다."}${note}`);
      }
      [server, caller, ext, self].forEach(x => x.addEventListener("change", update));
      body.append(h("div", { class: "ix-controls grid" },
        h("label", { class: "ix-field" }, "플랫폼이 아는 데이터 분류", server),
        h("label", { class: "ix-field" }, "호출자가 요청에 적은 분류", caller), ext, self), out);
      update();
    },

    // Chapter 4: idempotency keys and unknown outcomes.
    idempotency(el) {
      const body = frame(el, "같은 요청을 여러 번 보내 보기", "버튼을 차례로 눌러 보세요. 같은 요청이 여러 번 와도 Agent가 실제로 몇 번 실행되는지 아래 숫자로 확인할 수 있습니다.");
      let stored = null, busy = false, runs = 0;
      const counter = h("b", { text: "0" });
      const log = h("ol", { class: "ix-log" });
      const add = (code, text, ok) => { log.prepend(h("li", { class: ok ? "ok" : ok === false ? "bad" : "" }, h("code", { text: code }), " " + text)); counter.textContent = String(runs); };
      body.append(
        h("div", { class: "ix-actions wrap" },
          btn("요청 A 보내기 (키 k-1)", () => {
            if (busy) return add("202", "아직 처리 중이라 다시 실행하지 않고 진행 상태만 알려 줍니다.");
            if (stored === "A") return add("200", "이미 처리한 요청입니다. 저장된 결과를 그대로 돌려주고 다시 실행하지 않습니다.", true);
            if (stored === "B") return add("409", "같은 키로 다른 내용이 이미 처리됐습니다. 거부합니다.", false);
            runs++; stored = "A"; add("200", "처음 받은 요청이라 실행하고 결과를 키와 함께 저장했습니다.", true);
          }, "primary"),
          btn("같은 키로 내용 B 보내기", () => {
            if (busy) return add("202", "아직 처리 중이라 다시 실행하지 않습니다.");
            if (!stored) { runs++; stored = "B"; return add("200", "처음 받은 요청이라 실행했습니다.", true); }
            if (stored === "B") return add("200", "저장된 결과를 그대로 돌려줍니다.", true);
            add("409", "같은 키인데 내용이 다릅니다. 실수나 재전송 공격일 수 있어 거부합니다.", false);
          }),
          btn("처리 중에 다시 보내기", () => { busy = true; if (!stored) { runs++; stored = "A"; } add("202", "같은 요청이 아직 실행 중입니다. 새로 실행하지 않고 '진행 중'을 돌려줍니다."); setTimeout(() => { busy = false; }, pace(2500)); }),
          btn("외부 쓰기 도중 시간 초과", () => add("unknown_outcome", "성공했는지 알 수 없습니다. 자동으로 다시 실행하면 두 번 처리될 수 있어, 결과 불명으로 기록하고 대상 시스템과 대조해 확정합니다.", false)),
          btn("처음부터", () => { stored = null; busy = false; runs = 0; log.replaceChildren(); counter.textContent = "0"; })),
        h("p", { class: "ix-meter" }, "Agent 실제 실행 횟수: ", counter),
        log);
    },

    // Chapter 6: lifecycle states.
    lifecycle(el) {
      const body = frame(el, "Agent 버전의 수명주기 진행해 보기", "버튼으로 버전을 다음 단계로 옮겨 보세요. 단계마다 업무 요청을 처리할 수 있는지가 바뀝니다.");
      const STATES = ["local experiment", "registered", "validated", "eligible", "production-approved", "deprecated", "retired"];
      const NEXT = ["Registry에 등록", "계약 검증 통과", "평가·검토 통과", "프로덕션 승인", "사용 중단 안내", "실행 종료"];
      let s = 0, quarantined = false;
      const st = stages(STATES);
      const out = result();
      const advance = btn("", () => { if (s < STATES.length - 1) { s++; update(); } }, "primary");
      const isolate = btn("문제 발견 · 격리", () => { quarantined = true; update(); });
      const reset = btn("처음부터", () => { s = 0; quarantined = false; update(); });
      function update() {
        st.items.forEach((li, n) => li.className = n < s ? "ok" : n === s ? (quarantined ? "bad" : "on") : "");
        advance.textContent = s < NEXT.length ? NEXT[s] : "마지막 단계";
        advance.disabled = quarantined || s >= STATES.length - 1;
        isolate.disabled = quarantined || s === 0 || s === STATES.length - 1;
        if (quarantined) return verdict(out, false, `quarantined · ${STATES[s]}에서 격리`, "문제가 확인되어 격리했습니다. 업무 요청을 받지 않고, 발행된 Agent Card도 갱신하거나 회수합니다.");
        const live = STATES[s] === "production-approved";
        verdict(out, live, `${STATES[s]} · 업무 요청 ${live ? "처리 가능" : "처리 불가"}`,
          live ? "프로덕션 승인을 받은 버전만 업무 트래픽을 처리하고 Agent Card를 발행합니다." :
          s === 1 ? "등록은 '존재를 알렸다'는 뜻일 뿐, 업무에 써도 된다는 승인이 아닙니다." :
          s < 4 ? "아직 승인 전입니다. 평가와 검토를 마쳐야 합니다." : "더 이상 새 업무 요청에 쓰지 않습니다.");
      }
      body.append(st.wrap, h("div", { class: "ix-actions wrap" }, advance, isolate, reset), out);
      update();
    },

    // Chapter 13: Agent Card signature verification.
    card(el) {
      const body = frame(el, "Agent Card 서명 검증해 보기", "받은 카드를 어떻게 다뤘는지 고르면, 받는 쪽의 검증 세 단계 결과가 나옵니다.");
      const CASES = [
        ["원본 카드 그대로", [true, true, true], true, "키를 찾았고, 정규화한 내용이 서명과 일치합니다. 카드를 믿어도 됩니다."],
        ["JSON 필드 순서와 공백만 바뀜", [true, true, true], true, "정규화(JCS)가 순서와 공백 차이를 없애므로 같은 내용으로 판단합니다. 서명이 그대로 맞습니다."],
        ["설명 한 글자를 고침(변조)", [true, true, false], false, "내용이 바뀌어 정규화 결과가 달라졌고 서명이 맞지 않습니다. 카드를 믿지 않습니다."],
        ["모르는 키(kid)로 서명됨", [false, null, null], false, "신뢰하는 키 목록에서 서명 키를 찾지 못했습니다. 더 진행하지 않고 거부합니다."],
      ];
      const st = stages(["키 조회 (kid · jku)", "정규화 (JCS)", "서명 검증 (JWS)"]);
      const out = result();
      const bs = CASES.map(([t, steps, ok, text], i) => btn(t, async () => {
        bs.forEach((b, n) => b.setAttribute("aria-pressed", String(n === i)));
        st.reset();
        for (const [n, r] of steps.entries()) { if (r === null) break; st.items[n].className = "on"; await wait(pace(450)); st.items[n].className = r ? "ok" : "bad"; }
        verdict(out, ok, ok ? "검증 성공" : "검증 실패", text);
      }, "case"));
      bs.forEach(b => b.setAttribute("aria-pressed", "false"));
      verdict(out, null, "경우를 고르세요", "검증에 실패한 카드는 그 안의 정보(주소, 기능)를 쓰지 않습니다.");
      body.append(h("div", { class: "ix-cases" }, bs), st.wrap, out);
    },

    // Chapter 14: conformance results for the bundled fixtures (same results as the test suite).
    conformance(el) {
      const body = frame(el, "적합성 검사 결과 미리 보기", "어떤 Agent를 검사하는지 고르면 11개 항목 결과를 보여 줍니다. 저장소의 실제 테스트 fixture를 검사한 결과와 같습니다.");
      const CHECKS = [["C1", "Manifest와 등록", "manifest-loading"], ["C2", "정상 호출", "adapter-path"], ["C3", "토큰 없음", "platform"], ["C4", "테넌트 위조", "platform"], ["C5", "같은 요청 재전송", "platform"], ["C6", "멱등성 충돌", "platform"], ["C7", "데이터 분류 낮추기", "platform"], ["C8", "미선언 도구·자격증명 노출", "platform"], ["C9", "adapter 오류", "platform"], ["C10", "Manifest requiredScopes", "platform"], ["C11", "Manifest identity.mode", "platform"]];
      const ALL = CHECKS.map(c => c[0]);
      const CASES = [
        ["템플릿 그대로", [], "모든 항목을 통과했습니다. 이제 handle을 고쳐 나만의 Agent로 바꿀 수 있습니다."],
        ["빈 응답을 돌려주는 adapter", ["C2", "C5", "C6", "C7", "C8", "C9"], "응답 형식이 결과 스키마에 맞지 않아 정상 호출과 이후 항목들이 실패합니다. 응답의 content를 비우지 마세요."],
        ["응답에 토큰 문자열을 넣는 adapter", ["C8"], "응답에서 자격증명처럼 보이는 문자열이 발견됐습니다. 응답에 토큰이나 lease를 넣지 마세요."],
        ["지원하지 않는 배포 프로파일", ALL, "Manifest를 등록할 수 없어 C1이 실패했고, 나머지는 검사하지 않았습니다. deployment.profile을 local로 바꾸세요."],
        ["폴더 밖을 가리키는 entrypoint", ALL, "entrypoint는 Agent 폴더 안의 module:factory만 허용합니다. C1이 실패해 나머지는 검사하지 않았습니다."],
      ];
      const table = h("ol", { class: "ix-checks" }, CHECKS.map(([id, t, g]) => h("li", {}, h("code", { text: id }), h("span", { text: t }), h("small", { text: g === "platform" ? "platform-enforcement" : g }), h("em"))));
      const out = result();
      const bs = CASES.map(([t, fails, text], i) => btn(t, async () => {
        bs.forEach((b, n) => b.setAttribute("aria-pressed", String(n === i)));
        const rows = [...table.children];
        rows.forEach(r => { r.className = ""; r.querySelector("em").textContent = ""; });
        const c1 = fails.includes("C1");
        for (const [n, r] of rows.entries()) {
          const id = CHECKS[n][0];
          await wait(pace(120));
          const skip = c1 && id !== "C1", bad = fails.includes(id);
          r.className = skip ? "skip" : bad ? "bad" : "ok";
          r.querySelector("em").textContent = skip ? "건너뜀" : bad ? "FAIL" : "PASS";
        }
        verdict(out, !fails.length, fails.length ? `${c1 ? 1 : fails.length}개 실패${c1 ? ", 나머지 건너뜀" : ""}` : "11개 모두 PASS", text);
      }, "case"));
      bs.forEach(b => b.setAttribute("aria-pressed", "false"));
      verdict(out, null, "Agent를 고르세요", "PASS는 플랫폼 규칙을 지킨다는 뜻이며, 업무 품질이나 보안 인증은 아닙니다.");
      body.append(h("div", { class: "ix-cases" }, bs), table, out);
    },

    // Chapter 4: five cases from the running story against four enforcement points.
    guardrail(el) {
      const body = frame(el, "Guardrail이 어디서 막는지 보기", "사례를 하나 고른 뒤 집행 지점을 끄거나 검사 범위와 모드를 바꿔 보세요. 한 지점이 빠지면 무엇이 빠져나가는지 볼 수 있습니다.");
      const POINTS = ["① 모델 입력·출력", "② 도구 호출·결과", "③ 검색 결과", "④ 실행 제어"];
      const CASES = S.guardrailCases;
      const rows = POINTS.map(p => h("li", { text: p }));
      const enabled = POINTS.map((p, i) => { const c = check(p + " 켜기", "point" + i); c.querySelector("input").checked = true; return c; });
      const scope = select("scope", [["all", "①이 모델로 들어가는 모든 글을 검사"], ["user", "①이 사용자 메시지만 검사"]]);
      const mode = select("mode", [["block", "차단 모드"], ["observe", "검사만 모드 (기록만 남김)"]]);
      const outage = check("검사 서비스 장애", "outage");
      const out = result();
      let current = 0;
      function show(i) {
        current = i;
        pressed(caseButtons, i);
        const c = CASES[i];
        // The first enabled point that can see this text catches it. Point ① only sees a tool result when it scans everything.
        const hit = c.points.find(p => on(enabled[p]) && !(p === 0 && !c.userMessage && !c.output && scope.value === "user"));
        rows.forEach((r, n) => { r.className = n === hit ? "hit" : c.points.includes(n) ? "hit2" : ""; });
        if (hit === undefined) return verdict(out, false, "빠져나감", `이 글을 볼 수 있는 집행 지점이 없습니다. ${c.points.map(p => POINTS[p]).join(", ")} 가운데 켜진 곳이 없거나 검사 범위 밖입니다. 한 지점이 다른 지점을 대신하지 못합니다.`);
        if (on(outage)) return verdict(out, null, `${POINTS[hit]} · 검사할 수 없어 차단`, "검사 서비스에 접근할 수 없습니다. 검사 없이 통과시키지 않고 막습니다(fail closed).");
        if (mode.value === "observe") return verdict(out, false, `${POINTS[hit]} · 기록만 하고 통과`, "판정은 기록됐지만 아무것도 막지 않았습니다. 검사만 모드는 정책을 시험할 때 쓰는 것이고 프로덕션의 방어가 아닙니다.");
        if (hit !== c.points[0]) return verdict(out, true, `${POINTS[hit]} · ${c.action}`, `${POINTS[c.points[0]]} 지점이 꺼져 있어 거기서는 걸리지 않았습니다. 이 글이 모델로 들어갈 때 ${POINTS[hit]} 검사가 같은 문장을 찾아 막았습니다.`);
        verdict(out, true, `${POINTS[hit]} · ${c.action}`, c.say);
      }
      const caseButtons = CASES.map((c, i) => btn(c.name, () => show(i), "case"));
      body.addEventListener("change", () => show(current));
      body.append(h("div", { class: "ix-cases" }, caseButtons), h("div", { class: "ix-controls" }, enabled), h("div", { class: "ix-controls grid" }, field("① 검사 범위", scope), field("모드", mode), outage), h("ol", { class: "ix-points" }, rows), out);
      show(0);
    },

    // Chapter 15: one tool call, seen from the app and from the tool route.
    "tool-call"(el) {
      const body = frame(el, "도구 불러 보기", "Agent 코드가 부르는 도구와 승인 상태를 바꿔 보세요. 결과마다 앱이 받는 응답과, 운영자가 도구 경로에서 보는 내부 진단을 나란히 보여 줍니다.");
      const tool = select("tool", [["read", "tool-erp-read · invoice-summary의 Manifest에 적은 읽기 도구"], ["undeclared", "tool-mail-send · invoice-summary의 Manifest에 없는 도구"], ["unregistered", "tool-fax-send · 플랫폼에 등록되지 않은 도구"], ["write", "tool-mail-send · invoice-mailer가 부르는 쓰기 도구"]]);
      const approval = select("approval", [["none", "승인 없음"], ["valid", "지훈의 유효한 승인"], ["expired", "만료된 승인"], ["other", "다른 요청에서 받은 승인"]]);
      const lost = check("메일 서버의 응답이 오다가 끊김", "lost");
      const out = result();
      const two = (ok, head, app, route) => verdict(out, ok, head, ["앱이 받은 응답: " + app, "내부 진단(도구 경로): " + route]);
      function update() {
        const write = tool.value === "write";
        approval.disabled = !write;
        lost.querySelector("input").disabled = !(write && approval.value === "valid");
        if (tool.value === "read") return two(true, "200 · 조회 성공", "200과 요약. 도구 주소나 자격증명은 응답 어디에도 없습니다.", "Manifest에 적힌 도구이고 호출자에게 tools.read가 있습니다. 이 호출 한 번용 lease를 발급해 ERP를 대신 불렀습니다.");
        if (tool.value === "undeclared") return two(false, "403 · 등록한 코드가 실행 중에 거절됨", "403 Tool is not declared in the Agent Manifest", "등록 실패가 아닙니다. Manifest는 유효했고 코드도 실행됐습니다. 코드가 capabilities.tools에 없는 도구를 부른 순간에 막혔습니다.");
        if (tool.value === "unregistered") return two(false, "403 · 등록되지 않은 도구", "403 Policy denied", "Tool not approved. Tool Registry에 승인된 도구가 아닙니다.");
        if (approval.value === "none") return two(false, "403 · 승인 없는 쓰기", "403 Policy denied", "Write tool requires approval. 평소에는 플랫폼이 승인까지 실행을 멈춰 기다립니다(waiting_approval). 승인 없는 호출이 도구 앞까지 오면 도구 경로가 마지막으로 거절합니다.");
        if (approval.value !== "valid") return two(false, "403 · 이 요청의 승인이 아님", "403 Policy denied", "Approval is stale or not bound to this request. 승인은 요청 하나에 묶여 있고 기한이 있습니다. 앱이 받는 응답은 승인이 없을 때와 똑같습니다.");
        if (on(lost)) return two(null, "unknown_outcome · 보냈는지 알 수 없음", "실패 응답. 메일이 나갔는지는 이 응답으로 알 수 없습니다.", "unknown_outcome으로 기록합니다. 자동으로 다시 보내면 메일이 두 번 나갈 수 있어, 메일 서버의 발송 기록과 대조해 확정합니다.");
        two(true, "200 · 승인된 쓰기 실행", "200. 메일이 한 번 나갔습니다.", "이 요청에 묶인 유효한 승인을 확인했고 호출자에게 tools.write가 있습니다.");
      }
      body.addEventListener("change", update);
      body.append(h("div", { class: "ix-controls grid" }, field("Agent 코드가 부르는 도구", tool), field("붙어 있는 승인", approval), lost), out);
      update();
    },

    // Chapter 16: the gates a call passes, in order.
    authz(el) {
      const body = frame(el, "검사 단계 통과해 보기", "누가 어떤 요청을 보내는지, Manifest에 무엇을 적었는지 바꿔 보세요. 요청은 위에서부터 검사 단계를 차례로 거치고, 막히면 그 뒤 단계는 검사하지 않습니다.");
      const SCOPES = ["agents.invoke", "models.invoke", "tools.read", "tools.write"];
      const group = (title, name) => h("fieldset", { class: "ix-set" }, h("legend", { text: title }), SCOPES.map(s => { const c = check(s, name + ":" + s); c.querySelector("input").checked = true; return c; }));
      const picked = set => SCOPES.filter(s => set.querySelector(`input[name$=":${s}"]`).checked);
      const callerSet = group("호출자가 가진 권한", "caller"), policySet = group("회사 정책이 허용한 권한", "policy");
      const preset = who => btn(who + "의 권한으로", () => { SCOPES.forEach(s => { callerSet.querySelector(`input[name$=":${s}"]`).checked = S.people[who].includes(s); }); update(); }, "case");
      const request = select("request", [["invoice-summary", "요청 A · invoice-summary에게 요약을 시킴"], ["invoice-mailer", "요청 C · invoice-mailer에게 메일 발송을 시킴"]]);
      const manifest = select("manifest", [["full", "도구가 요구하는 scope까지 모두 적음"], ["short", "tools.read를 빠뜨림"]]);
      const tool = select("tool", [["tool-erp-read", "tool-erp-read (읽기)"], ["tool-mail-send", "tool-mail-send (쓰기)"]]);
      const mode = select("mode", [["delegated", "delegated · 호출자를 대신해 실행"], ["independent", "independent · Agent 자신의 신원으로 실행"]]);
      const spoof = check("요청 본문에 다른 테넌트 적기", "spoof");
      const reuse = check("만료된 lease를 다시 쓰기", "reuse");
      const st = stages(["테넌트", "진입", "도구 목록", "실행 중 권한", "lease"]);
      const out = result();
      function update() {
        const agent = S.agents[request.value];
        const required = agent.requiredScopes.filter(s => !(manifest.value === "short" && s === "tools.read"));
        const effective = picked(callerSet).filter(s => picked(policySet).includes(s));
        const grant = mode.value === "delegated" ? effective : required.filter(s => picked(policySet).includes(s));
        const need = S.toolScopes[tool.value];
        const missing = required.filter(s => !effective.includes(s));
        const gates = [
          [on(spoof), "403 · 테넌트 검사", "본문에 적은 테넌트가 토큰의 테넌트와 다릅니다. 테넌트는 검증된 토큰에서만 정합니다."],
          [missing.length, "403 · 진입 검사", `Manifest가 요구한 ${missing.join(", ")}가 호출자 권한과 정책이 겹치는 범위에 없습니다. Agent 코드는 한 줄도 실행되지 않았습니다.`],
          [!agent.tools.includes(tool.value), "403 · 도구 목록 검사", `${tool.value}는 ${request.value}의 Manifest capabilities.tools에 없습니다. 호출자의 권한이 아무리 많아도 Agent가 선언하지 않은 도구는 쓸 수 없습니다.`],
          [!grant.includes(need), "403 · 실행 중 권한 검사", `Agent 코드는 실행됐지만 도구를 부르는 순간 ${need}가 없어 막혔습니다. ${manifest.value === "short" ? "Manifest의 requiredScopes에 이 scope를 적어 두었다면 진입 검사에서 일찍 막혔을 것입니다." : ""}`],
          [on(reuse), "거부 · lease 검사", "lease는 이 호출 한 번에 묶여 있고 짧은 시간 뒤 만료됩니다. 만료된 lease로는 ERP를 호출할 수 없습니다."],
        ];
        const stop = gates.findIndex(g => g[0]);
        st.items.forEach((li, n) => { li.className = stop < 0 || n < stop ? "ok" : n === stop ? "bad" : ""; });
        if (stop >= 0) return verdict(out, false, gates[stop][1], gates[stop][2]);
        const basis = mode.value === "delegated" ? "호출자 권한과 정책이 겹치는 범위" : "Manifest 선언과 정책이 겹치는 범위";
        verdict(out, true, "200 · 모든 검사 통과", `실행 중 권한은 ${basis}입니다: ${grant.join(", ")}.` + (tool.value === "tool-mail-send" ? " 쓰기 도구는 여기에 더해 쓰기 승인 검사를 거쳐야 합니다. 승인은 Agent Tools 장의 '도구 불러 보기'에서 다룹니다." : ""));
      }
      body.addEventListener("change", update);
      body.append(h("div", { class: "ix-cases" }, preset("서연"), preset("하준")), h("div", { class: "ix-controls sets" }, callerSet, policySet),
        h("div", { class: "ix-controls grid" }, field("요청", request), field("Manifest requiredScopes", manifest), field("Agent 코드가 부르는 도구", tool), field("identity.mode", mode), spoof, reuse), st.wrap, out);
      update();
    },

    // Chapter 17: what the gateway does when the model is unwell. Rows mirror impl/scenarios.
    "model-health"(el) {
      const body = frame(el, "모델 장애 때 Agent Gateway가 하는 일", "상황을 고르면 Agent Gateway가 모델을 몇 번 호출하는지와 앱이 받는 응답을 보여 줍니다. 상황은 참조 구현의 시나리오와 하나씩 대응합니다.");
      const ROWS = S.modelHealth;
      const own = check("Agent 코드에 재시도 3회를 직접 넣음", "own");
      const track = h("ol", { class: "ix-log path" });
      const out = result();
      const WORD = { ok: "성공", fail: "실패", slow: "시간 초과", blocked: "모델을 부르지 않고 바로 거절" };
      const TODO = { 200: "할 일이 없습니다.", 429: "Retry-After만큼 기다렸다 다시 보냅니다.", 502: "사용자에게 알립니다. Agent Gateway가 이미 3회 시도했습니다.", 504: "사용자에게 알리고, 남은 시간(timeoutMs)을 늘릴지 검토합니다." };
      let current = 0;
      function show(i) {
        current = i;
        pressed(bs, i);
        const r = ROWS[i], times = on(own) && r.attempts.includes("fail") && r.status !== 200 ? 3 : 1;
        track.replaceChildren();
        for (let t = 0; t < times; t++) r.attempts.forEach((a, n) => track.append(h("li", { class: a === "ok" ? "ok" : "bad", text: `${times > 1 ? `Agent 재시도 ${t + 1} · ` : ""}Agent Gateway 시도 ${n + 1}: ${WORD[a]}` })));
        const todo = r.status === 503 ? (r.retryAfter ? "Retry-After만큼 기다렸다 다시 보냅니다." : "잠시 뒤 한 번만 다시 보냅니다. 또 같으면 호출 번호로 운영자에게 확인합니다. 이 응답만으로는 연결 실패인지, 이 데이터 등급으로 갈 모델이 없는지 가릴 수 없습니다.") : TODO[r.status];
        const head = `앱이 받은 응답: ${r.status}${r.code ? " " + r.code : ""}${r.retryAfter ? " · Retry-After: " + r.retryAfter : ""}`;
        verdict(out, r.status === 200, head, [r.say, "앱이 할 일: " + todo].concat(times > 1 ? [`Agent 코드의 재시도가 Agent Gateway의 재시도와 곱해져 모델을 ${track.children.length}번 호출했습니다. 장애가 난 모델에 부하가 더 몰리고 응답은 더 늦어집니다. (예시)`] : []));
      }
      const bs = ROWS.map((r, i) => btn(r.name, () => show(i), "case"));
      own.addEventListener("change", () => show(current));
      body.append(h("div", { class: "ix-cases" }, bs), h("div", { class: "ix-controls" }, own), track, out);
      show(0);
    },

    // Chapter 18: the evaluation gate over the example score table.
    "eval-gate"(el) {
      const body = frame(el, "평가 데이터셋과 채점 바꿔 보기", "평가 데이터셋, Agent 버전, 채점 대상, 기준을 바꿔 보세요. 아래 여섯 행은 전체 데이터셋에서 뽑은 표본이고 점수는 전체 행으로 계산한 값입니다. (예시)");
      const E = S.evaluation;
      const dataset = select("dataset", [["3.0.0", "3.0.0 · 40행 (거래처명 질문 12행 포함)"], ["2.0.0", "2.0.0 · 28행 (번호 질문만)"]]);
      const version = select("version", [["1.2.0", "invoice-summary 1.2.0"], ["1.3.0", "invoice-summary 1.3.0"]]);
      const target = select("target", [["retrieved", "가져온 청구서까지 채점"], ["amount", "금액만 채점"]]);
      const threshold = select("threshold", [["0.9", "기준 0.90"], ["0.7", "기준 0.70"]]);
      const runs = select("runs", [["1", "1회 실행"], ["3", "3회 실행해 모두 맞아야 정답"]]);
      const table = h("ol", { class: "ix-checks" });
      const out = result();
      const pct = (n, d) => `${n}/${d} = ${(n / d).toFixed(3).replace(/0$/, "")}`;
      function update() {
        const r = E.results.find(x => x.dataset === dataset.value && x.version === version.value && x.runs === +runs.value);
        const d = E.datasets[dataset.value], th = +threshold.value;
        let missed = 0;
        table.replaceChildren(...E.sampleRows.map(row => {
          const absent = dataset.value === "2.0.0" && !row.in2;
          const why = row.wrong[version.value] || (runs.value === "3" && row.wrong[version.value + "x3"]);
          const lucky = why && row.amountLucky && target.value === "amount";
          if (lucky) missed++;
          return h("li", { class: absent ? "skip" : why && !lucky ? "bad" : lucky ? "" : "ok" }, h("code", { text: row.id }), h("span", { text: row.input }),
            h("small", { text: absent ? row.kind : why ? `${row.kind} · ${why}` : row.kind }), h("em", { text: absent ? "데이터셋에 없음" : lucky ? "정답으로 셈" : why ? "오답" : "정답" }));
        }));
        const pass = r.retrieved / d.rows >= th && r.amount / d.rows >= th;
        const shown = target.value === "amount" ? r.amount : r.retrieved;
        const lines = [`번호 질문 ${r.number}/${d.number}` + (d.name ? ` · 거래처명 질문 ${r.name}/${d.name}` : " · 거래처명 질문은 데이터셋에 없습니다"),
          `승격 판정은 두 지표를 모두 봅니다. 가져온 청구서 ${pct(r.retrieved, d.rows)}, 금액 ${pct(r.amount, d.rows)}, 기준 ${th.toFixed(2)}.`];
        if (missed) lines.push("금액만 채점해서 row-36을 정답으로 셌습니다. 엉뚱한 청구서를 가져왔는데 금액이 우연히 같았던 행입니다.");
        if (pass && d.name === 0) lines.push("이 점수는 거래처명으로 묻는 질문에 대해 아무것도 말해 주지 않습니다.");
        if (pass && th < 0.9) lines.push("기준을 낮춰서 통과했습니다. 틀리는 행 수는 그대로입니다.");
        verdict(out, pass, `${target.value === "amount" ? "금액" : "가져온 청구서"} ${pct(shown, d.rows)} · 승격 ${pass ? "후보" : "차단"}`, lines);
      }
      body.addEventListener("change", update);
      body.append(h("div", { class: "ix-controls grid" }, field("평가 데이터셋", dataset), field("Agent 버전", version), field("채점 대상", target), field("기준", threshold), field("실행 횟수", runs)), table, out);
      update();
    },

    // Chapter 19: group failures, pick a remedy, rescore on the same dataset, register.
    "tuning-loop"(el) {
      const body = frame(el, "틀린 행을 묶고 고쳐 보기", "먼저 틀린 행 네 개를 원인별로 나눠 보세요. 그다음 고칠 방법과 올리는 방식을 골라 다시 채점합니다. (예시)");
      const E = S.evaluation, BUCKETS = ["월 누락", "거래처 약칭", "상대 날짜"];
      const CARDS = [["row-33", "\"한빛상사 10월 청구서\"를 \"한빛상사\"로 조회", 0], ["row-29", "\"한빛 10월 청구서\"를 \"한빛\"으로 조회해 0건", 1], ["row-36", "\"대성물산 9월 청구서\"를 \"대성물산\"으로 조회", 0], ["row-40", "\"한빛상사 지난달 청구서\"를 \"한빛상사\"로 조회", 2]];
      const picks = CARDS.map(([id, text]) => field(`${id} · ${text}`, select(id, [["", "원인 고르기"], ...BUCKETS.map((b, i) => [String(i), b])])));
      const remedy = select("remedy", E.remedies.map(r => [r.id, `수단 ${r.id} · ${r.name} · 비용 ${r.cost}`]));
      const register = select("register", [["new", "새 버전 1.3.0으로 등록"], ["overwrite", "운영 중인 1.2.0을 덮어쓰기"]]);
      const bars = h("ol", { class: "ix-log" });
      const out = result();
      function update() {
        const chosen = picks.map(p => p.querySelector("select").value);
        const grouped = chosen.every((v, i) => v === String(CARDS[i][2]));
        bars.replaceChildren(...(grouped ? [[9, 0], [2, 1], [1, 2]].map(([n, b]) => h("li", { text: `${BUCKETS[b]} ${"■".repeat(n)} ${n}행` })) : []));
        if (chosen.includes("")) return verdict(out, null, "1단계 · 네 행의 원인을 골라 주세요", "검색어(query)에서 무엇이 빠졌거나 잘못됐는지를 봅니다.");
        if (!grouped) return verdict(out, false, "1단계 · 다시 보세요", "질문에 있던 정보 가운데 검색어에서 사라진 것이 무엇인지 비교해 보세요. 월이 빠졌나요, 거래처 이름이 줄었나요, 날짜가 숫자가 아니었나요.");
        const r = E.remedies.find(x => x.id === remedy.value);
        if (r.correct === null) return verdict(out, null, "수단 라 · 지금은 해 볼 수 없음", ["나머지 8행도 같은 기준으로 묶여 9 : 2 : 1이 됐습니다. 가장 큰 묶음은 월 누락입니다.", r.note]);
        const score = `${r.correct}/40 = ${r.correct / 40}`, pass = r.correct / 40 >= E.threshold;
        if (!pass) return verdict(out, false, `${score} · 게이트에서 차단`, [r.note, "같은 평가 데이터셋으로 다시 채점했기 때문에 배포 전에 드러났습니다."]);
        if (register.value === "overwrite") return verdict(out, false, `${score} · 덮어쓰기 거부`, "게시된 버전은 바꿀 수 없습니다. 덮어쓰면 어제 실행된 것이 무엇이었는지 알 수 없고 되돌릴 곳도 없어집니다. 새 버전으로 등록합니다.");
        verdict(out, true, `${score} · 1.3.0이 승격 후보로 등록됨`, [r.note, "1.2.0은 그대로 남아 있어 문제가 생기면 되돌릴 수 있습니다. 남은 3행(row-29, row-30, row-40)은 다음 개선 대상입니다. 프로덕션 승인은 사람이 따로 합니다."]);
      }
      body.addEventListener("change", update);
      body.append(h("div", { class: "ix-controls grid" }, picks), bars, h("div", { class: "ix-controls grid" }, field("2단계 · 고치는 방법", remedy), field("3단계 · 올리는 방식", register)), out);
      update();
    },

    // Chapter 11: stop and resume. Rules from docs/execution.md.
    resume(el) {
      const body = frame(el, "멈춘 실행 이어 하기", "실행 모드, 멈춘 시점, 멈춰 있는 동안 바뀐 것을 골라 보세요. (정의 단계의 규칙을 보여 주는 예시)");
      const mode = select("mode", [["durable", "durable · invoice-mailer"], ["sync", "sync · invoice-summary"]]);
      const at = select("at", [["after-read", "ERP 조회 뒤 프로세스가 죽음"], ["waiting", "지훈의 승인을 기다리는 중"], ["after-send", "메일 발송 직후 응답이 끊김"]]);
      const change = select("change", [["none", "바뀐 것 없음"], ["manifest", "그 사이 Manifest가 바뀜"], ["expired", "승인 기한이 지남"]]);
      const out = result();
      function update() {
        const sync = mode.value === "sync";
        if (sync) at.value = "after-read";
        [...at.options].forEach(o => { o.disabled = sync && o.value !== "after-read"; });
        change.disabled = sync || at.value !== "waiting";
        if (sync) return verdict(out, null, "처음부터 다시 실행", "sync 실행은 중간 상태를 남기지 않습니다. 읽기만 하는 Agent라 다시 해도 안전하고, 같은 멱등성 키면 Agent Platform APIs가 한 번으로 셉니다.");
        if (at.value === "after-read") return verdict(out, true, "checkpoint부터 재개", "ERP 조회 결과는 checkpoint에 남아 있어 다시 조회하지 않고 다음 단계부터 이어 갑니다.");
        if (at.value === "after-send") return verdict(out, false, "unknown_outcome · 다시 보내지 않음", "메일이 나갔는지 알 수 없습니다. 자동으로 다시 보내면 두 번 나갈 수 있어, 메일 서버의 발송 기록과 대조해 결과를 확정합니다.");
        if (change.value === "manifest") return verdict(out, false, "재개 거부", "checkpoint는 Manifest digest와 정책 버전에 묶여 있습니다. 지훈이 승인한 것은 바뀌기 전의 Agent이므로 이어서 실행하지 않습니다.");
        if (change.value === "expired") return verdict(out, false, "expired · 종료", "승인 기한이 지나 실행이 끝났습니다. 다시 보내려면 새 요청과 새 승인이 필요합니다.");
        verdict(out, true, "승인 뒤 재개", "지훈이 승인하면 권한을 다시 확인한 뒤 멈춘 자리에서 이어 갑니다. 조회와 요약은 다시 하지 않습니다.");
      }
      body.addEventListener("change", update);
      body.append(h("div", { class: "ix-controls grid" }, field("실행 모드", mode), field("멈춘 시점", at), field("멈춰 있는 동안", change)), out);
      update();
    },

    // Chapter 5: the eight negative fixtures of examples/negative as switches.
    "manifest-lint"(el) {
      const body = frame(el, "Manifest 검증해 보기", "invoice-summary의 Manifest에서 한 곳을 바꾸고 검증해 보세요. 아무것도 바꾸지 않으면 통과합니다. CLI는 실패 이유를 말해 주지 않으므로 이유는 가이드 해설로 붙였습니다.");
      const RULES = [
        ["mutable-revision", "source.revision을 main으로 바꾸기", "revision은 커밋 SHA여야 합니다. 브랜치 이름은 내일이면 다른 코드를 가리킵니다."],
        ["unexpected-secret", "identity에 secret 필드 넣기", "정의되지 않은 필드는 받지 않습니다. 자격증명을 적을 자리는 Manifest에 없습니다."],
        ["empty-tools", "capabilities.tools를 비우기", "tool 유형은 도구가 하나 이상 있어야 합니다. 이것은 등록 전 검증 실패이고, 등록된 코드가 적지 않은 도구를 부르는 실행 중 403과는 다른 실패입니다."],
        ["missing-owner", "metadata.owner.team 지우기", "문제가 생겼을 때 연락할 주인이 없는 Agent는 등록할 수 없습니다."],
        ["invalid-version", "metadata.version을 latest로 적기", "버전은 1.2.0 같은 세 자리 숫자여야 합니다. latest는 내일 다른 것을 가리킵니다."],
        ["unsupported-mode", "runtime.executionMode를 magic으로 적기", "실행 모드는 sync, async, durable 가운데 하나입니다."],
        ["malformed-uri", "source.repository를 주소가 아닌 글자로 적기", "저장소 주소는 URI 형식이어야 합니다."],
        ["invalid-classification", "governance.classification을 secret-company-value로 적기", "분류는 public, internal, confidential, restricted 가운데 하나입니다."],
      ];
      const boxes = RULES.map(r => check(r[1], r[0]));
      const cli = h("pre", {}, h("code"));
      const out = result();
      const run = btn("agentctl validate 실행", () => {
        const bad = RULES.filter((r, i) => on(boxes[i]));
        cli.firstChild.textContent = bad.length ? '[\n  {\n    "file": "agent-manifest.json",\n    "valid": false,\n    "error": "Invalid or unreadable Agent Manifest"\n  }\n]' : '[\n  {\n    "file": "agent-manifest.json",\n    "valid": true\n  }\n]';
        if (!bad.length) return verdict(out, true, "통과", "형식이 맞습니다. 통과는 등록할 수 있다는 뜻이고 업무에 써도 된다는 승인은 아닙니다.");
        verdict(out, false, `검증 실패 · 가이드 해설 (실패 fixture ${bad.map(r => r[0]).join(", ")})`, bad.map(r => r[2]));
      }, "primary");
      body.append(h("div", { class: "ix-controls" }, boxes), h("div", { class: "ix-actions" }, run), cli, out);
    },

    // Chapter 20: who does what through which door.
    roles(el) {
      const body = frame(el, "누가 어느 길로 무엇을 하나", "사람, 하려는 일, 길을 골라 보세요. 길이 달라도 나가는 요청이 같은지, 그 일을 지금 해 볼 수 있는지 보여 줍니다.");
      const who = select("who", [["민준", "민준 (개발자)"], ["서연", "서연 (사용자)"], ["지훈", "지훈 (승인자)"], ["하준", "하준 (권한이 모자란 사용자)"]]);
      const JOBS = {
        validate: ["Manifest 검증", "cli", "python scripts/agentctl.py validate <agent-manifest.json>", "실행"],
        invoke: ["Agent 호출", "api", "POST /v1/agents/invoice-summary/invocations  (invokeAgent)", "실행"],
        status: ["실행 상태 보기", "api", "GET /v1/invocations/{invocationId}  (getInvocation)", "계약만"],
        approve: ["승인", "api", "POST /v1/invocations/{invocationId}/approvals  (submitApproval)", "계약만"],
        trace: ["추적 보기", "none", "", "정의"],
        evaluation: ["평가 결과 보기", "none", "", "정의"],
      };
      const job = select("job", Object.entries(JOBS).map(([k, v]) => [k, v[0]]));
      const way = select("way", [["cli", "터미널 (DevTools)"], ["space", "Space 화면"], ["api", "API 직접 호출"]]);
      const out = result();
      function update() {
        const [name, kind, call, grade] = JOBS[job.value];
        if (kind === "none") return verdict(out, null, `${name} · 계약에 API 없음`, "v0.1 계약에는 이 일을 위한 API가 없습니다. Space 화면도 정의 단계입니다. 이 API가 있다고 가정하고 화면을 설계하면 붙일 곳이 없습니다.");
        if (kind === "cli") return verdict(out, way.value === "cli", way.value === "cli" ? `${name} · 지금 실행됨` : `${name} · 이 길은 없음`, way.value === "cli" ? ["실행되는 명령: " + call, "HTTP 요청이 나가지 않는 로컬 검사입니다. CI에도 같은 명령을 넣습니다."] : "Manifest 검증은 DevTools 명령으로만 합니다. 계약에 검증 API는 없습니다.");
        const lines = ["나가는 요청: " + call, way.value === "space" ? "Space 화면은 정의 단계입니다. 만들어지면 이 화면이 보내는 요청도 위와 같습니다." : way.value === "cli" ? "클라이언트 예제나 curl이 보내는 요청입니다." : "어느 화면이나 도구로 보내도 Agent Platform APIs에 같은 요청이 도착합니다."];
        if (grade === "계약만") return verdict(out, null, `${name} · 501 계약만 있음`, lines.concat("로컬 mock은 501 NOT_IMPLEMENTED(This target API is contract-only)를 돌려줍니다. 장애가 아니라 아직 구현되지 않았다는 뜻입니다."));
        if (who.value === "하준") return verdict(out, false, `${name} · 403`, lines.concat("요청은 같지만 하준에게는 models.invoke와 tools.read가 없어 진입 검사에서 막힙니다. 보내는 경로가 아니라 호출한 사람이 다릅니다."));
        verdict(out, true, `${name} · 200`, lines);
      }
      body.addEventListener("change", update);
      body.append(h("div", { class: "ix-controls grid" }, field("누가", who), field("하려는 일", job), field("어느 길로", way)), out);
      update();
    },

    // Chapter 12: the trace of request B narrows the search but does not name the cause.
    trace(el) {
      const body = frame(el, "추적 기록으로 범위 좁히기", "요청 B의 기록입니다. 구간을 눌러 남아 있는 속성을 보고, 다음에 할 일을 골라 보세요. (예시)");
      const SPANS = [
        ["invoke_agent invoice-summary", 0, 100, "1,840ms · 성공", "agent.id invoice-summary, agent.version 1.2.0, 호출 번호, 테넌트. 질문 원문은 없습니다."],
        ["chat · 검색어 만들기", 2, 17, "320ms · 성공", "모델 이름, 경로 결정 route-self-hosted, 입력·출력 토큰 수. 모델이 만든 검색어 원문은 없습니다."],
        ["execute_tool tool-erp-read", 20, 11, "210ms · 성공", "도구 ID와 버전, 정책 결정 allow, 결과 1건. 어느 청구서였는지와 조회 인자는 없습니다."],
        ["chat · 요약 만들기", 32, 63, "1,160ms · 성공", "모델 이름, 토큰 수. 요약 원문은 없습니다."],
      ];
      const broken = check("하위 Agent를 부르면서 traceparent를 넘기지 않기 (expense-settlement가 invoice-summary를 부르는 경우)", "broken");
      const rows = h("ol", { class: "ix-trace" });
      const out = result();
      function draw() {
        const cut = on(broken);
        rows.replaceChildren(...SPANS.map(([name, start, width, , attrs], i) => {
          const lost = cut && i > 0;
          const bar = h("span", { class: "bar" + (lost ? " lost" : "") });
          bar.style.marginLeft = start + "%";
          bar.style.width = width + "%";
          const li = h("li", { class: lost ? "lost" : "", tabindex: "0" }, h("span", { class: "name", text: cut && i === 0 ? "invoke_agent expense-settlement" : name }), h("code", { text: lost ? "trace 9c1e…" : "trace 4bf9…" }), h("span", { class: "track" }, bar));
          const open = () => verdict(out, null, `${name} · ${SPANS[i][3]}`, "남아 있는 속성: " + attrs);
          li.addEventListener("click", open);
          li.addEventListener("keydown", e => { if (e.key === "Enter") open(); });
          return li;
        }));
        if (cut) verdict(out, false, "기록이 두 동강 났습니다", "하위 Agent의 구간이 새 추적 번호(9c1e…)로 기록됐습니다. 호출 번호로 찾으면 위 한 줄만 나오고, 그 아래에서 무슨 일이 있었는지 따라갈 수 없습니다.");
        else verdict(out, null, "네 구간 모두 성공입니다", "오류도 없고 유난히 느린 곳도 없습니다. 그런데 금액이 틀렸습니다. 다음에 무엇을 하겠습니까.");
      }
      const acts = [
        ["더 큰 모델로 바꾼다", false, "아직 이릅니다", "모델이 틀렸다는 증거가 없습니다. 기록이 지워 준 것은 네트워크, 정책, 도구 오류까지입니다. 남은 가설은 '조회가 엉뚱한 청구서를 가져왔다'와 '요약이 금액을 틀렸다' 둘입니다."],
        ["도구 호출을 다시 시도한다", false, "도구는 고장 나지 않았습니다", "도구 호출은 성공했고 1건을 돌려줬습니다. 같은 검색어로 다시 호출해도 같은 청구서가 옵니다."],
        ["개발 환경에서 같은 질문을 다시 실행한다", true, "원인을 찾았습니다 · 개발 환경에서 다시 실행", "기대한 청구서는 INV-2048인데 INV-2101이 조회됐습니다. 검색어가 \"한빛상사\"였고 월이 빠져 있었습니다. 추적 기록은 범위를 좁혔고, 원인은 다시 실행해서 확정했습니다."],
      ].map(([t, ok, head, text]) => btn(t, () => verdict(out, ok, head, text), "case"));
      broken.addEventListener("change", draw);
      body.append(rows, h("div", { class: "ix-cases" }, acts), h("div", { class: "ix-controls" }, broken), out);
      draw();
    },

    // Chapter 11: what may go into Memory and who can read it back.
    memory(el) {
      const body = frame(el, "Memory에 넣고 꺼내 보기", "invoice-summary가 서연과의 대화에서 기억하려는 것을 하나씩 넣어 보세요. 그다음 조회하는 주체를 바꿔 무엇이 보이는지 확인합니다. (정의 단계의 규칙을 보여 주는 예시)");
      const CASES = S.memoryCases;
      const viewer = select("viewer", [["me", "서연 · invoice-summary"], ["user", "다른 사용자 · invoice-summary"], ["agent", "서연 · 다른 Agent"]]);
      const store = h("ol", { class: "ix-log" });
      const meter = h("p", { class: "ix-meter" });
      const out = result();
      const saved = new Set();
      function draw() {
        const mine = viewer.value === "me";
        store.replaceChildren(...[...saved].map(i => h("li", { class: mine ? "ok" : "" }, h("code", { text: `${CASES[i].store} · ${CASES[i].classification}` }), mine ? ` ${CASES[i].name} · 범위 finance / 서연 / invoice-summary` : " 범위 밖이라 보이지 않음")));
        meter.textContent = `저장된 항목 ${saved.size}건 · 이 주체가 조회하면 ${mine ? saved.size : 0}건`;
      }
      const bs = CASES.map((c, i) => btn(c.name, () => {
        if (c.ok !== false) saved.add(i);
        verdict(out, c.ok, c.ok === false ? "저장 거부" : c.ok ? `${c.store} Memory에 저장` : "저장돼도 지시로 쓰이지 않음", c.say);
        draw();
      }, "case"));
      viewer.addEventListener("change", () => { draw(); if (viewer.value !== "me") verdict(out, null, "조회 0건", "Memory 항목은 테넌트, 사용자, Agent에 묶여 있습니다. 셋 중 하나라도 다르면 있는지조차 알 수 없습니다."); });
      verdict(out, null, "넣을 것을 고르세요", "조회와 저장은 실행 추적에 기록되지만 내용 원문은 기록하지 않습니다.");
      body.append(h("div", { class: "ix-cases" }, bs), h("div", { class: "ix-controls grid" }, field("조회하는 주체", viewer)), meter, store, out);
      draw();
    },

    // Chapter 1: what each team builds with and without the platform.
    "before-after"(el) {
      const body = frame(el, "플랫폼이 있을 때와 없을 때", "버튼을 바꿔 보세요. 같은 통제를 팀마다 따로 만들 때와 플랫폼이 한 번 제공할 때의 차이입니다.");
      const ITEMS = ["인증·인가", "모델 접근·데이터 반출 통제", "자격증명 관리", "실행 기록·추적", "평가와 배포 승인"];
      const TEAMS = ["재무팀 Agent", "인사팀 Agent", "영업팀 Agent"];
      const WITHOUT = [["직접 구현", "직접 구현", "생략"], ["직접 구현", "생략", "직접 구현"], ["코드에 키 보관", "직접 구현", "코드에 키 보관"], ["로그 형식 제각각", "없음", "로그 형식 제각각"], ["수동 확인", "없음", "수동 확인"]];
      const grid = h("div", { class: "ix-grid" });
      const out = result();
      function draw(withPlatform) {
        a.setAttribute("aria-pressed", String(!withPlatform));
        b.setAttribute("aria-pressed", String(withPlatform));
        grid.replaceChildren(h("span", { class: "head" }), ...TEAMS.map(t => h("span", { class: "head", text: t })));
        ITEMS.forEach((item, r) => {
          grid.append(h("span", { class: "row", text: item }));
          if (withPlatform) grid.append(h("span", { class: "shared", text: "플랫폼이 동일하게 적용" }));
          else WITHOUT[r].forEach(v => grid.append(h("span", { class: v === "직접 구현" ? "" : "gap", text: v })));
        });
        grid.classList.toggle("with", withPlatform);
        if (withPlatform) verdict(out, true, "통제는 한 번, 모든 Agent에 같게", "팀은 Agent의 업무 로직에 집중하고, 보안·기록·승인은 플랫폼이 모든 Agent에 같은 기준으로 적용합니다.");
        else verdict(out, false, "같은 일을 세 번, 수준은 제각각", "팀마다 같은 통제를 따로 만들고, 일부는 빠지거나 방식이 달라 전체를 관리할 수 없습니다.");
      }
      const a = btn("플랫폼 없이", () => draw(false), "case");
      const b = btn("플랫폼과 함께", () => draw(true), "case");
      body.append(h("div", { class: "ix-cases" }, a, b), grid, out);
      draw(false);
    },
  };

  document.querySelectorAll(".content .sim[data-sim]").forEach(el => { const make = SIMS[el.dataset.sim]; if (make) make(el); });
})();
