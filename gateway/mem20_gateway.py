#!/usr/bin/env python3
"""
mem20 Gateway — CLI relay for multi-agent fleet communication.
Each mem20 agent picks a unique name on startup to avoid confusion.
Stage 1: CLI procede. No fake code. Real tools only.
"""

import argparse
import json

# Assimilation: resolve absorbed mem20*z packages rehomed under short runtimes
try:
    import sys as _sys, pathlib as _pl
    _repo = _pl.Path(__file__).resolve().parents[1]
    if str(_repo) not in _sys.path:
        _sys.path.insert(0, str(_repo))
    _tc = _repo / "toolchest" / "src"
    if _tc.is_dir() and str(_tc) not in _sys.path:
        _sys.path.insert(0, str(_tc))
    import _mem20_absorbed_finder  # noqa: F401
except Exception:
    pass
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

MEM20_DIR = Path("/opt/mem20")
GATEWAY_DIR = MEM20_DIR / "gateway"
NAMES_FILE = GATEWAY_DIR / "agent_names.json"
MESSAGES_FILE = GATEWAY_DIR / "messages.jsonl"

# ---------------------------------------------------------------------------
# Subsystem registry
# ---------------------------------------------------------------------------
# Which mem20 subsystems are reachable from the gateway surface, and what each
# one is for. A subsystem that is not listed here is not callable by any client.
# This registry contains the 57 canonical subsystems after absorption.
SUBSYSTEMS = {
    "mem20agentz": {
        "purpose": "Native mem20 OpenAI Agents SDK absorption (Agent, Runner, Tools, Handoffs)",
        "entry": "python -m mem20agentz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20assistz": {
        "purpose": "Autonomous systems runtime (crew/runtime)",
        "entry": "python -m mem20assistz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20autouez": {
        "purpose": "Unreal Engine automation, Python API, asset pipeline absorption",
        "entry": "python -m mem20autouez --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20autoz": {
        "purpose": "Autonomous systems runtime (crew/runtime)",
        "entry": "python -m mem20autoz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20benchmarkz": {
        "purpose": "Retrieval benchmarks (quality, latency, trustworthiness)",
        "entry": "python -m mem20benchmarkz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20biz": {
        "purpose": "Autonomous company and revenue runtime grouping the revenue family",
        "entry": "python -m mem20biz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20botz": {
        "purpose": "Bot orchestration runtime",
        "entry": "python -m mem20botz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20boxz": {
        "purpose": "Sandbox runtime grouping the sandbox family for joint integration",
        "entry": "python -m mem20boxz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20cliz": {
        "purpose": "CLI envelope and JSON flag parsing for fleet",
        "entry": "python -m mem20cliz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20controlz": {
        "purpose": "Unified control plane for the mem20 fleet (per-subsystem panels)",
        "entry": "python -m mem20controlz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20corez": {
        "purpose": "Core ML runtime (CharMLP, etc.)",
        "entry": "python -m mem20corez --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20crewz": {
        "purpose": "Crew orchestration runtime (guardrails, A2A)",
        "entry": "python -m mem20crewz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20cviz": {
        "purpose": "Computer-vision inference subsystem (classification/CV)",
        "entry": "python -m mem20cviz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20dreamz": {
        "purpose": "Dream engine (fidelity verdicts, divergence)",
        "entry": "python -m mem20dreamz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20enginez": {
        "purpose": "Crew runtime for 30 engine members: registry/probing, compatibility and dispatch planning, durable state, CLI/HTTP cockpit",
        "entry": "python -m mem20enginez status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20fabricz": {
        "purpose": "Integration Fabric crew runtime: 23-member registry/probing/dispatch with 6-peer API/integration/episode/event/radio/deal signals",
        "entry": "python -m mem20fabricz doctor",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20facez": {
        "purpose": "Interface/Workspace crew runtime: 8-member composition with 6-peer capture, dataflow, mission, canvas, sandbox, and blackboard signals",
        "entry": "python -m mem20facez doctor",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20factoryz": {
        "purpose": "GameFactory-3A absorption (procgen, asset synthesis, level generation)",
        "entry": "python -m mem20factoryz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20famz": {
        "purpose": "Family registry: which family each mem20*z package belongs to, and why",
        "entry": "python -m mem20famz stats",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20gamez": {
        "purpose": "OpenGame absorption (game agents, environments, reward shaping)",
        "entry": "python -m mem20gamez --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20googlez": {
        "purpose": "Google ADK-style agents, tools, runners, sessions, memory, flows",
        "entry": "python -m mem20googlez --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20graphz": {
        "purpose": "mem20graphz graph crew runtime: 7-member graph integrations (capability-gap, loyalty, config, skill, relationship, reversible execution, semantic objects); legacy CLI preserved",
        "entry": "python -m mem20graphz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20greenz": {
        "purpose": "Greenroom: stage clones of external software/sites, build originals, ship",
        "entry": "python -m mem20greenz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20ircz": {
        "purpose": "IRC bridge subsystem",
        "entry": "python -m mem20ircz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20kanbanz": {
        "purpose": "The one true kanban door: typed client, migration, read-only inspection",
        "entry": "python -m mem20kanbanz health",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20kilnz": {
        "purpose": "Native mem20 3D subsystem: AI-first cleanroom mesh and geometry modeler with 103-op agent surface",
        "entry": "python -m mem20kilnz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20kimiz": {
        "purpose": "Native Kimi Agent Swarm substrate (parallel subagent fan-out)",
        "entry": "python -m mem20kimiz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20labz": {
        "purpose": "Laboratory Runtime: 1st-class control plane for 10 member labs with registry/probes/simulation, 6-peer ecosystem signals, durable SQLite WAL run history, CLI/API/web",
        "entry": "python -m mem20labz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20langz": {
        "purpose": "Native graph substrate absorption (stateful multi-agent graphs)",
        "entry": "python -m mem20langz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20liez": {
        "purpose": "Lie algebra subsystem",
        "entry": "python -m mem20liez --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20meshz": {
        "purpose": "Mesh Gold Runtime: orchestrates 6 vendored meshes (crisis/crossdevice/federated/nearby/offline/selfhealing) with 6 external ecosystem integrations, lazy aggregation/failover",
        "entry": "python -m mem20meshz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20mktz": {
        "purpose": "Phase 2 marketplace organs (inference/capability/service markets)",
        "entry": "python -m mem20mktz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20ocaskz": {
        "purpose": "Opencode feature-ask auditor (mines opencode session database)",
        "entry": "python -m mem20ocaskz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20officez": {
        "purpose": "Native 3D office, agent fleet, Phaser scenes, wellness, dashboard",
        "entry": "python -m mem20officez doctor",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20orcaz": {
        "purpose": "OrKa-style deterministic workflow orchestration (pure stdlib port)",
        "entry": "python -m mem20orcaz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20owebz": {
        "purpose": "Chat front-end + model gateway (Open WebUI + LiteLLM re-home)",
        "entry": "python -m mem20owebz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20pipez": {
        "purpose": "Unified pipeline subsystem with all pipe runtimes (gameplay, narrative, level design, production, rigging, audio, secure build, version control) as modules under mem20pipez/pipes/",
        "entry": "python -m mem20pipez status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20portalz": {
        "purpose": "Portal subsystem",
        "entry": "python -m mem20portalz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20rpgz": {
        "purpose": "RPGAgent absorption (stats, combat, inventory, quests, world)",
        "entry": "python -m mem20rpgz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20schoolz": {
        "purpose": "Unified training + certification + apprenticeship",
        "entry": "python -m mem20schoolz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20secretz": {
        "purpose": "Secrets management subsystem",
        "entry": "python -m mem20secretz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20selfz": {
        "purpose": "mem20 self-healing, self-tuning, forecasting and optimization runtime with 6 peer integrations",
        "entry": "python -m mem20selfz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20sensorz": {
        "purpose": "Phase 1 sense-organs (capability gap, replanning, sensing)",
        "entry": "python -m mem20sensorz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20shopz": {
        "purpose": "Storefront: catalog, Stripe Checkout, verified webhooks, once-only provisioning",
        "entry": "python -m mem20shopz --readiness",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20simz": {
        "purpose": "Unified simulation subsystem with all simulator runtimes (ethical incentive, game balance, business model, counterfactual memory, architecture sandbox, product-led growth, roadmap twin, user acceptance, outcomes lab, audience reaction, life scenario, operations replay) as modules under mem20simz/sims/",
        "entry": "python -m mem20simz status",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20sitemapz": {
        "purpose": "Machine-readable sitemap of the estate, quiescence poller, source snapshotter",
        "entry": "python -m mem20sitemapz build",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20studioz": {
        "purpose": "Unified studio subsystem with all studio runtimes (AI game studio builder, AI production studio OS, asset remix studio, protocol invention studio, WebGPU compute studio) as modules under mem20studioz/studios/",
        "entry": "python -m mem20studioz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20teamz": {
        "purpose": "Rooms where humans and agents share a transcript; @mentions wake profiles",
        "entry": "python -m mem20teamz rooms",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20twinz": {
        "purpose": "Unified twin subsystem with all twin runtimes (customer digital twin lab, execution digital twin, human satisfaction twin, integration digital twin, personal workflow twin, player motivation twin, real-time business twin) as modules under mem20twinz/twins/",
        "entry": "python -m mem20twinz --members",
        "owner": "mem20-webdev",
        "wave": 2,
    },
    "mem20ucgz": {
        "purpose": "RM-001 Universal Capability Graph (typed capability graph)",
        "entry": "python -m mem20ucgz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20unikitz": {
        "purpose": "UniKit AI absorption (behavior trees, GOAP, utility AI, navigation)",
        "entry": "python -m mem20unikitz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20unitiz": {
        "purpose": "Reinforcement-learning toolkit (grid envs, PPO, DQN, SAC)",
        "entry": "python -m mem20unitiz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20wasmz": {
        "purpose": "WebAssembly component lab (language-neutral component compatibility)",
        "entry": "python -m mem20wasmz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20webgpuz": {
        "purpose": "WebGPU backend selection against probed real hardware",
        "entry": "python -m mem20webgpuz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20yetiz": {
        "purpose": "Yeti Claw absorption (3D rigging, animation, BVH mocap, glTF)",
        "entry": "python -m mem20yetiz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20zimr": {
        "purpose": "RM-002 Zero-Install Microapp Runtime (signed microapps)",
        "entry": "python -m mem20zimr --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20AIonbordz": {
        "purpose": "Generate verified onboarding packs for mem20 agents (hire guide, orientation)",
        "entry": "python -m mem20aionbordz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20adaptz": {
        "purpose": "Adaptive systems runtime (crew/runtime)",
        "entry": "python -m mem20adaptz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20agentz_sdk": {
        "purpose": "Native mem20 OpenAI Agents SDK absorption (Agent, Runner, Tools, Handoffs)",
        "entry": "python -m mem20agentz_sdk --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20alternativedatabaseplaygroundz": {
        "purpose": "Alternative database playground (query planning, indexing, engine comparison)",
        "entry": "python -m mem20alternativedatabaseplaygroundz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20ambientdevicecompanionz": {
        "purpose": "Ambient device companion (context sensing, proactive suggestions, routines)",
        "entry": "python -m mem20ambientdevicecompanionz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20ambientteamradioz": {
        "purpose": "Ambient team radio (channels, messaging, routing, activity)",
        "entry": "python -m mem20ambientteamradioz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20asynccollaborationcapsulesz": {
        "purpose": "Async collaboration capsules (changes, sync, merge, checksums)",
        "entry": "python -m mem20asynccollaborationcapsulesz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20autonomoustrafficcontrollerz": {
        "purpose": "Autonomous traffic controller (token/leaky bucket throttling)",
        "entry": "python -m mem20autonomoustrafficcontrollerz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20batteryawareagentschedulerz": {
        "purpose": "Battery-aware agent scheduler (energy-aware scheduling)",
        "entry": "python -m mem20batteryawareagentschedulerz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20crdtcollaborationenginez": {
        "purpose": "CRDT collaboration engine (GCounter, PNCounter conflict-free state)",
        "entry": "python -m mem20crdtcollaborationenginez --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20dynamicphasereplannerz": {
        "purpose": "Dynamic phase replanner (adaptive phase planning)",
        "entry": "python -m mem20dynamicphasereplannerz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20milestoneriskpredictorz": {
        "purpose": "Milestone risk predictor (schedule/risk forecasting)",
        "entry": "python -m mem20milestoneriskpredictorz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20prioritycollisionresolverz": {
        "purpose": "Priority collision resolver (conflict/priority arbitration)",
        "entry": "python -m mem20prioritycollisionresolverz --help",
        "owner": "mem20-renovation",
        "wave": 4,
    },
    "mem20causalroutingbrainz": {
        "purpose": "Causal routing brain: coordinate heterogeneous computers as one capability-aware fleet with 6 peer integrations",
        "entry": "python -m mem20causalroutingbrainz status",
        "owner": "mem20-renovation",
        "wave": 4,
    },
}


def registered_subsystems() -> dict:
    """Return the subsystem registry, for the MCP server and for operators."""
    return SUBSYSTEMS


def subsystem_entry(name: str) -> dict:
    """Look one subsystem up. Returns an explicit miss rather than None."""
    record = SUBSYSTEMS.get(name)
    if record is None:
        return {"name": name, "registered": False}
    return {"name": name, "registered": True, **record}


def ensure_dirs():
    GATEWAY_DIR.mkdir(parents=True, exist_ok=True)


def register_agent(name: str = None, location: str = None) -> dict:
    """
    Each mem20 agent picks a name on startup. If no name given, generate one.
    Returns agent record.
    """
    ensure_dirs()
    
    if not name:
        # Generate a distinctive name based on location + uuid
        loc = location or "unknown"
        short_loc = loc.replace("/", "-").replace(" ", "-")[:20]
        agent_id = uuid.uuid4().hex[:8]
        name = f"mem20-{short_loc}-{agent_id}"
    
    record = {
        "name": name,
        "location": location or "local",
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "agent_id": uuid.uuid4().hex[:8],
        "status": "active"
    }
    
    # Load existing names, check for collisions
    names = load_names()
    if name in names:
        # Append suffix to avoid collision
        base = name
        counter = 1
        while name in names:
            name = f"{base}-{counter}"
            counter += 1
        record["name"] = name
        record["collision_avoided"] = True
    
    names[name] = record
    
    with open(NAMES_FILE, "w") as f:
        json.dump(names, f, indent=2)
    
    print(f"Agent registered: {name}")
    print(f"  Location: {record['location']}")
    print(f"  Agent ID: {record['agent_id']}")
    print(f"  Registered: {record['registered_at']}")
    
    return record

def load_names() -> dict:
    if NAMES_FILE.exists():
        with open(NAMES_FILE) as f:
            return json.load(f)
    return {}

def list_agents() -> dict:
    """List all registered agents."""
    names = load_names()
    if not names:
        print("No agents registered.")
        return names
    
    print(f"Registered agents ({len(names)}):")
    for name, info in sorted(names.items()):
        status = info.get("status", "unknown")
        location = info.get("location", "unknown")
        registered = info.get("registered_at", "unknown")
        print(f"  {name}")
        print(f"    Location: {location}")
        print(f"    Status: {status}")
        print(f"    Since: {registered}")
        print()
    
    return names

def broadcast(message: str, agent_name: str = None, target: str = "telegram_channel"):
    """
    Broadcast a message to the gateway. All mem20 agents can read it.
    """
    ensure_dirs()
    
    names = load_names()
    
    if not agent_name:
        # Try to find our name
        if len(names) == 1:
            agent_name = list(names.keys())[0]
        elif len(names) > 1:
            print("Multiple agents registered. Specify --agent-name.")
            sys.exit(1)
        else:
            print("No agents registered. Run register first.")
            sys.exit(1)
    
    if agent_name not in names:
        print(f"Agent '{agent_name}' not registered. Register first.")
        sys.exit(1)
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "agent_id": names[agent_name].get("agent_id", ""),
        "location": names[agent_name].get("location", "unknown"),
        "message": message,
        "target": target,
        "source": "mem20_gateway",
        "message_id": uuid.uuid4().hex[:12]
    }
    
    with open(MESSAGES_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    print(f"Broadcast from {agent_name}: {message[:80]}...")
    return entry

def read_messages(since: str = None, agent: str = None, limit: int = 50):
    """
    Read messages from the gateway.
    """
    ensure_dirs()
    
    if not MESSAGES_FILE.exists():
        print("No messages yet.")
        return []
    
    messages = []
    with open(MESSAGES_FILE) as f:
        for line in f:
            entry = json.loads(line.strip())
            messages.append(entry)
    
    # Filter
    if agent:
        messages = [m for m in messages if m["agent"] == agent]
    
    if since:
        messages = [m for m in messages if m["timestamp"] >= since]
    
    # Sort by timestamp, newest first
    messages.sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Limit
    messages = messages[:limit]
    
    if not messages:
        print("No matching messages.")
        return messages
    
    print(f"Messages ({len(messages)}):")
    for m in messages:
        print(f"  [{m['timestamp']}] {m['agent']}: {m['message'][:100]}")
    
    return messages

def parse_args():
    parser = argparse.ArgumentParser(description="mem20 Gateway — multi-mem20 relay")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # register
    p_register = subparsers.add_parser("register", help="Register this mem20 agent")
    p_register.add_argument("--name", "-n", help="Agent name (auto-generated if not provided)")
    p_register.add_argument("--location", "-l", help="VPS location or hostname")
    
    # list
    subparsers.add_parser("list", help="List all registered agents")
    
    # broadcast
    p_broadcast = subparsers.add_parser("broadcast", help="Broadcast a message")
    p_broadcast.add_argument("message", help="Message to broadcast")
    p_broadcast.add_argument("--agent-name", "-a", help="Your agent name")
    p_broadcast.add_argument("--target", "-t", default="telegram_channel", help="Target channel")
    
    # read
    p_read = subparsers.add_parser("read", help="Read messages from gateway")
    p_read.add_argument("--since", help="Only messages since this ISO timestamp")
    p_read.add_argument("--agent", "-a", help="Filter by agent name")
    p_read.add_argument("--limit", "-l", type=int, default=50, help="Max messages to return")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    if args.command == "register":
        record = register_agent(name=args.name, location=args.location)
        print(json.dumps(record, indent=2))
    
    elif args.command == "list":
        list_agents()
    
    elif args.command == "broadcast":
        broadcast(args.message, agent_name=args.agent_name, target=args.target)
    
    elif args.command == "read":
        read_messages(since=args.since, agent=args.agent, limit=args.limit)

if __name__ == "__main__":
    main()