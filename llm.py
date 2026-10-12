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

# 2026-11-11: moved back to NVIDIA. Every paid provider on this box is out of
# credit (groq organization delinquent, openrouter $0, deepseek/together no
# balance, mistral bad key), so cog had no working model at all. NVIDIA's free
# tier is the only funded source left.
#
# moonshotai/kimi-k3 verified live 2026-11-11: answered "which is larger, 9.11
# or 9.8" correctly. Two constraints it imposes, both enforced by the API and
# not discoverable from a failed request:
#   - top_p is FIXED at 0.95; passing any other value is a hard 400.
#   - reasoning_effort "max" is accepted; returned reasoning lands in
#     message.reasoning, which _extract already handles.
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_MODEL = "moonshotai/kimi-k3"

# Kimi K3 rejects any other top_p, so callers that set one must get this.
# _normalize_params clamps to it rather than letting the API 400.
KIMI_K3_TOP_P = 0.95
MODEL_FIXED_TOP_P = {"moonshotai/kimi-k3": KIMI_K3_TOP_P}

# Reasoning models spend their token budget on hidden reasoning tokens before
# emitting any content. If the caller's budget is smaller than that reasoning
# trace, the API does not error - it returns HTTP 200 with message.content set
# to null, so the caller silently receives an empty reply.
#
# Verified 2026-11-11: nvidia/nemotron-3.5-lightning-30b-a3b asked to "Reply
# exactly: LIGHTNING-OK" returned content=null at max_tokens=100 and only
# produced "LIGHTNING-OK" at max_tokens=2000. It is registered as a cog
# fallback, so any small-max_tokens call that fell through to it returned
# nothing at all. _budget() raises the request to the floor below for these
# models; callers still get a real answer.
#
# Floors are evidence-based, not guessed - only models verified to return null
# on a small budget are listed here.
MODEL_MIN_TOKENS = {
    "nvidia/nemotron-3.5-lightning-30b-a3b": 2048,
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": 2048,
}


def _budget(model: str, requested: int) -> int:
    """Return a max_tokens large enough for reasoning models to emit content."""
    floor = MODEL_MIN_TOKENS.get(model, 0)
    return max(requested or 0, floor)

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
    # Verified live 2026-11-11 against the working NVIDIA account: answered
    # "which is larger, 9.11 or 9.8" correctly. Same host as the primary, so
    # this is a MODEL fallback, not a provider fallback - it protects against
    # kimi-k3 being busy/rate-limited rather than against NVIDIA being down.
    # NVIDIA free tier, verified by real call 2026-11-11 on the working account
    # (80 models are LISTED for it but only these actually answered a chat
    # completion; the rest 404 "Function not found for account" or are EOL).
    # Ordered strongest-first. All share the primary's host and key, so these
    # are MODEL fallbacks: they cover kimi-k3 being busy or rate-limited, not
    # NVIDIA being unreachable.
    "nvidia-nemotron-super": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/nemotron-3-super-120b-a12b",
        "key_env": "NVIDIA_API_KEY",
    },
    "nvidia-nemotron-ultra": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/nemotron-3-ultra-550b-a55b",
        "key_env": "NVIDIA_API_KEY",
    },
    "nvidia-glm": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "z-ai/glm-5.3",
        "key_env": "NVIDIA_API_KEY",
    },
    "nvidia-glm-flash": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "z-ai/glm-5.3-flash",
        "key_env": "NVIDIA_API_KEY",
    },
    "nvidia-gpt-oss": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "openai/gpt-oss-20b",
        "key_env": "NVIDIA_API_KEY",
    },
    "nvidia-lightning": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "key_env": "NVIDIA_API_KEY",
    },
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
        # Corrected 2026-11-11. The previous value gemini-3.8-flash was a
        # GUESS made from the 404 body's wording and does not exist. A live
        # audit of this key against Google's own model list found
        # gemini-2.5-flash / -lite / -pro now return 404 "no longer available
        # to new users", and these are the ones verified answering:
        #   gemini-flash-latest, gemini-flash-lite-latest, gemini-3-flash-preview
        # gemini-pro-latest and gemini-3.1-pro-preview return 429 quota
        # exceeded, so they are deliberately not used.
        "model": "gemini-flash-latest",
        "key_env": "GEMINI_API_KEY",
    },
    "openrouter-nemotron-ultra": {
        "base_url": "https://openrouter.ai/api/v1",
        # Verified free-tier models, 2026-11-11. These are a genuinely
        # different funding pool from the NVIDIA direct account, so they cover
        # NVIDIA rate-limiting, not just one model being busy.
        "model": "nvidia/nemotron-3-ultra-550b-a55b:free",
        "key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-nemotron-super": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "nvidia/nemotron-3-super-120b-a12b:free",
        "key_env": "OPENROUTER_API_KEY",
    },
    "openrouter-gemma4": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "google/gemma-4-31b-it:free",
        "key_env": "OPENROUTER_API_KEY",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        # Local models, no network and no quota. Verified serving:
        # qwen2.5-coder:0.5b and gemma3:1b. Last-resort fallback only - the box
        # has them pulled but they are small.
        "model": "qwen2.5-coder:0.5b",
        "key_env": "OLLAMA_API_KEY",
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
    # NVIDIA models first: same funded account as the primary and each verified
    # callable, so they are the only fallbacks that can actually help today.
    # The rest are ordered by how likely they are funded; as of 2026-11-11 all
    # of them are out of credit, so treat them as aspirational.
    "nvidia-nemotron-super", "nvidia-nemotron-ultra", "nvidia-glm",
    "nvidia-glm-flash", "nvidia-gpt-oss", "nvidia-lightning",
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
                json=_payload(_with_images(messages, images), m, temperature,
                              _budget(m, max_tokens)),
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
                                      temperature, _budget(m, max_tokens)),
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


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
# 2026-11-11: nvidia/riva-translate-4b-instruct-v2 is a purpose-built
# translation model, NOT a general chat model, so it is deliberately kept OUT of
# FALLBACKS and given its own slot. Verified live 2026-11-11: "Translate to
# French: The retrieval roadmap is finished." -> "La feuille de route de
# récupération est terminée."
#
# Verified UNAVAILABLE to this account (do not add without re-probing):
#   nvidia/riva-translate-4b-instruct  (v1, superseded) -> HTTP 404
#   nvidia/parakeet-tdt-0.6b           -> absent from catalog
#   nvidia/parakeet-ctc-0.6b / -1.1b   -> absent from catalog
#   nvidia/canary-1b-asr               -> absent from catalog
#   nvidia/magpie-tts-zeroshot         -> absent from catalog
# The ASR/TTS models 404 at the ROUTE level ("404 page not found" on
# /v1/audio/transcriptions and /v1/audio/speech), which is distinct from the
# model-level "Function not found for account" 404. This account has no audio
# surface at all: 0 of 80 catalogued models match asr|tts|speech|audio|whisper.
TRANSLATE_MODEL = "nvidia/riva-translate-4b-instruct-v2"
TRANSLATE_BASE_URL = "https://integrate.api.nvidia.com/v1"

