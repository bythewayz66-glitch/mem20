from __future__ import annotations

from .openai_compat import OpenAICompatProviderBase


class OVHCloudProvider(OpenAICompatProviderBase):
    def __init__(self, *, base_url: str, api_key: str = "") -> None:
        key = (api_key or "").strip()
        super().__init__(
            name="ovhcloud",
            base_url=base_url,
            api_key=key,
            keyless=not bool(key),
            # Common OVH AI Endpoints model names vary; keep generic fallbacks and rely on probing when possible
            default_model="Meta-Llama-3_1-70B-Instruct",
            preferred_models=[
                "Meta-Llama-3_1-70B-Instruct",
                "Meta-Llama-3_1-8B-Instruct",
                "Mistral-7B-Instruct-v0.3",
                "Llama-3.1-70B-Instruct",
                "llama-3.1-70b-instruct",
            ],
            chat_path="/chat/completions",
            models_path="/models",
        )
