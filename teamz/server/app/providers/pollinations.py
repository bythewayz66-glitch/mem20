from __future__ import annotations

from typing import List, Optional

from .openai_compat import OpenAICompatProviderBase


class PollinationsProvider(OpenAICompatProviderBase):
    def __init__(self, *, base_url: str, keyed_base_url: str, api_key: str = "") -> None:
        key = (api_key or "").strip()
        if key:
            super().__init__(
                name="pollinations",
                base_url=keyed_base_url,
                api_key=key,
                keyless=False,
                default_model="openai",
                preferred_models=["openai", "openai-fast", "openai-large"],
                chat_path="/chat/completions",
                models_path="/models",
            )
            self._mode = "keyed"
        else:
            # Anon endpoint: POST to https://text.pollinations.ai/openai
            super().__init__(
                name="pollinations",
                base_url=base_url,
                api_key="",
                keyless=True,
                default_model="openai-fast",
                preferred_models=["openai-fast"],
                chat_path="",  # base_url is full endpoint
                models_path="",  # handled in override
            )
            self._mode = "anon"

    @property
    def chat_url(self) -> str:
        if self._mode == "anon":
            return self.base_url  # full endpoint
        return super().chat_url

    @property
    def models_url(self) -> str:
        if self._mode == "anon":
            # Public text models list
            if self.base_url.endswith("/openai"):
                return self.base_url.rsplit("/openai", 1)[0] + "/models"
            return "https://text.pollinations.ai/models"
        return super().models_url

    async def candidates(self, ctx, client):  # type: ignore[override]
        cands = await super().candidates(ctx, client)
        # Anon tier only reliably serves free/openai-fast style models; don't pretend others work keylessly.
        if self._mode == "anon":
            safe = [c for c in cands if c.get("model") in ("openai-fast", "openai")]
            if not safe and cands:
                safe = [dict(cands[0], model="openai-fast")]
            return safe or [{"provider": self.name, "model": "openai-fast", "url": self.chat_url, "headers": self.headers(), "keyless": True, "base_url": self.base_url, "local_runtime": False}]
        return cands
