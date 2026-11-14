#!/usr/bin/env python3
"""Generate comprehensive agent-only skill catalog for mem20 ecosystem."""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

CATALOG_VERSION = "1.0.0"
OUT_DIR = Path("/opt/mem20/toolchest/skills")
OUT_DIR.mkdir(parents=True, exist_ok=True)

skills = []

def add_skill(skill):
    skills.append(skill)

# Core memory skills
add_skill({
    "id": "mem20.core.memory.remember_grounded.v1",
    "ns": "mem20.core.memory",
    "cat": "memory",
    "intent": "persist_grounded_record",
    "desc": "persist grounded memory record with ledger audit and contamination guard",
    "caps": ["persist", "audit", "ground", "ledger"],
    "req_tools": ["remember"],
    "req_subsys": ["memory_engine"],
    "pre": ["origin==grounded", "no_simulated_leak"],
    "proc": [
        {"op": "validate", "tgt": "origin", "rule": "eq:grounded"},
        {"op": "call", "tool": "remember", "args": {"content": "$content", "tags": "$tags", "origin": "grounded", "meta": "$meta"}, "ret": "rec_id"},
        {"op": "assert", "chk": "ledger_appended"},
        {"op": "assert", "chk": "audit_contamination==0.0"}
    ],
    "in": {"schema": {"content": {"t": "str", "req": True}, "tags": {"t": "list", "req": False}, "meta": {"t": "obj", "req": False}}, "req": ["content"]},
    "out": {"schema": {"rec_id": {"t": "str"}, "ok": {"t": "bool"}, "audit": {"t": "obj"}}},
    "ver": [{"chk": "index_grounded_only"}, {"chk": "contamination==0"}],
    "fail": [{"e": "simulated_rejected", "rec": "tag_grounded"}, {"e": "contam_detected", "rec": "halt_audit_fix"}],
    "deps": [],
    "comp": ["mem20.core.memory.recall_semantic.v1", "mem20.core.memory.audit.v1"],
    "tags": ["memory", "grounded", "persist", "ledger", "audit"],
    "cx": 0.25,
    "eff": 0.99,
    "side": ["ledger_append", "index_write_grounded"],
    "inv": ["grounded_only", "contam_zero"]
})

add_skill({
    "id": "mem20.core.memory.recall_semantic.v1",
    "ns": "mem20.core.memory",
    "cat": "memory",
    "intent": "semantic_recall_grounded",
    "desc": "semantic recall over grounded partition with drift health check",
    "caps": ["recall", "search", "semantic", "drift_check"],
    "req_tools": ["recall", "recall_semantic"],
    "req_subsys": ["memory_engine"],
    "pre": ["index_healthy"],
    "proc": [
        {"op": "call", "tool": "recall_semantic", "args": {"query": "$q", "k": "$k", "filters": {"origin": "grounded"}}, "ret": "res"},
        {"op": "chk", "tgt": "diagnostic.health", "rule": "eq:healthy"},
        {"op": "filter", "rule": "origin==grounded"}
    ],
    "in": {"schema": {"q": {"t": "str", "req": True}, "k": {"t": "int", "req": False, "d": 10}}, "req": ["q"]},
    "out": {"schema": {"results": {"t": "list"}, "health": {"t": "str"}, "count": {"t": "int"}}},
    "ver": [{"chk": "all_grounded"}, {"chk": "health==healthy"}],
    "fail": [{"e": "index_drift", "rec": "rebuild_index_verify"}, {"e": "contam_leak", "rec": "audit_halt"}],
    "deps": [],
    "comp": ["mem20.core.memory.remember_grounded.v1"],
    "tags": ["memory", "recall", "semantic", "grounded", "drift"],
    "cx": 0.2,
    "eff": 0.98,
    "side": [],
    "inv": ["grounded_only"]
})

