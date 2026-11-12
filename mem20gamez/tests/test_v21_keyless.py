"""Keyless-provider contract for the v2.1 harness (rewired 2026-11-11).

The estate moved off keyed providers: pollinations (remote, free tier) and
local ollama answer with no credential. These tests pin the parts that are
easy to regress silently - the key inventory saying "ready" without keys,
keyless providers contributing a routing bucket, role assignments pointing at
keyless models, and the vision path using local moondream by default while
refusing to silently switch models when an explicit keyed model is requested.

Hermetic: no network, no model load. vision_chat's llm.chat is monkeypatched.
"""

from __future__ import annotations

import sys

import pytest

from mem20gamez.build_harness import v21


@pytest.fixture(autouse=True)
def _no_provider_env(monkeypatch):
    for name in ("GROQ_API_KEY", "GROQ_API_KEYS", "NVIDIA_API_KEY",
                 "NGC_API_KEY", "NVIDIA_API_KEYS", "NVAPI_KEY",
                 "XAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)


def test_keyless_providers_are_declared():
    assert v21.KEYLESS_PROVIDERS == frozenset({"pollinations", "ollama"})
    assert v21._is_keyless("pollinations")
    assert v21._is_keyless("ollama")
    assert not v21._is_keyless("groq")


def test_keyless_providers_have_a_base_url():
    for prov in v21.KEYLESS_PROVIDERS:
        assert v21.PROVIDER_BASE[prov].startswith("http")


def test_keyless_provider_keys_are_one_empty_bucket():
    for prov in v21.KEYLESS_PROVIDERS:
        assert v21.provider_keys(prov) == [""]
        assert v21._pick_key(prov) == ""


def test_keyed_provider_without_env_has_no_keys():
    assert v21.provider_keys("groq") == []
    assert v21.provider_keys("nvidia") == []


def test_collect_keys_ready_without_any_keys():
    report = v21.collect_keys()
    assert report["ready"] is True
    assert report["keyless"] == {"ollama": True, "pollinations": True}
    assert set(report["missing"]) == {"GROQ_API_KEY", "NVIDIA_API_KEY"}
    assert report["providers"]["pollinations"]["keyless"] is True
    assert report["providers"]["groq"]["present"] is False


def test_worker_buckets_non_empty_without_keys():
    buckets = v21.worker_buckets()
    assert buckets, "no worker bucket without keys - the loop cannot route"
    providers = {b[0] for b in buckets}
    assert providers <= v21.KEYLESS_PROVIDERS
    assert ("pollinations", v21.POLLINATIONS_MODEL, 0) in buckets


def test_role_assignments_are_keyless_first():
    for role, _keys, primary, fallback in v21.ROLE_ASSIGNMENTS:
        assert v21._is_keyless(primary[0]), f"{role} primary is keyed"
        assert v21._is_keyless(fallback[0]), f"{role} fallback is keyed"
    assert v21._is_keyless(v21.ORCHESTRATOR_ASSIGNMENT[0])
    assert v21._is_keyless(v21.SECONDARY_ORCH_ASSIGNMENT[0])


def test_text_candidates_keyless_first_and_deduped():
    cands = v21.text_candidates(v21.assignment_for("systems")[0])
    assert cands[0] == ("pollinations", v21.POLLINATIONS_MODEL)
    keyless = [c for c in cands if v21._is_keyless(c[0])]
    keyed = [c for c in cands if not v21._is_keyless(c[0])]
    assert len(keyless) >= 2, "keyless chain too thin for 402/503 resilience"
    assert cands.index(keyless[-1]) < (cands.index(keyed[0]) if keyed else len(cands))
    assert len(cands) == len(set(cands))


def test_vision_default_uses_local_moondream(monkeypatch):
    import llm

    calls = {}

    def fake_chat(messages, **kwargs):
        calls["messages"] = messages
        calls.update(kwargs)
        return "a red rectangle on blue"

    monkeypatch.setattr(llm, "chat", fake_chat)
    out = v21.vision_chat("/tmp/whatever.png", "describe")
    assert out == "a red rectangle on blue"
    assert calls["images"] == ["/tmp/whatever.png"]
    assert "model" not in calls, "explicit model skips the local vision path"


def test_vision_explicit_nim_model_raises_without_key():
    with pytest.raises(RuntimeError, match="keyed NVIDIA deck"):
        v21.vision_chat("/tmp/whatever.png", "describe", model=v21.NIM_VISION)
