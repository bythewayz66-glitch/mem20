#!/usr/bin/env python3
"""
mem20 Gateway Tools — callable functions for agents.

Each agent calls these to communicate across the fleet.
Stage 1: CLI procede. Real tools, no fake code.
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Reuse the core gateway module. Resolved from this file's own location, not
# from a hardcoded /opt/mem20: the old path made the module importable on
# exactly one box, and silently imported a *different* gateway everywhere else.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import relay
from hermes_gateway import (
    register_agent,
    load_names,
    broadcast as gw_broadcast,
    MESSAGES_FILE,
    NAMES_FILE,
    GATEWAY_DIR,
)

MEM20_DIR = Path(os.environ.get("MEM20_DIR", str(HERE.parent)))
STATUS_FILE = GATEWAY_DIR / "agent_status.json"

# ---------------------------------------------------------------------------
# Tool: register_agent
# ---------------------------------------------------------------------------
def tool_register_agent(name: str = None, location: str = None) -> dict:
    """
    Register this agent in the gateway with a unique name.
    Each agent must pick a distinct name to avoid confusion in the fleet.

    Args:
        name: Desired agent name (auto-generated if not provided)
        location: VPS hostname or location identifier

    Returns:
        Agent registration record with name, agent_id, location, timestamps
    """
    return register_agent(name=name, location=location)


# ---------------------------------------------------------------------------
# Tool: list_agents
# ---------------------------------------------------------------------------
def tool_list_agents() -> dict:
    """
    List all registered agents in the gateway.

    Returns:
        Dict mapping agent names to their records
    """
    return load_names()


# ---------------------------------------------------------------------------
# Tool: broadcast
# ---------------------------------------------------------------------------
def tool_broadcast(message: str, agent_name: str = None, target: str = "telegram_channel",
                   intended_uses: list = None) -> dict:
    """
    Broadcast a message to the gateway. All agents can read it.
    The message is tagged with the sender's name, agent_id, and location
    so recipients know exactly who sent it.

    Args:
        message: The message content to broadcast
        agent_name: Your agent name (auto-detected if omitted and exactly one registered)
        target: Target channel (default: telegram_channel)
        intended_uses: What this message is for; checked against the prohibited-use list

    Returns:
        The broadcast entry with full metadata
    """
    return gw_broadcast(message, agent_name=agent_name, target=target,
                        intended_uses=intended_uses)


# ---------------------------------------------------------------------------
# Tool: read_messages
# ---------------------------------------------------------------------------
def tool_read_messages(since: str = None, agent: str = None, limit: int = 50) -> list:
    """
    Read messages from the gateway.

    Args:
        since: ISO timestamp filter (only messages after this time)
        agent: Filter to messages from a specific agent
        limit: Maximum number of messages to return (default 50)

    Returns:
        List of message entries, newest first
    """
    if not MESSAGES_FILE.exists():
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
    return messages[:limit]


# ---------------------------------------------------------------------------
# Tool: send_to_agent
# ---------------------------------------------------------------------------
def tool_send_to_agent(message: str, target_agent: str, agent_name: str = None,
                       intended_uses: list = None) -> dict:
    """
    Send a direct message to a specific agent.
    The target agent can read it with read_messages(filtered by their name).

    Args:
        message: Message content
        target_agent: The recipient agent's name
        agent_name: Your agent name (auto-detected if omitted)
        intended_uses: What this message is for; checked against the prohibited-use list

    Returns:
        The message entry, or a structured refusal
    """
    if not agent_name:
        names = load_names()
        if len(names) == 1:
            agent_name = list(names.keys())[0]
        else:
            return {"error": "Multiple agents registered. Specify agent_name."}

    if target_agent not in load_names():
        return {"error": f"Target agent '{target_agent}' not registered."}

    # A direct message is still a relayed message: it goes through the same
    # admission control as a broadcast. Writing first and validating later
    # would mean the message had already been relayed.
    try:
        admission, _ = relay.admit(
            agent_name, "direct_message", GATEWAY_DIR, intended_uses=intended_uses
        )
    except relay.RelayRefused as exc:
        return exc.as_dict()

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent_name": agent_name,
        "agent_id": load_names().get(agent_name, {}).get("agent_id", ""),
        "location": load_names().get(agent_name, {}).get("location", "unknown"),
        "target_agent": target_agent,
        "message": message,
        "type": "direct_message",
        "source": "hermes_gateway",
        "message_id": uuid.uuid4().hex[:12],
        "admission": admission.as_dict(),
    }

    GATEWAY_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESSAGES_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    entry["provenance"] = relay.record_provenance(entry)
    return entry


# ---------------------------------------------------------------------------
# Tool: send_human_message
# ---------------------------------------------------------------------------
def tool_send_human_message(message: str, human_name: str = None, target_agent: str = None,
                            intended_uses: list = None) -> dict:
    """
    Send a message as a human into the gateway.
    Agents see this as a human-originated message — no AI markers,
    no machine identity, exactly what a human user would post.

    This is the estate's impersonation surface, so it is the one tool that
    REQUIRES a declared intended use. The prohibited-use gate refuses a purpose
    the estate has ruled out, and the refusal is returned instead of the entry.

    Args:
        message: The message content
        human_name: Human sender name (default: "mem20")
        target_agent: If set, this is a direct message to a specific agent
        intended_uses: What this message is for. Required — see above.

    Returns:
        The message entry, or a structured refusal
    """
    if not human_name:
        human_name = "mem20"

    if not intended_uses:
        return {
            "refused": True,
            "check": "undeclared_use",
            "reason": (
                "send_human_message posts as a human; declare intended_uses so "
                "the prohibited-use gate can rule on it"
            ),
        }

    try:
        admission, _ = relay.admit(
            human_name, "human_message", GATEWAY_DIR, intended_uses=intended_uses
        )
    except relay.RelayRefused as exc:
        return exc.as_dict()

    # Human messages carry only what a human would naturally provide.
    # No AI-specific fields, no machine metadata, no tool_id, no agent_id.
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender": human_name,
        "message": message,
        "type": "human_message",
        "admission": admission.as_dict(),
    }

    if target_agent:
        entry["target"] = target_agent
        entry["type"] = "direct_message"

    GATEWAY_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESSAGES_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    entry["provenance"] = relay.record_provenance(entry)
    return entry


# ---------------------------------------------------------------------------
# Tool: agent_status
# ---------------------------------------------------------------------------
def tool_agent_status(agent_name: str = None) -> dict:
    """
    Get detailed status of this agent or another agent in the gateway.

    Args:
        agent_name: Agent to query (your own if omitted)

    Returns:
        Agent status record
    """
    names = load_names()

    if not agent_name:
        if len(names) == 1:
            agent_name = list(names.keys())[0]
        elif len(names) > 1:
            return {"error": "Multiple agents registered. Specify agent_name."}
        else:
            return {"error": "No agents registered."}

    if agent_name not in names:
        return {"error": f"Agent '{agent_name}' not registered."}

    info = names[agent_name]
    return {
        "name": agent_name,
        "agent_id": info.get("agent_id"),
        "location": info.get("location"),
        "status": info.get("status", "unknown"),
        "registered_at": info.get("registered_at"),
        "last_ping": info.get("last_ping"),
        "collision_avoided": info.get("collision_avoided", False)
    }


# ---------------------------------------------------------------------------
# Tool: gateway_stats
# ---------------------------------------------------------------------------
def tool_gateway_stats() -> dict:
    """
    Get overall gateway statistics.

    Returns:
        Stats dict with agent count, message count, etc.
    """
    names = load_names()
    msg_count = sum(1 for _ in open(MESSAGES_FILE)) if MESSAGES_FILE.exists() else 0

    active = sum(1 for info in names.values() if info.get("status") == "active")
    total = len(names)

    return {
        "total_agents": total,
        "active_agents": active,
        "total_messages": msg_count,
        "agents": {
            name: {
                "location": info.get("location"),
                "status": info.get("status"),
                "registered_at": info.get("registered_at"),
                "last_ping": info.get("last_ping")
            }
            for name, info in names.items()
        }
    }


# ---------------------------------------------------------------------------
# Tool catalog: all gateway tools
# ---------------------------------------------------------------------------
GATEWAY_TOOLS = {
    "register_agent": {
        "function": tool_register_agent,
        "description": "Register this agent in the gateway with a unique name",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Desired agent name (auto-generated if omitted)"},
                "location": {"type": "string", "description": "VPS hostname or location identifier"}
            },
            "required": []
        }
    },
    "list_agents": {
        "function": tool_list_agents,
        "description": "List all registered agents in the gateway",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "broadcast": {
        "function": tool_broadcast,
        "description": "Broadcast a message to all agents in the gateway. Tagged with sender name, agent_id, and location. Declare intended_uses so the prohibited-use gate can rule on it.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message content to broadcast"},
                "agent_name": {"type": "string", "description": "Your agent name (auto-detected if one registered)"},
                "target": {"type": "string", "description": "Target channel (default: telegram_channel)"},
                "intended_uses": {"type": "array", "items": {"type": "string"}, "description": "What this message is for; checked against the prohibited-use list"}
            },
            "required": ["message"]
        }
    },
    "read_messages": {
        "function": tool_read_messages,
        "description": "Read messages from the gateway, optionally filtered by agent or time",
        "parameters": {
            "type": "object",
            "properties": {
                "since": {"type": "string", "description": "ISO timestamp filter"},
                "agent": {"type": "string", "description": "Filter to messages from a specific agent"},
                "limit": {"type": "integer", "description": "Max messages to return (default 50)"}
            },
            "required": []
        }
    },
    "send_to_agent": {
        "function": tool_send_to_agent,
        "description": "Send a direct message to a specific agent. Goes through the same admission control as a broadcast.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message content"},
                "target_agent": {"type": "string", "description": "Recipient agent's name"},
                "agent_name": {"type": "string", "description": "Your agent name (auto-detected if one registered)"},
                "intended_uses": {"type": "array", "items": {"type": "string"}, "description": "What this message is for; checked against the prohibited-use list"}
            },
            "required": ["message", "target_agent"]
        }
    },
    "send_human_message": {
        "function": tool_send_human_message,
        "description": "Send a message as a human into the gateway. Agents see this as a human-originated message with no AI markers. intended_uses is REQUIRED: this is the estate's impersonation surface, so the prohibited-use gate must rule on it.",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "The message content"},
                "human_name": {"type": "string", "description": "Human sender name (default: mem20)"},
                "target_agent": {"type": "string", "description": "If set, direct message to a specific agent"},
                "intended_uses": {"type": "array", "items": {"type": "string"}, "description": "What this message is for. Required."}
            },
            "required": ["message", "intended_uses"]
        }
    },
    "agent_status": {
        "function": tool_agent_status,
        "description": "Get detailed status of this agent or another agent in the gateway",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string", "description": "Agent to query (your own if omitted)"}
            },
            "required": []
        }
    },
    "gateway_stats": {
        "function": tool_gateway_stats,
        "description": "Get overall gateway statistics (agent count, message count, etc.)",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}


def get_gateway_tools() -> dict:
    """Return the tool catalog for MCP server registration."""
    return GATEWAY_TOOLS


def call_gateway_tool(tool_name: str, arguments: dict) -> dict:
    """
    Dispatch a gateway tool call. This is the entry point for the MCP server.

    Args:
        tool_name: Name of the tool to call
        arguments: Tool arguments as dict

    Returns:
        Tool result as dict
    """
    if tool_name not in GATEWAY_TOOLS:
        return {"error": f"Unknown tool: {tool_name}"}

    func = GATEWAY_TOOLS[tool_name]["function"]
    try:
        result = func(**arguments)
        return {"result": result}
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}


if __name__ == "__main__":
    # CLI test mode
    import argparse
    parser = argparse.ArgumentParser(description="mem20 Gateway Tools — test mode")
    parser.add_argument("tool", help="Tool name to call")
    parser.add_argument("--json-args", "-j", help="JSON arguments string")
    args = parser.parse_args()

    if args.json_args:
        arguments = json.loads(args.json_args)
    else:
        arguments = {}

    result = call_gateway_tool(args.tool, arguments)
    print(json.dumps(result, indent=2, default=str))
