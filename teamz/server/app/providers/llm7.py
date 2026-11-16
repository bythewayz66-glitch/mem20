from __future__ import annotations

from .openai_compat import OpenAICompatProviderBase


class LLM7Provider(OpenAICompatProviderBase):
    def __init__(self, *, base_url: str, api_key: str = "") -> None:
        key = (api_key or "").strip()
        super().__init__(
            name="llm7",
            base_url=base_url,
            api_key=key,
            keyless=not bool(key),
            # Conservative defaults; real selection will prefer probed chat models
            default_model="gpt-4o-mini",
            preferred_models=["gpt-4.1-mini", "gpt-4o-mini", "deepseek-chat", "gemini-2.0-flash", "llama-3.3-70b"],
            chat_path="/chat/completions",
            models_path="/models",
        )
