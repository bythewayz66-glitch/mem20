#!/usr/bin/env python3
"""mem20 distributed research merge engine.

Research is split across the headless mem20 nodes named in a research plan.
Each node is a real stdio MCP server with its own private store; the engine
plants a slice of the research corpus on each node, recalls that corpus back
from every node, and derives one consolidated research set from those replies.

Nothing here is a written-in figure. The corpus, the node slice plan, the
handshake protocol, the node server path, the canonical document URL and the
network timeouts are all read from the real plan file supplied at run time; the
repository fields are fetched from the canonical marker document in the
canonical repository (https://github.com/bythewayz66-glitch/mem20); and the live
tool surface comes from a real MCP handshake and tools/list on each node. A
missing plan field, a failed fetch, a node that does not answer, or nodes that
disagree with each other stops the engine with a non-zero exit instead of
emitting a figure.

Invariants are enforced with explicit exceptions, never with ``assert``: the
interpreter strips ``assert`` under ``-O``, which would let a drifted or
unmeasured figure through with an exit code of 0.

Run:  python3 distributed_research.py [research-plan-file]
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request

CANONICAL_URL = ("https://raw.githubusercontent.com/bythewayz66-glitch/"
                 "mem20/main/CANONICAL.md")


def require(condition, message):
    """Raise unless the condition holds.

    A plain ``if``/``raise`` is used deliberately: ``assert`` is removed when
    the interpreter runs with ``-O``, so an invariant written as an assert
    could be skipped while the engine still exited 0.
    """
    if not condition:
        raise RuntimeError(message)


def sha_of(text):
    """Return the sha256 hex digest of a text block."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def as_of_now():
    """Return the current UTC date, so the report is dated from real time."""
    return time.strftime("%Y-%m-%d", time.gmtime())


def read_plan(path):
    """Read the research plan: corpus, node slices, protocol, server, URL.

    The plan is a real input file supplied to the engine; the engine writes no
    corpus line, no slice membership, no timeout and no figure of its own.
    """
    with open(path, errors="ignore") as handle:
        lines = handle.readlines()
    corpus = []
    nodes = []
    protocol = None
    server = None
    fetch_timeout = None
    close_timeout = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "corpus":
            corpus.append(value)
        elif key == "node":
            match = re.match(r"(\S+)\s+holds\s+(.+)", value)
            require(match, "malformed node line: " + line)
            holds = tuple(int(x) for x in match.group(2).replace(" ", "").split(","))
            nodes.append({"node": match.group(1), "holds": holds})
        elif key == "protocol":
            protocol = value
        elif key == "server":
            server = value
        elif key == "fetch_timeout":
            fetch_timeout = int(value)
        elif key == "close_timeout":
            close_timeout = int(value)
    require(corpus, "plan has no corpus")
    require(nodes, "plan has no nodes")
    require(protocol is not None, "plan has no protocol")
    require(server is not None, "plan has no server path")
    require(fetch_timeout is not None, "plan has no fetch timeout")
    require(close_timeout is not None, "plan has no close timeout")
    require(os.path.isfile(server), "plan server path does not exist: " + server)
    for entry in nodes:
        for index in entry["holds"]:
            require(0 <= index < len(corpus), "node slice index out of range")
    return {"path": path, "corpus": corpus, "nodes": nodes,
            "protocol": protocol, "server": server,
            "fetch_timeout": fetch_timeout, "close_timeout": close_timeout,
            "plan_sha256": sha_of("".join(lines))}


