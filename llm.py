#!/usr/bin/env python3
"""
mem20 LLM client.

Thin OpenAI-compatible chat-completions wrapper used by the cognitive engine,
imagination, and theory-of-mind tools. Default target is Groq's
OpenAI-compatible endpoint (https://api.groq.com/openai/v1); NVIDIA's free
endpoint remains reachable via MEM20_LLM_BASE_URL / the fallback chain.

Configuration (environment variables):
  GROQ_API_KEY / MEM20_LLM_API_KEY / NVAPI_KEY / NVIDIA_API_KEY : bearer token
  MEM20_LLM_BASE_URL                              : default endpoint
  MEM20_LLM_MODEL                                 : default model name
  NVAPI_KEY / NVIDIA_API_KEY / MEM20_LLM_API_KEY  : primary bearer token (required)
  MEM20_LLM_BASE_URL                              : primary endpoint (default NVIDIA)
  MEM20_LLM_MODEL                                 : primary model name
  MEM20_LLM_FALLBACK_BASE_URL                     : optional single generic fallback
  MEM20_LLM_FALLBACK_MODEL                        : fallback model name
  MEM20_LLM_FALLBACK_API_KEY                      : fallback bearer token
  MEM20_LLM_FALLBACK_PROVIDERS                    : comma-separated ordered fallback
                                                    names (openrouter,groq,gemini,
                                                    deepseek,together,mistral,
                                                    sambanova). Default: all whose
                                                    key is present in the env.

Design rule: the primary provider is attempted first; on failure (missing key,
transport error, HTTP error, malformed reply) the configured fallback chain is
tried in order. We raise LLMError only when EVERY provider failed — and we NEVER
fabricate a completion. Callers surface the error so behavior is honest.

Fallback candidates are only used when their key is actually present in the
environment (loaded from the same candidate .env files), so a missing secondary
key never blocks the chain — it is simply skipped.
"""

import base64
import os
import re

try:
    import httpx
except ImportError:  # some venvs install the fork as "httpx2"
    import httpx2 as httpx

# 2026-09-20: moved default off NVIDIA (too slow for interactive dreaming)
# to Groq gpt-oss-120b. Groq gpt-oss returns reasoning in message.reasoning,
# which _extract already handles.
DEFAULT_BASE_URL = "https://api.groq.com/openai/v1"
DEFAULT_MODEL = "openai/gpt-oss-120b"

# Verified free vision-capable model (multimodal requests route here).
DEFAULT_VISION_MODEL = "meta/llama-3.2-11b-vision-instruct"

# Candidate .env files that may hold NVAPI_KEY / NVIDIA_API_KEY etc.
# 2026-09-07 key rule: the single permanent secrets home is
# /opt/mem20/secrets/.env — it must be read FIRST.
_ENV_CANDIDATES = [
    "/opt/mem20/secrets/.env",
    os.environ.get("MEM20_ENV_FILE"),
    "/home/jayson/Desktop/jayson-openwebui/.env",
    "/home/jayson/mem20/.env",
    "/root/.env",
]

# Built-in OpenAI-compatible fallback endpoints. A candidate is only included in
# the fallback chain when its key env var is set (so the chain is always honest).
FALLBACKS: dict[str, dict[str, str]] = {
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openrouter/auto",
        "key_env": "OPENROUTER_API_KEY",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "key_env": "GROQ_API_KEY",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-2.0-flash",
        "key_env": "GEMINI_API_KEY",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "key_env": "DEEPSEEK_API_KEY",
    },
    "together": {
        "base_url": "https://api.together.xyz/v1",
        "model": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
        "key_env": "TOGETHER_API_KEY",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "model": "mistral-large-latest",
        "key_env": "MISTRAL_API_KEY",
    },
    "sambanova": {
        "base_url": "https://api.sambanova.ai/v1",
        "model": "Meta-Llama-3.1-405B-Instruct",
        "key_env": "SAMBANOVA_API_KEY",
    },
}

DEFAULT_FALLBACK_ORDER = [
    "openrouter", "groq", "gemini", "deepseek", "together", "mistral",
    "sambanova",
]


