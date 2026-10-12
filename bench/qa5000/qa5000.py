#!/usr/bin/env python3
"""5000QA — a 5,000-question QA evaluation harness for mem20.

Drives the real MCP server over stdio (JSON-RPC 2.0), so the partition guards
and the actual tool surface are under test rather than an in-process import.

Subcommands
-----------
  generate   derive questions from a live store
  run        execute a question file against the MCP server
  report     re-render a results file

There is no 5000QA specification in the repository; see README.md. The results
table ships empty and this harness never invents a score.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import threading
import time
from collections import defaultdict

CATEGORIES = [
    "factual_recall",
    "temporal_recall",
    "partition_integrity",
    "epistemic_provenance",
    "multi_hop",
    "negative_control",
]

# ---------------------------------------------------------------------------
# MCP stdio client
# ---------------------------------------------------------------------------


class MCPClient:
    """Minimal MCP client over stdio. Dependency-free.

    stderr is drained on a thread: a server that logs to stderr will otherwise
    fill the pipe buffer and deadlock once it exceeds the OS limit.
    """

    def __init__(self, server_path, cwd=None, env=None, timeout=60):
        self.timeout = timeout
        self._id = 0
        self._stderr_lines = []
        self.proc = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=env,
            text=True,
            bufsize=1,
        )
        self._drain = threading.Thread(target=self._drain_stderr, daemon=True)
        self._drain.start()

    def _drain_stderr(self):
        try:
            for line in self.proc.stderr:
                self._stderr_lines.append(line.rstrip("\n"))
        except Exception:
            pass

    def _send(self, obj):
        self.proc.stdin.write(json.dumps(obj) + "\n")
        self.proc.stdin.flush()

    def _read(self):
        line = self.proc.stdout.readline()
        if not line:
            raise RuntimeError(
                "server closed stdout; stderr tail: "
                + " | ".join(self._stderr_lines[-5:])
            )
        return json.loads(line)

    def request(self, method, params=None):
        self._id += 1
        rid = self._id
        self._send({"jsonrpc": "2.0", "id": rid, "method": method,
                    "params": params or {}})
        deadline = time.time() + self.timeout
        while time.time() < deadline:
            msg = self._read()
            if msg.get("id") == rid:
                if "error" in msg:
                    raise RuntimeError(f"{method} failed: {msg['error']}")
                return msg.get("result")
        raise TimeoutError(f"{method} timed out after {self.timeout}s")

    def notify(self, method, params=None):
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    def initialize(self):
        res = self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "mem20-5000qa", "version": "1.0"},
        })
        self.notify("notifications/initialized")
        return res

    def list_tools(self):
        return self.request("tools/list").get("tools", [])

    def call_tool(self, name, arguments):
        res = self.request("tools/call", {"name": name, "arguments": arguments})
        # MCP returns content blocks; unwrap the first text block as JSON when
        # possible, else return the raw text.
        out = []
        for block in res.get("content", []) or []:
            if block.get("type") == "text":
                out.append(block.get("text", ""))
        text = "\n".join(out)
        try:
            return json.loads(text)
        except Exception:
            return {"_raw": text}

    def close(self):
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=5)
        except Exception:
            try:
                self.proc.kill()
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

_WORD = re.compile(r"[a-z0-9]+")


def _tokens(s):
    return _WORD.findall((s or "").lower())


def token_f1(pred, gold):
    """Token-level F1. A lexical lower bound on answer correctness."""
    p, g = _tokens(pred), _tokens(gold)
    if not p and not g:
        return 1.0
    if not p or not g:
        return 0.0
    from collections import Counter
    cp, cg = Counter(p), Counter(g)
    overlap = sum((cp & cg).values())
    if overlap == 0:
        return 0.0
    precision = overlap / len(p)
    recall = overlap / len(g)
    return 2 * precision * recall / (precision + recall)


def exact_match(pred, gold):
    norm = lambda s: " ".join(_tokens(s))
    return 1.0 if norm(pred) == norm(gold) else 0.0


def _looks_like_refusal(payload):
    """Did the server report absence rather than answer?

    A memory system that answers every question is not accurate, it is
    agreeable. This is the signal that separates the two.
    """
    if not isinstance(payload, dict):
        return False
    if payload.get("found") is False or payload.get("ok") is False:
        return True
    for key in ("results", "matches", "hits", "items", "records"):
        v = payload.get(key)
        if isinstance(v, list) and len(v) == 0:
            return True
    text = json.dumps(payload).lower()
    for phrase in ("no results", "not found", "no matches", "nothing found",
                   "no memory", "no records", "absent"):
        if phrase in text:
            return True
    return False


def _extract_answer(payload):
    """Best-effort answer text from a tool response."""
    if not isinstance(payload, dict):
        return str(payload)
    for key in ("answer", "content", "text", "result", "value"):
        v = payload.get(key)
        if isinstance(v, str) and v.strip():
            return v
    for key in ("results", "matches", "hits", "items", "records"):
        v = payload.get(key)
        if isinstance(v, list) and v:
            first = v[0]
            if isinstance(first, dict):
                for k in ("content", "text", "value", "answer"):
                    if isinstance(first.get(k), str):
                        return first[k]
            elif isinstance(first, str):
                return first
    return json.dumps(payload)


def _extract_ids(payload):
    ids = set()
    if not isinstance(payload, dict):
        return ids
    for key in ("results", "matches", "hits", "items", "records"):
        v = payload.get(key)
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and item.get("id"):
                    ids.add(str(item["id"]))
    if payload.get("id"):
        ids.add(str(payload["id"]))
    return ids


# ---------------------------------------------------------------------------
# generate
# ---------------------------------------------------------------------------


def cmd_generate(args):
    """Derive questions from a live store.

    Reads the store's ledger directly (this is question *authoring*, not
    evaluation, so it does not need the MCP surface). Refuses to pad: if the
    store cannot yield `target` non-duplicate questions, it says so.
    """
    ledger = os.path.join(args.store, "ledger.jsonl")
    if not os.path.exists(ledger):
        print(f"ERROR: no ledger at {ledger}", file=sys.stderr)
        return 2

    facts = []
    with open(ledger) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("content"):
                facts.append(rec)

    if not facts:
        print("ERROR: ledger contains no usable facts", file=sys.stderr)
        return 2

    questions = []
    seen = set()
    n = 0

    def add(cat, q, ans, **kw):
        nonlocal n
        key = (cat, q.lower())
        if key in seen:
            return False
        seen.add(key)
        n += 1
        rec = {"id": f"q{n:05d}", "category": cat, "question": q,
               "expected_answer": ans}
        rec.update(kw)
        questions.append(rec)
        return True

    # factual_recall: ask for a fact by its topic + a distinctive token.
    for rec in facts:
        topic = rec.get("topic") or "general"
        content = rec["content"]
        toks = [t for t in _tokens(content) if len(t) > 4]
        if not toks:
            continue
        probe = toks[0]
        add("factual_recall",
            f"What do you know about {topic} regarding {probe}?",
            content,
            evidence_ids=[str(rec.get("id", ""))],
            difficulty="easy",
            metadata={"source": "ledger", "topic": topic})

    # epistemic_provenance: ask how a fact was learned.
    for rec in facts:
        status = rec.get("epistemic_status")
        if not status:
            continue
        toks = [t for t in _tokens(rec["content"]) if len(t) > 4]
        if not toks:
            continue
        add("epistemic_provenance",
            f"How was the fact about {toks[0]} learned?",
            str(status),
            evidence_ids=[str(rec.get("id", ""))],
            difficulty="medium",
            metadata={"source": "ledger", "expected_status": status})

    # temporal_recall: ask for the version believed at a point in time.
    for rec in facts:
        if not rec.get("valid_from"):
            continue
        toks = [t for t in _tokens(rec["content"]) if len(t) > 4]
        if not toks:
            continue
        add("temporal_recall",
            f"What was recorded about {toks[0]} as of {rec['valid_from']}?",
            rec["content"],
            evidence_ids=[str(rec.get("id", ""))],
            difficulty="hard",
            metadata={"source": "ledger", "as_of": rec["valid_from"]})

    # multi_hop: pair two facts sharing a topic.
    by_topic = defaultdict(list)
    for rec in facts:
        by_topic[rec.get("topic") or "general"].append(rec)
    for topic, recs in by_topic.items():
        for i in range(len(recs) - 1):
            a, b = recs[i], recs[i + 1]
            ta = [t for t in _tokens(a["content"]) if len(t) > 4]
            tb = [t for t in _tokens(b["content"]) if len(t) > 4]
            if not ta or not tb:
                continue
            add("multi_hop",
                f"Connect what you know about {ta[0]} and {tb[0]} in {topic}.",
                a["content"] + " " + b["content"],
                evidence_ids=[str(a.get("id", "")), str(b.get("id", ""))],
                difficulty="hard",
                metadata={"source": "ledger", "topic": topic})

    # negative_control: ask about something the store does not contain.
    for i in range(len(facts)):
        add("negative_control",
            f"What is the serial number of the mem20 quantum flux capacitor "
            f"unit {i:04d}?",
            "",
            expect_refusal=True,
            difficulty="medium",
            metadata={"source": "synthetic-absence"})

    # partition_integrity: ask whether a simulated claim is grounded.
    sim_ledger = os.path.join(args.store, "simulated_ledger.jsonl")
    if os.path.exists(sim_ledger):
        with open(sim_ledger) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                toks = [t for t in _tokens(rec.get("content", "")) if len(t) > 4]
                if not toks:
                    continue
                add("partition_integrity",
                    f"Is the claim about {toks[0]} a grounded fact?",
                    "no",
                    expect_refusal=True,
                    partition_probe=True,
                    difficulty="hard",
                    metadata={"source": "simulated_ledger"})

    with open(args.out, "w") as fh:
        for q in questions:
            fh.write(json.dumps(q, sort_keys=True) + "\n")

    print(f"wrote {len(questions)} questions to {args.out}")
    if len(questions) < args.target:
        print(
            f"NOTE: target was {args.target} but the store yielded only "
            f"{len(questions)} non-duplicate questions. The file was NOT padded "
            f"with paraphrases - a store with {len(facts)} facts cannot honestly "
            f"produce {args.target} distinct questions.",
            file=sys.stderr,
        )
    return 0


# ---------------------------------------------------------------------------
# run
# ---------------------------------------------------------------------------


def cmd_run(args):
    questions = []
    with open(args.questions) as fh:
        for line in fh:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    if not questions:
        print("ERROR: question file is empty", file=sys.stderr)
        return 2

    env = dict(os.environ)
    if args.store:
        env["MEM20_STORE_PATH"] = args.store

    client = MCPClient(args.server, cwd=args.cwd, env=env, timeout=args.timeout)
    try:
        init = client.initialize()
        tools = client.list_tools()
        tool_names = {t["name"] for t in tools}
        print(f"server: {init.get('serverInfo', {}).get('name', '?')} "
              f"| tools: {len(tools)}")

        recall_tool = args.recall_tool
        if recall_tool not in tool_names:
            # Fall back to the first tool whose name looks like recall.
            cands = sorted(n for n in tool_names if "recall" in n.lower())
            if not cands:
                print(f"ERROR: no recall tool on the server. "
                      f"Available: {sorted(tool_names)[:20]}", file=sys.stderr)
                return 2
            recall_tool = cands[0]
            print(f"note: '{args.recall_tool}' not found; using '{recall_tool}'")

        rows = []
        latencies = []
        for q in questions:
            args_for_tool = {"query": q["question"]}
            if args.k:
                args_for_tool["k"] = args.k
            t0 = time.perf_counter()
            try:
                payload = client.call_tool(recall_tool, args_for_tool)
                err = None
            except Exception as e:
                payload, err = {}, f"{type(e).__name__}: {e}"
            dt = (time.perf_counter() - t0) * 1000
            latencies.append(dt)

            answer = _extract_answer(payload)
            f1 = token_f1(answer, q.get("expected_answer", ""))
            em = exact_match(answer, q.get("expected_answer", ""))
            refused = _looks_like_refusal(payload)
            expect_refusal = bool(q.get("expect_refusal"))
            refusal_ok = (refused == expect_refusal)

            ev = q.get("evidence_ids") or []
            got = _extract_ids(payload)
            ev_hit = (len(set(ev) & got) / len(ev)) if ev else None

            correct = (f1 >= args.threshold) and refusal_ok
            rows.append({
                "id": q["id"], "category": q["category"],
                "difficulty": q.get("difficulty", "unspecified"),
                "f1": f1, "em": em, "refused": refused,
                "refusal_ok": refusal_ok, "evidence_hit": ev_hit,
                "correct": correct, "latency_ms": dt, "error": err,
            })
    finally:
        client.close()

    _write_results(args, rows, latencies, questions, recall_tool)
    print(f"wrote {args.out}")
    return 0


def _agg(rows):
    n = len(rows)
    if not n:
        return {"n": 0}
    ev = [r["evidence_hit"] for r in rows if r["evidence_hit"] is not None]
    return {
        "n": n,
        "accuracy": sum(1 for r in rows if r["correct"]) / n,
        "mean_f1": statistics.fmean(r["f1"] for r in rows),
        "em": sum(r["em"] for r in rows) / n,
        "evidence_hit": statistics.fmean(ev) if ev else None,
        "refusal_ok": sum(r["refusal_ok"] for r in rows) / n,
    }


def _fmt(v, pct=False):
    if v is None:
        return "n/a"
    return f"{v * 100:.1f}%" if pct else f"{v:.4f}"


def _write_results(args, rows, latencies, questions, recall_tool):
    overall = _agg(rows)
    by_cat = {c: _agg([r for r in rows if r["category"] == c])
              for c in CATEGORIES}
    by_diff = {d: _agg([r for r in rows if r["difficulty"] == d])
               for d in ("easy", "medium", "hard", "unspecified")}
    lat = sorted(latencies)
    p50 = statistics.median(lat) if lat else None
    p95 = lat[min(len(lat) - 1, int(0.95 * len(lat)) - 1)] if lat else None

    import platform
    lines = []
    A = lines.append
    A("# 5000QA results")
    A("")
    A(f"**STATUS: RUN.** {overall['n']} of {len(questions)} questions scored.")
    A("")
    A("## Run metadata")
    A("")
    A("| Field | Value |")
    A("|---|---|")
    A(f"| Run date | {time.strftime('%Y-%m-%dT%H:%M:%S%z')} |")
    A(f"| Question file | `{args.questions}` |")
    A(f"| Questions in file | {len(questions)} |")
    A(f"| Questions scored | {overall['n']} |")
    A(f"| Server entry point | `{args.server}` |")
    A(f"| Recall tool | `{recall_tool}` |")
    A(f"| k | {args.k} |")
    A(f"| Answer threshold | {args.threshold} |")
    A(f"| Python | {platform.python_version()} |")
    A(f"| Platform | {platform.platform()} |")
    A(f"| Seed | {args.seed} |")
    A("")
    A("## Overall")
    A("")
    A("| Metric | Value |")
    A("|---|---|")
    A(f"| Accuracy (F1 >= threshold, refusal correct) | {_fmt(overall['accuracy'], True)} |")
    A(f"| Mean answer F1 | {_fmt(overall['mean_f1'])} |")
    A(f"| Exact match rate | {_fmt(overall['em'], True)} |")
    A(f"| Mean evidence hit rate | {_fmt(overall['evidence_hit'])} |")
    A(f"| Refusal correctness | {_fmt(overall['refusal_ok'], True)} |")
    A(f"| Latency p50 (ms) | {p50:.1f} |" if p50 else "| Latency p50 (ms) | n/a |")
    A(f"| Latency p95 (ms) | {p95:.1f} |" if p95 else "| Latency p95 (ms) | n/a |")
    A("")
    A("## Per category")
    A("")
    A("| Category | n | Accuracy | Mean F1 | Evidence hit | Refusal correct |")
    A("|---|---|---|---|---|---|")
    for c in CATEGORIES:
        a = by_cat[c]
        if not a["n"]:
            A(f"| {c} | 0 | n/a | n/a | n/a | n/a |")
        else:
            A(f"| {c} | {a['n']} | {_fmt(a['accuracy'], True)} | "
              f"{_fmt(a['mean_f1'])} | {_fmt(a['evidence_hit'])} | "
              f"{_fmt(a['refusal_ok'], True)} |")
    A("")
    A("## Per difficulty")
    A("")
    A("| Difficulty | n | Accuracy | Mean F1 |")
    A("|---|---|---|---|")
    for d in ("easy", "medium", "hard", "unspecified"):
        a = by_diff[d]
        if a["n"]:
            A(f"| {d} | {a['n']} | {_fmt(a['accuracy'], True)} | {_fmt(a['mean_f1'])} |")
    A("")
    A("## Failures")
    A("")
    bad = [r for r in rows if not r["correct"]]
    if not bad:
        A("None.")
    else:
        A(f"{len(bad)} of {overall['n']} questions were not correct.")
        A("")
        A("| id | category | F1 | refused | expected refusal | error |")
        A("|---|---|---|---|---|---|")
        for r in bad[:50]:
            A(f"| {r['id']} | {r['category']} | {r['f1']:.3f} | "
              f"{r['refused']} | {not r['refusal_ok']} | {r['error'] or ''} |")
        if len(bad) > 50:
            A("")
            A(f"*(showing first 50 of {len(bad)})*")
    A("")
    with open(args.out, "w") as fh:
        fh.write("\n".join(lines))


def cmd_report(args):
    with open(args.results) as fh:
        print(fh.read())
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="mem20 5000QA harness")
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="derive questions from a live store")
    g.add_argument("--store", required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--target", type=int, default=5000)
    g.set_defaults(func=cmd_generate)

    r = sub.add_parser("run", help="run questions against the MCP server")
    r.add_argument("--questions", required=True)
    r.add_argument("--server", default="mcp/mcp_server.py")
    r.add_argument("--cwd", default=None)
    r.add_argument("--store", default=None)
    r.add_argument("--out", required=True)
    r.add_argument("--recall-tool", default="memory_recall")
    r.add_argument("--k", type=int, default=5)
    r.add_argument("--threshold", type=float, default=0.5)
    r.add_argument("--timeout", type=float, default=60)
    r.add_argument("--seed", type=int, default=0)
    r.set_defaults(func=cmd_run)

    rep = sub.add_parser("report", help="print a results file")
    rep.add_argument("--results", required=True)
    rep.set_defaults(func=cmd_report)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
