"""Hermetic tests for mem20owebz — no network, no real keys.

Uses a fake upstream client so /v1/chat/completions failover logic is
exercised against canned responses/failures. Secrets resolution is tested
against explicitly-set env vars (never the host secrets file).
"""

from __future__ import annotations

import os
import sys
import unittest

from mem20owebz.config import (
    DEFAULT_BASES,
    KEYLESS_PROVIDERS,
    ModelConfig,
    Route,
    build_upstream_url,
    env,
    parse_config,
    upstream_base,
    upstream_model_name,
)
from mem20owebz.gateway import GatewayError, ModelGateway, _upstream_payload

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(HERE, os.pardir, os.pardir, "bridge", "litellm_config.yaml")


class FakeResponse:
    def __init__(self, json_data=None, status=200, exc=None):
        self._json = json_data
        self.status = status
        self._exc = exc

    def raise_for_status(self):
        if self._exc:
            raise self._exc

    def json(self):
        if self._exc:
            raise self._exc
        return self._json


class FakeClient:
    """Replays a script of responses; raises when empty."""

    def __init__(self, script=None):
        self.script = list(script or [])
        self.calls = []

    async def post(self, url, headers=None, json=None, **kw):
        self.calls.append((url, headers, json))
        if not self.script:
            raise AssertionError(f"unexpected upstream call: {url}")
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        if callable(item):
            return item(url, headers, json)
        return item


class TestEnvFallback(unittest.TestCase):
    """KEY / KEY_2 / KEY_3 resolution used by the secrets home."""

    def test_env_returns_main(self):
        os.environ["MEM20OWEBZ_TEST_MAIN"] = "first"
        self.assertEqual(env("MEM20OWEBZ_TEST_MAIN"), "first")
        del os.environ["MEM20OWEBZ_TEST_MAIN"]

    def test_env_falls_back_to_numbered_variants(self):
        for k in ("MEM20OWEBZ_TEST_FB", "MEM20OWEBZ_TEST_FB_2", "MEM20OWEBZ_TEST_FB_3"):
            os.environ.pop(k, None)
        os.environ["MEM20OWEBZ_TEST_FB_2"] = "second"
        self.assertEqual(env("MEM20OWEBZ_TEST_FB"), "second")
        os.environ.pop("MEM20OWEBZ_TEST_FB_2", None)

    def test_env_empty_when_absent(self):
        self.assertEqual(env("MEM20OWEBZ_TEST_ABSENT"), "")


class TestConfigParsing(unittest.TestCase):
    """Data-layer: the absorbed litellm config parses into routes/groups."""

    def test_parses_real_config(self):
        cfg = parse_config(CONFIG)
        self.assertGreaterEqual(len(cfg.routes), 40)
        self.assertIn("fast", cfg.router_groups)
        self.assertIn("balanced", cfg.router_groups)
        self.assertIn("strong", cfg.router_groups)
        self.assertEqual(set(cfg.group_fallbacks("fast")), {"balanced", "strong"})

    def test_route_holds_symbolic_key_env(self):
        cfg = parse_config(CONFIG)
        mr = cfg.route("mistral/mistral-small")
        self.assertIsNotNone(mr)
        self.assertEqual(mr.key_env, "MISTRAL_API_KEY")

    def test_default_base_for_provider(self):
        r = Route(alias="groq/x", upstream_model="groq/zx", key_env="GROQ_API_KEY", provider="groq")
        self.assertEqual(upstream_base(r), DEFAULT_BASES["groq"])

    def test_explicit_api_base_wins(self):
        r = Route(alias="tencent/x", upstream_model="openai/x",
                  key_env="TENCENT_MAAS_API_KEY", provider="openai",
                  api_base="https://tokenhub-intl.tencentcloudmaas.com/v1")
        self.assertEqual(upstream_base(r), "https://tokenhub-intl.tencentcloudmaas.com/v1")

    def test_azure_url_shape(self):
        r = Route(alias="foundry/gpt-4o", upstream_model="azure/gpt-4o",
                  key_env="AZURE_API_KEY", provider="azure", api_version="2024-08-01-preview",
                  api_base="https://foundry.example")
        url = build_upstream_url(upstream_base(r), r)
        self.assertIn("/openai/deployments/gpt-4o/chat/completions", url)
        self.assertIn("api-version=2024-08-01-preview", url)

    def test_upstream_model_strips_provider_prefix(self):
        for provider, model, expected in [
            ("nvidia_nim", "nvidia_nim/meta/llama-3.1-8b-instruct", "meta/llama-3.1-8b-instruct"),
            ("google", "gemini/gemini-3.6-flash", "gemini/gemini-3.6-flash"),  # already unprefixed
            ("groq", "groq/llama-3.3-70b-versatile", "llama-3.3-70b-versatile"),
            ("openrouter", "openrouter/meta-llama/llama-3.1-8b-instruct", "meta-llama/llama-3.1-8b-instruct"),
        ]:
            r = Route(alias="x", upstream_model=model, key_env="K", provider=provider)
            self.assertEqual(upstream_model_name(r), expected, model)

    def test_huggingface_url_uses_normalized_model(self):
        r = Route(alias="huggingface/qwen2.5-7b", upstream_model="huggingface/Qwen/Qwen2.5-7B-Instruct",
                  key_env="HF_TOKEN", provider="huggingface")
        url = build_upstream_url(upstream_base(r), r)
        self.assertEqual(url, "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct/chat/completions")

    def test_gemini_max_tokens_stripped(self):
        r = Route(alias="fast", upstream_model="google/gemini-3.6-flash",
                  key_env="GEMINI_API_KEY", provider="google")
        body = {"model": "fast", "max_tokens": 40, "messages": [{"role": "user", "content": "hi"}]}
        out = _upstream_payload(r, body)
        self.assertNotIn("max_tokens", out)
        self.assertEqual(out["model"], "gemini-3.6-flash")

    def test_max_tokens_kept_for_openai(self):
        r = Route(alias="deepseek/chat", upstream_model="deepseek/deepseek-chat",
                  key_env="DEEPSEEK_API_KEY", provider="deepseek")
        out = _upstream_payload(r, {"model": "x", "max_tokens": 100})
        self.assertEqual(out["max_tokens"], 100)