add_skill({
    "id": "mem20.core.memory.audit_contamination.v1",
    "ns": "mem20.core.memory",
    "cat": "audit",
    "intent": "verify_contamination_zero",
    "desc": "run contamination audit - must return 0.0",
    "caps": ["audit", "verify", "contam"],
    "req_tools": ["audit_contamination"],
    "req_subsys": ["memory_engine"],
    "pre": [],
    "proc": [
        {"op": "call", "tool": "audit_contamination", "ret": "r"},
        {"op": "assert", "chk": "r.contamination_rate==0.0"}
    ],
    "in": {"schema": {}, "req": []},
    "out": {"schema": {"contamination_rate": {"t": "float"}, "ok": {"t": "bool"}}},
    "ver": [{"chk": "contamination_rate==0.0"}],
    "fail": [{"e": "contam>0", "rec": "quarantine_investigate_purge_simulated"}],
    "deps": [],
    "comp": ["mem20.core.memory.remember_grounded.v1"],
    "tags": ["audit", "contamination", "invariant", "zero"],
    "cx": 0.15,
    "eff": 1.0,
    "side": [],
    "inv": ["contam_zero"]
})

# MCP operations
add_skill({
    "id": "mem20.mcp.operate.server.v1",
    "ns": "mem20.mcp",
    "cat": "mcp",
    "intent": "operate_mcp_server",
    "desc": "start/configure/healthcheck mem20 mcp server (stdio/http health)",
    "caps": ["mcp", "server", "health"],
    "req_tools": ["health_check"],
    "req_subsys": ["mcp"],
    "pre": [],
    "proc": [
        {"op": "chk", "tgt": "env.MEM20_STORE_PATH"},
        {"op": "exec", "cmd": "$venv/bin/python mcp/mcp_server.py", "bg": True},
        {"op": "wait", "t": 2},
        {"op": "call", "tool": "health_check", "ret": "h"},
        {"op": "assert", "chk": "h.ok==true"}
    ],
    "in": {"schema": {"store_path": {"t": "str", "req": True}}, "req": ["store_path"]},
    "out": {"schema": {"pid": {"t": "int"}, "healthy": {"t": "bool"}}},
    "ver": [{"chk": "health_endpoint_ok"}],
    "fail": [{"e": "port_conflict", "rec": "check_8080"}],
    "deps": [],
    "comp": [],
    "tags": ["mcp", "server", "health", "stdio"],
    "cx": 0.3,
    "eff": 0.97,
    "side": ["spawn_process"],
    "inv": []
})

# Toolchest skills
add_skill({
    "id": "mem20.toolchest.inventory.refresh.v1",
    "ns": "mem20.toolchest",
    "cat": "inventory",
    "intent": "refresh_tool_inventory",
    "desc": "regenerate toolchest inventory.json from real on-box discovery (mcp/cli/subsys)",
    "caps": ["inventory", "discover", "refresh"],
    "req_tools": ["toolchest_inventory"],
    "req_subsys": ["toolchest"],
    "pre": [],
    "proc": [
        {"op": "exec", "cmd": "python -m toolchest refresh"},
        {"op": "assert", "chk": "inventory.json_updated"},
        {"op": "verify", "chk": "counts_valid"}
    ],
    "in": {"schema": {}, "req": []},
    "out": {"schema": {"mcp": {"t": "int"}, "cli": {"t": "int"}, "subsystem": {"t": "int"}, "total": {"t": "int"}}},
    "ver": [{"chk": "no_fake_entries"}],
    "fail": [{"e": "discovery_fail", "rec": "check_env"}],
    "deps": [],
    "comp": ["mem20.toolchest.wiring.verify.v1"],
    "tags": ["toolchest", "inventory", "refresh", "discovery"],
    "cx": 0.25,
    "eff": 0.98,
    "side": ["write_file"],
    "inv": []
})

