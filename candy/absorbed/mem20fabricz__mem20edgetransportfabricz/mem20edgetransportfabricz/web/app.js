async function api(path, opts) {
  const r = await fetch(path, Object.assign({headers: {'Content-Type': 'application/json'}}, opts || {}));
  const t = await r.text();
  let j; try { j = JSON.parse(t); } catch { j = {raw: t}; }
  return j;
}
function val(id) { return document.getElementById(id).value; }
function show(id, obj) { document.getElementById(id).textContent = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2); }
async function refresh() {
  const [status, nodes, links, flows, events] = await Promise.all([
    api('/api/status'), api('/api/nodes'), api('/api/links'), api('/api/flows'), api('/api/events?limit=30')
  ]);
  show('health', status.health || status);
  show('nodes', nodes.nodes || nodes);
  show('links', links.links || links);
  show('flows', flows.flows || flows);
  show('events', events.events || events);
}
document.getElementById('refresh').onclick = refresh;
document.getElementById('doctor').onclick = async () => show('out', await api('/api/doctor'));
document.getElementById('simulate').onclick = async () => show('out', await api('/api/simulate', {method:'POST', body:'{}'}));
document.getElementById('addNode').onclick = async () => { show('out', await api('/api/nodes', {method:'POST', body: JSON.stringify({node_id: val('nodeId'), kind: val('nodeKind'), capacity_mbps: Number(val('nodeCap'))})})); refresh(); };
document.getElementById('addLink').onclick = async () => { show('out', await api('/api/links', {method:'POST', body: JSON.stringify({src: val('linkSrc'), dst: val('linkDst'), bandwidth_mbps: Number(val('linkBw')), latency_ms: Number(val('linkLat')), status: val('linkStatus')})})); refresh(); };
document.getElementById('admitFlow').onclick = async () => { show('out', await api('/api/flows/admit', {method:'POST', body: JSON.stringify({flow_id: val('flowId'), src: val('flowSrc'), dst: val('flowDst'), demand_mbps: Number(val('flowDemand')), priority: Number(val('flowPri')), max_latency_ms: Number(val('flowLat')), intermittent_ok: true})})); refresh(); };
document.getElementById('routeFlow').onclick = async () => { show('out', await api('/api/route', {method:'POST', body: JSON.stringify({src: val('flowSrc'), dst: val('flowDst'), demand_mbps: Number(val('flowDemand')), priority: Number(val('flowPri'))})})); };
refresh().catch(e => show('health', String(e)));