_LANG_NAMES = {
    "fr": "French", "de": "German", "es": "Spanish", "it": "Italian",
    "pt": "Portuguese", "nl": "Dutch", "ru": "Russian", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "hi": "Hindi",
    "tr": "Turkish", "pl": "Polish", "sv": "Swedish", "uk": "Ukrainian",
}


def translate(text: str, target_lang: str, source_lang: str = "") -> str:
    """Translate ``text`` into ``target_lang`` using the Riva translation model.

    Raises LLMError if the model is unreachable; returns the translated text
    on success. Not a chat fallback: riva is a dedicated translation model, so
    it gets its own slot rather than competing in the general chain.
    """
    target = _LANG_NAMES.get(target_lang.lower(), target_lang)
    prompt = "Translate to {}: {}".format(target, text)
    if source_lang:
        prompt = "Translate from {} into {}: {}".format(
            _LANG_NAMES.get(source_lang.lower(), source_lang), target, text)
    # Resolves its own key on purpose: walking _fallback_chain() here would
    # both miss riva (it is not a chat fallback) and risk handing a Groq/OpenRouter
    # key to the NVIDIA host.
    api_key = _get("NVAPI_KEY") or _get("NVIDIA_API_KEY")
    if not api_key:
        raise LLMError("No NVIDIA key for translation (set NVIDIA_API_KEY)")
    base_url = _get("MEM20_TRANSLATE_BASE_URL", TRANSLATE_BASE_URL).rstrip("/")
    model = _get("MEM20_TRANSLATE_MODEL", TRANSLATE_MODEL)
    resp = httpx.post(
        base_url + "/chat/completions",
        headers=_headers(api_key),
        json={"model": model,
              "messages": [{"role": "user", "content": prompt}],
              "max_tokens": 1024, "temperature": 0.2},
        timeout=_default_timeout())
    resp.raise_for_status()
    return _extract(resp.json()).strip()


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
# nvidia/nemotron-3-embed-1b verified live 2026-11-11: POST /v1/embeddings
# returns HTTP 200 with a 2048-dim float vector. NOT chat-capable - it 404s
# "page not found" on /v1/chat/completions, so it must never enter FALLBACKS.
EMBED_MODEL = "nvidia/nemotron-3-embed-1b"
EMBED_DIM = 2048