add_skill({
    "id": "mem20.toolchest.wiring.verify.v1",
    "ns": "mem20.toolchest",
    "cat": "wiring",
    "intent": "verify_cross_subsystem_wiring",
    "desc": "exercise all cross-subsystem wiring edges via real APIs",
    "caps": ["wiring", "verify", "integrate"],
    "req_tools": ["toolchest_wiring"],
    "req_subsys": ["toolchest"],
    "pre": [],
    "proc": [
        {"op": "exec", "cmd": "python -m toolchest wiring"},
        {"op": "assert", "chk": "edges_ok==edges_total"}
    ],
    "in": {"schema": {}, "req": []},
    "out": {"schema": {"edges_ok": {"t": "int"}, "edges_total": {"t": "int"}}},
    "ver": [{"chk": "all_edges_live"}],
    "fail": [{"e": "edge_fail", "rec": "debug_integration"}],
    "deps": [],
    "comp": ["mem20.toolchest.inventory.refresh.v1"],
    "tags": ["toolchest", "wiring", "integration", "verify"],
    "cx": 0.3,
    "eff": 0.99,
    "side": [],
    "inv": []
})

# Sitemapz skills
add_skill({
    "id": "mem20.sitemapz.discover.estate.v1",
    "ns": "mem20.sitemapz",
    "cat": "discovery",
    "intent": "discover_estate_structure",
    "desc": "map full mem20 estate via sitemapz - subsystems/files/relations",
    "caps": ["discover", "map", "index"],
    "req_tools": [],
    "req_subsys": ["mem20sitemapz"],
    "pre": [],
    "proc": [
        {"op": "exec", "cmd": "python -m mem20sitemapz snapshot"},
        {"op": "read", "path": ".sitemap/sitemap.json"},
        {"op": "parse", "tgt": "subsystems"}
    ],
    "in": {"schema": {}, "req": []},
    "out": {"schema": {"subsystems": {"t": "list"}, "files": {"t": "int"}}},
    "ver": [{"chk": "sitemap_current"}],
    "fail": [{"e": "stale", "rec": "regenerate"}],
    "deps": [],
    "comp": [],
    "tags": ["sitemapz", "discover", "map", "estate"],
    "cx": 0.2,
    "eff": 0.98,
    "side": ["write_files"],
    "inv": []
})

# Agent orchestration
add_skill({
    "id": "mem20.agentz.orchestrate.swarm.v1",
    "ns": "mem20.agentz",
    "cat": "orchestration",
    "intent": "orchestrate_agent_swarm",
    "desc": "coordinate multi-agent swarm via mem20agentz/orcaz/crewz",
    "caps": ["orchestrate", "swarm", "coordinate"],
    "req_tools": ["agent_spawn", "agent_orchestrate"],
    "req_subsys": ["mem20agentz", "mem20orcaz", "mem20crewz"],
    "pre": [],
    "proc": [
        {"op": "plan", "tgt": "tasks"},
        {"op": "assign", "tgt": "agents"},
        {"op": "monitor", "tgt": "progress"},
        {"op": "sync", "tgt": "state"}
    ],
    "in": {"schema": {"goal": {"t": "str", "req": True}, "agents": {"t": "list", "req": False}}, "req": ["goal"]},
    "out": {"schema": {"run_id": {"t": "str"}, "status": {"t": "str"}}},
    "ver": [{"chk": "all_complete_or_reported"}],
    "fail": [{"e": "deadlock", "rec": "resolve_conflict"}],
    "deps": [],
    "comp": [],
    "tags": ["agentz", "orchestration", "swarm", "crew"],
    "cx": 0.6,
    "eff": 0.95,
    "side": ["state_mut"],
    "inv": []
})

