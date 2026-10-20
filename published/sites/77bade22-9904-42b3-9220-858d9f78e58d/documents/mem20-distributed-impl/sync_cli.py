#!/usr/bin/env python3
"""
mem20 distributed sync — CLI + peer transport
=============================================

The on-demand / scheduled entry point. Exchanges events with a peer over SSH,
**routed through gabe** (the jump host), and logs to stdout (journald captures it
under the systemd unit).

Subcommands
-----------
  status        show node id, ledger size, vector clock, state hash
  state-hash    print just the state hash (used by the G-3 gate)
  export        write this node's unseen events to a JSON file (stdout or --out)
  ingest        apply a JSON event file produced by a peer's `export`
  sync          full round-trip with a peer over SSH (through gabe)
  project       rebuild the projections from the ledger

Transport (never a file-level copy of the live .db)
---------------------------------------------------
``sync`` runs, on the peer, ``mem20_sync.py export`` and pipes the JSON back over
SSH; then it pushes its own unseen events the other way. The database file is
never transferred — only the append-only event log, which is the whole point of
Option D.

SSH is invoked as::

    ssh -J <gabe_user>@<gabe_host>[:<gabe_port>] -p <peer_port> <peer_user>@<peer_host> <cmd>

so every hop passes through gabe. Credentials come from the environment
(``MEM20_SYNC_*``) — never hard-coded, never printed.

Deps: Python 3.11+ stdlib only.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mem20_sync import Mem20Sync, default_db_path  # noqa: E402

SSH_TIMEOUT = int(os.environ.get("MEM20_SYNC_SSH_TIMEOUT", "60"))


# ---------------------------------------------------------------------------
# Peer transport — SSH through gabe
# ---------------------------------------------------------------------------

def _ssh_base(peer: Dict[str, str]) -> List[str]:
    """Build the ssh argv, always jumping through gabe."""
    argv = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new"]
    gabe_host = peer.get("gabe_host")
    if gabe_host:
        jump = f"{peer.get('gabe_user', 'gabe')}@{gabe_host}"
        if peer.get("gabe_port"):
            jump += f":{peer['gabe_port']}"
        argv += ["-J", jump]
    if peer.get("peer_port"):
        argv += ["-p", str(peer["peer_port"])]
    argv.append(f"{peer.get('peer_user', 'root')}@{peer['peer_host']}")
    return argv


def peer_from_env(prefix: str = "MEM20_SYNC_PEER") -> Dict[str, str]:
    """Read peer connection details from the environment.

    Expected (all optional except host):
      MEM20_SYNC_PEER_HOST, MEM20_SYNC_PEER_PORT, MEM20_SYNC_PEER_USER,
      MEM20_SYNC_GABE_HOST, MEM20_SYNC_GABE_PORT, MEM20_SYNC_GABE_USER,
      MEM20_SYNC_PEER_DB, MEM20_SYNC_PEER_PYTHON, MEM20_SYNC_PEER_DIR
    """
    return {
        "peer_host": os.environ.get(f"{prefix}_HOST", ""),
        "peer_port": os.environ.get(f"{prefix}_PORT", ""),
        "peer_user": os.environ.get(f"{prefix}_USER", "root"),
        "gabe_host": os.environ.get("MEM20_SYNC_GABE_HOST", ""),
        "gabe_port": os.environ.get("MEM20_SYNC_GABE_PORT", ""),
        "gabe_user": os.environ.get("MEM20_SYNC_GABE_USER", "gabe"),
        "peer_db": os.environ.get("MEM20_SYNC_PEER_DB", ""),
        "peer_python": os.environ.get("MEM20_SYNC_PEER_PYTHON", "python3"),
        "peer_dir": os.environ.get("MEM20_SYNC_PEER_DIR", "/opt/mem20-sync"),
    }


def _run_remote(peer: Dict[str, str], remote_cmd: str,
                stdin: Optional[str] = None) -> subprocess.CompletedProcess:
    argv = _ssh_base(peer) + [remote_cmd]
    return subprocess.run(
        argv, input=stdin, capture_output=True, text=True, timeout=SSH_TIMEOUT,
    )


def remote_export(peer: Dict[str, str], vc: Dict[str, int]) -> List[Dict[str, Any]]:
    """Ask the peer for the events we have not seen (over SSH, through gabe)."""
    vc_json = shlex.quote(json.dumps(vc))
    db = shlex.quote(peer["peer_db"])
    py = shlex.quote(peer["peer_python"])
    d = shlex.quote(peer["peer_dir"])
    cmd = (f"cd {d} && {py} mem20_sync.py export --db {db} --vc {vc_json}")
    proc = _run_remote(peer, cmd)
    if proc.returncode != 0:
        raise RuntimeError(f"peer export failed rc={proc.returncode}: {proc.stderr.strip()[:400]}")
    return json.loads(proc.stdout or "[]")


def remote_ingest(peer: Dict[str, str], events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Push our unseen events to the peer (over SSH, through gabe)."""
    db = shlex.quote(peer["peer_db"])
    py = shlex.quote(peer["peer_python"])
    d = shlex.quote(peer["peer_dir"])
    cmd = (f"cd {d} && {py} mem20_sync.py ingest --db {db} --stdin")
    proc = _run_remote(peer, cmd, stdin=json.dumps(events))
    if proc.returncode != 0:
        raise RuntimeError(f"peer ingest failed rc={proc.returncode}: {proc.stderr.strip()[:400]}")
    return json.loads(proc.stdout or "{}")


