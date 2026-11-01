#!/usr/bin/env python3
"""Regenerate the mem20 4.0 subsystem inventory and assignment CSV.

Walks the repo, measures every subsystem directory, assigns each to a named
agent by domain affinity, balances the leftovers by LOC load, and writes:

    docs/renovation/4.0/inventory.json
    docs/renovation/4.0/subsystem-assignments.csv

Run from the repo root:
    python3 scripts/renovation/build_inventory.py
"""
from __future__ import annotations

import ast
import csv
import json
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "docs" / "renovation" / "4.0"

NON_SUBSYSTEM = {
    "docs", "published", "plans", "tests", "bench", "benchmarks", "backups",
    "entries", "bridge", "cog", "dashboard", "reference_store", "braid_keyz",
    "mem20-orchestration", "scripts", ".github", "node_modules",
}

CORE_MODULES = {"memory_engine", "gateway", "toolchest", "mcp", "braid", "corez"}

STUB_PATTERN = re.compile(
    r"\bTODO\b|\bFIXME\b|NotImplementedError|raise\s+NotImplemented", re.MULTILINE
)

# Non-Python subsystems named explicitly in the owner directive.
EXTRA = [
    {"module": "braid", "lang": "rust", "loc": 12621, "py": 0},
    {"module": "gateway", "lang": "python", "loc": 846, "py": 3},
]

# Domain affinity: agent -> keyword fragments matched against the module name.
AGENTS = [
    ("mem20 Orchestrator", ["orchestr", "mission", "intent", "goal", "phase", "priority", "workflow", "task", "plan"]),
    ("GitHub Repo Assistant", ["versioncontrol", "reversible", "deterministic", "configuration", "migration", "recovery"]),
    ("Server Builder", ["gateway", "mcp", "runtime", "kernel", "microkernel", "fabric", "transport", "protocol", "webhook", "integration"]),
    ("Webpage Developer", ["oweb", "studio", "canvas", "visual", "dataflow", "instantapp"]),
    ("mem20-webdev", ["sitemap", "office", "shop", "kanban", "team", "fam", "box", "biz"]),
    ("mem20-frontends", ["controlz", "face", "frontend", "ambient", "presence"]),
    ("AI Engineer", ["agent", "model", "inference", "prompt", "lora", "rag", "cognitive", "memory", "recall", "episodic", "counterfactual", "skillmemory", "sensory"]),
    ("Mem20 C++ Expert", ["wasm", "hardware", "device", "energy", "battery", "edge", "locality", "compute"]),
    ("Mem20-Ruby-Expert", ["agentz_sdk", "sdk"]),
    ("Mem20-Perl-Expert", ["lang", "modality", "compiler", "intentto"]),
    ("mem20-sybsystems", ["scheduler", "resource", "governor", "healing", "fault", "health", "selfoptimizing", "selftuning", "roaming", "workload"]),
    ("Mem20 Benchmark Dataset Builder", ["benchmark", "evaluat", "arena", "stress"]),
    ("Experiment Tracker", ["experiment", "tracker", "twin", "simulat", "outcome"]),
    ("Market Research", ["market", "opportunity", "research", "federated", "scout", "acquisition"]),
    ("Pricing Analyst", ["pricing", "econom", "cost", "bundle", "exchange"]),
    ("Finance Assistant", ["finance", "revenue", "leak", "unit", "businessmodel"]),
    ("Growth Hacker", ["growth", "loyalty", "challenge", "community", "multibrand", "swarm", "productled", "compounding"]),
    ("mem20 GTM Team Lead", ["offer", "gtm", "deal", "sales", "customer", "lifecycle", "demand", "forecast"]),
    ("Mem20 Content Creator", ["content", "narrative", "dialogue", "quest", "story", "style", "localization"]),
    ("Slides Assistant", ["slide", "deck", "presentation", "art", "rigging", "animation", "audio", "music", "voice"]),
    ("UX Researcher", ["human", "cowork", "apprentice", "personal", "motivation", "focus", "onboard", "aionbord"]),
    ("Analytics Reporter", ["analytics", "telemetry", "event", "stream", "observ", "metric"]),
    ("Mem20-naration", ["narration", "radio", "media", "demo", "demonstration"]),
    ("Super Agent", ["verify", "ops", "secret", "security", "secure", "identity", "qa", "adversarial", "green", "unikit", "corez", "toolchest", "memory_engine"]),
]

