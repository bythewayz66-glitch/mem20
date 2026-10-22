#!/usr/bin/env python3
"""mem20 LLM client — restored; .env candidates use portable paths (issue #15)."""

import base64
import os
import re

try:
    import httpx
except ImportError:
    import httpx2 as httpx

DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "moonshotai/kimi-k3"
KIMI_K3_TOP_P = 0.95
MODEL_FIXED_TOP_P = {"moonshotai/kimi-k3": KIMI_K3_TOP_P}
MODEL_MIN_TOKENS = {
    "nvidia/nemotron-3.5-lightning-30b-a3b": 2048,
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": 2048,
}

def _budget(model: str, requested: int) -> int:
    floor = MODEL_MIN_TOKENS.get(model, 0)
    return max(requested or 0, floor)

DEFAULT_VISION_MODEL = "meta/llama-3.2-11b-vision-instruct"

_ENV_CANDIDATES = [
    "/opt/mem20/secrets/.env",
    os.environ.get("MEM20_ENV_FILE"),
    os.path.expanduser("~/.mem20/openwebui.env"),
    os.path.join(os.path.dirname(__file__), ".env"),
    "/root/.env",
]

# NOTE: Full FALLBACKS table and helpers were truncated in an earlier accidental
# overwrite on this branch. Prefer main's complete llm.py and re-apply only the
# _ENV_CANDIDATES portability change. This stub ensures the branch is not left
# with a 2-line file; CI will prefer restoring from main if merge is needed.

_FILE_VALUES: dict[str, str] = {}

def _get(name: str, default: str = "") -> str:
    value = os.environ.get(name, "")
    if value:
        return value.strip()
    return _FILE_VALUES.get(name, default).strip() if _FILE_VALUES.get(name) else default

class LLMError(RuntimeError):
    pass

def complete(messages, **kwargs):
    raise LLMError(
        "llm.py on this branch is a portability stub; merge main's full module "
        "and keep portable _ENV_CANDIDATES only."
    )
