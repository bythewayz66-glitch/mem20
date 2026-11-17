"""Provider registry - central place for provider building and management."""

from __future__ import annotations

from typing import Any, List

from ..config import settings
from .base import Attempt, ProviderResult, RouteContext, StreamEvent
from .common import is_dead_local_error
from .llm7 import LLM7Provider
from .local_runtime import LocalOpenAIProvider
from .ovhcloud import OVHCloudProvider
from .pollinations import PollinationsProvider
from .ollama import OllamaProvider
from .llamacpp import LlamaCppProvider
from .vllm import VLLMProvider
from .tgi import TGIProvider


def build_providers(cfg=settings) -> List[Any]:
    providers: List[Any] = []
    # Keyless-first order: providers that can work without keys come early
    providers.append(PollinationsProvider(
        base_url=cfg.pollinations_base_url,
        keyed_base_url=cfg.pollinations_keyed_base_url,
        api_key=cfg.pollinations_api_key,
    ))
    providers.append(LLM7Provider(base_url=cfg.llm7_base_url, api_key=cfg.llm7_api_key))
    providers.append(OVHCloudProvider(base_url=cfg.ovh_base_url, api_key=cfg.ovh_api_key))
    
    # Local providers (keyless, prefer local)
    providers.append(OllamaProvider(
        base_url=cfg.ollama_base_url or "http://localhost:11434",
        default_model=cfg.ollama_default_model,
    ))
    providers.append(LlamaCppProvider(
        base_url=cfg.llamacpp_base_url or "http://localhost:8080",
        default_model=cfg.llamacpp_default_model,
    ))
    providers.append(VLLMProvider(
        base_url=cfg.vllm_base_url or "http://localhost:8000",
        default_model=cfg.vllm_default_model,
    ))
    providers.append(TGIProvider(
        base_url=cfg.tgi_base_url or "http://localhost:8080",
        default_model=cfg.tgi_default_model,
    ))
    
    # Existing local OpenAI-compatible runtimes
    for i, url in enumerate(cfg.local_openai_base_urls, start=1):
        if url:
            providers.append(LocalOpenAIProvider(url, index=i))
    
    # Cloud providers (with keys)
    providers.append(LLM7Provider(base_url=cfg.llm7_base_url, api_key=cfg.llm7_api_key))
    providers.append(OVHCloudProvider(base_url=cfg.ovh_base_url, api_key=cfg.ovh_api_key))
    
    # If keyless_first, ensure providers with keys are not deprioritized incorrectly?
    # "Keyless-first" means prefer keyless-capable paths/providers when available.
    if cfg.keyless_first:
        providers.sort(key=lambda p: 0 if getattr(p, "keyless", False) and not getattr(p, "api_key", "") else 1)
    return providers