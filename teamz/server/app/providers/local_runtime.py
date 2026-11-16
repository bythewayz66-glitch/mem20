from __future__ import annotations

from .openai_compat import OpenAICompatProviderBase


class LocalOpenAIProvider(OpenAICompatProviderBase):
    def __init__(self, base_url: str, index: int = 1) -> None:
        super().__init__(
            name=f"local-{index}",
            base_url=base_url,
            api_key="",
            keyless=True,
            default_model="local-model",
            preferred_models=["local-model"],
            chat_path="/chat/completions",
            models_path="/models",
            local_runtime=True,
        )
