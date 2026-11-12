"""Hermetic tests for the llm.py provider fallback chain.

No network, no real keys: every provider is a local fake HTTP endpoint and every
auto-loaded .env key is blocked (llm._FILE_VALUES is cleared) so tests can never
silently hit a real provider. Tests that seal the chain use
MEM20_LLM_FALLBACK_PROVIDERS="groq,mistral" - keyed providers with no key set,
so they are honestly skipped and NOTHING outside the fake servers is reached.
(An explicit empty value would fall back to the default order, which now
contains the real local Ollama - that would not be hermetic.)

Verifies:

  * primary success   -> primary serves, no fallback hit
  * primary failure   -> fallback serves (ordered chain)
  * all fail          -> aggregated, honest LLMError (never fabricates)
  * fallback chain    -> only providers with keys present are candidates
  * keyless defaults  -> no key required at all; keyless entries always in
                         the default chain, keyed ones skipped without keys
  * vision routing    -> default vision model routes to _vision_answer
                         locally (sync and async), no provider call
  * dedup             -> a fallback identical to the primary is not retried
"""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import llm

# Force-hermetic: blank the values llm read from the secrets file at import.
# Nulling `llm._load_dotenv` never did this - the load happens at import, before
# this line runs - so the real provider keys were present throughout. llm keeps
# file values in `_FILE_VALUES` rather than in `os.environ` (that leak is what
# `tests/test_llm_dotenv_isolation.py` guards), so this is the map to clear.
llm._FILE_VALUES.clear()


class _FakeLLM(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        if self.server.code >= 400:
            self.send_response(self.server.code)
            self.end_headers()
            self.wfile.write(b'{"error":"down"}')
            return
        body = {"choices": [{"message": {"content": f"{self.server.tag}"}}]}
        self.send_response(self.server.code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *args):  # silence
        pass


def _start(code: int, tag: str):
    srv = ThreadingHTTPServer(("127.0.0.1", 0), _FakeLLM)
    srv.code, srv.tag = code, tag
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1]


def _isolate_env(pairs: dict) -> None:
    """Set ONLY the given env, removing every real key first.

    llm._env() resolves a key plus its numbered *_N variants, and the mem20
    module also reads the whole MEM20_LLM_* namespace; both must be scrubbed
    so stale real keys can never leak into the chain under test.

    Both of llm's sources are scrubbed: the process environment *and*
    ``_FILE_VALUES``, which holds what it read from the secrets file at import.
    Scrubbing only the environment is not isolation any more, and a test that
    believed it was hermetic while reading the estate's real provider keys would
    be worse than no test at all.
    """
    remove = [
        k for k in list(llm.os.environ)
        if "API_KEY" in k or k.startswith("MEM20_LLM")
    ]
    for k in remove:
        llm.os.environ.pop(k, None)
    llm._FILE_VALUES.clear()
    llm.os.environ.update(pairs)