# Values read from the secrets file, private to this module.
#
# This used to be poured into ``os.environ`` at import time, and that was wrong
# on two counts. It leaked: every process that imports this module - the dream
# engine, the control plane, the cognitive engine, the game build harness - ended
# up holding *every* secret in the estate, including the control-plane admin
# password, the sudo password, database credentials and cloud keys that have
# nothing to do with calling a model. And it was sticky: because the loader
# snapshots once at import and ``_password()``-style lookups prefer the
# environment, a rotated secret in the file was silently ignored for the life of
# the process, which is exactly how the control plane ended up serving a stale
# admin password until someone restarted it.
#
# So the file is read into a private map and consulted only for LLM settings. The
# real environment still wins, which is what a deployment that injects secrets
# that way expects.
_FILE_VALUES: dict[str, str] = {}


def _load_dotenv() -> dict[str, str]:
    """Read LLM settings from the first candidate .env that provides a key.

    Best-effort, and deliberately *not* a mutation of the process environment.
    Returns the values it found so `_get` can consult them.
    """
    for path in _ENV_CANDIDATES:
        if not path or not os.path.exists(path):
            continue
        values: dict[str, str] = {}
        try:
            with open(path, "r") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip().strip('"').strip("'")
                    if key:
                        values[key] = val
        except OSError:
            continue
        _FILE_VALUES.update(values)
        # Only need one successful load for the keys we care about.
        if _get("NVIDIA_API_KEY") or _get("NVAPI_KEY"):
            break
    return _FILE_VALUES


def _get(name: str, default: str = "") -> str:
    """Resolve one setting: the real environment first, then the secrets file."""
    value = os.environ.get(name, "")
    if value:
        return value.strip()
    value = _FILE_VALUES.get(name, "")
    return value.strip() if value else default


def env_value(name: str, default: str = "") -> str:
    """Resolve an LLM setting from the environment or the secrets file.

    Public because other modules legitimately need to know whether a provider is
    funded, and they used to answer that by reading ``os.environ`` directly. That
    only worked because this module used to publish the whole secrets file into
    the environment at import; once it stopped, the dream panel silently found no
    funded members at all. One resolver, so this cannot drift again.
    """
    return _get(name, default)


# Load the private LLM settings map once at import.
_load_dotenv()



class LLMError(RuntimeError):
    """Raised when the LLM cannot produce a real completion."""