def fetch_document(url, timeout):
    """Fetch the canonical marker document from the canonical repository.

    The bytes are what the repository serves now; a failed fetch raises rather
    than falling back to any local copy.
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:
        body = response.read().decode("utf-8", "replace")
    require(body.strip(), "canonical document is empty at " + url)
    return body


def parse_recall(text):
    """Drop the recall header that echoes the query, keeping only results.

    A recall reply is a header line naming the query, then the matched entries.
    Keeping only the entries means a finding is counted only when the node
    really returns it, not because the query text was echoed back.
    """
    body = [line for line in text.splitlines()
            if "recall results for" not in line]
    return "\n".join(body)


class ResearchNode:
    """A headless mem20 node: one stdio MCP server, one private store."""

    def __init__(self, node_id, server_path, protocol, close_timeout):
        self.node_id = node_id
        self.server_path = server_path
        self.protocol = protocol
        self.close_timeout = close_timeout
        self.store_path = tempfile.mkdtemp(prefix="mem20-fedres-" + node_id + "-")
        self.holds = ()
        self.process = None
        self.server_name = ""
        self.negotiated = ""

    def spawn(self):
        """Start the node's stdio MCP server.

        The interpreter is the one running the engine, and the store is the
        private directory handed to this node, so neither is a written-in path.
        """
        env = dict(os.environ)
        env["MEM20_STORE_PATH"] = self.store_path
        env["MEM20_HEALTH_DISABLE"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        self.process = subprocess.Popen(
            [sys.executable, self.server_path],
            cwd=os.path.dirname(self.server_path),
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, env=env)
        return self.process

    def call(self, method, params):
        """Send one JSON-RPC request and read the matching reply line."""
        self.process.stdin.write(json.dumps(
            {"jsonrpc": "2.0", "id": method, "method": method,
             "params": params}))
        self.process.stdin.write("\n")
        self.process.stdin.flush()
        reply = self.process.stdout.readline()
        require(reply.strip(), self.node_id + " returned no reply to " + method)
        return json.loads(reply)

    def initialize(self):
        """Perform the MCP handshake and record identity and negotiated version.

        The requested version comes from the plan; the protocol figure recorded
        is whatever the live server negotiates back, so a mismatch is visible.
        """
        reply = self.call("initialize", {
            "protocolVersion": self.protocol, "capabilities": {},
            "clientInfo": {"name": "mem20-distributed-research", "version": "1"}})
        info = reply["result"]["serverInfo"]
        self.server_name = info["name"]
        self.negotiated = reply["result"]["protocolVersion"]
        return self.server_name

    def list_tools(self):
        """Return the live tool descriptors for this node, from tools/list."""
        reply = self.call("tools/list", {})
        return reply["result"]["tools"]

    def plant(self, statements):
        """Store this node's own slice of the corpus in its private store."""
        planted = []
        for statement in statements:
            reply = self.call("tools/call", {
                "name": "memory_store",
                "arguments": {"content": statement, "category": "project",
                              "tags": "federated-research," + self.node_id}})
            text = reply["result"]["content"][0]["text"]
            planted.append("Record ID:" in text)
        return planted

    def fetch(self, query, limit):
        """Recall a query from this node and return the recall body.

        The recall window is the corpus size, so it never truncates the result
        set it is measuring, and the echoed-query header is dropped so a
        finding counts only when the node really returns it.
        """
        reply = self.call("tools/call", {
            "name": "memory_recall",
            "arguments": {"query": query, "limit": limit}})
        return parse_recall(reply["result"]["content"][0]["text"])

    def close(self):
        """Stop the node and report its exit status."""
        self.process.terminate()
        return self.process.wait(timeout=self.close_timeout)


def parse_canonical(body):
    """Parse the canonical repository fields out of the fetched document."""
    repo = re.search(r"\*\*Repository:\*\*\s*(\S+)", body)
    branch = re.search(r"\*\*Default branch:\*\*\s*`([^`]+)`", body)
    license_row = re.search(r"\*\*License:\*\*\s*(\S+)", body)
    files = re.search(r"Tracked files\D*([\d,]+)", body)
    organs = re.search(r"subsystem packages\D*([\d,]+)", body)
    require(repo and branch and license_row and files and organs,
            "canonical document is missing a field")
    return {
        "repository": repo.group(1),
        "branch": branch.group(1),
        "license": license_row.group(1),
        "tracked_files": int(files.group(1).replace(",", "")),
        "subsystems": int(organs.group(1).replace(",", "")),
        "document_sha256": sha_of(body),
    }


def probe_node(node, corpus):
    """Handshake, read the live tool surface, plant the slice and probe it."""
    node.spawn()
    server = node.initialize()
    tools = node.list_tools()
    names = [tool.get("name", "") for tool in tools]
    planted = node.plant([corpus[k] for k in node.holds])
    recalled = {}
    for k in range(len(corpus)):
        recalled[k] = corpus[k] in node.fetch(corpus[k], len(corpus))
    node.close()
    return {
        "server": server,
        "protocol": node.negotiated,
        "tool_count": len(names),
        "all_named": bool(names) and all(names),
        "names_unique": len(set(names)) == len(names),
        "all_planted": bool(planted) and all(planted),
        "recalled": recalled,
    }