class FallbackChainTest(unittest.TestCase):
    def test_primary_success_no_fallback(self):
        prim, pp = _start(200, "PRIMARY")
        _isolate_env({
            "NVIDIA_API_KEY": "k1",
            "MEM20_LLM_BASE_URL": f"http://127.0.0.1:{pp}/v1",
            "MEM20_LLM_MODEL": "prim",
        })
        result = llm.chat([{"role": "user", "content": "hi"}], timeout=10)
        prim.shutdown()
        self.assertEqual(result, "PRIMARY")

    def test_primary_down_fallback_serves(self):
        prim, pp = _start(503, "PRIMARY")
        fb, fp = _start(200, "FALLBACK")
        _isolate_env({
            "NVIDIA_API_KEY": "k1",
            "MEM20_LLM_BASE_URL": f"http://127.0.0.1:{pp}/v1",
            "MEM20_LLM_MODEL": "prim",
            "MEM20_LLM_FALLBACK_BASE_URL": f"http://127.0.0.1:{fp}/v1",
            "MEM20_LLM_FALLBACK_MODEL": "fb",
            "MEM20_LLM_FALLBACK_API_KEY": "k2",
            "MEM20_LLM_FALLBACK_PROVIDERS": "groq,mistral",
        })
        result = llm.chat([{"role": "user", "content": "hi"}], timeout=10)
        prim.shutdown()
        fb.shutdown()
        self.assertEqual(result, "FALLBACK")

    def test_all_fail_raises_honest_error(self):
        a, ap = _start(503, "A")
        b, bp = _start(503, "B")
        _isolate_env({
            "NVIDIA_API_KEY": "k1",
            "MEM20_LLM_BASE_URL": f"http://127.0.0.1:{ap}/v1",
            "MEM20_LLM_FALLBACK_BASE_URL": f"http://127.0.0.1:{bp}/v1",
            "MEM20_LLM_FALLBACK_API_KEY": "k2",
            "MEM20_LLM_FALLBACK_PROVIDERS": "groq,mistral",
        })
        with self.assertRaises(llm.LLMError) as cm:
            llm.chat([{"role": "user", "content": "hi"}], timeout=10)
        a.shutdown()
        b.shutdown()
        msg = str(cm.exception)
        self.assertIn("HTTP 503", msg)
        self.assertIn("primary", msg)
        self.assertIn("fallback", msg)

    def test_chain_skips_providers_without_key(self):
        _isolate_env({
            "NVIDIA_API_KEY": "k1",
            "OPENROUTER_API_KEY": "or-k",
            "GEMINI_API_KEY": "",          # empty -> skipped
            "MEM20_LLM_FALLBACK_PROVIDERS": "openrouter,gemini,mistral",
        })
        chain = llm._fallback_chain()
        names = [c["name"] for c in chain]
        self.assertIn("openrouter", names)
        self.assertNotIn("gemini", names)   # empty key -> honest skip
        self.assertNotIn("mistral", names)  # no key set -> honest skip

    def test_async_fallback_serves(self):
        import asyncio
        prim, pp = _start(503, "PRIMARY")
        fb, fp = _start(200, "FALLBACK")
        _isolate_env({
            "NVIDIA_API_KEY": "k1",
            "MEM20_LLM_BASE_URL": f"http://127.0.0.1:{pp}/v1",
            "MEM20_LLM_FALLBACK_BASE_URL": f"http://127.0.0.1:{fp}/v1",
            "MEM20_LLM_FALLBACK_API_KEY": "k2",
            "MEM20_LLM_FALLBACK_PROVIDERS": "groq,mistral",
        })
        result = asyncio.run(llm.achat([{"role": "user", "content": "hi"}],
                                       timeout=10, max_retries=0))
        prim.shutdown()
        fb.shutdown()
        self.assertEqual(result, "FALLBACK")

    def test_keyless_primary_no_key_required(self):
        """The keyless rewire: no API key anywhere and chat still serves."""
        prim, pp = _start(200, "KEYLESS")
        _isolate_env({
            "MEM20_LLM_BASE_URL": f"http://127.0.0.1:{pp}/v1",
            "MEM20_LLM_MODEL": "prim",
            "MEM20_LLM_FALLBACK_PROVIDERS": "groq,mistral",
        })
        result = llm.chat([{"role": "user", "content": "hi"}], timeout=10)
        prim.shutdown()
        self.assertEqual(result, "KEYLESS")

    def test_keyless_fallbacks_always_in_default_chain(self):
        """Default order: keyless entries present, keyed entries skipped."""
        _isolate_env({})
        chain = llm._fallback_chain()
        names = [c["name"] for c in chain]
        for expected in ("ollama-qwen", "ollama-gemma", "pollinations"):
            self.assertIn(expected, names)
        self.assertNotIn("groq", names)       # keyed, no key -> honest skip
        self.assertNotIn("openrouter", names)

    def test_fallback_same_endpoint_as_primary_is_deduped(self):
        """A fallback with the same base URL + model as the primary is not
        retried - the chain must not waste an attempt on a known failure."""
        a, ap = _start(503, "A")
        _isolate_env({
            "MEM20_LLM_BASE_URL": f"http://127.0.0.1:{ap}/v1",
            "MEM20_LLM_MODEL": "prim",
            "MEM20_LLM_FALLBACK_BASE_URL": f"http://127.0.0.1:{ap}/v1",
            "MEM20_LLM_FALLBACK_MODEL": "prim",
            "MEM20_LLM_FALLBACK_PROVIDERS": "groq,mistral",
        })
        with self.assertRaises(llm.LLMError) as cm:
            llm.chat([{"role": "user", "content": "hi"}], timeout=10)
        a.shutdown()
        msg = str(cm.exception)
        self.assertIn("HTTP 503", msg)
        self.assertNotIn("fallback-explicit", msg)

    def test_vision_routes_to_local_sentinel(self):
        """Default vision model = local moondream sentinel: images never reach
        a remote provider; _vision_answer is consulted with the images."""
        saved = llm._vision_answer
        seen = {}

        def fake_vision(messages, images):
            seen["args"] = (messages, images)
            return "LOCAL-VISION"

        llm._vision_answer = fake_vision
        try:
            result = llm.chat(
                [{"role": "user", "content": "what is this"}],
                images=["x.png"], timeout=10)
        finally:
            llm._vision_answer = saved
        self.assertEqual(result, "LOCAL-VISION")
        self.assertEqual(seen["args"][1], ["x.png"])

    def test_async_vision_routes_to_local_sentinel(self):
        import asyncio
        saved = llm._vision_answer
        llm._vision_answer = lambda messages, images: "LOCAL-VISION"
        try:
            result = asyncio.run(llm.achat(
                [{"role": "user", "content": "what is this"}],
                images=["x.png"], timeout=10))
        finally:
            llm._vision_answer = saved
        self.assertEqual(result, "LOCAL-VISION")


if __name__ == "__main__":
    unittest.main()