(() => {
  'use strict';

  const state = {
    user: null,
    route: 'browse',
    loading: false,
    error: '',
    notice: '',
    stats: null,
    health: null,
    browse: { records: [], limit: 50, loaded: false },
    recall: { topic: '', tags: '', k: 10, records: [], ran: false },
    query: { query: '', mode: 'hybrid', k: 10, topic: '', tags: '', result: null, ran: false },
    entities: { records: [], limit: 50, loaded: false },
    selected: null,
  };

  const appEl = () => document.getElementById('app');

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function fmtTime(ts) {
    if (!ts) return '—';
    try { return String(ts).replace('T', ' ').replace('Z', ' UTC'); } catch { return String(ts); }
  }

  function short(s, n = 180) {
    const t = String(s == null ? '' : s);
    if (t.length <= n) return t;
    return t.slice(0, n - 1) + '…';
  }

  function parseTags(raw) {
    return String(raw || '')
      .split(',')
      .map(x => x.trim())
      .filter(Boolean);
  }

  function arr(v) { return Array.isArray(v) ? v : []; }

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
      ...opts,
    });
    let body = null;
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
      try { body = await res.json(); } catch { body = null; }
    } else {
      try { body = await res.text(); } catch { body = null; }
    }
    if (res.status === 401) {
      const err = new Error('unauthorized');
      err.status = 401;
      err.body = body;
      throw err;
    }
    if (!res.ok) {
      const msg = body && body.error && body.error.message ? body.error.message : (typeof body === 'string' && body ? body : `HTTP ${res.status}`);
      const err = new Error(msg);
      err.status = res.status;
      err.body = body;
      throw err;
    }
    return body;
  }

  function setState(patch) {
    Object.assign(state, patch);
    render();
  }

  function mergeState(key, patch) {
    state[key] = { ...(state[key] || {}), ...(patch || {}) };
    render();
  }

  function healthyPill(health) {
    if (!health) return '<span class="pill">unknown</span>';
    if (health.healthy === true) return '<span class="pill good"><span class="dot"></span>healthy</span>';
    if (health.healthy === false) return '<span class="pill warn"><span class="dot"></span>needs attention</span>';
    return '<span class="pill">unknown</span>';
  }

  function renderLogin(errorMsg = '') {
    appEl().innerHTML = `
      <div class="login-wrap">
        <div class="login-card">
          <div class="brand">
            <div class="brand-mark">20</div>
            <div>
              <h1>mem20 memories</h1>
            </div>
          </div>
          <p class="subtle">Sign in to access your saved memories. Your account is scoped to your own memory store.</p>
          ${errorMsg ? `<div class="error">${esc(errorMsg)}</div>` : ''}
          <form id="login-form">
            <div class="field">
              <label for="username">Username</label>
              <input class="input" id="username" name="username" autocomplete="username" required />
            </div>
            <div class="field">
              <label for="password">Password</label>
              <input class="input" id="password" name="password" type="password" autocomplete="current-password" required />
            </div>
            <div class="row" style="margin-top:18px">
              <button class="btn primary" type="submit" id="login-btn">Sign in</button>
            </div>
          </form>
        </div>
      </div>`;
    const form = document.getElementById('login-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const btn = document.getElementById('login-btn');
      btn.disabled = true;
      btn.textContent = 'Signing in…';
      const username = document.getElementById('username').value.trim();
      const password = document.getElementById('password').value;
      try {
        const data = await api('/api/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) });
        state.user = data.user || { username };
        state.error = '';
        await loadInitial();
      } catch (err) {
        renderLogin(err.message || 'Sign in failed');
      }
    });
  }

  async function loadInitial() {
    try {
      const [statsRes, healthRes, browseRes] = await Promise.all([
        api('/api/memories/stats'),
        api('/api/memories/health'),
        api('/api/memories/browse?limit=50'),
      ]);
      state.stats = statsRes.stats || null;
      state.health = healthRes.health || (state.stats ? state.stats.health : null);
      state.browse = { records: arr(browseRes.records), limit: 50, loaded: true };
      state.route = 'browse';
      state.error = '';
      render();
    } catch (err) {
      if (err.status === 401) { state.user = null; renderLogin(); return; }
      state.error = err.message || 'Failed to load memories';
      render();
    }
  }

  function navBtn(id, label) {
    const active = state.route === id ? 'active' : '';
    return `<button class="${active}" data-route="${id}">${esc(label)}</button>`;
  }

  function recordRows(records) {
    if (!records.length) return `<tr><td colspan="5" class="muted">No memories found.</td></tr>`;
    return records.map((r, i) => {
      const tags = arr(r.tags).map(t => `<span class="tag">${esc(t)}</span>`).join('');
      const content = esc(short(r.content || r.text || '', 160));
      const topic = esc(r.topic || '—');
      const when = esc(fmtTime(r.ts || r.created_at || r.valid_from || ''));
      return `<tr data-idx="${i}">
        <td class="mono">${esc(short(r.id || '—', 18))}</td>
        <td>${topic}</td>
        <td class="muted">${when}</td>
        <td><div class="tags">${tags || '<span class="muted">—</span>'}</div></td>
        <td><div class="content-preview">${content || '<span class="muted">—</span>'}</div></td>
      </tr>`;
    }).join('');
  }

  function detailPanel(record) {
    if (!record) {
      return `<div class="card detail"><div class="card-h"><h3>Memory detail</h3></div><div class="card-b"><div class="empty">Select a memory to view its details.</div></div></div>`;
    }
    const tags = arr(record.tags).map(t => `<span class="tag">${esc(t)}</span>`).join('') || '<span class="muted">—</span>';
    const kv = (k, v) => `<div class="k">${esc(k)}</div><div class="v">${v}</div>`;
    return `<div class="card detail">
      <div class="card-h"><h3>Memory detail</h3><span class="spacer"></span><button class="btn sm ghost" id="close-detail">Close</button></div>
      <div class="card-b">
        <div class="kv" style="margin-bottom:12px">
          ${kv('ID', `<span class="mono">${esc(record.id || '—')}</span>`)}
          ${kv('Topic', esc(record.topic || '—'))}
          ${kv('Time', esc(fmtTime(record.ts || record.created_at || record.valid_from || '')))}
          ${kv('Priority', esc(record.priority || '—'))}
          ${kv('Action', esc(record.action || '—'))}
          ${kv('Status', esc(record.epistemic_status || '—'))}
          ${kv('Tags', `<div class="tags">${tags}</div>`)}
        </div>
        <div style="margin-bottom:8px;color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.05em">Content</div>
        <pre class="json" style="max-height:220px;margin-bottom:12px">${esc(record.content || record.text || '')}</pre>
        <div style="margin-bottom:8px;color:var(--dim);font-size:12px;text-transform:uppercase;letter-spacing:.05em">Record (JSON)</div>
        <pre class="json">${esc(JSON.stringify(record, null, 2))}</pre>
      </div>
    </div>`;
  }

  function statsCards() {
    const s = state.stats || {};
    const h = state.health || s.health || {};
    const grounded = s.grounded_facts != null ? s.grounded_facts : '—';
    const events = s.ledger_events != null ? s.ledger_events : '—';
    const topics = s.topics != null ? s.topics : '—';
    const vec = s.vector_available === true ? 'available' : (s.vector_available === false ? 'unavailable' : '—');
    const bm = s.bm25_available === true ? 'available' : (s.bm25_available === false ? 'unavailable' : '—');
    return `
      <div class="grid stats">
        <div class="card stat"><div class="k">Saved memories</div><div class="v">${esc(grounded)}</div><div class="s">grounded facts</div></div>
        <div class="card stat"><div class="k">Ledger events</div><div class="v">${esc(events)}</div><div class="s">total events</div></div>
        <div class="card stat"><div class="k">Topics</div><div class="v">${esc(topics)}</div><div class="s">distinct topics</div></div>
        <div class="card stat"><div class="k">Store health</div><div class="v" style="font-size:18px;margin-top:10px">${healthyPill(h)}</div><div class="s">vector: ${esc(vec)} · bm25: ${esc(bm)}</div></div>
      </div>`;
  }

  function renderBrowse() {
    const recs = state.browse.records || [];
    return `
      ${statsCards()}
      <div class="split">
        <div class="card">
          <div class="card-h"><h3>Recent memories</h3><span class="spacer"></span><span class="pill">${esc(recs.length)} shown</span>
            <button class="btn sm" id="refresh-browse">Refresh</button></div>
          <div class="card-b">
            <div class="toolbar">
              <div class="field"><label>Limit</label><input class="input" id="browse-limit" type="number" min="1" max="500" value="${esc(state.browse.limit || 50)}" /></div>
              <div class="field" style="align-self:flex-end"><button class="btn sm primary" id="load-browse">Load</button></div>
            </div>
            <div class="table-wrap"><table>
              <thead><tr><th>ID</th><th>Topic</th><th>Time</th><th>Tags</th><th>Content</th></tr></thead>
              <tbody id="browse-body">${recordRows(recs)}</tbody>
            </table></div>
          </div>
        </div>
        ${detailPanel(state.selected && state.selected.source === 'browse' ? state.selected.record : null)}
      </div>`;
  }

  function renderRecall() {
    const recs = state.recall.records || [];
    return `
      <div class="split">
        <div class="card">
          <div class="card-h"><h3>Recall memories</h3><span class="spacer"></span>${state.recall.ran ? `<span class="pill">${esc(recs.length)} results</span>` : ''}</div>
          <div class="card-b">
            <div class="toolbar">
              <div class="field grow"><label>Topic (optional)</label><input class="input" id="recall-topic" value="${esc(state.recall.topic)}" placeholder="e.g. deploys, preferences, project-x" /></div>
              <div class="field grow"><label>Tags (comma-separated, optional)</label><input class="input" id="recall-tags" value="${esc(state.recall.tags)}" placeholder="tag1, tag2" /></div>
              <div class="field"><label>Max results</label><input class="input" id="recall-k" type="number" min="1" max="100" value="${esc(state.recall.k)}" /></div>
              <div class="field" style="align-self:flex-end"><button class="btn primary" id="run-recall">Recall</button></div>
            </div>
            ${!state.recall.ran ? '<div class="notice">Search your saved memories by topic and/or tags. Leave both empty to retrieve recent memories.</div>' : ''}
            <div class="table-wrap"><table>
              <thead><tr><th>ID</th><th>Topic</th><th>Time</th><th>Tags</th><th>Content</th></tr></thead>
              <tbody id="recall-body">${recordRows(recs)}</tbody>
            </table></div>
          </div>
        </div>
        ${detailPanel(state.selected && state.selected.source === 'recall' ? state.selected.record : null)}
      </div>`;
  }

  function renderQueryResult(res) {
    if (!res) return '';
    const mode = res.mode || 'query';
    const hits = arr(res.hits || res.records || res.facts || res.entities || []);
    let meta = [];
    if (res.healthy === true) meta.push('<span class="pill good"><span class="dot"></span>index healthy</span>');
    if (res.healthy === false) meta.push('<span class="pill warn"><span class="dot"></span>index drift reported</span>');
    if (res.degraded_to) meta.push(`<span class="pill warn">degraded to: ${esc(res.degraded_to)}</span>`);
    if (res.count != null) meta.push(`<span class="pill">${esc(res.count)} results</span>`);
    if (mode === 'graph') {
      const entities = arr(res.entities);
      const facts = arr(res.facts);
      meta.push(`<span class="pill">${esc(entities.length)} entities</span>`);
      meta.push(`<span class="pill">${esc(facts.length)} facts</span>`);
    }
    const diag = res.diagnostic || res._retrieval || null;
    const diagHtml = diag ? `<details style="margin-top:10px"><summary class="muted" style="cursor:pointer">Diagnostics</summary><pre class="json" style="margin-top:8px;max-height:220px">${esc(JSON.stringify(diag, null, 2))}</pre></details>` : '';

    let body = '';
    if (mode === 'graph') {
      const ents = arr(res.entities);
      const facts = arr(res.facts);
      body = `
        ${ents.length ? `<div style="margin-bottom:10px"><div class="muted" style="margin-bottom:6px">Entities</div><div class="tags">${ents.slice(0,40).map(e => `<span class="tag">${esc(typeof e === 'string' ? e : (e.entity || e.name || JSON.stringify(e)))}</span>`).join('')}</div></div>` : ''}
        <div class="table-wrap"><table>
          <thead><tr><th>Type</th><th>Topic / Entity</th><th>Info</th><th>Content</th></tr></thead>
          <tbody id="query-body">${(facts.length ? facts : hits).map((h, i) => {
            const isObj = h && typeof h === 'object';
            const content = esc(short(isObj ? (h.content || h.text || JSON.stringify(h)) : String(h), 180));
            const topic = esc(isObj ? (h.topic || h.entity || h.name || '—') : '—');
            const info = esc(isObj ? (h.relation || h.hop != null ? `hop ${h.hop}` : (h.ts || '')) : '');
            return `<tr data-idx="${i}"><td class="muted">fact</td><td>${topic}</td><td class="muted">${info || '—'}</td><td><div class="content-preview">${content}</div></td></tr>`;
          }).join('') || '<tr><td colspan="4" class="muted">No graph results.</td></tr>'}</tbody>
        </table></div>`;
    } else {
      body = `
        <div class="table-wrap"><table>
          <thead><tr><th>ID</th><th>Topic</th><th>Score</th><th>Tags</th><th>Content</th></tr></thead>
          <tbody id="query-body">${hits.map((h, i) => {
            const tags = arr(h && h.tags).map(t => `<span class="tag">${esc(t)}</span>`).join('');
            const score = (h && (h.score != null || h._score != null)) ? Number(h.score != null ? h.score : h._score).toFixed(4) : '—';
            const content = esc(short(h && (h.content || h.text || ''), 180));
            return `<tr data-idx="${i}">
              <td class="mono">${esc(short(h && h.id || '—', 18))}</td>
              <td>${esc(h && h.topic || '—')}</td>
              <td class="mono muted">${esc(score)}</td>
              <td><div class="tags">${tags || '<span class="muted">—</span>'}</div></td>
              <td><div class="content-preview">${content || '<span class="muted">—</span>'}</div></td>
            </tr>`;
          }).join('') || '<tr><td colspan="5" class="muted">No results.</td></tr>'}</tbody>
        </table></div>`;
    }
    return `<div style="margin-top:14px"><div class="row wrap" style="margin-bottom:10px;gap:8px">${meta.join('') || ''}</div>${body}${diagHtml}</div>`;
  }

  function renderQuery() {
    const q = state.query;
    return `
      <div class="split">
        <div class="card">
          <div class="card-h"><h3>Search & query</h3><span class="spacer"></span>${q.ran && q.result ? `<span class="pill">${esc(q.result.mode || q.mode)}</span>` : ''}</div>
          <div class="card-b">
            <div class="toolbar">
              <div class="field grow"><label>Query</label><input class="input" id="query-text" value="${esc(q.query)}" placeholder="Ask in natural language or enter an entity/topic…" /></div>
              <div class="field"><label>Mode</label>
                <select class="select" id="query-mode">
                  <option value="hybrid" ${q.mode==='hybrid'?'selected':''}>Hybrid (semantic + keyword)</option>
                  <option value="semantic" ${q.mode==='semantic'?'selected':''}>Semantic</option>
                  <option value="graph" ${q.mode==='graph'?'selected':''}>Graph (entity hops)</option>
                </select>
              </div>
              <div class="field"><label>Results / hops</label><input class="input" id="query-k" type="number" min="1" max="50" value="${esc(q.k)}" /></div>
            </div>
            <div class="toolbar">
              <div class="field grow"><label>Topic filter (optional, semantic/hybrid)</label><input class="input" id="query-topic" value="${esc(q.topic)}" placeholder="topic" /></div>
              <div class="field grow"><label>Tags filter (optional, semantic/hybrid)</label><input class="input" id="query-tags" value="${esc(q.tags)}" placeholder="tag1, tag2" /></div>
              <div class="field" style="align-self:flex-end"><button class="btn primary" id="run-query">Run query</button></div>
            </div>
            ${!q.ran ? '<div class="notice">Use <strong>hybrid</strong> or <strong>semantic</strong> to search by meaning, or <strong>graph</strong> to explore related entities/facts from a starting entity.</div>' : ''}
            ${q.ran ? renderQueryResult(q.result) : ''}
          </div>
        </div>
        ${detailPanel(state.selected && state.selected.source === 'query' ? state.selected.record : null)}
      </div>`;
  }

  function renderEntities() {
    const ents = state.entities.records || [];
    return `
      <div class="card">
        <div class="card-h"><h3>Entities</h3><span class="spacer"></span><span class="pill">${esc(ents.length)} shown</span><button class="btn sm" id="refresh-entities">Refresh</button></div>
        <div class="card-b">
          <div class="toolbar">
            <div class="field"><label>Limit</label><input class="input" id="entities-limit" type="number" min="1" max="500" value="${esc(state.entities.limit || 50)}" /></div>
            <div class="field" style="align-self:flex-end"><button class="btn sm primary" id="load-entities">Load</button></div>
          </div>
          <div class="table-wrap"><table>
            <thead><tr><th>Entity</th><th>Degree</th><th>Facts</th><th>Topics</th></tr></thead>
            <tbody>${ents.length ? ents.map(e => `<tr><td><strong>${esc(e.entity || e.name || '—')}</strong></td><td class="mono">${esc(e.degree != null ? e.degree : '—')}</td><td class="mono">${esc(e.facts != null ? e.facts : '—')}</td><td><div class="tags">${arr(e.topics).map(t => `<span class="tag">${esc(t)}</span>`).join('') || '<span class="muted">—</span>'}</div></td></tr>`).join('') : '<tr><td colspan="4" class="muted">No entities found.</td></tr>'}</tbody>
          </table></div>
        </div>
      </div>`;
  }

  function renderHealth() {
    const h = state.health || {};
    const s = state.stats || {};
    const idx = h.indexes || {};
    const idxRows = Object.keys(idx).map(name => {
      const v = idx[name] || {};
      const status = v.healthy === true ? '<span class="pill good">healthy</span>' : (v.present === false ? '<span class="pill warn">not present</span>' : '<span class="pill warn">attention</span>');
      const detail = esc(JSON.stringify(v, null, 2));
      return `<tr><td><strong>${esc(name)}</strong></td><td>${status}</td><td><pre class="json" style="max-height:160px">${detail}</pre></td></tr>`;
    }).join('');
    return `
      ${statsCards()}
      <div class="grid two">
        <div class="card">
          <div class="card-h"><h3>Store & index health</h3><span class="spacer"></span><button class="btn sm" id="refresh-health">Refresh</button></div>
          <div class="card-b">
            <div style="margin-bottom:12px">${healthyPill(h)} ${h.ledger_records != null ? `<span class="pill" style="margin-left:6px">${esc(h.ledger_records)} ledger records</span>` : ''}</div>
            <div class="table-wrap"><table>
              <thead><tr><th>Index</th><th>Status</th><th>Details</th></tr></thead>
              <tbody>${idxRows || '<tr><td colspan="3" class="muted">No index details available.</td></tr>'}</tbody>
            </table></div>
          </div>
        </div>
        <div class="card">
          <div class="card-h"><h3>Stats (sanitized)</h3></div>
          <div class="card-b">
            <pre class="json">${esc(JSON.stringify(s, null, 2))}</pre>
          </div>
        </div>
      </div>`;
  }

  function renderMain() {
    const route = state.route;
    const titles = {
      browse: ['Your memories', 'Browse and review your saved memories.'],
      recall: ['Recall', 'Find memories by topic and tags.'],
      query: ['Search & query', 'Search by meaning or explore the memory graph.'],
      entities: ['Entities', 'Entities known in your memory graph.'],
      health: ['Health & stats', 'Store status and diagnostics for your memories.'],
    };
    const [title, sub] = titles[route] || ['Memories', ''];
    let body = '';
    if (route === 'browse') body = renderBrowse();
    else if (route === 'recall') body = renderRecall();
    else if (route === 'query') body = renderQuery();
    else if (route === 'entities') body = renderEntities();
    else if (route === 'health') body = renderHealth();

    return `
      <div class="shell">
        <aside class="sidebar">
          <div class="side-brand">
            <div class="brand-mark" style="width:30px;height:30px;border-radius:8px;font-size:13px">20</div>
            <div><div class="t">mem20 memories</div><div class="s">Your saved memories</div></div>
          </div>
          <nav class="nav">
            ${navBtn('browse', 'Browse memories')}
            ${navBtn('recall', 'Recall')}
            ${navBtn('query', 'Search & query')}
            ${navBtn('entities', 'Entities')}
            ${navBtn('health', 'Health & stats')}
          </nav>
          <div class="side-foot">
            <div class="userbox">
              <div class="name">${esc(state.user && (state.user.display_name || state.user.username) || 'Signed in')}</div>
              <div class="meta">@${esc(state.user && state.user.username || '')}</div>
            </div>
            <div class="row" style="padding:0 8px 8px">
              <button class="btn sm ghost" id="logout-btn">Sign out</button>
            </div>
            <div style="padding:0 8px;font-size:12px">Authenticated access to your own memory store.</div>
          </div>
        </aside>
        <main class="main">
          <div class="topbar">
            <div>
              <h2>${esc(title)}</h2>
              <p>${esc(sub)}</p>
            </div>
            <span class="spacer"></span>
            ${state.loading ? '<span class="pill">Loading…</span>' : ''}
          </div>
          ${state.error ? `<div class="error">${esc(state.error)}</div>` : ''}
          ${body}
        </main>
      </div>`;
  }

  function bindCommon() {
    document.querySelectorAll('[data-route]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const route = btn.getAttribute('data-route');
        state.route = route;
        state.error = '';
        state.selected = null;
        render();
        if (route === 'browse' && !state.browse.loaded) await refreshBrowse();
        if (route === 'entities' && !state.entities.loaded) await refreshEntities();
        if (route === 'health') await refreshHealth();
      });
    });
    const logout = document.getElementById('logout-btn');
    if (logout) logout.addEventListener('click', async () => {
      try { await api('/api/auth/logout', { method: 'POST', body: '{}' }); } catch {}
      state.user = null; state.selected = null; renderLogin();
    });
    const closeDetail = document.getElementById('close-detail');
    if (closeDetail) closeDetail.addEventListener('click', () => { state.selected = null; render(); });
  }

  async function refreshBrowse() {
    const limitEl = document.getElementById('browse-limit');
    const limit = limitEl ? parseInt(limitEl.value, 10) || 50 : (state.browse.limit || 50);
    try {
      state.loading = true; render();
      const res = await api(`/api/memories/browse?limit=${encodeURIComponent(limit)}`);
      state.browse = { records: arr(res.records), limit, loaded: true };
      state.error = '';
    } catch (err) {
      if (err.status === 401) return handle401();
      state.error = err.message || 'Failed to load memories';
    } finally { state.loading = false; render(); }
  }

  async function refreshEntities() {
    const limitEl = document.getElementById('entities-limit');
    const limit = limitEl ? parseInt(limitEl.value, 10) || 50 : (state.entities.limit || 50);
    try {
      state.loading = true; render();
      const res = await api(`/api/memories/entities?limit=${encodeURIComponent(limit)}`);
      state.entities = { records: arr(res.entities), limit, loaded: true };
      state.error = '';
    } catch (err) {
      if (err.status === 401) return handle401();
      state.error = err.message || 'Failed to load entities';
    } finally { state.loading = false; render(); }
  }

  async function refreshHealth() {
    try {
      state.loading = true; render();
      const [statsRes, healthRes] = await Promise.all([api('/api/memories/stats'), api('/api/memories/health')]);
      state.stats = statsRes.stats || null;
      state.health = healthRes.health || (state.stats ? state.stats.health : null);
      state.error = '';
    } catch (err) {
      if (err.status === 401) return handle401();
      state.error = err.message || 'Failed to load health';
    } finally { state.loading = false; render(); }
  }

  function handle401() { state.user = null; state.selected = null; renderLogin('Your session expired. Please sign in again.'); }

  function bindRoute() {
    const r = state.route;
    if (r === 'browse') {
      const b = document.getElementById('load-browse');
      if (b) b.addEventListener('click', refreshBrowse);
      const rb = document.getElementById('refresh-browse');
      if (rb) rb.addEventListener('click', refreshBrowse);
      document.querySelectorAll('#browse-body tr[data-idx]').forEach(tr => tr.addEventListener('click', () => {
        const idx = parseInt(tr.getAttribute('data-idx'), 10);
        state.selected = { source: 'browse', record: state.browse.records[idx] };
        render();
      }));
    }
    if (r === 'recall') {
      const run = document.getElementById('run-recall');
      if (run) run.addEventListener('click', async () => {
        const topic = document.getElementById('recall-topic').value;
        const tagsRaw = document.getElementById('recall-tags').value;
        const k = parseInt(document.getElementById('recall-k').value, 10) || 10;
        state.recall.topic = topic; state.recall.tags = tagsRaw; state.recall.k = k;
        try {
          state.loading = true; state.error = ''; render();
          const res = await api('/api/memories/recall', { method: 'POST', body: JSON.stringify({ topic: topic.trim() || null, tags: parseTags(tagsRaw), k }) });
          state.recall.records = arr(res.records); state.recall.ran = true; state.selected = null;
        } catch (err) {
          if (err.status === 401) return handle401();
          state.error = err.message || 'Recall failed';
        } finally { state.loading = false; render(); }
      });
      document.querySelectorAll('#recall-body tr[data-idx]').forEach(tr => tr.addEventListener('click', () => {
        const idx = parseInt(tr.getAttribute('data-idx'), 10);
        state.selected = { source: 'recall', record: state.recall.records[idx] };
        render();
      }));
    }
    if (r === 'query') {
      const run = document.getElementById('run-query');
      if (run) run.addEventListener('click', async () => {
        const query = document.getElementById('query-text').value;
        const mode = document.getElementById('query-mode').value;
        const k = parseInt(document.getElementById('query-k').value, 10) || 10;
        const topic = document.getElementById('query-topic').value;
        const tagsRaw = document.getElementById('query-tags').value;
        state.query = { ...state.query, query, mode, k, topic, tags: tagsRaw };
        if (!query.trim()) { state.error = 'Enter a query.'; render(); return; }
        try {
          state.loading = true; state.error = ''; render();
          const res = await api('/api/memories/query', { method: 'POST', body: JSON.stringify({ query: query.trim(), mode, k, topic: topic.trim() || null, tags: parseTags(tagsRaw) }) });
          state.query.result = res; state.query.ran = true; state.selected = null;
        } catch (err) {
          if (err.status === 401) return handle401();
          state.error = err.message || 'Query failed';
        } finally { state.loading = false; render(); }
      });
      document.querySelectorAll('#query-body tr[data-idx]').forEach(tr => tr.addEventListener('click', () => {
        const idx = parseInt(tr.getAttribute('data-idx'), 10);
        const res = state.query.result || {};
        const items = arr(res.hits && res.hits.length ? res.hits : (res.facts || []));
        state.selected = { source: 'query', record: items[idx] };
        render();
      }));
    }
    if (r === 'entities') {
      const b = document.getElementById('load-entities');
      if (b) b.addEventListener('click', refreshEntities);
      const rb = document.getElementById('refresh-entities');
      if (rb) rb.addEventListener('click', refreshEntities);
    }
    if (r === 'health') {
      const rb = document.getElementById('refresh-health');
      if (rb) rb.addEventListener('click', refreshHealth);
    }
  }

  function render() {
    if (!state.user) { /* login rendered separately */ bindCommon(); return; }
    appEl().innerHTML = renderMain();
    bindCommon();
    bindRoute();
  }

  async function boot() {
    try {
      const me = await api('/api/auth/me');
      state.user = me.user || null;
      if (state.user) await loadInitial();
      else renderLogin();
    } catch (err) {
      if (err.status === 401) renderLogin();
      else renderLogin(err.message || 'Unable to connect to the portal.');
    }
  }

  boot();
})();