# Waves are curated by risk and dependency (see RENOVATION_PLAN.md section 4),
# NOT derived from LOC. Wave 1 is the substrate every later wave imports.
WAVE_1 = [
    "Server Builder", "AI Engineer", "Super Agent", "mem20 Orchestrator",
    "GitHub Repo Assistant", "mem20-sybsystems", "Mem20 C++ Expert", "Analytics Reporter",
]
WAVE_2 = [
    "Webpage Developer", "mem20-webdev", "mem20-frontends", "Mem20-Perl-Expert",
    "Mem20-Ruby-Expert", "Mem20 Benchmark Dataset Builder", "Experiment Tracker",
    "mem20 GTM Team Lead",
]
WAVE_3 = [
    "Market Research", "Pricing Analyst", "Finance Assistant", "Growth Hacker",
    "Mem20 Content Creator", "Slides Assistant", "UX Researcher", "Mem20-naration",
]

# Wave 1 is the substrate: the modules every later subsystem must import to
# satisfy criterion 6, plus the MCP/gateway registration surface (criterion 7).
WAVE_1_SUBSYSTEMS = {
    "mcp", "mem20_mcp", "gateway", "memory_engine", "toolchest", "braid",
    "mem20corez", "mem20agentz", "mem20orcaz", "mem20meshz", "mem20verify",
    "mem20ops", "mem20dreamz", "mem20crewz", "mem20kilnz",
    "mem20versioncontrollargeassetandrecoverypipelinez",
    "mem20reversibleexecutiongraphz",
    "mem20selfhealingruntimecivilizationz",
    "mem20universalhealthnervoussystemz",
    "mem20wasmz", "mem20eventstreamsuperhighwayz",
    "mem20crossruntimeeventlatticez", "mem20apishapeshiftinggatewayz",
    "mem20-orchestration",
}


