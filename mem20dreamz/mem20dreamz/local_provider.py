"""Local OpenAI-compatible chat-completions server backed by transformers.

Used by the dream engine as a keyless local LLM provider. Each server instance
loads a specific Hugging Face causal-LM model (typically a tiny/test model) and
serves ``POST /v1/chat/completions`` so the existing ``llm.chat`` HTTP client
can call it without special-casing.

This is intentionally small: it exists to provide a real, locally-inferable,
keyless LLM endpoint for the dream engine's provider roster and its e2e tests.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


_PIPELINES: dict[str, Any] = {}
_PIPELINE_LOCK = threading.Lock()


def _get_pipeline(model: str):
    with _PIPELINE_LOCK:
        pipe = _PIPELINES.get(model)
        if pipe is not None:
            return pipe
        from transformers import pipeline  # lazy import: heavy dependency

        pipe = pipeline("text-generation", model=model, device=-1)
        _PIPELINES[model] = pipe
        return pipe


def _messages_to_prompt(messages: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for message in messages or []:
        role = str(message.get("role", "user"))
        content = message.get("content", "")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
        parts.append(f"{role}: {content}")
    parts.append("assistant:")
    return "\n".join(parts)


def generate(model: str, messages: list[dict[str, Any]], max_tokens: int = 64) -> str:
    """Run a local transformers generation and return the assistant text."""
    pipe = _get_pipeline(model)
    prompt = _messages_to_prompt(messages)
    kwargs: dict[str, Any] = {
        "max_new_tokens": max(1, int(max_tokens or 64)),
        "do_sample": False,
        "return_full_text": False,
        "num_return_sequences": 1,
    }
    try:
        result = pipe(prompt, **kwargs)
    except TypeError:
        # Some test/tiny model pipelines reject specific kwargs.
        kwargs.pop("return_full_text", None)
        result = pipe(prompt, **kwargs)
    if not result:
        return ""
    text = result[0].get("generated_text", "")
    if isinstance(text, str):
        return text.strip()
    return str(text).strip()


def make_handler(default_model: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "mem20dreamz-local-provider/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003 - BaseHTTPRequestHandler API
            return

        def _send_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path.rstrip("/") in {"/v1/models", "/models"}:
                self._send_json(
                    200,
                    {"object": "list", "data": [{"id": default_model, "object": "model"}]},
                )
                return
            if self.path.rstrip("/") in {"", "/"}:
                self._send_json(200, {"ok": True, "model": default_model})
                return
            self._send_json(404, {"error": {"message": "not found", "type": "not_found"}})

        def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
            if self.path.rstrip("/") not in {"/v1/chat/completions", "/chat/completions"}:
                self._send_json(404, {"error": {"message": "not found", "type": "not_found"}})
                return
            try:
                length = int(self.headers.get("Content-Length", "0") or "0")
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8") or "{}")
            except Exception as exc:  # noqa: BLE001
                self._send_json(400, {"error": {"message": f"bad request: {exc}", "type": "invalid_request_error"}})
                return

            model = str(payload.get("model") or default_model)
            messages = payload.get("messages") or []
            max_tokens = int(payload.get("max_tokens") or 64)
            try:
                text = generate(model, messages, max_tokens=max_tokens)
            except Exception as exc:  # noqa: BLE001
                self._send_json(500, {"error": {"message": f"{type(exc).__name__}: {exc}", "type": "server_error"}})
                return

            created = int(time.time())
            response = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                "object": "chat.completion",
                "created": created,
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": text},
                        "finish_reason": "stop",
                    }
                ],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            }
            self._send_json(200, response)

    return Handler


def start_local_provider(model: str, host: str = "127.0.0.1", port: int = 0) -> tuple[ThreadingHTTPServer, threading.Thread, str]:
    """Start a background OpenAI-compatible server for ``model``.

    Returns ``(server, thread, base_url)``. ``base_url`` points at the
    OpenAI-compatible root (e.g. ``http://127.0.0.1:PORT/v1``).
    """
    server = ThreadingHTTPServer((host, port), make_handler(model))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    actual_port = server.server_address[1]
    return server, thread, f"http://{host}:{actual_port}/v1"


def stop_local_provider(server: ThreadingHTTPServer) -> None:
    try:
        server.shutdown()
    finally:
        server.server_close()