class TestGatewayRouting(unittest.TestCase):
    """Failover + honesty, fully hermetic with a fake client."""

    def _cfg(self):
        return ModelConfig(
            routes=[
                Route(alias="fast", upstream_model="google/gemini-3.6-flash",
                      key_env="GEMINI_API_KEY", provider="google"),
                Route(alias="balanced", upstream_model="groq/llama-3.3-70b-versatile",
                      key_env="GROQ_API_KEY", provider="groq"),
                Route(alias="balanced", upstream_model="google/gemini-3.6-flash",
                      key_env="GEMINI_API_KEY", provider="google"),
            ],
            router_groups={
                "fast": [
                    Route(alias="fast", upstream_model="google/gemini-3.6-flash",
                          key_env="GEMINI_API_KEY", provider="google"),
                ],
                "balanced": [
                    Route(alias="balanced", upstream_model="groq/llama-3.3-70b-versatile",
                          key_env="GROQ_API_KEY", provider="groq"),
                    Route(alias="balanced", upstream_model="google/gemini-3.6-flash",
                          key_env="GEMINI_API_KEY", provider="google"),
                ],
            },
            router_fallbacks={"fast": ["balanced", "strong"]},
        )

    def test_models_honest_only_keyed(self):
        os.environ["GEMINI_API_KEY"] = "test-gemini"
        os.environ.pop("GROQ_API_KEY", None)
        gw = ModelGateway(self._cfg(), client=FakeClient())
        gw.cfg.router_fallbacks = {}
        # balanced has groq (no key) + gemini (key) -> still one keyed alias
        self.assertEqual(len(gw.cfg.keyed()), 2)  # fast + balanced 

    def test_chat_success(self):
        os.environ["GROQ_API_KEY"] = "test-groq"
        script = [FakeResponse({"choices": [{"message": {"content": "hi from groq"}}]})]
        gw = ModelGateway(self._cfg(), client=FakeClient(script))
        body = {"model": "balanced", "messages": [{"role": "user", "content": "yo"}]}
        out = _run(gw.chat_completions(body))
        self.assertEqual(out["choices"][0]["message"]["content"], "hi from groq")
        del os.environ["GROQ_API_KEY"]

    def test_failover_within_group(self):
        os.environ["GROQ_API_KEY"] = "test-groq"
        os.environ["GEMINI_API_KEY"] = "test-gemini"

        def failing(url, headers, payload):
            raise httpx_http_status_error(url)

        import httpx
        script = [
            failing,  # groq member fails
            FakeResponse({"choices": [{"message": {"content": "gemini fallback"}}]}),
        ]
        gw = ModelGateway(self._cfg(), client=FakeClient(script))
        body = {"model": "balanced", "messages": [{"role": "user", "content": "yo"}]}
        out = _run(gw.chat_completions(body))
        content = out["choices"][0]["message"]["content"]
        self.assertEqual(content, "gemini fallback")
        del os.environ["GROQ_API_KEY"], os.environ["GEMINI_API_KEY"]

    def test_all_routes_fail_raises_honestly(self):
        os.environ["GROQ_API_KEY"] = "test-groq"
        os.environ["GEMINI_API_KEY"] = "test-gemini"
        import httpx

        class _ResetNoKey:
            pass
        calls = {"n": 0}
        script = [
            _MakeFail(httpx.ConnectError, "conn refused"),
            _MakeFail(httpx.ConnectError, "conn refused"),
        ]
        gw = ModelGateway(self._cfg(), client=FakeClient(script))
        body = {"model": "balanced", "messages": [{"role": "user", "content": "yo"}]}
        with self.assertRaises(GatewayError) as ctx:
            _run(gw.chat_completions(body))
        self.assertIn("all routes failed", str(ctx.exception))
        del os.environ["GROQ_API_KEY"], os.environ["GEMINI_API_KEY"]

    def test_no_route_raises(self):
        gw = ModelGateway(self._cfg(), client=FakeClient())
        with self.assertRaises(GatewayError):
            _run(gw.chat_completions({"model": "nope"}))