# Explicit owner overrides. The keyword matcher is a fallback, not an authority:
# these are the modules whose ownership is decided by domain expertise, and a
# substring collision must never move them.
OVERRIDES = {
    # substrate / server surface
    "mcp": "Server Builder",
    "mem20_mcp": "Server Builder",
    "gateway": "Server Builder",
    "mem20meshz": "Server Builder",
    "mem20apishapeshiftinggatewayz": "Server Builder",
    "mem20fabricz": "Server Builder",
    "mem20temporaldatabasefabricz": "Server Builder",
    # memory + agent core
    "memory_engine": "AI Engineer",
    "mem20agentz": "AI Engineer",
    "mem20dreamz": "AI Engineer",
    "mem20crewz": "AI Engineer",
    "mem20kilnz": "AI Engineer",
    "mem20episodicmemorygraphz": "AI Engineer",
    "mem20predictiverecallenginez": "AI Engineer",
    "mem20counterfactualmemorysimulatorz": "AI Engineer",
    "mem20memorytimemachinez": "AI Engineer",
    "mem20sensorymemoryingestz": "AI Engineer",
    "mem20skillmemorytransferz": "AI Engineer",
    # verification / ops / core
    "toolchest": "Super Agent",
    "mem20corez": "Super Agent",
    "mem20verify": "Super Agent",
    "mem20ops": "Super Agent",
    "mem20secretz": "Super Agent",
    "mem20greenz": "Super Agent",
    "mem20unikitz": "Super Agent",
    "mem20adversarialqacrewz": "Super Agent",
    # orchestration
    "mem20orcaz": "mem20 Orchestrator",
    "mem20-orchestration": "mem20 Orchestrator",
    "mem20prioritycollisionresolverz": "mem20 Orchestrator",
    "mem20dynamicphasereplannerz": "mem20 Orchestrator",
    # git / reversibility
    "mem20versioncontrollargeassetandrecoverypipelinez": "GitHub Repo Assistant",
    "mem20reversibleexecutiongraphz": "GitHub Repo Assistant",
    "mem20deterministicconfigurationgraphz": "GitHub Repo Assistant",
    "mem20zerodowntimemigrationbrainz": "GitHub Repo Assistant",
    # self-healing / scheduling
    "mem20selfhealingruntimecivilizationz": "mem20-sybsystems",
    "mem20universalhealthnervoussystemz": "mem20-sybsystems",
    "mem20selfhealingplansz": "mem20-sybsystems",
    "mem20selftuningresourcegovernorz": "mem20-sybsystems",
    "mem20roamingworkloadschedulerz": "mem20-sybsystems",
    "mem20batteryawareagentschedulerz": "mem20-sybsystems",
    # native / edge
    "braid": "Mem20 C++ Expert",
    "mem20wasmz": "Mem20 C++ Expert",
    "mem20datalocalityoptimizerz": "Mem20 C++ Expert",
    "mem20energyawarecomputemigrationz": "Mem20 C++ Expert",
    # events / telemetry
    "mem20eventstreamsuperhighwayz": "Analytics Reporter",
    "mem20crossruntimeeventlatticez": "Analytics Reporter",
    "mem20realtimeeventautopilotz": "Analytics Reporter",
    # web / frontend
    "mem20owebz": "Webpage Developer",
    "mem20studioz": "Webpage Developer",
    "mem20visualdataflowcomposerz": "Webpage Developer",
    "mem20instantappsynthesisz": "Webpage Developer",
    "mem20controlz": "mem20-frontends",
    "mem20facez": "mem20-frontends",
    "mem20realtimeteampresencez": "mem20-frontends",
    "mem20sitemapz": "mem20-webdev",
    "mem20officez": "mem20-webdev",
    "mem20shopz": "mem20-webdev",
    "mem20kanbanz": "mem20-webdev",
    "mem20teamz": "mem20-webdev",
    # language / compiler
    "mem20langz": "Mem20-Perl-Expert",
    "mem20modalitybridgez": "Mem20-Perl-Expert",
    "mem20intentcompilerz": "Mem20-Perl-Expert",
    "mem20intenttomissioncompilerz": "Mem20-Perl-Expert",
    # sdk
    "mem20agentz_sdk": "Mem20-Ruby-Expert",
    # benchmark / experiment
    "mem20benchmarkz": "Mem20 Benchmark Dataset Builder",
    "mem20syntheticevaluatorarenaz": "Mem20 Benchmark Dataset Builder",
    "mem20executabledesignstresslabz": "Mem20 Benchmark Dataset Builder",
    "mem20twinz": "Experiment Tracker",
    "mem20executiondigitaltwinz": "Experiment Tracker",
    "mem20outcomesimulationlabz": "Experiment Tracker",
    # gtm / finance
    "mem20offergenomeenginez": "mem20 GTM Team Lead",
    "mem20offerassemblyfabricz": "mem20 GTM Team Lead",
    "mem20customerlifecycleenginez": "mem20 GTM Team Lead",
    "mem20revenueleakhunterz": "Finance Assistant",
    "mem20businessmodelsimulatorz": "Finance Assistant",
    "mem20uniteconomicsautopilotz": "Pricing Analyst",
    "mem20servicebundlingenginez": "Pricing Analyst",
    "mem20resourceexchangemarketz": "Pricing Analyst",
    "mem20productledgrowthsimulatorz": "Growth Hacker",
    "mem20crossproductloyaltygraphz": "Growth Hacker",
    "mem20communitychallengeenginez": "Growth Hacker",
    "mem20opportunityradarz": "Market Research",
    "mem20federatedresearchgridz": "Market Research",
    "mem20acquisitionandpartnershipscoutz": "Market Research",
    # content / media
    "mem20dynamicnarrativeenginez": "Mem20 Content Creator",
    "mem20narrativedialogueandlocalizationpipelinez": "Mem20 Content Creator",
    "mem20styleguideagentz": "Mem20 Content Creator",
    "mem20audiovoiceandmusicpipelinez": "Slides Assistant",
    "mem202dand3dartproductionoptimizationpipelinez": "Slides Assistant",
    "mem20rigginganimationandmotionpipelinez": "Slides Assistant",
    "mem20humanagentcoworkcanvasz": "UX Researcher",
    "mem20personalworkflowtwinz": "UX Researcher",
    "mem20playermotivationtwinz": "UX Researcher",
    "mem20liveprojectdemonstrationenginez": "Mem20-naration",
    "mem20ambientteamradioz": "Mem20-naration",
}


def python_files(path: Path) -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__", "node_modules", ".venv"}]
        for f in filenames:
            if f.endswith(".py"):
                out.append(Path(dirpath) / f)
    return out