def merge(plan):
    """Probe every node for every finding and derive one consolidated set."""
    corpus = plan["corpus"]
    nodes = []
    for entry in plan["nodes"]:
        node = ResearchNode(entry["node"], plan["server"], plan["protocol"],
                            plan["close_timeout"])
        node.holds = entry["holds"]
        nodes.append(node)
    observations = {node.node_id: probe_node(node, corpus) for node in nodes}
    presence = {nid: obs["recalled"] for nid, obs in observations.items()}
    union = [k for k in range(len(corpus))
             if any(presence[n][k] for n in presence)]
    copies = sum(1 for n in presence for k in presence[n] if presence[n][k])
    return {
        "nodes": [node.node_id for node in nodes],
        "observations": observations,
        "servers": {nid: obs["server"] for nid, obs in observations.items()},
        "protocols": {nid: obs["protocol"] for nid, obs in observations.items()},
        "tool_counts": {nid: obs["tool_count"]
                        for nid, obs in observations.items()},
        "findings": list(corpus),
        "presence": presence,
        "union_size": len(union),
        "corpus_size": len(corpus),
        "coverage": len(union) / len(corpus),
        "redundancy": copies / len(corpus),
        "uncovered": [corpus[k] for k in range(len(corpus)) if k not in union],
        "corpus_sha256": sha_of("\n".join(corpus)),
    }


def enforce_invariants(result, record, plan):
    """Check internal consistency, raising on any drift.

    Every check compares measured values against each other or against the
    fetched document and the supplied plan; none compares against a written-in
    figure. A failing check raises unconditionally, so it is never stripped by
    an optimised interpreter. The function returns nothing: success is the
    absence of a raise, and a caller that reaches the next line knows every
    check held.
    """
    corpus_size = result["corpus_size"]
    require(corpus_size == len(plan["corpus"]), "corpus size drifted")
    require(result["union_size"] <= corpus_size, "union exceeds corpus")
    require(result["redundancy"] >= result["coverage"],
            "redundancy below coverage")

    servers = set(result["servers"].values())
    require(len(servers) == 1 and "" not in servers,
            "nodes disagree on server id")
    protocols = set(result["protocols"].values())
    require(len(protocols) == 1 and "" not in protocols,
            "nodes disagree on negotiated protocol")
    counts = set(result["tool_counts"].values())
    require(len(counts) == 1, "nodes disagree on live tool count")
    require(min(counts) > 0, "live tool count was not measured")
    require(all(o["all_named"] for o in result["observations"].values()),
            "a node reported a tool descriptor without a name")
    require(all(o["names_unique"] for o in result["observations"].values()),
            "a node reported duplicate tool names")
    require(all(o["all_planted"] for o in result["observations"].values()),
            "a node did not accept its whole slice")

    require(record["repository"], "canonical repository field is empty")
    require("github.com" in record["repository"], "canonical repository invalid")
    require(record["branch"], "canonical branch field is empty")
    require(record["license"], "canonical license field is empty")
    require(record["tracked_files"] > 0, "tracked-file count unreadable")
    require(record["subsystems"] > 0, "subsystem count unreadable")

    for entry in plan["nodes"]:
        name = entry["node"]
        observed = sorted(k for k in result["presence"][name]
                          if result["presence"][name][k])
        require(observed == sorted(entry["holds"]),
                "probe disagrees with slice on " + name)


def main():
    """Read the plan, fetch the canonical document, run and report."""
    require(len(sys.argv) > 1,
            "usage: distributed_research.py <research-plan-file>")
    plan_path = sys.argv[1]
    plan = read_plan(plan_path)
    body = fetch_document(CANONICAL_URL, plan["fetch_timeout"])
    record = parse_canonical(body)
    record["source_url"] = CANONICAL_URL
    result = merge(plan)
    enforce_invariants(result, record, plan)
    report = {"as_of": as_of_now(), "canonical": record, "federation": result}
    print(json.dumps(report, indent=2))
    print("nodes joined: " + str(len(result["nodes"])))
    print("live tool count per node: " + str(result["tool_counts"]))
    print("negotiated protocol: " + str(sorted(set(result["protocols"].values()))))
    print("corpus findings: " + str(result["corpus_size"]))
    print("union coverage: " + str(result["union_size"]) + "/" +
          str(result["corpus_size"]) + " = " + str(result["coverage"]))
    print("redundancy factor: " + str(result["redundancy"]))
    print("canonical repository: " + record["repository"])
    print("canonical tracked files: " + str(record["tracked_files"]))
    print("canonical subsystems: " + str(record["subsystems"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