class TestKeylessReality(unittest.TestCase):
    """2026-11-11 rewire: with an empty secrets home the gateway must still
    serve real (keyless) providers, and must not lie that they are keyed."""

    KEY_ENVS = ("GEMINI_API_KEY", "GROQ_API_KEY", "DEEPSEEK_API_KEY",
                "OPENAI_API_KEY", "NVIDIA_API_KEY")

    def setUp(self):
        for k in self.KEY_ENVS:
            os.environ.pop(k, None)

    def test_keyless_providers_have_bases(self):
        self.assertEqual(DEFAULT_BASES["pollinations"], "https://text.pollinations.ai/openai")
        self.assertEqual(DEFAULT_BASES["ollama"], "http://localhost:11434/v1")

    def test_route_available_without_key_for_keyless_provider(self):
        r = Route(alias="ollama/gemma3:1b", upstream_model="ollama/gemma3:1b",
                  provider="ollama")
        self.assertEqual(r.key(), "")
        self.assertTrue(r.available())
        keyed = Route(alias="groq/x", upstream_model="groq/zx",
                      key_env="GROQ_API_KEY", provider="groq")
        self.assertFalse(keyed.available())

    def test_real_config_keyless_routes_usable_with_no_keys(self):
        cfg = parse_config(CONFIG)
        usable = {r.display_name() for r in cfg.keyed()}
        for alias in ("fast", "balanced", "strong",
                      "pollinations/gpt-oss-20b", "ollama/gemma3:1b",
                      "ollama/qwen2.5-coder:0.5b"):
            self.assertIn(alias, usable, alias)
        # keyed-only aliases stay honestly absent
        self.assertNotIn("groq/llama-3.3-70b", usable)

    def test_gateway_picks_keyless_member_with_no_keys(self):
        cfg = parse_config(CONFIG)
        gw = ModelGateway(cfg, client=FakeClient())
        picks = gw._pick("fast")
        self.assertTrue(picks)
        self.assertEqual(picks[0].upstream_model, "ollama/gemma3:1b")

    def test_keyless_proxy_sends_no_authorization_header(self):
        cfg = parse_config(CONFIG)
        script = [FakeResponse({"choices": [{"message": {"content": "local ok"}}]})]
        client = FakeClient(script)
        gw = ModelGateway(cfg, client=client)
        body = {"model": "ollama/gemma3:1b",
                "messages": [{"role": "user", "content": "yo"}]}
        out = _run(gw.chat_completions(body))
        self.assertEqual(out["choices"][0]["message"]["content"], "local ok")
        url, headers, payload = client.calls[0]
        self.assertEqual(url, "http://localhost:11434/v1/chat/completions")
        self.assertNotIn("Authorization", headers)
        self.assertEqual(payload["model"], "gemma3:1b")

    def test_pollinations_url_shape(self):
        r = Route(alias="pollinations/gpt-oss-20b",
                  upstream_model="pollinations/gpt-oss-20b",
                  provider="pollinations")
        self.assertEqual(
            build_upstream_url(upstream_base(r), r),
            "https://text.pollinations.ai/openai/chat/completions")
        self.assertIn(r.provider, KEYLESS_PROVIDERS)
        self.assertTrue(r.available())


class _MakeFail:
    def __init__(self, exc_type, msg):
        self.exc_type = exc_type
        self.msg = msg

    def __call__(self, url, headers, payload):
        raise self.exc_type(self.msg)


def httpx_http_status_error(url):
    import httpx

    req = httpx.Request("POST", url)
    return httpx.HTTPStatusError("500", request=req, response=_StatusResponse(500))


class _StatusResponse:
    status_code = 500

    def __init__(self, code):
        self.status_code = code


def _run(coro):
    import asyncio

    return asyncio.run(coro)


if __name__ == "__main__":
    unittest.main()