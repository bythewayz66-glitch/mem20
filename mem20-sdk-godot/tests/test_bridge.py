#!/usr/bin/env python3
"""Fast checks for the committed Godot bridge, with no mem20 server needed.

Run with:  python3 mem20-sdk-godot/tests/test_bridge.py
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest

HERE = pathlib.Path(__file__).resolve().parent
BRIDGE = HERE.parent / "addons" / "mem20" / "mem20_bridge.py"


def run_bridge(request: dict) -> tuple[subprocess.CompletedProcess, dict]:
    with tempfile.TemporaryDirectory() as directory:
        request_path = pathlib.Path(directory) / "request.json"
        response_path = pathlib.Path(directory) / "response.json"
        request_path.write_text(json.dumps(request), encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(BRIDGE), str(request_path), str(response_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if not response_path.exists():
            raise AssertionError(
                "bridge wrote no response file: %s / %s"
                % (completed.stdout, completed.stderr)
            )
        return completed, json.loads(response_path.read_text(encoding="utf-8"))


class BridgeTest(unittest.TestCase):
    def test_compiles(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "py_compile", str(BRIDGE)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_missing_command_is_a_bridge_error(self) -> None:
        completed, response = run_bridge(
            {
                "server_command": ["definitely-not-a-real-mem20-binary"],
                "timeout_sec": 5,
                "messages": [{"jsonrpc": "2.0", "id": 1, "method": "initialize"}],
            }
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("error", response)
        self.assertIn("not found", response["error"])

    def test_missing_messages_is_a_bridge_error(self) -> None:
        completed, response = run_bridge(
            {"server_command": [sys.executable, "-c", "pass"], "messages": []}
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("messages", response["error"])

    def test_roundtrip_parses_ids_and_keeps_server_errors(self) -> None:
        server = textwrap.dedent(
            """
            import json
            import sys

            for line in sys.stdin:
                message = json.loads(line)
                if "id" not in message:
                    continue
                if message["method"] == "initialize":
                    result = {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "fixture", "version": "0"},
                    }
                else:
                    result = {"content": [{"type": "text", "text": "ok"}]}
                print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
            """
        )
        completed, response = run_bridge(
            {
                "server_command": [sys.executable, "-c", server],
                "timeout_sec": 10,
                "messages": [
                    {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
                    {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {}},
                ],
            }
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(response["missing_ids"], [])
        self.assertEqual(response["responses"]["0"]["result"]["protocolVersion"], "2025-06-18")
        self.assertEqual(response["responses"]["7"]["result"]["content"][0]["text"], "ok")

    def test_timeout_is_reported(self) -> None:
        server = "import sys, time\ntime.sleep(30)\n"
        completed, response = run_bridge(
            {
                "server_command": [sys.executable, "-c", server],
                "timeout_sec": 0.5,
                "messages": [{"jsonrpc": "2.0", "id": 1, "method": "initialize"}],
            }
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertTrue(response.get("timeout"), response)


if __name__ == "__main__":
    unittest.main(verbosity=2)
