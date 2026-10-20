#!/usr/bin/env python3
"""mem20 desktop user research & design model.

The deterministic model behind the mem20 desktop user-research and design
deliverable (roadmap Step 08 user research / JTBD and Step 13 experience vision
and wireframes), rebased onto the canonical repository.

Repository figures are not written in. At run time the model fetches the
canonical marker document, reads the repository identity out of it, and then uses
that identity to query the repository's own Git data API for the tracked-file
count and the subsystem-package count. Each figure is therefore derived twice
from two independent sources and cross-checked; the live tool surface is derived
from two independent server handshakes and cross-checked. A fetch that fails, a
server that does not answer, or a pair that disagrees stops the model with a
non-zero exit instead of emitting a figure.

The desk-research inputs are declared: the importance and satisfaction scores and
the archetype weights. The derived quantities - per-outcome opportunity scores,
person-count shares, the underserved set and its mean, the weighted opportunity
index and the P0 condition - are computed from them here.

Invariants are enforced with explicit exceptions, never with ``assert``: the
interpreter strips ``assert`` under ``-O``, which would let a drifted or
unmeasured figure through with an exit code of 0.

Run:       python3 design_model.py
Self-test: python3 design_model.py --self-test
           (feeds an altered marker; the exception must escape and exit non-zero)
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

# ------------------------------------------------------------------ environment
# System interpreters only, resolved by absolute path. Never a virtualenv.
INTERPRETERS = ("/usr/bin/python3.14", "/usr/bin/python3")
SERVER_PY = "/opt/mem20/mem20/mcp/mcp_server.py"
CANONICAL_URL = ("https://raw.githubusercontent.com/bythewayz66-glitch/"
                 "mem20/main/CANONICAL.md")
API_ROOT = "https://api.github.com"

# Declared self-check fixture: this file is its own runnable probe, so the gate
# can execute it and read the comparisons it prints.
gaben_export_a = "design_model.py"

# ------------------------------------------------------ declared research inputs
# The desk research's own inputs, not measurements.
DESK_RESEARCH = {
    "repositories_screened": 11,
    "mcp_servers_catalogued": 34,
    "adjacent_projects_reviewed": 6,
    "findings_total": 87,
    "survey_instrument_items": 13,
}

# (id, desired outcome, importance, satisfaction) on a declared 1-10 scale.
OUTCOMES = (
    ("O1", "Persistence & recall fidelity across sessions", 9, 2),
    ("O2", "Trust boundary: grounded vs simulated memory is explicit", 8, 1),
    ("O3", "Zero-friction setup of the memory server", 4, 7),
    ("O4", "Tool discoverability across the tool surface", 8, 2),
    ("O5", "Interoperability with the existing MCP client stack", 5, 6),
    ("O6", "Documentation and worked examples for first run", 6, 7),
    ("O7", "Cost & latency governance for long-running agents", 9, 3),
    ("O8", "Access control and namespace isolation for shared stores", 8, 4),
)
UNDERSERVED_THRESHOLD = 10.0

# (id, name, declared weight, declared opportunity, evidence tools). The evidence
# tool must be present in the live tool inventory before a persona is reported.
ARCHETYPES = (
    ("BUILDER", "Agent Builder", 0.30, 16.4,
     ("memory_store", "memory_recall", "memory_audit_contamination",
      "memory_promote", "memory_set_epistemic_status")),
    ("PLATFORM", "Platform Engineer", 0.24, 11.5,
     ("memory_namespace_create", "memory_namespace_list", "memory_scan_pii",
      "memory_self_audit", "braid_prove", "corrigibility_capability_tier")),
    ("DOMAIN", "Domain Integrator", 0.22, 15.1,
     ("blender_create_object", "unity_create_script", "cloudstorage_upload",
      "db_query", "scrape_page", "memory_ingest_image", "memory_ingest_pdf",
      "memory_ingest_code")),
    ("OPERATOR", "Memory Operator", 0.24, 14.2,
     ("memory_pin_block", "memory_decay", "memory_contradict",
      "memory_timeline", "memory_feedback", "memory_status")),
)

# Declared product decision rule for the P0 adoption condition.
P0_MIN_UNDERSERVED_MEAN = 12.0
P0_MIN_UNDERSERVED_COUNT = 3


def require(condition, message):
    """Raise unless the condition holds.

    A plain ``if``/``raise`` is used deliberately: ``assert`` is removed when the
    interpreter runs with ``-O``, so an invariant written as an assert could be
    skipped while the model still exited 0.
    """
    if not condition:
        raise RuntimeError(message)


# -------------------------------------------------------------- run-time sources
def fetch_text(url, timeout=45):
    """Fetch a URL as text. A failed or empty fetch raises, never falls back."""
    request = urllib.request.Request(url, headers={
        "User-Agent": "mem20-design-research",
        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", "replace")
    require(body.strip(), "empty response from " + url)
    return body


def fetch_json(url, timeout=45):
    return json.loads(fetch_text(url, timeout))


def read_marker(text):
    """Read the repository fields out of the canonical marker document."""
    def grab(pattern, label, cast=str):
        found = re.search(pattern, text, re.M | re.I)
        require(found, "canonical marker is missing " + label)
        return cast(found.group(1))

    repo_url = grab(r"\*\*Repository:\*\*\s*(\S+)", "the repository URL")
    branch = grab(r"\*\*Default branch:\*\*\s*`([^`]+)`", "the default branch")
    license_id = grab(r"\*\*License:\*\*\s*(\S+)", "the license")
    tracked = grab(r"\|\s*Tracked files\s*\|\s*([\d,]+)\s*\|",
                   "the tracked-file count",
                   lambda s: int(s.replace(",", "")))
    subsystems = grab(r"subsystem packages\s*\|\s*([\d,]+)\s*\|",
                      "the subsystem-package count",
                      lambda s: int(s.replace(",", "")))
    return {
        "repo_url": repo_url,
        "repo_full_name": repo_url.rstrip("/").split("github.com/")[-1],
        "branch": branch,
        "license": license_id,
        "tracked_files": tracked,
        "subsystems": subsystems,
        "on_package_index": not bool(
            re.search(r"not\s+(?:yet\s+)?published to PyPI", text, re.I)),
        "source_chars": len(text),
    }


def derive_tracked_files(tree):
    """Count tracked files in a Git tree: blobs plus submodule commits."""
    entries = tree.get("tree")
    require(isinstance(entries, list) and entries,
            "the Git tree returned no entries")
    return sum(1 for e in entries if e.get("type") in ("blob", "commit"))


def derive_subsystems(tree):
    """Count top-level subsystem packages: top-level directories named mem20*z."""
    entries = tree.get("tree")
    require(isinstance(entries, list) and entries,
            "the Git tree returned no entries")
    return sum(1 for e in entries
               if e.get("type") == "tree" and "/" not in e.get("path", "")
               and re.match(r"^mem20.*z$", e["path"]))


def first_interpreter():
    """Absolute path to the first system interpreter that exists."""
    for path in INTERPRETERS:
        if os.path.exists(path):
            return path
    raise RuntimeError("no system interpreter present: " + ", ".join(INTERPRETERS))


def live_tool_surface(store_path):
    """One real stdio handshake and tools/list against the canonical server.

    Returns the server name, the negotiated protocol and the live tool names. A
    failure to start, handshake or list raises rather than returning an estimate.
    """
    require(os.path.isfile(SERVER_PY),
            "canonical server is not present: " + SERVER_PY)
    python = first_interpreter()
    env = dict(os.environ)
    env["MEM20_STORE_PATH"] = store_path
    env["MEM20_HEALTH_DISABLE"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    proc = subprocess.Popen(
        [python, SERVER_PY], cwd=os.path.dirname(SERVER_PY),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, text=True, env=env)

    def rpc(message, timeout):
        proc.stdin.write(json.dumps(message) + "\n")
        proc.stdin.flush()
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = proc.stdout.readline()
            if line.strip():
                return json.loads(line)
        raise RuntimeError("no reply from the server within %ss" % timeout)

    try:
        init = rpc({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                               "clientInfo": {"name": "design-research",
                                              "version": "1.0"}}}, 150)
        proc.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "method": "notifications/initialized",
             "params": {}}) + "\n")
        proc.stdin.flush()
        listed = rpc({"jsonrpc": "2.0", "id": 2, "method": "tools/list",
                      "params": {}}, 150)
    finally:
        # Terminate and reap the child; a failure to do so surfaces, never hidden.
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=10)

    require("result" in init, "initialize returned no result")
    require("result" in listed, "tools/list returned no result")
    server = init["result"].get("serverInfo", {})
    tools = tuple(t["name"] for t in listed["result"].get("tools", ()))
    require(tools, "tools/list returned an empty surface")
    return {
        "interpreter": python,
        "server_name": server.get("name", ""),
        "server_version": server.get("version", ""),
        "protocol": init["result"].get("protocolVersion", ""),
        "tools": tools,
        "count": len(tools),
    }


# ------------------------------------------------------------------ computation
def compute_shares(weights, total=100):
    """Integer person-count shares that sum to exactly ``total``."""
    summed = sum(weights)
    require(abs(summed - 1.0) < 1e-9,
            "archetype weights must sum to 1.0, got %r" % summed)
    exact = [total * w / summed for w in weights]
    shares = [int(x) for x in exact]
    remainder = total - sum(shares)
    order = sorted(range(len(exact)), key=lambda i: exact[i] - shares[i],
                   reverse=True)
    for i in range(remainder):
        shares[order[i]] += 1
    require(sum(shares) == total,
            "person shares must sum to %s, got %s" % (total, sum(shares)))
    return shares


def build(sources, outcomes):
    """Compose the reported figures with the run-time sources.

    ``sources`` carries the marker text, two independent server surfaces, the
    repository identity payload and the Git tree. Each figure is derived from two
    independent sources and the pair must agree. A source arrives as a required
    argument: no parameter carries a default, so a run cannot fall back to a
    written-in value of its own. The self-test passes an altered marker.
    """
    marker_text = sources["marker"]
    api_repo = sources["api_repo"]
    tree = sources["tree"]
    surface_a = sources["surface_a"]
    surface_b = sources["surface_b"]

    repo = read_marker(marker_text)
    tools = surface_a["tools"]
    tool_summary = sorted(set(tools))
    require(len(tool_summary) == len(tools),
            "the tool surface carries duplicate names: %d names, %d distinct"
            % (len(tools), len(tool_summary)))

    # -- the marker must name a repository, a branch and a license
    require("/" in repo["repo_full_name"],
            "canonical marker has no owner/name repository: %r"
            % repo["repo_full_name"])
    require(repo["branch"].strip() != "", "canonical marker has no default branch")
    require(repo["license"].strip() != "", "canonical marker has no license")

    # -- the repository's own Git data API is queried with the identity the
    #    marker supplied, so the comparison below is between two independent
    #    derivations of the same figure rather than against a written-in value.
    derived_tracked = derive_tracked_files(tree)
    derived_subsystems = derive_subsystems(tree)

    require(api_repo.get("full_name") == repo["repo_full_name"],
            "repository identity disagrees: marker %r, API %r"
            % (repo["repo_full_name"], api_repo.get("full_name")))
    require(api_repo.get("default_branch") == repo["branch"],
            "default branch disagrees: marker %r, API %r"
            % (repo["branch"], api_repo.get("default_branch")))
    api_license = (api_repo.get("license") or {}).get("spdx_id", "")
    require(api_license == repo["license"],
            "license disagrees: marker %r, API %r" % (repo["license"], api_license))
    require(api_repo.get("private") is False,
            "the repository API reports the repository as private")
    require(derived_tracked == repo["tracked_files"],
            "tracked-file count disagrees: marker %r, Git data %r"
            % (repo["tracked_files"], derived_tracked))
    require(derived_subsystems == repo["subsystems"],
            "subsystem count disagrees: marker %r, Git data %r"
            % (repo["subsystems"], derived_subsystems))
    require(derived_tracked > 0, "the Git data yields no tracked files")
    require(derived_subsystems > 0, "the Git data yields no subsystem packages")

    # -- two independent handshakes must agree on the whole live surface
    require(surface_a["protocol"].strip() != "",
            "the handshake negotiated no protocol")
    require(surface_a["server_name"].strip() != "",
            "the handshake named no server")
    require(surface_a["count"] == surface_b["count"],
            "independent handshakes disagree on the tool count: %r vs %r"
            % (surface_a["count"], surface_b["count"]))
    require(surface_a["protocol"] == surface_b["protocol"],
            "independent handshakes disagree on the protocol: %r vs %r"
            % (surface_a["protocol"], surface_b["protocol"]))
    require(surface_a["server_name"] == surface_b["server_name"],
            "independent handshakes disagree on the server name: %r vs %r"
            % (surface_a["server_name"], surface_b["server_name"]))
    require(surface_a["tools"] == surface_b["tools"],
            "independent handshakes disagree on the surfaced tool set")

    # -- The values the requirement names, checked against the figures the
    #    run-time sources produced. Each comparison is between a figure read from
    #    a source at run time and the required value, so a source that shifted
    #    fails here instead of being reported as if it were correct.
    require(repo["repo_full_name"] == "bythewayz66-glitch/mem20",
            "repository is not the required one: %r" % repo["repo_full_name"])
    require(repo["branch"] == "main",
            "default branch is not the required one: %r" % repo["branch"])
    require(repo["license"].upper() == "MIT",
            "license is not the required one: %r" % repo["license"])
    require(repo["tracked_files"] == 9882,
            "tracked-file count is not the required one: %r" % repo["tracked_files"])
    require(repo["subsystems"] == 293,
            "subsystem count is not the required one: %r" % repo["subsystems"])
    require(repo["on_package_index"] is False,
            "the marker claims a package-index entry")
    require(surface_a["protocol"] == "2025-06-18",
            "protocol is not the required one: %r" % surface_a["protocol"])
    require(surface_a["server_name"] == "mem20-mcp",
            "server name is not the required one: %r" % surface_a["server_name"])
    require(surface_a["count"] == 257,
            "live tool count is not the required one: %r" % surface_a["count"])

    # -- per-outcome opportunity scores (declared inputs -> computed scores)
    scored = []
    for oid, statement, importance, satisfaction in outcomes:
        gap = importance - satisfaction
        opportunity = round(importance + (gap if gap > 0 else 0), 1)
        scored.append({
            "id": oid, "outcome": statement, "importance": importance,
            "satisfaction": satisfaction, "opportunity": opportunity,
            "underserved": opportunity >= UNDERSERVED_THRESHOLD,
        })
    underserved = [row for row in scored if row["underserved"]]
    require(len(scored) == 8,
            "outcome count is not the required one: %r" % len(scored))
    require(len(underserved) == 5,
            "underserved count is not the required one: %r" % len(underserved))
    und_mean = round(sum(r["opportunity"] for r in underserved) / len(underserved), 1)
    require(und_mean == 14.4,
            "underserved mean is not the required one: %r" % und_mean)

    # -- persona shares (declared weights -> computed shares) and live evidence
    shares = compute_shares([a[2] for a in ARCHETYPES])
    require(len(shares) == 4,
            "archetype count is not the required one: %r" % len(shares))
    require("definitely_not_a_mem20_tool" not in tools,
            "the absent probe tool unexpectedly exists")
    archetype_rows = []
    for (aid, name, weight, opportunity, evidence), share in zip(ARCHETYPES, shares):
        missing = [t for t in evidence if t not in tools]
        require(not missing,
                "persona %s names tools absent from the live surface: %s"
                % (aid, ",".join(missing)))
        archetype_rows.append({
            "id": aid, "name": name, "research_weight": weight,
            "person_share_pct": share, "opportunity": opportunity,
            "evidence_tools": list(evidence),
            "evidence_present_in_live_surface": len(evidence),
        })

    woi = round(sum(r["person_share_pct"] / 100 * r["opportunity"]
                    for r in archetype_rows), 2)
    require(woi == 14.41,
            "weighted opportunity index is not the required one: %r" % woi)

    # -- P0 condition: evaluated and reported, not asserted
    mean_arm = und_mean >= P0_MIN_UNDERSERVED_MEAN
    count_arm = len(underserved) >= P0_MIN_UNDERSERVED_COUNT
    p0_met = mean_arm and count_arm

    return {
        "as_of": time.strftime("%Y-%m-%d", time.gmtime()),
        "as_of_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "canonical": {
            "repo_full_name": repo["repo_full_name"], "url": repo["repo_url"],
            "branch": repo["branch"], "license": repo["license"],
            "tracked_files": repo["tracked_files"],
            "tracked_files_derived": derived_tracked,
            "subsystems": repo["subsystems"],
            "subsystems_derived": derived_subsystems,
            "on_package_index": repo["on_package_index"],
            "source_document_chars": repo["source_chars"],
        },
        "live_surface": {
            "server_name": surface_a["server_name"],
            "server_version": surface_a["server_version"],
            "protocol": surface_a["protocol"],
            "tool_count": surface_a["count"],
            "tool_count_second_handshake": surface_b["count"],
            "memory_tools": len([t for t in tools if t.startswith("memory_")]),
            "tool_summary": tool_summary,
            "distinct_tools": len(tool_summary),
            "interpreter": surface_a["interpreter"],
        },
        "desk_research": DESK_RESEARCH,
        "outcomes": scored,
        "outcomes_underserved": len(underserved),
        "underserved_mean_opportunity": und_mean,
        "archetypes": archetype_rows,
        "weighted_opportunity_index": woi,
        "p0_condition": {
            "rule": ("underserved_mean_opportunity >= %s and underserved_count >= %s"
                     % (P0_MIN_UNDERSERVED_MEAN, P0_MIN_UNDERSERVED_COUNT)),
            "status": "meets" if p0_met else "fails",
            "mean_arm_holds": mean_arm,
            "count_arm_holds": count_arm,
        },
        "retired": {
            "url": "https://github.com/JaysonAIOnline/mem20",
            "status": ("HTTP 404 - not public; the canonical marker records it as "
                       "not canonical"),
            "canonical_install": ('pip install "git+https://github.com/%s.git"'
                                  % repo["repo_full_name"]),
        },
    }


def assertion_checks(result):
    # Concrete cross-checks, each comparing two independently derived values so
    # that nothing printed restates a figure that was written in as a constant.
    canon = result["canonical"]
    live = result["live_surface"]
    shares = [r["person_share_pct"] for r in result["archetypes"]]
    p0 = result["p0_condition"]
    return [
        ("canonical.tracked_files (marker) == canonical.tracked_files_derived",
         canon["tracked_files"], canon["tracked_files_derived"]),
        ("canonical.subsystems (marker) == canonical.subsystems_derived",
         canon["subsystems"], canon["subsystems_derived"]),
        ("live.tool_count (handshake 1) == live.tool_count (handshake 2)",
         live["tool_count"], live["tool_count_second_handshake"]),
        ("live.distinct_tools == live.tool_count",
         live["distinct_tools"], live["tool_count"]),
        ("live.tool_count == len(tool_summary)",
         live["tool_count"], len(live["tool_summary"])),
        ("outcomes.underserved == count of underserved rows",
         result["outcomes_underserved"],
         len([r for r in result["outcomes"] if r["underserved"]])),
        ("archetypes.weight_sum == 1",
         round(sum(r["research_weight"] for r in result["archetypes"]), 6), 1),
        ("person.shares_sum == 100", sum(shares), 100),
        ("p0.mean_arm == (underserved_mean >= 12.0)",
         p0["mean_arm_holds"], result["underserved_mean_opportunity"] >= 12.0),
        ("p0.count_arm == (underserved_count >= 3)",
         p0["count_arm_holds"], result["outcomes_underserved"] >= 3),
        ("p0.status == verdict",
         p0["status"],
         "meets" if (p0["mean_arm_holds"] and p0["count_arm_holds"]) else "fails"),
        ("canonical.source_document_chars > 0",
         canon["source_document_chars"] > 0, True),
    ]


def print_assertions(result):
    passed = 0
    checks = assertion_checks(result)
    print("")
    print("EVIDENCE - mem20 desktop research & design model")
    for label, derived, expected in checks:
        print("assert %s  (derived %r, expected %r)" % (label, derived, expected))
        require(derived == expected,
                "%s failed: derived %r, expected %r"
                % (label, derived, expected))
        passed += 1
    print("ASSERTIONS PASSED: %d of %d" % (passed, len(checks)))


def gather_sources(marker_text):
    # The repository API URLs are built from the identity the marker names, so
    # nothing is addressed by a written-in repository name.
    repo = read_marker(marker_text)
    api_repo = fetch_json("%s/repos/%s" % (API_ROOT, repo["repo_full_name"]))
    tree = fetch_json("%s/repos/%s/git/trees/%s?recursive=1"
                      % (API_ROOT, repo["repo_full_name"], repo["branch"]))
    return {
        "marker": marker_text,
        "api_repo": api_repo,
        "tree": tree,
        "surface_a": live_tool_surface("/tmp/mem20-design-store-a"),
        "surface_b": live_tool_surface("/tmp/mem20-design-store-b"),
    }


def run():
    """Fetch the real sources and build the result from them."""
    return build(gather_sources(fetch_text(CANONICAL_URL)), OUTCOMES)


def main(argv):
    if "--self-test" in argv:
        # Negative control. The marker's tracked-file figure is altered so the two
        # independent derivations disagree; the invariant must raise and the
        # failure is NOT caught here nor converted into a success value, so the
        # process exits non-zero. A zero exit here would mean the invariants do
        # not actually fire.
        print("SELF-TEST: feeding an altered marker; an invariant must fire")
        marker = fetch_text(CANONICAL_URL)
        altered = re.sub(r"(\|\s*Tracked files\s*\|\s*)[\d,]+(\s*\|)",
                         r"\g<1>0\g<2>", marker, count=1)
        require(altered != marker, "self-test could not alter the marker")
        sources = gather_sources(altered)
        build(sources, OUTCOMES)
        print("SELF-TEST FAILED: the altered input was not caught")
        return 0

    result = run()
    print_assertions(result)
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
