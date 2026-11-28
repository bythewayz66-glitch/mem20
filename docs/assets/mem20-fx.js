/* mem20.com effects: reveal, counters, tilt, lattice, marquee pause, sticky CTA, theme, estate filter.
   Vanilla, no deps. Decorative motion never shows numbers; every number on screen comes from the HTML or surface.json. */
(function () {
  'use strict';
  var d = document, R = d.documentElement, $ = function (s, c) { return (c || d).querySelector(s); },
    $$ = function (s, c) { return [].slice.call((c || d).querySelectorAll(s)); },
    mq = function (q) { return window.matchMedia && matchMedia(q).matches; },
    RM = mq('(prefers-reduced-motion: reduce)'), FINE = mq('(hover:hover) and (pointer:fine)'),
    IO = 'IntersectionObserver' in window;
  R.classList.add('fx');
  function seen(el, cb, opt) { // fire once when el enters view
    if (!IO) return cb(el);
    var o = new IntersectionObserver(function (es) { es.forEach(function (e) { if (e.isIntersecting) { o.unobserve(e.target); cb(e.target); } }); }, opt || { threshold: .15, rootMargin: '0px 0px -10% 0px' });
    o.observe(el);
  }
  function inView(el, cb) { // toggling visibility (for ambient loops)
    if (!IO) return cb(true);
    new IntersectionObserver(function (es) { cb(es[0].isIntersecting); }).observe(el);
  }

  /* theme (5.15) */
  function theme() { return R.dataset.theme || (mq('(prefers-color-scheme: light)') ? 'light' : 'dark'); }
  $$('.theme-toggle').forEach(function (b) {
    b.addEventListener('click', function () {
      var t = theme() === 'light' ? 'dark' : 'light';
      R.dataset.theme = t; try { localStorage.setItem('mem20-theme', t); } catch (e) {}
      syncTheme(); d.dispatchEvent(new Event('mem20:theme'));
    });
  });
  function syncTheme() { $$('.theme-toggle').forEach(function (b) { b.setAttribute('aria-pressed', theme() === 'light'); }); }
  syncTheme();

  /* nav: scroll state + burger (5.1) */
  var nav = $('nav'), burger = $('.burger');
  function onScroll() { nav.classList.toggle('is-scrolled', scrollY > 8); }
  addEventListener('scroll', onScroll, { passive: true }); onScroll();
  if (burger) {
    var setOpen = function (o) { nav.classList.toggle('is-open', o); burger.setAttribute('aria-expanded', o); };
    burger.addEventListener('click', function () { setOpen(!nav.classList.contains('is-open')); });
    $$('.nav-links a').forEach(function (a) { a.addEventListener('click', function () { setOpen(false); }); });
    d.addEventListener('keydown', function (e) { if (e.key === 'Escape' && nav.classList.contains('is-open')) { setOpen(false); burger.focus(); } });
  }

  /* surface.json status pill: reports how the inline loader's fetch went */
  var pill = $('#surface-pill');
  if (pill) Promise.resolve(window.__m20surface || false).then(function (ok) {
    pill.classList.toggle('is-sim', !ok);
    $('.dot', pill).className = 'dot ' + (ok ? 'ok' : 'hollow');
    $('.lt', pill).textContent = ok ? 'surface.json pinned' : 'static fallback';
    pill.setAttribute('aria-label', 'Numbers: ' + (ok ? 'surface.json pinned' : 'static fallback'));
  });

  /* scroll reveal (5.8) */
  $$('.reveal').forEach(function (el) { seen(el, function () { el.classList.add('is-in'); }); });

  /* counters (5.5): count to the element's current text; follow later writes from the surface.json loader */
  $$('[data-count]').forEach(function (el) {
    var target = parseInt(el.textContent, 10); if (isNaN(target)) return;
    el.style.minWidth = String(target).length + 'ch';
    if (RM) return;
    var last = null, t0 = 0, run = false;
    function paint(v) { el.innerHTML = '<span class="sr-only">' + target + '</span><span aria-hidden="true">' + v + '</span>'; last = el.textContent; }
    new MutationObserver(function () {
      if (el.textContent === last) return;
      var v = parseInt(el.textContent, 10); if (isNaN(v)) return;
      target = v; el.style.minWidth = String(v).length + 'ch';
      if (!run) { last = el.textContent; }
    }).observe(el, { childList: true, characterData: true, subtree: true });
    seen(el, function () {
      run = true; paint(0);
      requestAnimationFrame(function step(ts) {
        t0 = t0 || ts; var p = Math.min(1, (ts - t0) / 900), e = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
        if (p < 1) { paint(Math.round(target * e)); requestAnimationFrame(step); }
        else { run = false; el.textContent = String(target); last = el.textContent; el.setAttribute('aria-label', target); }
      });
    }, { threshold: .4 });
  });
  $$('[data-stamp]').forEach(function (el) { if (!RM) seen(el, function () { el.classList.add('stamp-in'); }, { threshold: .4 }); });

  /* largest-domains bars: width = count / max, recomputed whenever the loader rewrites the rows */
  var tb = $('#largest-domains');
  function bars() {
    var rows = $$('tr', tb), n = rows.map(function (r) { return parseFloat(r.cells[1] && r.cells[1].textContent) || 0; }),
      max = Math.max.apply(null, n.concat(1));
    rows.forEach(function (r, i) { r.cells[0].style.setProperty('--w', (n[i] / max).toFixed(3)); r.cells[0].style.setProperty('--i', i); });
  }
  if (tb) { bars(); new MutationObserver(bars).observe(tb, { childList: true }); }

  /* card spotlight + tilt (5.6): one delegated listener, CSS vars only, rAF-batched */
  var CARDS = '.card:not(.is-sim),.fx-card';
  d.addEventListener('pointermove', function (e) {
    var c = e.target.closest && e.target.closest(CARDS); if (!c || e.pointerType === 'touch') return;
    var r = c.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    requestAnimationFrame(function () {
      c.style.setProperty('--mx', (x * 100).toFixed(1) + '%'); c.style.setProperty('--my', (y * 100).toFixed(1) + '%');
      if (FINE && !RM) { c.classList.add('is-tilting'); c.style.setProperty('--rx', ((.5 - y) * 8).toFixed(2) + 'deg'); c.style.setProperty('--ry', ((x - .5) * 8).toFixed(2) + 'deg'); }
    });
  }, { passive: true });
  d.addEventListener('pointerout', function (e) {
    var c = e.target.closest && e.target.closest(CARDS); if (!c || c.contains(e.relatedTarget)) return;
    requestAnimationFrame(function () { c.classList.remove('is-tilting'); c.style.removeProperty('--rx'); c.style.removeProperty('--ry'); });
  });

  /* ambient loops pause off-screen (rule 6.4) */
  $$('.marquee, .hero').forEach(function (el) { inView(el, function (v) { el.classList.toggle('is-paused', !v); }); });

  /* estate: family filter chips + domain search (5.11, 9) */
  var fam = $('.fam'), tools = $('.estate-tools');
  if (fam && tools) {
    var cards = $$('.fam-card', fam), status = $('#estate-status'), grp = $('.filters', tools), q = $('input', tools), cur = 'all';
    var total = 0;
    cards.forEach(function (c, i) {
      var n = $$('.chip', c).length; total += n; c.dataset.fam = i;
      $$('.chip', c).forEach(function (ch) { ch.title = ch.textContent; });
      var s = d.createElement('span'); s.className = 'cnt'; s.textContent = n + ' domains'; $('h3', c).appendChild(s);
    });
    function chip(label, n, key) {
      var b = d.createElement('button'); b.type = 'button'; b.className = 'fchip'; b.dataset.key = key;
      b.setAttribute('aria-pressed', key === 'all'); b.innerHTML = label + ' <b>' + n + '</b>'; grp.appendChild(b);
    }
    chip('All', total, 'all');
    cards.forEach(function (c, i) { chip($('h3', c).firstChild.textContent.trim(), $$('.chip', c).length, String(i)); });
    function apply() {
      var term = q.value.trim().toLowerCase(), shown = 0, hits = 0, doms = 0;
      cards.forEach(function (c) {
        var on = cur === 'all' || c.dataset.fam === cur; c.hidden = !on; if (!on) return; shown++;
        $$('.chip', c).forEach(function (ch) {
          doms++; var m = term && ch.textContent.toLowerCase().indexOf(term) > -1; if (m) hits++;
          ch.classList.toggle('is-hit', !!m); ch.classList.toggle('is-dim', !!term && !m);
        });
      });
      status.textContent = 'Showing ' + shown + ' of ' + cards.length + ' families, ' + doms + ' domains' + (term ? '; ' + hits + ' match "' + q.value.trim() + '"' : '') + '.';
    }
    grp.addEventListener('click', function (e) {
      var b = e.target.closest('.fchip'); if (!b) return; cur = b.dataset.key;
      $$('.fchip', grp).forEach(function (x) { x.setAttribute('aria-pressed', x === b); }); apply();
    });
    q.addEventListener('input', apply);
    tools.hidden = false;
  }

  /* terminal: copy + type-in on first reveal (5.14) */
  var pre = $('pre.code'), copy = $('.copy');
  if (copy && pre && navigator.clipboard) {
    copy.hidden = false;
    copy.addEventListener('click', function () {
      navigator.clipboard.writeText(pre.textContent).then(function () {
        copy.textContent = 'Copied ✓'; setTimeout(function () { copy.textContent = 'Copy'; }, 1600);
      }, function () { copy.textContent = 'Copy failed'; });
    });
  }
  if (pre && !RM) {
    var nodes = [], w = d.createTreeWalker(pre, NodeFilter.SHOW_TEXT);
    while (w.nextNode()) nodes.push([w.currentNode, w.currentNode.data]);
    seen(pre, function () {
      pre.style.minHeight = pre.offsetHeight + 'px'; pre.classList.add('is-typing'); pre.setAttribute('aria-busy', 'true');
      nodes.forEach(function (n) { n[0].data = ''; });
      var k = 0, j = 0;
      (function tick() {
        for (var s = 0; s < 2 && k < nodes.length; s++) { // ~18ms per character
          var n = nodes[k]; n[0].data = n[1].slice(0, ++j); if (j >= n[1].length) { k++; j = 0; }
        }
        if (k < nodes.length) setTimeout(tick, 36);
        else { pre.classList.remove('is-typing'); pre.removeAttribute('aria-busy'); pre.style.minHeight = ''; }
      })();
    }, { threshold: .5 });
  }

  /* sticky CTA (5.9): after the hero, hidden near the footer, dismissible per session */
  var dock = $('.dock'), hero = $('.hero'), foot = $('footer');
  if (dock && IO && hero && foot) {
    var off = false; try { off = sessionStorage.getItem('mem20-dock') === '0'; } catch (e) {}
    if (!off) {
      dock.hidden = false;
      var pastHero = false, nearFoot = false, upd = function () { dock.classList.toggle('is-shown', pastHero && !nearFoot); dock.inert = !(pastHero && !nearFoot); };
      new IntersectionObserver(function (es) { pastHero = !es[0].isIntersecting && es[0].boundingClientRect.top < 0; upd(); }).observe(hero);
      new IntersectionObserver(function (es) { nearFoot = es[0].isIntersecting; upd(); }).observe(foot);
      $('.x', dock).addEventListener('click', function () { dock.remove(); try { sessionStorage.setItem('mem20-dock', '0'); } catch (e) {} });
    }
  }

  /* hero lattice (5.4): grounded = filled + solid edges, simulated = hollow + dashed edges. No numbers. */
  var cv = $('#lattice');
  if (cv && cv.getContext) {
    var cx = cv.getContext('2d'), W = 0, H = 0, DPR = Math.min(2, devicePixelRatio || 1), N = innerWidth < 760 ? 8 : 16,
      nodes2 = [], edges = [], col = {}, px = 0, py = 0, comet = null, lastPulse = 0, visible = true, raf = 0, lastF = 0;
    var readCol = function () { var cs = getComputedStyle(R); ['grounded', 'simulated', 'pop', 'line-2', 'muted', 'surface'].forEach(function (k) { col[k] = cs.getPropertyValue('--' + k).trim(); }); };
    var size = function () { var r = cv.getBoundingClientRect(); W = r.width; H = r.height; cv.width = W * DPR; cv.height = H * DPR; cx.setTransform(DPR, 0, 0, DPR, 0, 0); };
    var rnd = function (a, b) { return a + Math.random() * (b - a); };
    readCol(); size();
    for (var i = 0; i < N; i++) nodes2.push({ x: rnd(.12, .88), y: rnd(.14, .84), vx: 0, vy: 0, sim: i % 3 === 2, r: i % 3 === 2 ? 6 : rnd(5, 8), f: 0 });
    nodes2[0].sim = false; nodes2[0].r = 9; // query node
    nodes2.forEach(function (a, i) { // connect each node to its 2 nearest neighbours
      nodes2.map(function (b, j) { return [Math.hypot(a.x - b.x, a.y - b.y), j]; }).sort(function (p, q) { return p[0] - q[0]; }).slice(1, 3)
        .forEach(function (p) { var j = p[1]; if (!edges.some(function (e) { return (e[0] === i && e[1] === j) || (e[0] === j && e[1] === i); })) edges.push([i, j]); });
    });
    var nb = function (i) { return edges.filter(function (e) { return e[0] === i || e[1] === i; }).map(function (e) { return e[0] === i ? e[1] : e[0]; }); };
    var physics = function () { // soft force layout: weak repulsion + springy edges + gentle drift
      nodes2.forEach(function (a, i) {
        nodes2.forEach(function (b, j) { if (i === j) return; var dx = a.x - b.x, dy = a.y - b.y, q = dx * dx + dy * dy + 1e-4; if (q < .04) { a.vx += dx / q * 2e-5; a.vy += dy / q * 2e-5; } });
        a.vx += (.5 - a.x) * 4e-5 + Math.sin(performance.now() / 2400 + i) * 3e-5; a.vy += (.5 - a.y) * 4e-5 + Math.cos(performance.now() / 2800 + i * 1.7) * 3e-5;
      });
      edges.forEach(function (e) { var a = nodes2[e[0]], b = nodes2[e[1]], dx = b.x - a.x, dy = b.y - a.y, L = Math.hypot(dx, dy) || 1, k = (L - .22) * 4e-4; a.vx += dx / L * k; a.vy += dy / L * k; b.vx -= dx / L * k; b.vy -= dy / L * k; });
      nodes2.forEach(function (a) { a.vx *= .9; a.vy *= .9; a.x = Math.min(.92, Math.max(.08, a.x + a.vx)); a.y = Math.min(.88, Math.max(.12, a.y + a.vy)); a.f *= .94; });
    };
    var P = function (n) { return [n.x * W + px * (n.r / 9) * 6, n.y * H + py * (n.r / 9) * 6]; };
    var draw = function (now) {
      cx.clearRect(0, 0, W, H); cx.lineWidth = 1.2;
      edges.forEach(function (e) {
        var a = nodes2[e[0]], b = nodes2[e[1]], s = a.sim || b.sim, p = P(a), q = P(b);
        cx.setLineDash(s ? [4, 4] : []); cx.strokeStyle = s ? col.simulated : col.grounded; cx.globalAlpha = s ? .45 : .4;
        cx.beginPath(); cx.moveTo(p[0], p[1]); cx.lineTo(q[0], q[1]); cx.stroke();
      });
      cx.setLineDash([]); cx.globalAlpha = 1;
      if (comet) { // retrieval pulse
        var seg = Math.min(comet.path.length - 2, Math.floor(comet.t)), u = comet.t - seg, A = P(nodes2[comet.path[seg]]), B = P(nodes2[comet.path[seg + 1]]),
          x = A[0] + (B[0] - A[0]) * u, y = A[1] + (B[1] - A[1]) * u, g = cx.createRadialGradient(x, y, 0, x, y, 16);
        g.addColorStop(0, col.pop); g.addColorStop(1, 'transparent'); cx.fillStyle = g; cx.beginPath(); cx.arc(x, y, 16, 0, 7); cx.fill();
        cx.fillStyle = col.pop; cx.beginPath(); cx.arc(x, y, 3, 0, 7); cx.fill();
      }
      nodes2.forEach(function (n, i) {
        var p = P(n), r = n.r + n.f * 4;
        if (n.f > .05) { cx.globalAlpha = n.f * .5; cx.strokeStyle = n.sim ? col.simulated : col.pop; cx.lineWidth = 2; cx.beginPath(); cx.arc(p[0], p[1], r + 6, 0, 7); cx.stroke(); cx.globalAlpha = 1; }
        cx.beginPath(); cx.arc(p[0], p[1], r, 0, 7);
        if (n.sim) { cx.fillStyle = col.surface; cx.fill(); cx.lineWidth = 2; cx.strokeStyle = col.simulated; cx.stroke(); } // stays hollow, even when touched
        else { cx.fillStyle = col.grounded; cx.fill(); }
        if (i === 0) { cx.lineWidth = 2; cx.strokeStyle = col.pop; cx.beginPath(); cx.arc(p[0], p[1], r + 4, 0, 7); cx.stroke(); }
      });
      cx.font = '500 10px "JetBrains Mono", monospace'; cx.fillStyle = col.muted;
      var g1 = nodes2.filter(function (n, i) { return i && !n.sim; })[0], s1 = nodes2.filter(function (n) { return n.sim; })[0];
      if (g1) { var a = P(g1); cx.fillText('grounded', a[0] + g1.r + 6, a[1] + 3); }
      if (s1) { var b = P(s1); cx.fillText('simulated', b[0] + s1.r + 6, b[1] + 3); }
    };
    var pulse = function () { // walk 3-4 hops from the query node
      var path = [0], cur2 = 0;
      for (var h = 0; h < 4; h++) { var o = nb(cur2).filter(function (j) { return path.indexOf(j) < 0; }); if (!o.length) break; cur2 = o[Math.floor(Math.random() * o.length)]; path.push(cur2); }
      if (path.length > 1) comet = { path: path, t: 0 };
    };
    var loop = function (now) {
      raf = 0; if (!visible || d.hidden) return;
      raf = requestAnimationFrame(loop);
      if (now - lastF < 33) return; lastF = now; // <= 30fps
      physics();
      if (now - lastPulse > 2500) { lastPulse = now; pulse(); }
      if (comet) { var before = Math.floor(comet.t); comet.t += .06; var at = Math.floor(comet.t); if (at !== before || comet.t < .07) nodes2[comet.path[Math.min(at, comet.path.length - 1)]].f = 1; if (comet.t >= comet.path.length - 1) comet = null; }
      draw(now);
    };
    var start = function () { if (!raf && visible && !d.hidden && !RM) raf = requestAnimationFrame(loop); };
    if (RM) { for (var s = 0; s < 120; s++) physics(); draw(0); }
    else {
      inView(cv, function (v) { visible = v; start(); });
      d.addEventListener('visibilitychange', start);
      if (FINE) cv.parentNode.addEventListener('pointermove', function (e) { var r = cv.getBoundingClientRect(); px = (e.clientX - r.left) / r.width - .5; py = (e.clientY - r.top) / r.height - .5; }, { passive: true });
      start();
    }
    var redraw = function () { readCol(); size(); if (RM || !raf) draw(0); };
    addEventListener('resize', redraw); d.addEventListener('mem20:theme', redraw);
    if (window.matchMedia) matchMedia('(prefers-color-scheme: light)').addEventListener('change', redraw);
  }
})();