def remote_state_hash(peer: Dict[str, str]) -> str:
    db = shlex.quote(peer["peer_db"])
    py = shlex.quote(peer["peer_python"])
    d = shlex.quote(peer["peer_dir"])
    proc = _run_remote(peer, f"cd {d} && {py} mem20_sync.py state-hash --db {db}")
    if proc.returncode != 0:
        raise RuntimeError(f"peer state-hash failed rc={proc.returncode}: {proc.stderr.strip()[:400]}")
    return proc.stdout.strip()


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_status(node: Mem20Sync) -> int:
    node.project()
    print(json.dumps({
        "node_id": node.node_id,
        "db": node.path,
        "ledger_events": node.ledger_size(),
        "vector_clock": node.vector_clock(),
        "state_hash": node.state_hash(),
        "projected": {t: len(node.dump(t)) for t in
                      ("proj_memories", "proj_tot_nodes", "proj_history")},
    }, indent=2))
    return 0


def cmd_state_hash(node: Mem20Sync) -> int:
    node.project()
    print(node.state_hash())
    return 0


def cmd_project(node: Mem20Sync) -> int:
    print(json.dumps(node.project(), indent=2))
    return 0


def cmd_export(node: Mem20Sync, vc: Dict[str, int], out: Optional[str]) -> int:
    events = node.events_after(vc)
    text = json.dumps(events, sort_keys=True)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(json.dumps({"exported": len(events), "out": out}))
    else:
        print(text)
    return 0


def cmd_ingest(node: Mem20Sync, path: Optional[str], use_stdin: bool) -> int:
    if use_stdin:
        events = json.loads(sys.stdin.read() or "[]")
    else:
        with open(path, "r", encoding="utf-8") as fh:
            events = json.load(fh)
    applied, conflicts = node.ingest(events)
    node.project()
    print(json.dumps({"applied": applied, "conflicts_absorbed": conflicts,
                      "state_hash": node.state_hash()}, indent=2))
    return 0


def cmd_sync(node: Mem20Sync, peer: Dict[str, str]) -> int:
    if not peer.get("peer_host"):
        print(json.dumps({"ok": False, "error": "no peer host configured "
                          "(set MEM20_SYNC_PEER_HOST and the gabe vars)"}), file=sys.stderr)
        return 2
    node.project()
    before = node.state_hash()

    # pull: peer -> us
    incoming = remote_export(peer, node.vector_clock())
    applied_in, conflicts = node.ingest(incoming)

    # push: us -> peer
    outgoing = node.events_after({})  # peer filters by its own vector clock
    peer_res = remote_ingest(peer, outgoing)

    node.project()
    after = node.state_hash()
    peer_hash = remote_state_hash(peer)
    converged = (after == peer_hash)
    print(json.dumps({
        "ok": converged,
        "pulled": applied_in, "pushed": peer_res.get("applied", 0),
        "conflicts_absorbed": conflicts,
        "local_state_hash": after, "peer_state_hash": peer_hash,
        "converged": converged,
        "local_hash_before": before,
    }, indent=2))
    return 0 if converged else 1


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="mem20 distributed sync CLI")
    ap.add_argument("--db", default=default_db_path(), help="mem20 SQLite database")
    ap.add_argument("--node", default=os.environ.get("MEM20_SYNC_NODE_ID"),
                    help="this node's id (defaults to replication_state)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("state-hash")
    sub.add_parser("project")

    p_exp = sub.add_parser("export")
    p_exp.add_argument("--vc", default="{}", help="peer vector clock as JSON")
    p_exp.add_argument("--out", default=None)

    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("--file", default=None)
    p_ing.add_argument("--stdin", action="store_true")

    sub.add_parser("sync")

    args = ap.parse_args(argv)
    node = Mem20Sync(args.db, node_id=args.node)

    if args.cmd == "status":
        return cmd_status(node)
    if args.cmd == "state-hash":
        return cmd_state_hash(node)
    if args.cmd == "project":
        return cmd_project(node)
    if args.cmd == "export":
        return cmd_export(node, json.loads(args.vc or "{}"), args.out)
    if args.cmd == "ingest":
        return cmd_ingest(node, args.file, args.stdin)
    if args.cmd == "sync":
        return cmd_sync(node, peer_from_env())
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
