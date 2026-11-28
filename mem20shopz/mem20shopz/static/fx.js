// mem20 shop fx: motion and filters layered on what app.js renders.
// It observes the DOM only and never fetches. #groups is rebuilt every 10s, so all
// state lives on stable elements and entrances play once.
(() => {
  "use strict";
  const d = document, root = d.documentElement, body = d.body;
  const $ = (s, c = d) => c.querySelector(s), $$ = (s, c = d) => [...c.querySelectorAll(s)];
  const RM = matchMedia("(prefers-reduced-motion: reduce)");
  const mo = (fn, node, opts) => node && new MutationObserver(fn).observe(node, opts);
  const replay = (n, c) => { n.classList.remove(c); void n.offsetWidth; n.classList.add(c); };

  // Theme toggle (head script already applied the saved choice before paint).
  const tb = $("#theme-btn");
  if (tb) tb.addEventListener("click", () => {
    const cur = root.dataset.theme || (matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    const t = cur === "dark" ? "light" : "dark";
    root.dataset.theme = t;
    try { localStorage.setItem("mem20-theme", t); } catch {}
  });

  // Nav scroll state, hidden-tab pause, off-screen hero pause, scroll reveal.
  const bar = $(".topbar");
  const onScroll = () => bar.classList.toggle("is-scrolled", scrollY > 8);
  addEventListener("scroll", onScroll, { passive: true }); onScroll();
  d.addEventListener("visibilitychange", () => root.classList.toggle("is-hidden", d.hidden));
  const hero = $(".hero");
  new IntersectionObserver(([e]) => hero.classList.toggle("is-paused", !e.isIntersecting)).observe(hero);
  const rv = new IntersectionObserver((es) => es.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add("is-in"); rv.unobserve(e.target); }
  }), { threshold: 0.15, rootMargin: "0px 0px -10% 0px" });
  $$(".reveal").forEach((n) => rv.observe(n));

  // Readiness: shop open/closed from #mode-pill, provisioning from its check tile,
  // and a one-shot stamp on any tile whose state really flipped.
  const mode = $("#mode-pill"), sb = $("#status-body"), seen = new Map();
  const syncStatus = () => {
    if (mode.classList.contains("ok")) body.dataset.shop = "open";
    else if (mode.classList.contains("warn")) body.dataset.shop = "closed";
    $$(".check", sb).forEach((n) => {
      const label = (n.firstChild ? n.firstChild.textContent : "").trim(), on = n.classList.contains("on");
      if (label === "Provisioning") body.dataset.prov = on ? "on" : "off";
      if (seen.has(label) && seen.get(label) !== on) n.classList.add("stamp");
      seen.set(label, on);
    });
  };
  mo(syncStatus, mode, { attributes: true, attributeFilter: ["class"] });
  mo(syncStatus, sb, { childList: true });

  // Toast: close button, tone from the heading, confetti only on a real "open".
  const note = $("#notice");
  const title = () => { const h = $("h3", note); return h ? h.textContent : ""; };
  let auto = 0;
  mo((ms) => {
    const hs = ms.flatMap((m) => [...m.addedNodes].filter((n) => n.nodeName === "H3").map((n) => n.textContent));
    if (!hs.length) return;
    const x = d.createElement("button");
    x.type = "button"; x.className = "notice-x"; x.textContent = "×";
    x.setAttribute("aria-label", "Dismiss notice");
    x.onclick = () => { note.hidden = true; };
    note.append(x);
    const t = title();
    const tone = /^The shop is open/.test(t) ? "ok" : /^Lost contact|could not start/.test(t) ? "bad"
      : /^New payment/.test(t) ? "gold" : "warn";
    note.dataset.tone = tone;
    replay(note, "is-new");
    clearTimeout(auto);
    if (tone === "ok" || tone === "gold") auto = setTimeout(() => { note.hidden = true; }, 9000);
    if (hs.includes("The shop is open")) confetti();
  }, note, { childList: true });

  // Live pill: mirror into the mobile bar; clear "Lost contact" once really reconnected.
  const dot = $("#dot"), lt = $("#live-text"), md = $("#mbar-dot"), mt = $("#mbar-text");
  mo(() => {
    if (md) { md.className = dot.className; mt.textContent = lt.textContent; }
    if (!dot.classList.contains("bad") && /^Lost contact/.test(title())) note.hidden = true;
  }, $("#live"), { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ["class"] });
  const mb = $("#mbar");
  if (mb) {
    const near = new Set();
    const io = new IntersectionObserver((es) => {
      es.forEach((e) => (e.isIntersecting ? near.add(e.target) : near.delete(e.target)));
      mb.classList.toggle("is-away", near.size > 0);
    });
    io.observe($("#catalog")); io.observe($(".hero-actions"));
  }

  // Activity: roll a count up only when it really increased.
  const al = $("#activity-list"), counts = new Map();
  mo(() => $$("li", al).forEach((li) => {
    const k = li.firstChild.textContent, n = +li.lastChild.textContent.replace(/\D/g, "");
    if (counts.has(k) && n > counts.get(k)) li.lastChild.classList.add("roll");
    counts.set(k, n);
  }), al, { childList: true });

  // Catalog filters. State lives on #groups, which survives replaceChildren().
  const G = $("#groups"), prices = new Map();
  G.dataset.filterState = "all"; G.dataset.filterGroup = "all";
  const fb = d.createElement("div");
  fb.className = "filters"; fb.hidden = true;
  const mkGroup = (label) => { const g = d.createElement("div"); g.className = "chips"; g.setAttribute("role", "group"); g.setAttribute("aria-label", label); fb.append(g); return g; };
  const cs = mkGroup("Filter by state"), cg = mkGroup("Filter by group");
  const say = d.createElement("p"); say.className = "sr-only"; say.setAttribute("aria-live", "polite"); fb.append(say);
  G.before(fb);
  const chip = (parent, k, v, label) => {
    const b = d.createElement("button"); b.type = "button"; b.className = "fchip";
    b.dataset.k = k; b.dataset.v = v; b.append(label + " ");
    const n = d.createElement("span"); n.className = "n"; b.append(n); parent.append(b);
  };
  [["all", "All"], ["buyable", "Buyable"], ["unpriced", "Price not set"], ["paused", "Checkout paused"]]
    .forEach(([v, l]) => chip(cs, "filterState", v, l));
  const gt = (g) => { const h = $(".group-head h3", g); return h ? h.textContent : ""; };
  let gkey = null;
  const apply = () => {
    const gs = $$(".group", G), key = gs.map(gt).join("\n");
    if (key !== gkey) {
      gkey = key; cg.replaceChildren(); chip(cg, "filterGroup", "all", "All groups");
      gs.forEach((g) => chip(cg, "filterGroup", gt(g), gt(g)));
      if (!gs.some((g) => gt(g) === G.dataset.filterGroup)) G.dataset.filterGroup = "all";
    }
    const fs = G.dataset.filterState, fg = G.dataset.filterGroup;
    const sc = { all: 0, buyable: 0, unpriced: 0, paused: 0 }, gc = { all: 0 };
    let shown = 0, total = 0;
    gs.forEach((g) => {
      const t = gt(g), inG = fg === "all" || t === fg;
      let vis = 0;
      $$(".card", g).forEach((c) => {
        const s = c.dataset.state; total++;
        if (inG) { sc.all++; sc[s] = (sc[s] || 0) + 1; }
        if (fs === "all" || s === fs) { gc.all++; gc[t] = (gc[t] || 0) + 1; if (inG) vis++; }
      });
      g.toggleAttribute("data-off", !inG || (fs !== "all" && !vis));
      shown += vis;
    });
    for (const b of $$(".fchip", fb)) {
      const isS = b.dataset.k === "filterState", n = (isS ? sc : gc)[b.dataset.v] || 0;
      const on = G.dataset[b.dataset.k] === b.dataset.v;
      b.setAttribute("aria-pressed", on); b.lastChild.textContent = n; b.disabled = !n && !on;
    }
    fb.hidden = !total;
    return `Showing ${shown} of ${total} products`;
  };
  fb.addEventListener("click", (e) => {
    const b = e.target.closest(".fchip");
    if (!b) return;
    G.dataset[b.dataset.k] = b.dataset.v;
    say.textContent = apply();
    if (!RM.matches) replay(b, "pop");
  });

  // Rebuilds: stagger once, flash honest price changes, re-apply filters synchronously
  // (before paint, so no flicker). Button text tells us busy / error.
  let ready = false;
  mo((ms) => {
    let rebuilt = false;
    for (const m of ms) {
      if (m.target === G) { rebuilt = true; continue; }
      const b = m.target;
      if (b.nodeName !== "BUTTON") continue;
      const t = b.textContent, busy = t === "Starting…";
      b.classList.toggle("is-busy", busy);
      busy ? b.setAttribute("aria-busy", "true") : b.removeAttribute("aria-busy");
      if (t === "Try again") replay(b, "is-error"); else b.classList.remove("is-error");
    }
    if (!rebuilt) return;
    const cards = $$(".card", G);
    cards.forEach((c, i) => {
      const p = $(".price", c), t = p ? p.textContent : "", id = c.dataset.sku, k = id && id !== "undefined" ? id : "#" + i;
      if (prices.has(k) && prices.get(k) !== t) c.classList.add("flash");
      prices.set(k, t);
      if (!ready) c.style.setProperty("--i", Math.min(i, 12));
    });
    if (cards.length && !ready) { ready = true; setTimeout(() => { G.dataset.ready = ""; }, 1600); }
    apply();
  }, G, { childList: true, subtree: true });

  // Tilt + spotlight: one delegated listener; only CSS vars are written, via rAF.
  if (matchMedia("(hover:hover) and (pointer:fine)").matches && !RM.matches) {
    let cur = null, ev = null, q = 0;
    const reset = (c) => c && (c.style.removeProperty("--rx"), c.style.removeProperty("--ry"));
    const draw = () => {
      q = 0; if (!cur || !ev) return;
      const r = cur.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width, y = (ev.clientY - r.top) / r.height;
      cur.style.setProperty("--mx", (x * 100).toFixed(1) + "%");
      cur.style.setProperty("--my", (y * 100).toFixed(1) + "%");
      if (cur.dataset.state !== "buyable") return;
      cur.style.setProperty("--rx", ((0.5 - y) * 8).toFixed(2) + "deg");
      cur.style.setProperty("--ry", ((x - 0.5) * 8).toFixed(2) + "deg");
    };
    G.addEventListener("pointermove", (e) => {
      const c = e.target.closest(".card");
      if (c !== cur) { reset(cur); cur = c; }
      ev = e; if (c && !q) { q = 1; requestAnimationFrame(draw); }
    });
    G.addEventListener("pointerleave", () => { reset(cur); cur = null; });
  }

  // One-shot confetti (40 particles, 1.2s) for a real change to "open".
  function confetti() {
    if (RM.matches) return;
    const c = d.createElement("canvas"), x = c.getContext("2d"), W = (c.width = innerWidth), H = (c.height = innerHeight);
    c.className = "confetti"; c.setAttribute("aria-hidden", "true"); body.append(c);
    const cs2 = getComputedStyle(root), col = ["--grounded", "--violet", "--pop", "--gold"].map((v) => cs2.getPropertyValue(v).trim());
    const r = note.getBoundingClientRect(), ox = r.width ? r.left + r.width / 2 : W / 2, oy = r.width ? r.top : H / 2;
    const P = Array.from({ length: 40 }, (_, i) => ({ x: ox, y: oy, vx: (Math.random() - 0.5) * 10, vy: -4 - Math.random() * 9, a: Math.random() * 6, c: col[i % 4], s: 5 + Math.random() * 5 }));
    const t0 = performance.now();
    const f = (t) => {
      const k = (t - t0) / 1200;
      x.clearRect(0, 0, W, H);
      if (k >= 1) return c.remove();
      for (const p of P) {
        p.vy += 0.35; p.x += p.vx; p.y += p.vy; p.a += 0.2;
        x.save(); x.globalAlpha = 1 - k; x.translate(p.x, p.y); x.rotate(p.a);
        x.fillStyle = p.c; x.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2); x.restore();
      }
      requestAnimationFrame(f);
    };
    requestAnimationFrame(f);
  }
})();