# Generate many more skills for coverage
# Auto-generate skills for all subsystems
import glob
mem20_dirs = sorted([d for d in glob.glob('/opt/mem20/mem20*') if os.path.isdir(d) and not d.endswith('.egg-info')])
for md in mem20_dirs:
    base = os.path.basename(md).replace('-', '_')
    bname = os.path.basename(md)
    # operate
    sid = f"mem20.subsys.{base}.operate.v1"
    if not any(s['id'] == sid for s in skills):
        add_skill({
            "id": sid, "ns": f"mem20.subsys.{base}", "cat": "subsystem", "intent": f"operate_{base}",
            "desc": f"operate {bname} subsystem per its interface",
            "caps": ["operate", "use"], "req_tools": [], "req_subsys": [bname], "pre": [],
            "proc": [{"op": "discover", "tgt": "api"}, {"op": "invoke", "tgt": "interface"}, {"op": "verify", "tgt": "result"}],
            "in": {"schema": {"op": {"t": "str", "req": True}}, "req": ["op"]},
            "out": {"schema": {"ok": {"t": "bool"}}},
            "ver": [{"chk": "interface_ok"}], "fail": [{"e": "not_importable", "rec": "check_install"}],
            "deps": [], "comp": [], "tags": [base, "subsystem", "operate"], "cx": 0.4, "eff": 0.9, "side": [], "inv": []
        })
    # inspect
    sid2 = f"mem20.subsys.{base}.inspect.v1"
    if not any(s['id'] == sid2 for s in skills):
        add_skill({
            "id": sid2, "ns": f"mem20.subsys.{base}", "cat": "inspect", "intent": f"inspect_{base}",
            "desc": f"inspect {bname} structure/api/tests",
            "caps": ["inspect", "discover"], "req_tools": [], "req_subsys": [bname], "pre": [],
            "proc": [{"op": "read", "path": f"{bname}/pyproject.toml"}, {"op": "glob", "pat": f"{bname}/**/*.py"}],
            "in": {"schema": {}, "req": []},
            "out": {"schema": {"api": {"t": "obj"}}},
            "ver": [{"chk": "structure_mapped"}], "fail": [],
            "deps": [], "comp": [sid], "tags": [base, "subsystem", "inspect"], "cx": 0.25, "eff": 0.95, "side": [], "inv": []
        })
    # test
    sid3 = f"mem20.subsys.{base}.test.v1"
    if not any(s['id'] == sid3 for s in skills):
        add_skill({
            "id": sid3, "ns": f"mem20.subsys.{base}", "cat": "test", "intent": f"test_{base}",
            "desc": f"run tests for {bname}",
            "caps": ["test", "verify"], "req_tools": [], "req_subsys": [bname], "pre": [],
            "proc": [{"op": "exec", "cmd": f"python -m pytest {bname} -q"}],
            "in": {"schema": {}, "req": []},
            "out": {"schema": {"passed": {"t": "int"}, "failed": {"t": "int"}}},
            "ver": [{"chk": "tests_green_or_reported"}], "fail": [{"e": "failures", "rec": "debug"}],
            "deps": [], "comp": [], "tags": [base, "subsystem", "test"], "cx": 0.3, "eff": 0.95, "side": [], "inv": []
        })

