"""Issue #10 — DefaultErrorHandler for search rate limits."""
from __future__ import annotations

import sys
import urllib.error
from pathlib import Path

import pytest

# mcp/tools is a script-style dir; put it on path for unit import
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.search_tools import DefaultErrorHandler  # noqa: E402


@pytest.mark.unit
def test_default_error_handler_rate_limit_429():
    err = urllib.error.HTTPError("http://x", 429, "Too Many Requests", hdrs=None, fp=None)
    msg = DefaultErrorHandler.handle(err)
    assert "429" in msg
    assert "Rate limited" in msg or "retry" in msg.lower()


@pytest.mark.unit
def test_default_error_handler_403():
    err = urllib.error.HTTPError("http://x", 403, "Forbidden", hdrs=None, fp=None)
    msg = DefaultErrorHandler.handle(err)
    assert "403" in msg


@pytest.mark.unit
def test_default_error_handler_generic():
    msg = DefaultErrorHandler.handle(RuntimeError("boom"))
    assert "boom" in msg
