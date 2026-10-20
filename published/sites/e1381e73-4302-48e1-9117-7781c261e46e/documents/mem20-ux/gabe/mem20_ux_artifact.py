#!/usr/bin/env python3
"""mem20 UX lane — gabe-runnable verification artifact.

Derives the tool surface twice from independent sources, reconciles the ranked
memory-surface grouping against the server's own registration, and checks that
the delivered prototype renders that surface.

gaben_export_a = "mem20_ux_artifact.py"

Every figure is computed at run time from the repository checkout and the
delivered documents. Nothing is hardcoded except the house positioning targets,
which are the values the requirement pins and which the artifact compares
against what the delivered grouping document declares.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import re
import sys
import traceback

gaben_export_a = "mem20_ux_artifact.py"

REQUIRED_TOOL_TOTAL = 257
REQUIRED_MEMORY_TOTAL = 49
REQUIRED_MARKET = {
    "tools_total": 257,
    "memory_tools": 49,
    "tam_usd": 1280000000,
    "sam_usd": 282000000,
    "som_usd": 1680000,
    "blended_acv_usd": 14000,
}


def _fail(message):
    raise RuntimeError(message)


# --------------------------------------------------------------------------
# source A — instantiate the repository's server and read its registration
# --------------------------------------------------------------------------
def runtime_registration(repo_root):
    root = pathlib.Path(repo_root).resolve()
    server_path = root / "mcp" / "server.py"
    if not server_path.is_file():
        _fail(f"server module absent at {server_path}")

    # The distribution named "mcp" shadows the repository package, so the
    # server module is loaded by path with its own package directory first.
    inserted = [str(root / "mcp"), str(root)]
    for path in reversed(inserted):
        if path not in sys.path:
            sys.path.insert(0, path)

    spec = importlib.util.spec_from_file_location("mem20_server_probe", str(server_path))
    if spec is None or spec.loader is None:
        _fail("server module could not be loaded by path")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    holder = {}
    for name, value in vars(module).items():
        if name.endswith("MCPServer") and isinstance(value, type):
            holder[name] = value
    if "Mem20MCPServer" not in holder:
        _fail(f"Mem20MCPServer absent from server module; saw {sorted(holder)}")

    server = holder["Mem20MCPServer"]()
    tools = getattr(server, "tools", None)
    if not isinstance(tools, dict):
        _fail("registered tool mapping is not a mapping")
    names = sorted(tools.keys())
    if not names:
        _fail("registered tool mapping is empty")
    return names


# --------------------------------------------------------------------------
# source B — abstract syntax tree scan of every module in the server package
# --------------------------------------------------------------------------
def static_declarations(repo_root):
    root = pathlib.Path(repo_root).resolve()
    package = root / "mcp"
    if not package.is_dir():
        _fail(f"server package absent at {package}")

    names = set()
    scanned = 0
    for path in sorted(package.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        scanned += 1

        # Some registrations assign the name to a local first, then pass the
        # variable, so the scan resolves simple one-hop string bindings.
        bound = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                    if isinstance(node.value.value, str):
                        bound[target.id] = node.value.value

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            callee = node.func
            attribute = getattr(callee, "attr", None) or getattr(callee, "id", None)
            if attribute != "Tool":
                continue
            for keyword in node.keywords:
                if keyword.arg != "name":
                    continue
                candidate = None
                if isinstance(keyword.value, ast.Name):
                    candidate = bound.get(keyword.value.id)
                else:
                    try:
                        candidate = ast.literal_eval(keyword.value)
                    except Exception:
                        candidate = None
                if isinstance(candidate, str):
                    names.add(candidate)
    if scanned == 0:
        _fail("no modules parsed under the server package")
    if not names:
        _fail("no tool declarations found by the syntax scan")
    return sorted(names)


def reconcile_sources(runtime_names, static_names):
    runtime_set = set(runtime_names)
    static_set = set(static_names)
    if runtime_set != static_set:
        absent_at_runtime = sorted(static_set - runtime_set)
        absent_in_source = sorted(runtime_set - static_set)
        _fail(
            "the two sources disagree on the tool surface: "
            f"declared but unregistered={absent_at_runtime[:8]}, "
            f"registered but undeclared={absent_in_source[:8]}"
        )
    return runtime_set


def memory_slice(tool_names):
    memory = [n for n in tool_names if n.startswith("memory_")]
    return memory


# --------------------------------------------------------------------------
# delivered documents
# --------------------------------------------------------------------------
def load_grouping(grouping_path):
    path = pathlib.Path(grouping_path)
    if not path.is_file():
        _fail(f"grouping document absent at {path}")
    document = json.loads(path.read_text(encoding="utf-8"))
    clusters = document.get("clusters")
    if not isinstance(clusters, list) or not clusters:
        _fail("grouping document carries no clusters")
    return document


def reconcile_grouping(grouping, memory_names):
    listed = []
    for cluster in grouping["clusters"]:
        tools = cluster.get("tools")
        if not isinstance(tools, list) or not tools:
            _fail(f"cluster {cluster.get('id')!r} carries no tools")
        for entry in tools:
            name = entry.get("name") if isinstance(entry, dict) else None
            if not isinstance(name, str):
                _fail(f"cluster {cluster.get('id')!r} carries an entry without a name")
            listed.append(name)

    listed_set = set(listed)
    memory_set = set(memory_names)

    missing = sorted(memory_set - listed_set)
    if missing:
        _fail(f"grouping omits registered memory tools: {missing}")

    invented = sorted(listed_set - memory_set)
    if invented:
        _fail(f"grouping introduces names the server does not register: {invented}")

    repeated = sorted({n for n in listed if listed.count(n) > 1})
    if repeated:
        _fail(f"grouping lists the same tool more than once: {repeated}")

    if len(listed) != len(memory_set):
        _fail(f"grouping covers {len(listed)} entries for {len(memory_set)} memory tools")

    return listed


def recompute_ranks(grouping):
    personas = grouping.get("personas")
    if not isinstance(personas, list) or len(personas) < 2:
        _fail("grouping carries fewer than two personas")

    share_total = 0.0
    for persona in personas:
        share = persona.get("share")
        opportunity = persona.get("opportunity")
        if not isinstance(share, (int, float)) or not isinstance(opportunity, (int, float)):
            _fail(f"persona {persona.get('id')!r} lacks numeric share or opportunity")
        share_total += float(share)
    if abs(share_total - 1.0) > 0.005:
        _fail(f"persona shares total {share_total:.4f}, expected 1.0")

    scored = []
    for cluster in grouping["clusters"]:
        affinity = cluster.get("affinity")
        if not isinstance(affinity, dict):
            _fail(f"cluster {cluster.get('id')!r} carries no affinity map")
        score = 0.0
        for persona in personas:
            key = persona["id"]
            if key not in affinity:
                _fail(f"cluster {cluster.get('id')!r} has no affinity for persona {key!r}")
            score += float(persona["share"]) * float(persona["opportunity"]) * float(affinity[key])
        scored.append((cluster["id"], score, len(cluster["tools"])))

    scored.sort(key=lambda item: (-item[1], -item[2], item[0]))
    expected_rank = {cluster_id: index + 1 for index, (cluster_id, _score, _count) in enumerate(scored)}

    delivered_rank = {}
    for cluster in grouping["clusters"]:
        rank = cluster.get("rank")
        if not isinstance(rank, int):
            _fail(f"cluster {cluster.get('id')!r} carries no integer rank")
        delivered_rank[cluster["id"]] = rank

    if expected_rank != delivered_rank:
        _fail(f"delivered ranks {delivered_rank} do not match the derived ranks {expected_rank}")

    top = scored[0][0]
    if top != "core-recall":
        _fail(f"the blended ranking does not lead with core recall; it leads with {top}")

    return expected_rank


def check_house_numbers(grouping):
    declared = grouping.get("meta", {}).get("house_numbers")
    if not isinstance(declared, dict):
        _fail("grouping document declares no house numbers")
    drift = {}
    for key, expected in REQUIRED_MARKET.items():
        actual = declared.get(key)
        if actual != expected:
            drift[key] = {"declared": actual, "required": expected}
    if drift:
        _fail(f"house positioning numbers drifted: {drift}")


def check_prototype(prototype_path, memory_names, tool_total):
    path = pathlib.Path(prototype_path)
    if not path.is_file():
        _fail(f"prototype document absent at {path}")
    text = path.read_text(encoding="utf-8", errors="ignore")

    absent = [name for name in memory_names if name not in text]
    if absent:
        _fail(f"prototype does not render these memory tools: {absent[:10]}")

    for required in (str(tool_total), str(len(memory_names))):
        if required not in text:
            _fail(f"prototype does not carry the count {required}")

    if "JaysonAIOnline" in text:
        _fail("prototype references the retired repository")

    canonical = "bythewayz66-glitch/mem20"
    if canonical not in text:
        _fail("prototype does not cite the canonical repository")

    match = re.search(r"var GROUPS = \[(.*?)\];", text, re.S)
    if not match:
        _fail("prototype carries no group totals")
    counts = [int(value) for value in re.findall(r",\s*(\d+)\]", match.group(1))]
    if not counts:
        _fail("prototype group totals could not be read")
    if sum(counts) != tool_total:
        _fail(f"prototype group totals sum to {sum(counts)}, expected {tool_total}")

    return {"groups": len(counts), "sum": sum(counts)}


# --------------------------------------------------------------------------
# orchestration
# --------------------------------------------------------------------------
def verify(repo_root, grouping_path, prototype_path):
    runtime_names = runtime_registration(repo_root)
    static_names = static_declarations(repo_root)
    reconciled = reconcile_sources(runtime_names, static_names)

    if len(reconciled) != REQUIRED_TOOL_TOTAL:
        _fail(f"the two sources agree on {len(reconciled)} tools, required {REQUIRED_TOOL_TOTAL}")

    memory_names = memory_slice(sorted(reconciled))
    if len(memory_names) != REQUIRED_MEMORY_TOTAL:
        _fail(f"the memory slice holds {len(memory_names)} tools, required {REQUIRED_MEMORY_TOTAL}")

    grouping = load_grouping(grouping_path)
    listed = reconcile_grouping(grouping, memory_names)
    ranks = recompute_ranks(grouping)
    check_house_numbers(grouping)
    prototype = check_prototype(prototype_path, memory_names, len(reconciled))

    return {
        "tools_total": len(reconciled),
        "memory_tools": len(memory_names),
        "grouping_entries": len(listed),
        "clusters": len(grouping["clusters"]),
        "leading_cluster": min(ranks, key=ranks.get),
        "prototype_group_sum": prototype["sum"],
        "prototype_groups": prototype["groups"],
    }


def main():
    if len(sys.argv) != 4:
        _fail("usage: mem20_ux_artifact.py <repo_root> <grouping_json> <prototype_html>")
    result = verify(sys.argv[1], sys.argv[2], sys.argv[3])
    for key in ("tools_total", "memory_tools", "grouping_entries", "clusters",
                "leading_cluster", "prototype_groups", "prototype_group_sum"):
        print(f"{key}={result[key]}")


def self_test(repo_root, grouping_path, prototype_path):
    """Feed an altered grouping and require the resulting error to escape."""
    document = json.loads(pathlib.Path(grouping_path).read_text(encoding="utf-8"))
    document["clusters"][0]["tools"] = document["clusters"][0]["tools"][1:]
    scratch = pathlib.Path("/tmp/mem20_ux_self_test_grouping.json")
    scratch.write_text(json.dumps(document), encoding="utf-8")

    # The refusal must remain observable, so the error is caught only to be
    # reported and then re-raised: a swallowed error would exit zero.
    try:
        verify(repo_root, str(scratch), prototype_path)
    except RuntimeError as error:
        print(f"self_test=refused ({str(error)[:90]})")
        raise
    _fail("the reconcile step accepted a grouping with a memory tool removed")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        default_repo = pathlib.Path("/tmp/mem20chk")
        base = pathlib.Path(__file__).resolve().parents[1]
        self_test(default_repo, base / "memory_surface.json", base / "prototype.html")
    else:
        try:
            main()
        except RuntimeError as error:
            print(f"REFUSED: {error}", file=sys.stderr)
            traceback.print_exc()
            raise SystemExit(2)
