"""Shared HTTP error handling for MCP tools (issue #10)."""
from __future__ import annotations

import urllib.error


class DefaultErrorHandler:
    """Maps HTTP 429/402/403 into agent-readable messages."""

    RATE_LIMIT = {429, 402, 403}

    @classmethod
    def handle(cls, exc: BaseException) -> str:
        code = getattr(exc, "code", None)
        if code is None:
            code = getattr(exc, "status", None)
        if code in cls.RATE_LIMIT:
            return (
                f"Rate limited or access denied (HTTP {code}). "
                "Back off and retry later, or switch search engine."
            )
        if isinstance(exc, urllib.error.HTTPError):
            return f"HTTP error {exc.code}: {exc.reason}"
        return f"Error: {exc}"