def _config():
    base = _get("MEM20_LLM_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    # Key must match the provider the base URL points at. Previously NVAPI_KEY
    # was always preferred, so a Groq base URL paired with NVAPI_KEY sent the
    # NVIDIA key to Groq and failed with HTTP 401 "Invalid API Key".
    if "groq" in base.lower():
        key = (
            _get("GROQ_API_KEY")
            or _get("GROQ_API_KEYS")
            or _get("MEM20_LLM_API_KEY")
            or _get("NVAPI_KEY")
            or _get("NVIDIA_API_KEY")
            or ""
        )
    else:
        key = (
            _get("NVAPI_KEY")
            or _get("NVIDIA_API_KEY")
            or _get("MEM20_LLM_API_KEY")
            or ""
        )
    key = key.strip()
    model = _get("MEM20_LLM_MODEL", DEFAULT_MODEL)
    vision_model = _get("MEM20_LLM_VISION_MODEL", DEFAULT_VISION_MODEL)
    return base, key, model, vision_model


def _headers(key: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def _payload(messages, model, temperature, max_tokens):
    return {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def _extract(content: dict) -> str:
    msg = content["choices"][0]["message"]
    text = msg.get("content") or ""
    if isinstance(text, list):
        text = "".join(p.get("text", "") for p in text if isinstance(p, dict))
    if not text:
        # Reasoning models differ: Groq gpt-oss uses message.reasoning,
        # NVIDIA / others use message.reasoning_content.
        text = msg.get("reasoning") or msg.get("reasoning_content") or ""
    return _strip_thinking(text).strip()


_OPEN  = r"\n\s*<think(?:ing)?>\s*\n?"
_CLOSE = r"\n\s*</think(?:ing)?>\s*\n?"
_RESP  = r"\n\s*response\s*\n?"


def _strip_thinking(text: str) -> str:
    """Drop the model's reasoning preamble up to the answer marker.

    Delimiters vary per provider/model: plain ` thinking ... /thinking`,
    `<thinking> ... </thinking>`, and Groq qwen3.x which emits
    ` thinking ... response` or `<thinking> ... response` (no close tag).
    """
    pairs = [
        (_OPEN, _CLOSE),
        (_OPEN, _RESP),
        (r"\n\s*thinking\s*\n", _RESP),
        (r"\n\s*thinking\s*\n", r"\n\s*/thinking\s*\n?"),
        (r"\n\s*thinking\s*\n", _CLOSE),
        (r"<thinking>\s*", r"</thinking>"),
    ]
    for start, end in pairs:
        m = re.search(start + r".*?" + end, text, flags=re.S | re.I)
        if m:
            return re.sub(start + r".*?" + end, "\n", text, flags=re.S | re.I)
    return text


def _env(name: str, default: str = "") -> str:
    """Resolve an env var plus its numbered *_N variants, first present wins."""
    for i in range(10):
        key = name if i == 0 else f"{name}_{i}"
        val = _get(key)
        if val:
            return val.strip()
    return default






def _image_url(p: str) -> str:
    """Turn a local path or data://http(s):// URL into an OpenAI image_url value."""
    if p.startswith("data:") or p.startswith("http://") or p.startswith("https://"):
        return p
    with open(p, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:image/png;base64,{b64}"


def _with_images(messages, images):
    """Attach image content blocks to the trailing user message (OpenAI multimodal)."""
    if not images:
        return messages
    out = [dict(m) for m in messages]
    for i in range(len(out) - 1, -1, -1):
        if out[i]["role"] == "user":
            content = out[i].get("content")
            if isinstance(content, str):
                blocks = [{"type": "text", "text": content}]
            elif isinstance(content, list):
                blocks = list(content)
            else:
                blocks = [{"type": "text", "text": str(content or "")}]
            for p in images:
                blocks.append({"type": "image_url", "image_url": {"url": _image_url(p)}})
            out[i] = {"role": "user", "content": blocks}
            break
    return out


def _default_timeout() -> float:
    try:
        return float(os.environ.get("MEM20_LLM_TIMEOUT", "900"))
    except ValueError:
        return 900.0


def _fallback_chain() -> list[dict]:
    """Ordered fallbacks with a key actually present, honoring any explicit
    single fallback config (MEM20_LLM_FALLBACK_BASE_URL) before the built-ins.

    Returns a list of dicts: {base_url, model, api_key, name}.
    """
    chain: list[dict] = []
    explicit_base = os.environ.get("MEM20_LLM_FALLBACK_BASE_URL")
    if explicit_base:
        chain.append({
            "base_url": explicit_base.rstrip("/"),
            "model": os.environ.get("MEM20_LLM_FALLBACK_MODEL", ""),
            "api_key": _env("MEM20_LLM_FALLBACK_API_KEY"),
            "name": "fallback-explicit",
        })
    ordered = os.environ.get("MEM20_LLM_FALLBACK_PROVIDERS")
    names = [n.strip() for n in ordered.split(",") if n.strip()] if ordered \
        else DEFAULT_FALLBACK_ORDER
    for name in names:
        spec = FALLBACKS.get(name)
        if not spec:
            continue
        key = _env(spec["key_env"])
        if not key:
            continue  # no key for this provider — skip honestly
        chain.append({
            "base_url": spec["base_url"],
            "model": spec["model"],
            "api_key": key,
            "name": name,
        })
    return chain


def _attempt_error(exc: Exception) -> str:
    """Compact, honest error tag for one provider attempt."""
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:300]}"
    if isinstance(exc, httpx.HTTPError):
        return f"request failed: {exc}"
    return f"malformed response: {exc}"


def chat(
    messages: list,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    base_url: str = None,
    api_key: str = None,
    timeout: float = None,
    images: list = None,
) -> str:
    """Synchronous chat completion. Raises LLMError when EVERY provider fails.

    Primary (NVIDIA by default) is tried first; on failure the configured
    fallback chain (existing keys only) is tried in order. Never fabricates.

    If `images` (list of local paths or data://http(s):// URLs) is provided, they
    are attached as multimodal content to the last user message and the request is
    routed to the vision-capable model (DEFAULT_VISION_MODEL / MEM20_LLM_VISION_MODEL)
    unless an explicit `model` is given.
    """
    base, key, def_model, def_vision = _config()
    base = (base_url or base).rstrip("/")
    key = api_key if api_key is not None else key
    if model is None:
        model = def_vision if images else def_model
    timeout = _default_timeout() if timeout is None else timeout

    if not key:
        raise LLMError(
            "No LLM API key configured. Set NVAPI_KEY / NVIDIA_API_KEY / "
            "MEM20_LLM_API_KEY. Refusing to fabricate reasoning output."
        )

    attempts: list[dict] = []

    def _post(base_url_: str, bearer: str, m: str) -> str:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(
                f"{base_url_}/chat/completions",
                headers=_headers(bearer),
                json=_payload(_with_images(messages, images), m, temperature, max_tokens),
            )
            resp.raise_for_status()
            return _extract(resp.json())

    try:
        return _post(base, key, model)
    except (httpx.HTTPStatusError, httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        attempts.append({"provider": "primary", "model": model,
                         "error": _attempt_error(exc)})

    for fb in _fallback_chain():
        fb_model = fb["model"] or model
        try:
            return _post(fb["base_url"], fb["api_key"], fb_model)
        except (httpx.HTTPStatusError, httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            attempts.append({"provider": fb["name"], "model": fb_model,
                             "error": _attempt_error(exc)})

    raise LLMError(
        "All LLM providers failed (primary + {} fallback{}): {}".format(
            len(attempts) - 1, "s" if len(attempts) - 1 != 1 else "",
            " || ".join(f"{a['provider']}[{a['model']}]: {a['error']}"
                        for a in attempts))
    )



async def achat(
    messages: list,
    model: str = None,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    base_url: str = None,
    api_key: str = None,
    timeout: float = None,
    max_retries: int = 2,
    images: list = None,
) -> str:
    """Async chat completion with retries + fallback. Raises LLMError when EVERY
    provider fails. Primary (NVIDIA by default) is tried first (with the usual
    429/503 backoff); on failure the configured fallback chain is tried in order.

    If `images` (list of local paths or data://http(s):// URLs) is provided, they
    are attached as multimodal content to the last user message and the request is
    routed to the vision-capable model (DEFAULT_VISION_MODEL / MEM20_LLM_VISION_MODEL)
    unless an explicit `model` is given.
    """
    base, key, def_model, def_vision = _config()
    base = (base_url or base).rstrip("/")
    key = api_key if api_key is not None else key
    if model is None:
        model = def_vision if images else def_model
    timeout = _default_timeout() if timeout is None else timeout

    if not key:
        raise LLMError(
            "No LLM API key configured. Set NVAPI_KEY / NVIDIA_API_KEY / "
            "MEM20_LLM_API_KEY. Refusing to fabricate reasoning output."
        )

    import asyncio

    attempts: list[dict] = []

    async def _apost(base_url_: str, bearer: str, m: str,
                     retries: int) -> str:
        last = None
        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    resp = await client.post(
                        f"{base_url_}/chat/completions",
                        headers=_headers(bearer),
                        json=_payload(_with_images(messages, images), m,
                                      temperature, max_tokens),
                    )
                    resp.raise_for_status()
                    return _extract(resp.json())
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code in (429, 503) and attempt < retries:
                    last = exc
                    await asyncio.sleep(30)  # free-tier cooldown
                    continue
                if exc.response.status_code >= 500 and attempt < retries:
                    last = exc
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
            except httpx.HTTPError as exc:
                last = exc
                if attempt < retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
        raise last  # exhausted retries

    try:
        return await _apost(base, key, model, max_retries)
    except (httpx.HTTPStatusError, httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
        attempts.append({"provider": "primary", "model": model,
                         "error": _attempt_error(exc)})

    for fb in _fallback_chain():
        fb_model = fb["model"] or model
        try:
            return await _apost(fb["base_url"], fb["api_key"], fb_model,
                                max_retries)
        except (httpx.HTTPStatusError, httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            attempts.append({"provider": fb["name"], "model": fb_model,
                             "error": _attempt_error(exc)})

    raise LLMError(
        "All LLM providers failed (primary + {} fallback{}): {}".format(
            len(attempts) - 1, "s" if len(attempts) - 1 != 1 else "",
            " || ".join(f"{a['provider']}[{a['model']}]: {a['error']}"
                        for a in attempts))
    )
