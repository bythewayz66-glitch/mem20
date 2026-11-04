#!/usr/bin/env python3
"""One-shot JSON-RPC bridge between the Godot addon and a mem20 MCP server.

Godot's ``OS.execute()`` can run a process and capture its whole output, but it
cannot write to that process's stdin while it runs. The mem20 server speaks
newline-delimited JSON-RPC 2.0 over stdio, so the addon writes one request
file, runs this bridge, and reads one response file:

    python3 mem20_bridge.py <request.json> <response.json>

The request file is a JSON object:

    {
      "server_command": ["python3", "mcp/mcp_server.py"],
      "cwd": "/opt/mem20",
      "env": {"MEM20_STORE_PATH": "/opt/mem20/store"},
      "timeout_sec": 60.0,
      "messages": [ <JSON-RPC message>, ... ]
    }

Every message is written to the server's stdin in one batch (initialize,
notifications/initialized and the actual request), then the server's stdout is
read to EOF. The response file is:

    {"responses": {"<id>": <JSON-RPC response>}, "returncode": 0,
     "stderr": "...", "unparsed": [...]}

or, when the bridge itself cannot complete the transaction:

    {"error": "<human readable reason>", ...}

The bridge exits non-zero only for bridge-level failures. A JSON-RPC error
returned by the server is a successful bridge transaction and is reported in
``responses``.

Standard library only. This file ships inside the Godot addon, so it must run
under any Python 3 interpreter; only the *server* needs the mem20 virtualenv.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys


def _write(path: str, payload: dict) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)


def _fail(path: str, message: str, **extra) -> int:
    payload = {"error": message}
    payload.update(extra)
    _write(path, payload)
    return 1


def _tail(text: str, limit: int = 4000) -> str:
    text = text or ""
    return text[-limit:]


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        sys.stderr.write(
            "usage: mem20_bridge.py <request.json> <response.json>\n"
        )
        return 2

    request_path, response_path = argv[1], argv[2]
    try:
        with open(request_path, encoding="utf-8") as handle:
            request = json.load(handle)
    except OSError as exc:
        return _fail(response_path, "cannot read bridge request: %s" % exc)
    except ValueError as exc:
        return _fail(response_path, "bridge request is not valid JSON: %s" % exc)

    if not isinstance(request, dict):
        return _fail(response_path, "bridge request must be a JSON object")

    command = request.get("server_command")
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(part, str) and part for part in command)
    ):
        return _fail(
            response_path,
            "server_command must be a non-empty array of non-empty strings",
        )

    messages = request.get("messages")
    if not isinstance(messages, list) or not messages:
        return _fail(response_path, "messages must be a non-empty array")

    cwd = request.get("cwd") or None
    if cwd is not None:
        cwd = os.path.expanduser(str(cwd))
        if not os.path.isdir(cwd):
            return _fail(response_path, "server_cwd is not a directory: %s" % cwd)

    env = os.environ.copy()
    extra_env = request.get("env") or {}
    if not isinstance(extra_env, dict):
        return _fail(response_path, "env must be a JSON object")
    for key, value in extra_env.items():
        if not isinstance(key, str) or not key:
            return _fail(response_path, "env keys must be non-empty strings")
        env[key] = str(value)

    try:
        timeout = float(request.get("timeout_sec", 60.0))
    except (TypeError, ValueError):
        return _fail(response_path, "timeout_sec must be a number")
    if timeout <= 0:
        return _fail(response_path, "timeout_sec must be greater than zero")

    payload = "".join(json.dumps(message) + "\n" for message in messages)

    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return _fail(
            response_path,
            "server command not found: %r (%s)" % (command[0], exc),
            server_command=command,
            cwd=cwd,
        )
    except PermissionError as exc:
        return _fail(
            response_path,
            "server command is not executable: %r (%s)" % (command[0], exc),
            server_command=command,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired as exc:
        return _fail(
            response_path,
            "server did not answer within %gs" % timeout,
            timeout=True,
            stderr=_tail(exc.stderr if isinstance(exc.stderr, str) else ""),
            server_command=command,
            cwd=cwd,
        )
    except OSError as exc:
        return _fail(
            response_path,
            "could not start server command %r: %s" % (command[0], exc),
            server_command=command,
            cwd=cwd,
        )

    responses: dict[str, object] = {}
    unparsed: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            unparsed.append(line)
            continue
        if isinstance(message, dict) and "id" in message:
            responses[str(message["id"])] = message

    expected = [
        str(message["id"])
        for message in messages
        if isinstance(message, dict) and "id" in message
    ]
    missing = [identifier for identifier in expected if identifier not in responses]

    result = {
        "responses": responses,
        "returncode": completed.returncode,
        "stderr": _tail(completed.stderr),
        "unparsed": unparsed,
        "missing_ids": missing,
    }

    if not responses and completed.returncode != 0:
        result["error"] = (
            "server exited with code %d before answering" % completed.returncode
        )

    _write(response_path, result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
