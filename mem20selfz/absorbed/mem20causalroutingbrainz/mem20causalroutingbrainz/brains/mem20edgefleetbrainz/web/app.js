// Edge Fleet Brain cockpit. No framework: the whole surface is fetch + DOM.
// The page is served by the subsystem itself at GET / and can also be opened
// from docs/app/fleet/ with ?api=http://127.0.0.1:8771.

const state = {
  api: new URLSearchParams(location.search).get('api')
    || localStorage.getItem('fleet.api')
    || (location.protocol.startsWith('http') && location.port === '8771'
      ? location.origin
      : 'http://127.0.0.1:8771'),
  eventsSince: 0,
  poll: null,
};

const $ = (selector) => document.querySelector(selector);
const el = (tag, cls, text) => {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined) node.textContent = text;
  return node;
};

function toast(message, bad = false) {
  const box = $('#toast');
  box.textContent = message;
  box.classList.toggle('bad', bad);
  box.hidden = false;
  clearTimeout(box._timer);
  box._timer = setTimeout(() => { box.hidden = true; }, bad ? 9000 : 4500);
}

async function api(path, options = {}) {
  const base = state.api.replace(/\/$/, '');
  const response = await fetch(base + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  let payload = {};
  try { payload = await response.json(); } catch { /* non-JSON body */ }
  if (!response.ok) {
    throw new Error(payload.error || `${response.status} ${response.statusText}`);
  }
  return payload;
}

function pct(value) {
  return `${Math.round(Number(value || 0) * 100)}%`;
}

function number(value, digits = 2) {
  return Number(value || 0).toFixed(digits);
}

// --------------------------------------------------------------------------
// render
// --------------------------------------------------------------------------
function renderStats(status) {
  const health = status.health || {};
  const metrics = status.metrics || {};
  const stats = [
    ['Health', pct(health.health), `${health.usable || 0}/${health.nodes || 0} usable`],
    ['CPU', pct(health.cpu_utilisation), `${number(health.cpu_used, 1)}/${health.cpu_capacity || 0} cores`],
    ['Memory', pct(health.memory_utilisation), `${number(health.memory_used_gb, 1)}/${number(health.memory_capacity_gb, 1)} GB`],
    ['Workloads', `${health.running || 0}`, `${health.queued || 0} queued · ${health.failed || 0} failed`],
    ['Energy', `${number(status.energy?.total_kwh, 3)}`, 'kWh / 24 h'],
    ['Events', `${metrics.events || 0}`, `seq ${metrics.latest_event_seq || 0}`],
  ];
  const root = $('#stats');
  root.replaceChildren();
  for (const [label, value, detail] of stats) {
    const card = el('div', 'stat');
    card.append(el('div', 'label', label));
    const v = el('div', 'value', value);
    if (detail) {
      v.append(document.createTextNode(' '));
      const small = el('small', '', detail);
      v.append(small);
    }
    card.append(v);
    root.append(card);
  }
}

function badge(status) {
  return el('span', `badge ${status || ''}`, status || 'unknown');
}

function nodeCard(node, forecast) {
  const card = el('div', 'card');
  const top = el('div', 'card-top');
  const title = el('div', 'card-title', node.node_id);
  top.append(title, badge(node.status));
  card.append(top);

  const load = Math.max(
    (node.current_cpu || 0) / Math.max(1, node.cpu_cores || 1),
    (node.current_memory_gb || 0) / Math.max(0.1, node.memory_gb || 1),
  );
  const meta = el('div', 'meta');
  meta.textContent = [
    node.kind,
    node.region,
    `${node.cpu_cores}c / ${node.memory_gb}GB`,
    node.gpu_count ? `${node.gpu_count} GPU` : null,
    `$${number(node.price_per_hour, 3)}/h`,
    `rel ${number(node.reliability, 2)}`,
  ].filter(Boolean).join(' · ');
  if (node.capabilities?.length) {
    meta.textContent += ` · ${node.capabilities.join(', ')}`;
  }
  if (forecast) {
    meta.textContent += ` · fault ${pct(forecast.risk)} (${forecast.recommendation})`;
  }
  card.append(meta);

  const bar = el('div', `bar${load > 0.8 ? ' hot' : ''}`);
  const fill = el('span');
  fill.style.width = `${Math.min(100, load * 100)}%`;
  bar.append(fill);
  card.append(bar);

  const actions = el('div', 'actions');
  const drain = el('button', 'ghost small', 'Drain');
  drain.onclick = () => act(() => api(`/api/nodes/${node.node_id}/drain`, { method: 'POST' }), `drained ${node.node_id}`);
  const evacuate = el('button', 'ghost small', 'Evacuate');
  evacuate.onclick = () => act(() => api(`/api/nodes/${node.node_id}/evacuate`, { method: 'POST' }), `evacuated ${node.node_id}`);
  const next = node.status === 'offline' || node.status === 'sleeping' ? 'online' : 'offline';
  const toggle = el('button', 'ghost small', next === 'online' ? 'Wake' : 'Offline');
  toggle.onclick = () => act(() => api(`/api/nodes/${node.node_id}/status`, {
    method: 'POST', body: JSON.stringify({ status: next }),
  }), `${node.node_id} -> ${next}`);
  const remove = el('button', 'danger small', 'Delete');
  remove.onclick = () => act(() => api(`/api/nodes/${node.node_id}`, { method: 'DELETE' }), `deleted ${node.node_id}`);
  actions.append(drain, evacuate, toggle, remove);
  card.append(actions);
  return card;
}

function workloadCard(workload) {
  const card = el('div', 'card');
  const top = el('div', 'card-top');
  top.append(el('div', 'card-title', workload.workload_id), badge(workload.state));
  card.append(top);

  const meta = el('div', 'meta');
  meta.textContent = [
    workload.name || null,
    `${workload.cpu}c / ${workload.memory_gb}GB`,
    `priority ${workload.priority}`,
    workload.required_capabilities?.length ? `needs ${workload.required_capabilities.join(', ')}` : null,
    workload.assigned_node ? `on ${workload.assigned_node}` : null,
    workload.deadline_s ? `${workload.deadline_s}s deadline` : null,
    workload.max_price_per_hour != null ? `max $${workload.max_price_per_hour}/h` : null,
  ].filter(Boolean).join(' · ');
  card.append(meta);

  const actions = el('div', 'actions');
  if (workload.state === 'queued') {
    const dispatch = el('button', 'primary small', 'Dispatch');
    dispatch.onclick = () => act(async () => {
      const result = await api('/api/dispatch', {
        method: 'POST', body: JSON.stringify({ workload_id: workload.workload_id }),
      });
      const decision = result.decisions?.[0]?.decision;
      if (decision?.placed) {
        toast(`${workload.workload_id} -> ${decision.chosen} (score ${number(decision.score, 3)}, confidence ${number(decision.confidence, 2)})`);
      } else {
        toast(`${workload.workload_id} could not be placed:\n${(decision?.bottlenecks || []).join('\n') || 'no nodes'}`, true);
      }
    }, '', false);
    actions.append(dispatch);
  }
  if (workload.state === 'running') {
    const done = el('button', 'ghost small', 'Complete');
    done.onclick = () => act(() => api(`/api/workloads/${workload.workload_id}/complete`, {
      method: 'POST', body: JSON.stringify({ success: true }),
    }), `completed ${workload.workload_id}`);
    const fail = el('button', 'danger small', 'Fail');
    fail.onclick = () => act(() => api(`/api/workloads/${workload.workload_id}/complete`, {
      method: 'POST', body: JSON.stringify({ success: false, reason: 'operator marked failed' }),
    }), `failed ${workload.workload_id}`);
    actions.append(done, fail);
  }
  card.append(actions);
  return card;
}

function renderNodes(nodes, forecasts) {
  const root = $('#nodes');
  root.replaceChildren();
  if (!nodes.length) {
    root.append(el('div', 'empty', 'No nodes registered yet.'));
    return;
  }
  const risk = Object.fromEntries((forecasts || []).map((item) => [item.node_id, item]));
  for (const node of nodes) root.append(nodeCard(node, risk[node.node_id]));
}

function renderWorkloads(workloads) {
  const root = $('#workloads');
  root.replaceChildren();
  if (!workloads.length) {
    root.append(el('div', 'empty', 'Queue is empty.'));
    return;
  }
  const order = { running: 0, queued: 1, failed: 2, completed: 3, evicted: 4 };
  const sorted = [...workloads].sort((a, b) =>
    (order[a.state] ?? 9) - (order[b.state] ?? 9) || b.priority - a.priority);
  for (const workload of sorted) root.append(workloadCard(workload));
}

function renderEnergy(energy) {
  const root = $('#energy');
  root.replaceChildren();
  if (!energy?.nodes?.length) {
    root.append(el('div', 'empty', 'No active nodes.'));
    return;
  }
  for (const row of energy.nodes.slice(0, 8)) {
    const card = el('div', 'card');
    const top = el('div', 'card-top');
    top.append(el('div', 'card-title', row.node_id), el('span', 'badge', `${number(row.wh, 1)} Wh`));
    card.append(top);
    card.append(el('div', 'meta', `${number(row.watts, 1)} W · load ${pct(row.load)} · $${number(row.cost, 4)}`));
    root.append(card);
  }
}

function renderFaults(forecasts) {
  const root = $('#faults');
  root.replaceChildren();
  if (!forecasts?.length) {
    root.append(el('div', 'empty', 'No schedulable nodes.'));
    return;
  }
  for (const item of forecasts.slice(0, 8)) {
    const card = el('div', 'card');
    const top = el('div', 'card-top');
    top.append(el('div', 'card-title', item.node_id),
      el('span', `badge ${item.risk >= 0.6 ? 'failed' : item.risk >= 0.3 ? 'draining' : 'online'}`,
        `${pct(item.risk)} · ${item.recommendation}`));
    card.append(top);
    if (item.drivers?.length) card.append(el('div', 'meta', item.drivers.join(' · ')));
    root.append(card);
  }
}

function renderEvents(events) {
  const root = $('#events');
  for (const event of events) {
    const item = el('li');
    item.append(el('time', '', new Date(event.ts * 1000).toLocaleTimeString()));
    item.append(el('span', 'kind', event.kind));
    item.append(el('span', 'payload', JSON.stringify(event.payload)));
    root.prepend(item);
    state.eventsSince = Math.max(state.eventsSince, event.seq);
  }
  while (root.children.length > 120) root.lastChild.remove();
}

async function refresh() {
  try {
    const [status, nodes, workloads, energy, faults] = await Promise.all([
      api('/api/status'),
      api('/api/nodes'),
      api('/api/workloads'),
      api('/api/energy'),
      api('/api/predict'),
    ]);
    renderStats(status);
    renderNodes(nodes.nodes || [], faults.forecasts || []);
    renderWorkloads(workloads.workloads || []);
    renderEnergy(energy.energy);
    renderFaults(faults.forecasts || []);
  } catch (error) {
    toast(`Cannot reach fleet API at ${state.api}: ${error.message}`, true);
  }
}

async function pollEvents() {
  try {
    const result = await api(`/api/events?since=${state.eventsSince}&limit=100`);
    if (result.events?.length) renderEvents(result.events);
  } catch { /* the refresh loop already reports connectivity */ }
}

async function act(fn, message, refreshAfter = true) {
  try {
    const result = await fn();
    if (message) toast(message);
    if (refreshAfter) await refresh();
    return result;
  } catch (error) {
    toast(error.message, true);
    return null;
  }
}

// --------------------------------------------------------------------------
// wiring
// --------------------------------------------------------------------------
function fields(form) {
  const data = {};
  for (const [key, value] of new FormData(form).entries()) {
    if (value === '') continue;
    data[key] = value;
  }
  return data;
}

function coerceNode(data) {
  const out = { ...data };
  for (const key of ['cpu_cores', 'gpu_count']) if (key in out) out[key] = parseInt(out[key], 10);
  for (const key of ['memory_gb', 'price_per_hour', 'reliability']) if (key in out) out[key] = parseFloat(out[key]);
  if (out.capabilities) out.capabilities = out.capabilities.split(',').map((s) => s.trim()).filter(Boolean);
  out.auto_capabilities = Boolean(out.auto_capabilities);
  return out;
}

function coerceWorkload(data) {
  const out = { ...data };
  for (const key of ['cpu', 'memory_gb', 'duration_s', 'max_price_per_hour', 'energy_budget_wh', 'deadline_s']) {
    if (key in out) out[key] = parseFloat(out[key]);
  }
  if ('priority' in out) out.priority = parseInt(out.priority, 10);
  if (out.required_capabilities) {
    out.required_capabilities = out.required_capabilities.split(',').map((s) => s.trim()).filter(Boolean);
  }
  return out;
}

$('#api-base').value = state.api;
$('#api-save').onclick = () => {
  state.api = $('#api-base').value.trim().replace(/\/$/, '') || state.api;
  localStorage.setItem('fleet.api', state.api);
  state.eventsSince = 0;
  $('#events').replaceChildren();
  refresh();
};

$('#node-form').onsubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = coerceNode(fields(form));
  const result = await act(() => api('/api/nodes', {
    method: 'POST', body: JSON.stringify(payload),
  }), `registered ${payload.node_id}`);
  if (result) form.reset();
};

