"""LLM provider adapters and routing helpers."""

from .base import Attempt, Provider, ProviderResult, RouteContext
from .ollama import OllamaProvider
from .llamacpp import LlamaCppProvider
from .vllm import VLLMProvider
from .tgi import TGIProvider
from .registry import build_providers
from .health import HealthMonitor, ProviderMetrics, get_health_monitor, score_providers
from .cache import PromptCache, CacheEntry, get_prompt_cache
from .structured import StructuredOutputEnforcer, get_common_schema
from .functions import FunctionCallingShim, FunctionCall, get_function_adapter
from .templates import PromptTemplateManager, ModelPromptTemplate, get_template_manager

__all__ = [
    "Attempt", "Provider", "ProviderResult", "RouteContext",
    "OllamaProvider", "LlamaCppProvider", "VLLMProvider", "TGIProvider",
    "build_providers",
    "HealthMonitor", "ProviderMetrics", "get_health_monitor", "score_providers",
    "PromptCache", "CacheEntry", "get_prompt_cache",
    "StructuredOutputEnforcer", "get_common_schema",
    "FunctionCallingShim", "FunctionCall", "get_function_adapter",
    "PromptTemplateManager", "ModelPromptTemplate", "get_template_manager",
]