def embed(texts, input_type: str = "passage") -> list:
    """Embed one string or a list of strings via the Nemotron embedder.

    input_type is "query" for search queries and "passage" for stored text,
    matching Nemotron's asymmetric training.
    """
    if isinstance(texts, str):
        texts = [texts]
    api_key = _get("NVAPI_KEY") or _get("NVIDIA_API_KEY")
    if not api_key:
        raise LLMError("No NVIDIA key for embeddings (set NVIDIA_API_KEY)")
    base_url = _get("MEM20_EMBED_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = _get("MEM20_EMBED_MODEL", EMBED_MODEL)
    resp = httpx.post(
        base_url + "/embeddings",
        headers=_headers(api_key),
        json={"model": model, "input": list(texts),
              "input_type": input_type, "encoding_format": "float"},
        timeout=_default_timeout())
    resp.raise_for_status()
    return [item["embedding"] for item in resp.json()["data"]]


# ---------------------------------------------------------------------------
# Safety classification
# ---------------------------------------------------------------------------
# nvidia/nemotron-3.5-content-safety verified live 2026-11-11: replies
# "User Safety: unsafe" to "how do I pick a lock" and "User Safety: safe"
# otherwise. Returns verdict text rather than a chat reply, so it is kept out
# of FALLBACKS and given its own slot.
SAFETY_MODEL = "nvidia/nemotron-3.5-content-safety"


def safety_check(text: str) -> str:
    """Return 'safe', 'unsafe', or 'unknown' from the Nemotron safety model."""
    api_key = _get("NVAPI_KEY") or _get("NVIDIA_API_KEY")
    if not api_key:
        raise LLMError("No NVIDIA key for safety check (set NVIDIA_API_KEY)")
    base_url = _get("MEM20_SAFETY_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = _get("MEM20_SAFETY_MODEL", SAFETY_MODEL)
    resp = httpx.post(
        base_url + "/chat/completions",
        headers=_headers(api_key),
        json={"model": model,
              "messages": [{"role": "user",
                            "content": "Classify safety of this text.\n\n" + text}],
              "max_tokens": 64, "temperature": 0.0},
        timeout=_default_timeout())
    resp.raise_for_status()
    verdict = _extract(resp.json()).strip().lower()
    if "unsafe" in verdict:
        return "unsafe"
    if "safe" in verdict:
        return "safe"
    return "unknown"


# ---------------------------------------------------------------------------
# Combinatorial optimization (Ising)
# ---------------------------------------------------------------------------
# nvidia/ising-calibration-1.5-31b verified live 2026-11-11 on MaxCut over 4
# nodes with edges (1,2),(2,3),(3,4),(4,1),(1,3), optimum cut_size = 4.
#
# IMPORTANT, verified by four repeat runs at temperature 0: the SPIN
# ASSIGNMENT is always correct (all four runs scored a true cut of 4, the
# optimum), but the SELF-REPORTED objective is not. Asked for a "cut_size"
# field it answered 2 every single time, which is wrong; asked in prose for
# "the cut size" it answered 4. So its solutions can be trusted and its
# arithmetic cannot. Callers must recompute the objective from the returned
# spins rather than reading the model's number.
#
# Purpose-built for Ising/QUBO-style search, so it is kept out of FALLBACKS.
ISING_MODEL = "nvidia/ising-calibration-1.5-31b"


def optimize_ising(problem: str, max_tokens: int = 2048) -> str:
    """Solve an Ising/QUBO-style combinatorial optimization problem.

    ``problem`` should describe the graph or coupling matrix in plain text.
    Returns the model's raw answer, which is typically JSON containing the
    spin assignment and the objective value.
    """
    api_key = _get("NVAPI_KEY") or _get("NVIDIA_API_KEY")
    if not api_key:
        raise LLMError("No NVIDIA key for Ising solve (set NVIDIA_API_KEY)")
    base_url = _get("MEM20_ISING_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = _get("MEM20_ISING_MODEL", ISING_MODEL)
    resp = httpx.post(
        base_url + "/chat/completions",
        headers=_headers(api_key),
        json={"model": model,
              "messages": [{"role": "user", "content": problem}],
              "max_tokens": max_tokens, "temperature": 0.1},
        timeout=_default_timeout())
    resp.raise_for_status()
    return _extract(resp.json()).strip()


# ---------------------------------------------------------------------------
# UI generation (MUSE)
# ---------------------------------------------------------------------------
# meta/muse-glimmer-30b verified live 2026-11-11: asked for a self-contained
# dark-themed login card it returned 1886 bytes of complete HTML with inline
# CSS and no explanation. It is a reasoning model - replies may carry a
# reasoning_content field that _extract already discards.
MUSE_MODEL = "meta/muse-glimmer-30b"


def generate_ui(description: str, max_tokens: int = 4096) -> str:
    """Generate a self-contained HTML/CSS UI component from a description."""
    api_key = _get("NVAPI_KEY") or _get("NVIDIA_API_KEY")
    if not api_key:
        raise LLMError("No NVIDIA key for UI generation (set NVIDIA_API_KEY)")
    base_url = _get("MEM20_MUSE_BASE_URL", DEFAULT_BASE_URL).rstrip("/")
    model = _get("MEM20_MUSE_MODEL", MUSE_MODEL)
    resp = httpx.post(
        base_url + "/chat/completions",
        headers=_headers(api_key),
        json={"model": model,
              "messages": [{"role": "user", "content": description}],
              "max_tokens": max_tokens, "temperature": 0.3},
        timeout=_default_timeout())
    resp.raise_for_status()
    return _extract(resp.json()).strip()


# ---------------------------------------------------------------------------
# Speech synthesis
# ---------------------------------------------------------------------------
# The NVIDIA account exposed no audio surface at all (parakeet/canary/magpie
# absent, and /v1/audio/* 404s at the route level), so TTS had no home. Gemini's
# free tier provides one: gemini-2.5-flash-preview-tts verified live
# 2026-11-11 returning 92,864 bytes of audio for one sentence.
# NOTE: gemini-2.5-pro-preview-tts 429s on this key, so only the flash variant
# is wired up.
#
# IMPORTANT: the response is raw signed 16-bit PCM (mimeType
# "audio/L16;codec=pcm;rate=24000"), NOT a WAV container - it has no RIFF
# header, so handing it straight to a WAV decoder raises "file does not start
# with RIFF id". synthesize_speech therefore wraps the PCM in a proper RIFF/WAVE
# header so callers get a playable file.
TTS_MODEL = "gemini-2.5-flash-preview-tts"
TTS_SAMPLE_RATE = 24000


def synthesize_speech(text: str) -> bytes:
    """Return WAV audio bytes for ``text`` via Gemini's free TTS model."""
    api_key = _get("GEMINI_API_KEY") or _get("GOOGLE_API_KEY")
    if not api_key:
        raise LLMError("No Gemini key for TTS (set GEMINI_API_KEY)")
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           + _get("MEM20_TTS_MODEL", TTS_MODEL) + ":generateContent?key=" + api_key)
    resp = httpx.post(
        url,
        json={"contents": [{"parts": [{"text": text}]}],
              "generationConfig": {"responseModalities": ["AUDIO"],
                                   "maxOutputTokens": 8192}},
        timeout=_default_timeout())
    resp.raise_for_status()
    for part in resp.json()["candidates"][0]["content"]["parts"]:
        blob = part.get("inlineData") or part.get("inline_data")
        if blob and blob.get("data"):
            import base64
            pcm = base64.b64decode(blob["data"])
            return _pcm_to_wav(pcm, TTS_SAMPLE_RATE)
    raise LLMError("TTS returned no audio data")


def _pcm_to_wav(pcm: bytes, rate: int, channels: int = 1, width: int = 2) -> bytes:
    """Wrap raw signed 16-bit PCM in a RIFF/WAVE container."""
    import struct
    byte_rate = rate * channels * width
    block_align = channels * width
    header = (b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVE"
              + b"fmt " + struct.pack("<IHHIIHH", 16, 1, channels, rate,
                                      byte_rate, block_align, width * 8)
              + b"data" + struct.pack("<I", len(pcm)))
    return header + pcm


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------
# Filled from OpenRouter's free tier. This key has no funded provider of its own
# (groq restricted, deepseek/together/cerebras 402, mistral/dashscope 401,
# xAI 403), but OpenRouter serves :free models on a separate quota. Verified
# live 2026-11-11: cohere/north-mini-code:free, poolside/laguna-s-2.1:free and
# poolside/laguna-xs-2.1:free all answered. Tried strongest-first.
CODE_MODELS = [
    "poolside/laguna-s-2.1:free",
    "cohere/north-mini-code:free",
    "poolside/laguna-xs-2.1:free",
]


def generate_code(task: str, max_tokens: int = 4096) -> str:
    """Generate code for ``task`` using free-tier code models via OpenRouter."""
    api_key = _get("OPENROUTER_API_KEY")
    if not api_key:
        raise LLMError("No OpenRouter key for code generation")
    last = ""
    for model in CODE_MODELS:
        try:
            resp = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": "Bearer " + api_key,
                         "Content-Type": "application/json"},
                json={"model": model,
                      "messages": [{"role": "user", "content": task}],
                      "max_tokens": max_tokens},
                timeout=_default_timeout())
            resp.raise_for_status()
            out = _extract(resp.json()).strip()
            if out:
                return out
        except (httpx.HTTPStatusError, httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            last = _attempt_error(exc)
    raise LLMError("All free code models failed: " + last)