$('#workload-form').onsubmit = async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = coerceWorkload(fields(form));
  const result = await act(() => api('/api/workloads', {
    method: 'POST', body: JSON.stringify(payload),
  }), `submitted ${result?.workload?.workload_id || payload.workload_id || 'workload'}`);
  if (result) form.reset();
};

$('#dispatch-all').onclick = () => act(async () => {
  const result = await api('/api/dispatch', { method: 'POST', body: JSON.stringify({}) });
  toast(`dispatched ${result.dispatched} of ${result.decisions.length}`);
  return result;
}, '');

$('#rebalance').onclick = () => act(async () => {
  const result = await api('/api/rebalance', { method: 'POST', body: JSON.stringify({ apply: true }) });
  toast(`rebalance applied ${result.applied} move(s)`);
  return result;
}, '');

$('#run-simulate').onclick = () => act(async () => {
  const result = await api('/api/simulate', { method: 'POST', body: JSON.stringify({}) });
  const output = $('#doctor');
  output.hidden = false;
  output.textContent = JSON.stringify(result, null, 2);
  toast(`simulator ${result.passed}/${result.total} scenarios`);
  return result;
}, '', false);

$('#run-doctor').onclick = () => act(async () => {
  const result = await api('/api/doctor');
  const output = $('#doctor');
  output.hidden = false;
  output.textContent = JSON.stringify(result, null, 2);
  toast(result.ok ? 'all six peers reachable' : 'some peers unreachable', !result.ok);
  return result;
}, '', false);

$('#refresh-nodes').onclick = refresh;

refresh();
pollEvents();
state.poll = setInterval(pollEvents, 3000);
setInterval(refresh, 12000);