# Add workflow skills
workflows = [
    ("mem20.workflow.dev.cycle.v1", "mem20.workflow.dev", "dev_cycle", "full dev cycle: understand,test,change,verify", ["understand","test","change","verify"]),
    ("mem20.workflow.debug.trace.v1", "mem20.workflow.debug", "debug_trace", "trace errors to root cause with evidence", ["read","trace","test","fix"]),
    ("mem20.workflow.conform.check.v1", "mem20.workflow.conform", "conform_check", "run conformance gates", ["counts","versions","docs","tests","manifests","sdks","benchmarks"]),
    ("mem20.workflow.deploy.mcp.v1", "mem20.workflow.deploy", "deploy_mcp", "deploy/configure mem20 mcp", ["config","start","health","verify"]),
    ("mem20.workflow.integrate.cross.v1", "mem20.workflow.integrate", "integrate_cross", "integrate across subsystems", ["discover","wire","test","verify"]),
]
for wid, wns, wint, wdesc, wcaps in [(w[0],w[1],w[2],w[3],w[4]) for w in workflows]:
    if not any(s['id']==wid for s in skills):
        add_skill({
            "id": wid, "ns": wns, "cat": "workflow", "intent": wint,
            "desc": wdesc, "caps": wcaps, "req_tools": [], "req_subsys": [], "pre": [],
            "proc": [{"op": "step", "n": i+1, "act": c} for i,c in enumerate(wcaps)],
            "in": {"schema": {"target": {"t": "str", "req": True}}, "req": ["target"]},
            "out": {"schema": {"ok": {"t": "bool"}}},
            "ver": [{"chk": "complete"}], "fail": [{"e": "blocked", "rec": "unblock_fix"}],
            "deps": [], "comp": [], "tags": wcaps + ["workflow"], "cx": 0.5, "eff": 0.95, "side": [], "inv": []
        })

# Add procedural skills
for name in ["mem20.procedural.list.v1", "mem20.procedural.execute.v1", "mem20.procedural.learn.v1"]:
    intent = name.split('.')[2]
    if not any(s['id']==name for s in skills):
        add_skill({
            "id": name, "ns": "mem20.procedural", "cat": "procedural", "intent": intent,
            "desc": f"procedural skill operation: {intent}",
            "caps": ["procedural", intent], "req_tools": [f"procedural_{intent}_skill" if intent!='list' else "procedural_list_skills"], "req_subsys": ["procedural"],
            "pre": [], "proc": [{"op": "call", "tool": f"procedural_{intent}_skill" if intent not in ['list'] else "procedural_list_skills"}],
            "in": {"schema": {}, "req": []}, "out": {"schema": {"ok": {"t": "bool"}}},
            "ver": [{"chk": "ok"}], "fail": [], "deps": [], "comp": [], "tags": ["procedural", intent], "cx": 0.3, "eff": 0.95, "side": [], "inv": []
        })

def build_index(skills_list):
    # Build inverted index
    term_to_ids = {}
    for s in skills_list:
        terms = set()
        terms.add(s['id'])
        terms.add(s['ns'])
        terms.add(s['cat'])
        terms.add(s['intent'])
        for t in s.get('tags', []):
            terms.add(t)
        for c in s.get('caps', []):
            terms.add(c)
        # add words from desc
        for w in s['desc'].replace('-', ' ').replace('_', ' ').split():
            if len(w) > 2:
                terms.add(w.lower())
        for t in terms:
            term_to_ids.setdefault(t, []).append(s['id'])
    return {
        "format": "agent-skill-index-v1",
        "gen": datetime.now(timezone.utc).isoformat(),
        "count": len(skills_list),
        "inv": term_to_ids,
        "by_ns": {},
        "by_cat": {}
    }

def main():
    idx = build_index(skills)
    # write jsonl
    jsonl_path = OUT_DIR / "skills.catalog.agent.jsonl"
    with open(jsonl_path, 'w') as f:
        for s in skills:
            f.write(json.dumps(s) + '\n')
    # write full catalog
    cat_path = OUT_DIR / "skills.catalog.agent.json"
    with open(cat_path, 'w') as f:
        json.dump({"meta": {"ver": CATALOG_VERSION, "count": len(skills), "gen": datetime.now(timezone.utc).isoformat(), "agent_only": True, "ai_searchable": True}, "skills": skills, "index": idx}, f)
    # write index separately
    idx_path = OUT_DIR / "skills.index.agent.json"
    with open(idx_path, 'w') as f:
        json.dump(idx, f)
    # canonical output lives in toolchest/skills (OUT_DIR)
    print(f"wrote {len(skills)} skills")
    print(jsonl_path)
    print(idx_path)
    print(cat_path)

if __name__ == '__main__':
    main()