def measure(name: str) -> dict | None:
    path = REPO_ROOT / name
    pys = python_files(path)
    if len(pys) < 5:
        return None
    loc = stubs = 0
    imported: set[str] = set()
    for p in pys:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        loc += len(text.splitlines())
        if STUB_PATTERN.search(text):
            stubs += 1
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                mods = [node.module]
            for m in mods:
                top = m.split(".")[0]
                if top != name and (top.startswith("mem20") or top in CORE_MODULES):
                    imported.add(top)
    tests = [p for p in pys if "test" in p.name.lower() or "tests" in p.parts]
    return {
        "module": name,
        "lang": "python",
        "py": len(pys),
        "loc": loc,
        "stub_files": stubs,
        "tests": len(tests),
        "readme": (path / "README.md").is_file(),
        "cli": any(p.name in {"cli.py", "__main__.py", "main.py"} for p in pys) or (path / "cli").is_dir(),
        "cross_modules": len(imported),
        "cross_sample": sorted(imported)[:8],
    }


def assign(rows: list[dict]) -> None:
    chosen: dict[str, str] = {}
    leftovers: list[str] = []
    for r in rows:
        m = r["module"].lower()
        if r["module"] in OVERRIDES:
            chosen[r["module"]] = OVERRIDES[r["module"]]
            continue
        best = None
        for agent, keys in AGENTS:
            for k in keys:
                if k in m and (best is None or len(k) > best[1]):
                    best = (agent, len(k))
        if best:
            chosen[r["module"]] = best[0]
        else:
            leftovers.append(r["module"])

    load = {a: 0 for a, _ in AGENTS}
    by_name = {r["module"]: r for r in rows}
    for mod, agent in chosen.items():
        load[agent] += by_name[mod]["loc"]
    for mod in sorted(leftovers, key=lambda m: -by_name[m]["loc"]):
        agent = min(load, key=lambda k: load[k])
        chosen[mod] = agent
        load[agent] += by_name[mod]["loc"]

    for r in rows:
        r["owner"] = chosen[r["module"]]


def slug(agent: str) -> str:
    return agent.lower().replace(" ", "-").replace("++", "pp").replace(".", "")


def main() -> int:
    rows = []
    for d in sorted(REPO_ROOT.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in NON_SUBSYSTEM:
            continue
        m = measure(d.name)
        if m:
            rows.append(m)

    have = {r["module"] for r in rows}
    for e in EXTRA:
        if e["module"] not in have:
            rows.append({
                "module": e["module"], "lang": e["lang"], "py": e["py"], "loc": e["loc"],
                "stub_files": 0, "tests": 0, "readme": True, "cli": True,
                "cross_modules": 0, "cross_sample": [],
            })

    assign(rows)

    wave = {}
    for a in WAVE_1:
        wave[a] = 1
    for a in WAVE_2:
        wave[a] = 2
    for a in WAVE_3:
        wave[a] = 3
    missing = [a for a, _ in AGENTS if a not in wave]
    if missing:
        raise SystemExit(f"agents missing a wave assignment: {missing}")

    for r in rows:
        # Wave 1 is exactly the substrate set. Everything else follows its
        # owner's wave, so each agent finishes its own portfolio in order.
        if r["module"] in WAVE_1_SUBSYSTEMS:
            r["wave"] = 1
        elif r["owner"] in WAVE_1 or r["owner"] in WAVE_2:
            r["wave"] = 2
        else:
            r["wave"] = 3
        r["branch"] = f"feat/4.0-{slug(r['owner'])}-{r['module'].replace('_', '-')}"

    rows.sort(key=lambda r: (-r["loc"], r["module"]))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "inventory.json").write_text(json.dumps(rows, indent=1))

    with (OUT_DIR / "subsystem-assignments.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["subsystem", "lang", "py_files", "loc", "existing_tests", "has_readme",
                    "has_cli", "cross_module_imports", "stub_files", "owner", "wave", "branch"])
        for r in rows:
            w.writerow([r["module"], r["lang"], r["py"], r["loc"], r["tests"], r["readme"],
                        r["cli"], r["cross_modules"], r["stub_files"], r["owner"], r["wave"], r["branch"]])

    print(f"{len(rows)} subsystems written to {OUT_DIR}")
    for a, _ in AGENTS:
        ms = [r for r in rows if r["owner"] == a]
        print(f"  {a:34s} n={len(ms):3d} loc={sum(m['loc'] for m in ms):6d} wave={wave[a]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
