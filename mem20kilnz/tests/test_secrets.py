"""Tests for the LLM provider resolution policy in secrets.py.

The engine binary is NOT needed here: these exercise the pure-Python
resolution that decides which endpoint the engine subprocess will be told to
use. The policy under test is the 2026-11-11 keyless rewire: with no secrets
file and no env keys, the resolved provider must be one that answers without
a credential (pollinations), not an unfunded keyed endpoint that would 401.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from mem20kilnz import secrets as S


@pytest.fixture
def hermetic(monkeypatch, tmp_path):
    """No secrets file, no env overrides, no cache."""
    monkeypatch.setattr(S, "SECRETS_PATH", tmp_path / "absent.env")
    monkeypatch.setattr(S, "_cache", None)
    for name in ("KILNZ_API_KEY", "OPENAI_API_KEY", "KILNZ_API_BASE",
                 "OPENAI_API_BASE", "OPENAI_BASE_URL", "KILNZ_MODEL"):
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def test_keyless_pollinations_is_resolved_with_no_key(hermetic):
    cfg = S.llm_config()
    assert cfg["_provider"] == "pollinations"
    assert cfg["KILN_API_KEY"] == ""
    assert cfg["KILN_API_BASE"] == "https://text.pollinations.ai/openai"
    assert cfg["KILN_MODEL"] == "gpt-oss-20b"


def test_engine_env_strips_internal_markers(hermetic):
    env = S.engine_env()
    assert "_provider" not in env
    assert env["KILN_API_BASE"] == "https://text.pollinations.ai/openai"


def test_explicit_env_key_still_wins(hermetic):
    hermetic.setenv("KILNZ_API_KEY", "k-explicit")
    hermetic.setenv("KILNZ_API_BASE", "http://localhost:9999/v1")
    cfg = S.llm_config()
    assert cfg["_provider"] == "explicit"
    assert cfg["KILN_API_KEY"] == "k-explicit"
    assert cfg["KILN_API_BASE"] == "http://localhost:9999/v1"


def test_keyed_provider_needs_a_real_key(hermetic, tmp_path):
    secrets_file = tmp_path / "secrets.env"
    secrets_file.write_text("GROQ_API_KEY=gk-1\n", encoding="utf-8")
    hermetic.setattr(S, "SECRETS_PATH", secrets_file)
    # keyless-first: pollinations is the standing primary even with a groq key
    cfg = S.llm_config()
    assert cfg["_provider"] == "pollinations"
    # but the keyed entry is reported as configured for keyed deployments
    groq = next(p for p in S.provider_candidates() if p["provider"] == "groq")
    assert groq["configured"] is True
    assert groq["keyless"] is False


def test_provider_candidates_report_keyless_providers_as_available(hermetic):
    poll = next(p for p in S.provider_candidates()
                if p["provider"] == "pollinations")
    assert poll["configured"] is True
    assert poll["keyless"] is True
    assert poll["key_name"] == ""


def test_status_reports_keyless_provider(hermetic):
    st = S.status()
    assert st["llm_configured"] is True
    assert st["llm_provider"] == "pollinations"
    assert "pollinations" in st["providers_available"]
    assert st["llm_base"] == "https://text.pollinations.ai/openai"


def test_missing_file_is_empty_not_an_error(hermetic):
    assert S.secrets_available() is False
    assert S.load() == {}
