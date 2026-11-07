"""Edge transport fabric (RM-077): routing, QoS, bandwidth, link/flow health.

This module keeps the legacy-compatible surface used by other subsystems
(`route_path`, `qos_class`, `allocate_bandwidth`, `transport_health`) and adds
a real fabric domain model for intermittently connected edge transport:
topology/link state, path scoring, QoS/SLA classification, bounded bandwidth
reservation, congestion/health, and reroute planning.

Compatibility notes
-------------------
- ``route_path(src, dst, nodes)`` accepts the historical neighbor map
  ``{node_id: [neighbor_ids...]}`` and preserves its return shape/semantics.
- ``qos_class(latency_ms, priority)`` preserves historical tier thresholds.
- ``allocate_bandwidth(total, demands)`` preserves proportional allocation with
  ``allocated`` rounded to 2 decimals.
- ``transport_health(links)`` preserves ``{total, up, health}`` over
  ``status == "up"``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import heapq
import math
import time
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class LinkStatus(str, Enum):
    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    INTERMITTENT = "intermittent"


class QosTier(str, Enum):
    PREMIUM = "premium"
    STANDARD = "standard"
    BEST_EFFORT = "best_effort"
    CONTROL = "control"


class FlowState(str, Enum):
    PENDING = "pending"
    ADMITTED = "admitted"
    ACTIVE = "active"
    REROUTED = "rerouted"
    DROPPED = "dropped"
    COMPLETED = "completed"


def _now() -> float:
    return time.time()


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


@dataclass
class FabricNode:
    node_id: str
    kind: str = "edge"  # edge/device/site/cloud/gateway
    region: str = ""
    status: str = "online"
    capacity_mbps: float = 1000.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.node_id or not str(self.node_id).strip():
            raise ValueError("node_id is required")
        if self.capacity_mbps < 0:
            raise ValueError("capacity_mbps must be >= 0")


@dataclass
class FabricLink:
    link_id: str
    src: str
    dst: str
    bandwidth_mbps: float = 100.0
    latency_ms: float = 10.0
    loss_rate: float = 0.0
    jitter_ms: float = 0.0
    status: str = "up"
    cost: float = 1.0
    reserved_mbps: float = 0.0
    tags: List[str] = field(default_factory=list)
    last_seen: float = field(default_factory=_now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in ("link_id", "src", "dst"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        if self.bandwidth_mbps < 0 or self.reserved_mbps < 0:
            raise ValueError("bandwidth/reserved_mbps must be >= 0")
        if self.latency_ms < 0 or self.jitter_ms < 0:
            raise ValueError("latency/jitter must be >= 0")
        if not (0.0 <= self.loss_rate <= 1.0):
            raise ValueError("loss_rate must be in [0,1]")
        if self.cost < 0:
            raise ValueError("cost must be >= 0")

    @property
    def available_mbps(self) -> float:
        if self.status in ("down", LinkStatus.DOWN.value):
            return 0.0
        return max(0.0, self.bandwidth_mbps - self.reserved_mbps)

    @property
    def healthy(self) -> bool:
        return self.status in ("up", LinkStatus.UP.value, "degraded", LinkStatus.DEGRADED.value, "intermittent", LinkStatus.INTERMITTENT.value) and self.available_mbps >= 0.0

    def score_weight(self, qos: str = "standard") -> float:
        # Lower is better. Degraded/intermittent links are penalized; down is infinite.
        if self.status in ("down", LinkStatus.DOWN.value):
            return math.inf
        q = str(qos)
        lat = self.latency_ms + self.jitter_ms * (1.5 if q == QosTier.PREMIUM.value else 0.5)
        loss_penalty = self.loss_rate * (500.0 if q == QosTier.PREMIUM.value else 120.0)
        util = 0.0
        if self.bandwidth_mbps > 0:
            util = (self.reserved_mbps / self.bandwidth_mbps) * (40.0 if q != QosTier.BEST_EFFORT.value else 10.0)
        state_penalty = {"up": 0.0, "degraded": 25.0, "intermittent": 60.0}.get(str(self.status), 20.0)
        return max(0.001, lat + loss_penalty + util + self.cost + state_penalty)


@dataclass
class FlowDemand:
    flow_id: str
    src: str
    dst: str
    demand_mbps: float = 1.0
    priority: int = 1
    qos: str = "standard"
    max_latency_ms: Optional[float] = None
    min_bandwidth_mbps: Optional[float] = None
    payload_bytes: int = 0
    intermittent_ok: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        for name in ("flow_id", "src", "dst"):
            if not getattr(self, name):
                raise ValueError(f"{name} is required")
        if self.demand_mbps < 0:
            raise ValueError("demand_mbps must be >= 0")
        if self.min_bandwidth_mbps is not None and self.min_bandwidth_mbps < 0:
            raise ValueError("min_bandwidth_mbps must be >= 0")


@dataclass
class PathDecision:
    flow_id: str
    src: str
    dst: str
    path: List[str]
    links: List[str]
    admitted: bool
    qos: str
    latency_ms: float
    bottleneck_mbps: float
    score: float
    reasons: List[str] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    fallback_used: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "src": self.src,
            "dst": self.dst,
            "path": self.path,
            "links": self.links,
            "admitted": self.admitted,
            "qos": self.qos,
            "latency_ms": round(self.latency_ms, 3),
            "bottleneck_mbps": round(self.bottleneck_mbps, 3),
            "score": round(self.score, 6) if math.isfinite(self.score) else None,
            "reasons": self.reasons,
            "alternatives": self.alternatives,
            "fallback_used": self.fallback_used,
        }


def normalize_nodes(nodes: Any) -> Dict[str, List[str]]:
    """Accept legacy neighbor map or list of node/link dicts; return neighbor map."""
    if nodes is None:
        return {}
    if isinstance(nodes, Mapping):
        # Could be neighbor map or richer topology; detect neighbor-map shape.
        if nodes and all(isinstance(v, (list, tuple, set)) or v is None for v in nodes.values()):
            return {str(k): [str(x) for x in (v or [])] for k, v in nodes.items()}
        # Rich topology map with "nodes"/"links" not expected here; fall through.
    if isinstance(nodes, Sequence) and not isinstance(nodes, (str, bytes)):
        out: Dict[str, List[str]] = {}
        for item in nodes:
            if isinstance(item, Mapping):
                nid = item.get("node_id") or item.get("id")
                if nid is not None:
                    out.setdefault(str(nid), [])
                    for nb in item.get("links") or item.get("neighbors") or []:
                        out[str(nid)].append(str(nb))
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                a, b = str(item[0]), str(item[1])
                out.setdefault(a, []).append(b)
        return out
    return {}


def links_from_neighbor_map(nodes: Mapping[str, Sequence[str]], **defaults: Any) -> List[FabricLink]:
    links: List[FabricLink] = []
    seen = set()
    for src, nbs in normalize_nodes(nodes).items():
        for dst in nbs:
            key = (src, dst)
            if key in seen:
                continue
            seen.add(key)
            links.append(FabricLink(link_id=f"{src}->{dst}", src=src, dst=dst, **defaults))
    return links


def topology_from_legacy(nodes: Any, links: Any = None) -> Tuple[Dict[str, FabricNode], Dict[str, FabricLink]]:
    node_map: Dict[str, FabricNode] = {}
    link_map: Dict[str, FabricLink] = {}
    if links is None and isinstance(nodes, Mapping) and nodes and all(isinstance(v, (list, tuple, set)) or v is None for v in nodes.values()):
        nmap = normalize_nodes(nodes)
        for nid in nmap:
            node_map[nid] = FabricNode(node_id=nid)
        for l in links_from_neighbor_map(nmap):
            link_map[l.link_id] = l
        return node_map, link_map
    # nodes list/dicts
    if isinstance(nodes, Sequence) and not isinstance(nodes, (str, bytes)):
        for item in nodes:
            if isinstance(item, Mapping):
                nid = str(item.get("node_id") or item.get("id") or item.get("name") or "")
                if nid:
                    node_map[nid] = FabricNode(
                        node_id=nid,
                        kind=str(item.get("kind") or item.get("tier") or "edge"),
                        region=str(item.get("region") or ""),
                        status=str(item.get("status") or "online"),
                        capacity_mbps=float(item.get("capacity_mbps") or item.get("bandwidth_mbps") or 1000.0),
                        metadata={k: v for k, v in item.items() if k not in {"node_id", "id", "name", "kind", "tier", "region", "status", "capacity_mbps", "bandwidth_mbps", "links", "neighbors"}},
                    )
    # explicit links
    if isinstance(links, Sequence):
        for i, item in enumerate(links):
            if isinstance(item, FabricLink):
                link_map[item.link_id] = item
            elif isinstance(item, Mapping):
                src = str(item.get("src") or item.get("from") or item.get("source") or "")
                dst = str(item.get("dst") or item.get("to") or item.get("target") or "")
                lid = str(item.get("link_id") or item.get("id") or f"{src}->{dst or i}")
                if src and dst:
                    link_map[lid] = FabricLink(
                        link_id=lid,
                        src=src,
                        dst=dst,
                        bandwidth_mbps=float(item.get("bandwidth_mbps") or item.get("capacity_mbps") or 100.0),
                        latency_ms=float(item.get("latency_ms") or 10.0),
                        loss_rate=float(item.get("loss_rate") or 0.0),
                        jitter_ms=float(item.get("jitter_ms") or 0.0),
                        status=str(item.get("status") or "up"),
                        cost=float(item.get("cost") or 1.0),
                        reserved_mbps=float(item.get("reserved_mbps") or 0.0),
                        tags=list(item.get("tags") or []),
                    )
                    node_map.setdefault(src, FabricNode(node_id=src))
                    node_map.setdefault(dst, FabricNode(node_id=dst))
    return node_map, link_map


def _adjacency(links: Iterable[FabricLink], qos: str = "standard", min_bandwidth_mbps: Optional[float] = None) -> Dict[str, List[Tuple[str, str, float]]]:
    adj: Dict[str, List[Tuple[str, str, float]]] = {}
    need = None if min_bandwidth_mbps is None else max(0.0, float(min_bandwidth_mbps))
    for l in links:
        if l.status in ("down", LinkStatus.DOWN.value):
            continue
        if need is not None and l.available_mbps < need:
            continue
        adj.setdefault(l.src, []).append((l.dst, l.link_id, l.score_weight(qos)))
        adj.setdefault(l.dst, [])
    return adj


def shortest_path(nodes: Dict[str, FabricNode], links: Dict[str, FabricLink], src: str, dst: str, qos: str = "standard", min_bandwidth_mbps: Optional[float] = None) -> Tuple[List[str], List[str], float]:
    src, dst = str(src), str(dst)
    if not src or not dst:
        return [], [], math.inf
    if src == dst:
        return [src], [], 0.0
    adj = _adjacency(links.values(), qos=qos, min_bandwidth_mbps=min_bandwidth_mbps)
    # also include isolated known nodes
    for nid in nodes:
        adj.setdefault(nid, [])
    dist: Dict[str, float] = {src: 0.0}
    prev: Dict[str, Tuple[str, str]] = {}
    pq: List[Tuple[float, str]] = [(0.0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist.get(u, math.inf):
            continue
        if u == dst:
            break
        for v, lid, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, math.inf):
                dist[v] = nd
                prev[v] = (u, lid)
                heapq.heappush(pq, (nd, v))
    if dst not in dist:
        return [], [], math.inf
    path = [dst]
    link_ids: List[str] = []
    cur = dst
    while cur != src:
        pu, lid = prev[cur]
        link_ids.append(lid)
        path.append(pu)
        cur = pu
    path.reverse(); link_ids.reverse()
    return path, link_ids, dist[dst]


# ---- legacy-compatible API (do not break callers) ----

def route_path(src, dst, nodes):
    # Historical behavior: neighbor map, direct if exists else via hub, else [src,dst].
    nmap = normalize_nodes(nodes)
    src, dst = str(src), str(dst)
    if dst in nmap.get(src, []):
        return [src, dst]
    for hub in nmap:
        if dst in nmap.get(hub, []) and src in nmap.get(hub, []):
            return [src, hub, dst]
    # improved fallback: try weighted shortest path over derived links
    if nmap:
        nm, lm = topology_from_legacy(nmap)
        path, _, _score = shortest_path(nm, lm, src, dst)
        if path:
            return path
    return [src, dst]


def qos_class(latency_ms, priority):
    # Historical thresholds preserved.
    try:
        lat = float(latency_ms)
        pri = float(priority)
    except Exception:
        lat, pri = 9999.0, 0.0
    if pri >= 2 or lat < 20:
        return "premium"
    if lat < 100:
        return "standard"
    return "best_effort"


def allocate_bandwidth(total, demands):
    # Historical: proportional by demand, allocated rounded to 2 decimals.
    total_d = sum(float(d.get("demand", 0) or 0) for d in demands) or 1.0
    try:
        total_v = float(total)
    except Exception:
        total_v = 0.0
    out = []
    for d in demands:
        dem = float(d.get("demand", 0) or 0)
        share = total_v * dem / total_d
        out.append({"id": d.get("id"), "allocated": round(share, 2)})
    return out


def transport_health(links):
    seq = list(links or [])
    up = sum(1 for l in seq if isinstance(l, Mapping) and l.get("status") == "up")
    return {"total": len(seq), "up": up, "health": round(up / max(1, len(seq)), 4)}


# ---- advanced fabric operations ----

def classify_qos(flow: FlowDemand, path_latency_ms: float) -> str:
    if flow.max_latency_ms is not None and path_latency_ms > flow.max_latency_ms and flow.priority < 90:
        return QosTier.BEST_EFFORT.value
    return qos_class(path_latency_ms, flow.priority)


def path_metrics(links: Dict[str, FabricLink], link_ids: Sequence[str]) -> Dict[str, float]:
    latency = 0.0
    bottleneck = math.inf
    loss = 0.0
    for lid in link_ids:
        l = links.get(lid)
        if not l:
            continue
        latency += l.latency_ms + l.jitter_ms
        bottleneck = min(bottleneck, l.available_mbps)
        # independent-ish approximation
        loss = 1.0 - (1.0 - loss) * (1.0 - l.loss_rate)
    if bottleneck is math.inf:
        bottleneck = 0.0
    return {"latency_ms": latency, "bottleneck_mbps": bottleneck, "loss_rate": loss}


def admit_flow(nodes: Dict[str, FabricNode], links: Dict[str, FabricLink], flow: FlowDemand) -> PathDecision:
    flow.validate()
    qos = qos_class(flow.max_latency_ms if flow.max_latency_ms is not None else 1000.0, flow.priority)
    need = flow.min_bandwidth_mbps if flow.min_bandwidth_mbps is not None else flow.demand_mbps
    # Prefer a feasible path that can carry required bandwidth.
    path, link_ids, weight = shortest_path(nodes, links, flow.src, flow.dst, qos=qos, min_bandwidth_mbps=need)
    constrained = bool(path)
    if not path:
        path, link_ids, weight = shortest_path(nodes, links, flow.src, flow.dst, qos=qos)
        constrained = False
    reasons: List[str] = []
    if not path:
        return PathDecision(flow.flow_id, flow.src, flow.dst, [], [], False, qos, math.inf, 0.0, math.inf,
                            reasons=["no path found"], fallback_used=False)
    m = path_metrics(links, link_ids)
    admitted = True
    if need > m["bottleneck_mbps"]:
        admitted = False
        reasons.append(f"insufficient bandwidth: need {need} Mbps, bottleneck {m['bottleneck_mbps']:.3f} Mbps")
    if flow.max_latency_ms is not None and m["latency_ms"] > flow.max_latency_ms:
        admitted = False
        reasons.append(f"latency {m['latency_ms']:.3f}ms exceeds max {flow.max_latency_ms}ms")
    if not constrained and m["bottleneck_mbps"] >= need:
        reasons.append("best-effort path selected; feasible bandwidth not guaranteed on all scoring constraints")
    # intermittent poor connectivity: if not admitted but intermittent is allowed, return degraded plan
    if not admitted and flow.intermittent_ok and path:
        reasons.append("intermittent delivery acceptable: degraded path returned for bounded/store-and-forward planning")
    final_qos = classify_qos(flow, m["latency_ms"])
    # alternatives: next-best by temporarily penalizing first hop
    alts = []
    if link_ids:
        first = links.get(link_ids[0])
        if first:
            orig = first.cost
            first.cost = orig + 1000.0
            p2, l2, w2 = shortest_path(nodes, links, flow.src, flow.dst, qos=qos, min_bandwidth_mbps=need if constrained else None)
            first.cost = orig
            if p2 and p2 != path:
                m2 = path_metrics(links, l2)
                alts.append({"path": p2, "links": l2, "latency_ms": round(m2["latency_ms"], 3), "bottleneck_mbps": round(m2["bottleneck_mbps"], 3), "score": round(w2, 6) if math.isfinite(w2) else None})
    return PathDecision(flow.flow_id, flow.src, flow.dst, path, link_ids, admitted, final_qos, m["latency_ms"], m["bottleneck_mbps"], weight,
                        reasons=reasons, alternatives=alts, fallback_used=bool(not admitted and flow.intermittent_ok and path))


def reserve_path(links: Dict[str, FabricLink], link_ids: Sequence[str], demand_mbps: float) -> Dict[str, Any]:
    demand_mbps = max(0.0, float(demand_mbps))
    changed = []
    for lid in link_ids:
        l = links.get(lid)
        if not l:
            return {"ok": False, "error": f"unknown link {lid}", "changed": changed}
        if l.available_mbps < demand_mbps:
            return {"ok": False, "error": f"insufficient capacity on {lid}", "available_mbps": l.available_mbps, "changed": changed}
    for lid in link_ids:
        l = links[lid]
        l.reserved_mbps += demand_mbps
        changed.append({"link_id": lid, "reserved_mbps": round(l.reserved_mbps, 3), "available_mbps": round(l.available_mbps, 3)})
    return {"ok": True, "demand_mbps": demand_mbps, "changed": changed}


def release_path(links: Dict[str, FabricLink], link_ids: Sequence[str], demand_mbps: float) -> Dict[str, Any]:
    demand_mbps = max(0.0, float(demand_mbps))
    changed = []
    for lid in link_ids:
        l = links.get(lid)
        if l:
            l.reserved_mbps = max(0.0, l.reserved_mbps - demand_mbps)
            changed.append({"link_id": lid, "reserved_mbps": round(l.reserved_mbps, 3), "available_mbps": round(l.available_mbps, 3)})
    return {"ok": True, "demand_mbps": demand_mbps, "changed": changed}


def fabric_health(nodes: Mapping[str, FabricNode], links: Mapping[str, FabricLink]) -> Dict[str, Any]:
    link_rows = [l.__dict__ if hasattr(l, "__dict__") else l for l in links.values()]
    legacy = transport_health([{"status": getattr(l, "status", l.get("status") if isinstance(l, Mapping) else None)} for l in links.values()])
    up_links = sum(1 for l in links.values() if getattr(l, "status", None) == "up")
    degraded = sum(1 for l in links.values() if getattr(l, "status", None) == "degraded")
    intermittent = sum(1 for l in links.values() if getattr(l, "status", None) == "intermittent")
    down = sum(1 for l in links.values() if getattr(l, "status", None) == "down")
    bw = sum(getattr(l, "bandwidth_mbps", 0.0) for l in links.values())
    reserved = sum(getattr(l, "reserved_mbps", 0.0) for l in links.values())
    util = round(reserved / bw, 4) if bw > 0 else 0.0
    online_nodes = sum(1 for n in nodes.values() if getattr(n, "status", "online") in ("online", "up"))
    score = _clamp((up_links + 0.6 * degraded + 0.3 * intermittent) / max(1, len(links)) * 0.7 + (online_nodes / max(1, len(nodes))) * 0.3)
    return {
        **legacy,
        "nodes": len(nodes),
        "online_nodes": online_nodes,
        "links": len(links),
        "up_links": up_links,
        "degraded_links": degraded,
        "intermittent_links": intermittent,
        "down_links": down,
        "bandwidth_mbps": round(bw, 3),
        "reserved_mbps": round(reserved, 3),
        "utilization": util,
        "fabric_health": round(score, 4),
    }


def reroute_plan(nodes: Dict[str, FabricNode], links: Dict[str, FabricLink], flow: FlowDemand, avoid_links: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    avoid = set(avoid_links or [])
    original = {lid: (l.status, l.cost) for lid, l in links.items()}
    try:
        for lid in avoid:
            if lid in links:
                links[lid].status = "down"
        decision = admit_flow(nodes, links, flow)
        return {
            "ok": True,
            "avoided_links": sorted(avoid),
            "decision": decision.to_dict(),
            "rerouted": bool(decision.path),
            "admitted": decision.admitted,
        }
    finally:
        for lid, (status, cost) in original.items():
            if lid in links:
                links[lid].status = status
                links[lid].cost = cost


def sla_report(decision: PathDecision, flow: FlowDemand) -> Dict[str, Any]:
    checks = []
    if flow.max_latency_ms is not None:
        checks.append({"name": "max_latency", "ok": decision.latency_ms <= flow.max_latency_ms, "actual": decision.latency_ms, "limit": flow.max_latency_ms})
    need = flow.min_bandwidth_mbps if flow.min_bandwidth_mbps is not None else flow.demand_mbps
    checks.append({"name": "bandwidth", "ok": decision.bottleneck_mbps >= need, "actual": decision.bottleneck_mbps, "limit": need})
    checks.append({"name": "path_exists", "ok": bool(decision.path), "actual": len(decision.path)})
    return {"flow_id": flow.flow_id, "ok": all(c["ok"] for c in checks), "checks": checks, "qos": decision.qos}
