#!/usr/bin/env python3
"""mem20 Gateway — CLI relay for multi-agent fleet communication.

Each agent picks a unique name on startup to avoid confusion. Real tools only.

Every message passes ``relay.admit`` before it is written: the agent name must
be an estate address, the declared intended use must not be prohibited, the
gateway's own source must not be stubbed, the timestamp must be inside its
window, and inbound transport lines are filtered for noise. A refusal is
returned as a structured refusal and the message is NOT written -- a relay that
writes first and validates later has already relayed it.

Two defects fixed here, both found by reading the module rather than by a test:

* ``read_messages`` filtered on ``m["agent"]`` and printed ``m['agent']``, but
  every entry written by ``broadcast`` carries ``agent_name``. Any call with
  ``--agent`` raised KeyError, and any call at all raised KeyError on the print.
* ``MEM20_DIR`` was hardcoded to ``/opt/mem20``, so the module only worked on
  one box. It now resolves from the file's own location, with the env var as an
  override.
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MEM20_DIR = Path(os.environ.get("MEM20_DIR", str(HERE.parent)))
GATEWAY_DIR = Path(os.environ.get("MEM20_GATEWAY_DIR", str(HERE)))
NAMES_FILE = GATEWAY_DIR / "agent_names.json"
MESSAGES_FILE = GATEWAY_DIR / "messages.jsonl"

if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import relay


def ensure_dirs():
    GATEWAY_DIR.mkdir(parents=True, exist_ok=True)


def register_agent(name: str = None, location: str = None) -> dict:
    """Register this agent. If no name is given, generate an estate address.

    The generated name goes through ``relay.generate_agent_name`` so it is a
    name the rest of the estate recognises. This module used to generate
    ``hermes-<loc>-<id>``, which classifies as "other" -- every agent it
    registered had an address no other subsystem could resolve.
    """
    ensure_dirs()

    if not name:
        name = relay.generate_agent_name(location, uuid.uuid4().hex[:8])

    # An explicit name is checked, not trusted: a caller can pass anything.
    naming = relay.check_agent_name(name)

    record = {
        "name": name,
        "location": location or "local",
        "registered_at": datetime.now(timezone.utc).isoformat(),
        "agent_id": uuid.uuid4().hex[:8],
        "status": "active",
        "naming": naming,
    }

    names = load_names()
    if name in names:
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
        print(f"  {name}")
        print(f"    Location: {info.get('location', 'unknown')}")
        print(f"    Status: {info.get('status', 'unknown')}")
        print(f"    Since: {info.get('registered_at', 'unknown')}")
        print()

    return names


def _resolve_sender(agent_name: str | None) -> str:
    """Work out who is sending, or refuse.

    Returns the name; raises ``relay.RelayRefused`` if it cannot be resolved.
    """
    names = load_names()
    if agent_name:
        if agent_name not in names:
            raise relay.RelayRefused(
                "unregistered", f"agent {agent_name!r} is not registered"
            )
        return agent_name
    if len(names) == 1:
        return list(names.keys())[0]
    if len(names) > 1:
        raise relay.RelayRefused(
            "ambiguous_sender", "multiple agents registered; specify --agent-name"
        )
    raise relay.RelayRefused("unregistered", "no agents registered; run register first")


def broadcast(
    message: str,
    agent_name: str = None,
    target: str = "telegram_channel",
    intended_uses=None,
    wire=None,
    at: str = None,
) -> dict:
    """Broadcast a message to the gateway. All agents can read it."""
    ensure_dirs()

    sender = _resolve_sender(agent_name)
    admission, kept = relay.admit(
        sender,
        "broadcast",
        GATEWAY_DIR,
        intended_uses=intended_uses,
        wire=wire,
        at=at,
    )

    names = load_names()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": sender,
        "agent_id": names[sender].get("agent_id", ""),
        "location": names[sender].get("location", "unknown"),
        "message": message,
        "target": target,
        "source": "hermes_gateway",
        "message_id": uuid.uuid4().hex[:12],
        "admission": admission.as_dict(),
    }
    if kept:
        entry["wire"] = [line.text for line in kept]

    with open(MESSAGES_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    entry["provenance"] = relay.record_provenance(entry)

    print(f"Broadcast from {sender}: {message[:80]}...")
    return entry


def read_messages(since: str = None, agent: str = None, limit: int = 50):
    """Read messages from the gateway.

    Entries carry ``agent_name``; this used to filter and print ``m["agent"]``,
    which raised KeyError on every call.
    """
    ensure_dirs()

    if not MESSAGES_FILE.exists():
        print("No messages yet.")
        return []

    messages = []
    with open(MESSAGES_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            messages.append(json.loads(line))

    if agent:
        messages = [m for m in messages if m.get("agent_name") == agent]

    if since:
        messages = [m for m in messages if m.get("timestamp", "") >= since]

    messages.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    messages = messages[:limit]

    if not messages:
        print("No matching messages.")
        return messages

    print(f"Messages ({len(messages)}):")
    for m in messages:
        who = m.get("agent_name") or m.get("sender") or "unknown"
        print(f"  [{m.get('timestamp', '')}] {who}: {str(m.get('message', ''))[:100]}")

    return messages


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="mem20 Gateway — multi-agent relay")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_register = subparsers.add_parser("register", help="Register this agent")
    p_register.add_argument("--name", "-n", help="Agent name (auto-generated if not provided)")
    p_register.add_argument("--location", "-l", help="VPS location or hostname")

    subparsers.add_parser("list", help="List all registered agents")

    p_broadcast = subparsers.add_parser("broadcast", help="Broadcast a message")
    p_broadcast.add_argument("message", help="Message to broadcast")
    p_broadcast.add_argument("--agent-name", "-a", help="Your agent name")
    p_broadcast.add_argument("--target", "-t", default="telegram_channel", help="Target channel")
    p_broadcast.add_argument(
        "--intended-use", action="append", default=None,
        help="Declare what this message is for; checked against the prohibited-use list",
    )

    p_read = subparsers.add_parser("read", help="Read messages from gateway")
    p_read.add_argument("--since", help="Only messages since this ISO timestamp")
    p_read.add_argument("--agent", "-a", help="Filter by agent name")
    p_read.add_argument("--limit", "-l", type=int, default=50, help="Max messages to return")

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    try:
        if args.command == "register":
            record = register_agent(name=args.name, location=args.location)
            print(json.dumps(record, indent=2))
        elif args.command == "list":
            list_agents()
        elif args.command == "broadcast":
            broadcast(
                args.message,
                agent_name=args.agent_name,
                target=args.target,
                intended_uses=args.intended_use,
            )
        elif args.command == "read":
            read_messages(since=args.since, agent=args.agent, limit=args.limit)
    except relay.RelayRefused as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
