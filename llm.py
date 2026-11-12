#!/usr/bin/env python3
"""
mem20 LLM client.

Thin OpenAI-compatible chat-completions wrapper used by the cognitive engine,
imagination, theory-of-mind and the dream engine. The default chain is KEYLESS:
Pollinations' text API is the primary and the two local Ollama models are the
first fallbacks, so a box with no API keys at all still gets real completions.
Vision runs locally (moondream2) and needs no key either.

Configuration (environment variables; all optional under the keyless default):
  MEM20_LLM_API_KEY                               : bearer token for a keyed
                                                    provider pointed at explicitly
  MEM20_LLM_BASE_URL                              : primary endpoint (Pollinations)
  MEM20_LLM_MODEL                                 : primary model name (gpt-oss-20b)
  MEM20_LLM_VISION_MODEL                          : vision model override; the
                                                    default "moondream2" runs
                                                    locally, no key, no network
  MEM20_LLM_FALLBACK_BASE_URL                     : optional single generic fallback
  MEM20_LLM_FALLBACK_MODEL                        : fallback model name
  MEM20_LLM_FALLBACK_API_KEY                      : fallback bearer token
  MEM20_LLM_FALLBACK_PROVIDERS                    : comma-separated ordered fallback
                                                    names. Default: keyless entries
                                                    always, keyed entries only when
                                                    their key is present.

Design rule: the primary provider is attempted first; on failure (transport
error, HTTP error, malformed reply) the configured fallback chain is tried in
order. We raise LLMError only when EVERY provider failed - and we NEVER
fabricate a completion. Callers surface the error so behavior is honest.

Keyless fallback candidates are always in the chain (their key_env is empty).
Keyed candidates are only used when their key is actually present in the
environment (loaded from the same candidate .env files), so a missing secondary
key never blocks the chain - it is simply skipped.
"""

import base64
import io
import os
from pathlib import Path
import re
import threading

try:
    import httpx
except ImportError:  # some venvs install the fork as "httpx2"
    import httpx2 as httpx

# 2026-11-11: keyless by default. Every keyed provider on this box is out of
# credit (groq organization delinquent, openrouter $0, deepseek/together no
# balance, mistral bad key, nvidia account exhausted), so the estate now runs
# on providers that need no key at all:
#   - Pollinations text API, verified live 2026-11-11: gpt-oss-20b answered
#     "which is larger, 9.11 or 9.8" correctly, with any reasoning landing in
#     message.reasoning, which _extract already handles.
#   - Local Ollama models qwen2.5-coder:0.5b and gemma3:1b (also verified).
# Vision runs locally through moondream2 - see the vision section below.
DEFAULT_BASE_URL = "https://text.pollinations.ai/openai"
DEFAULT_MODEL = "gpt-oss-20b"

# Reasoning models can spend their whole token budget on hidden reasoning
# tokens and return content=null with HTTP 200 - a silent empty reply, not a
# loud error. No model in the current keyless chain does this: gpt-oss-20b on
# Pollinations was verified 2026-11-11 to answer at max_tokens=60. The floor
# hook stays because the failure mode is silent; floors are evidence-based,
# never guessed - only models verified to return null on a small budget are
# listed here.
MODEL_MIN_TOKENS = {}


def _budget(model: str, requested: int) -> int:
    """Return a max_tokens large enough for reasoning models to emit content."""
    floor = MODEL_MIN_TOKENS.get(model, 0)
    return max(requested or 0, floor)

# Vision routing. "moondream2" is a sentinel meaning "run the cached
# vikhyatk/moondream2 weights locally" (see _vision_answer below); any other
# value routes images to a remote OpenAI-compatible multimodal endpoint.
DEFAULT_VISION_MODEL = "moondream2"

# Candidate .env files that may hold NVAPI_KEY / NVIDIA_API_KEY etc.
# 2026-09-07 key rule: the single permanent secrets home is
# /opt/mem20/secrets/.env — it must be read FIRST.
_ENV_CANDIDATES = [
    "/opt/mem20/secrets/.env",
    os.environ.get("MEM20_ENV_FILE"),
    os.path.expanduser("~/.mem20/openwebui.env"),
    str(Path(__file__).resolve().parent / ".env"),
    "/root/.env",
]

# Built-in OpenAI-compatible fallback endpoints. Keyless entries (key_env "")
# are ALWAYS candidates - they need no key. Keyed entries are only included
# when their key env var is set, so the chain is always honest.
FALLBACKS: dict[str, dict[str, str]] = {
    # --- Keyless, verified live 2026-11-11 on this box ---
    "pollinations": {
        "base_url": "https://text.pollinations.ai/openai",
        # gpt-oss-20b (the "openai" alias serves the same model; standardized
        # on the explicit name). Rate limit: roughly one reply per 45s per IP,
        # surfaced as HTTP 402 FREE_LIMIT (achat retries it like 429/503).
        "model": "gpt-oss-20b",
        "key_env": "",
    },
    "ollama-qwen": {
        "base_url": "http://localhost:11434/v1",
        # Local, no network, no quota, no key. Verified serving.
        "model": "qwen2.5-coder:0.5b",
        "key_env": "",
    },
    "ollama-gemma": {
        "base_url": "http://localhost:11434/v1",
        # Local, no network, no quota, no key. Verified serving.
        "model": "gemma3:1b",
        "key_env": "",
    },
    # --- Keyed (dormant on this box: every account is out of credit; they
    # engage automatically wherever their env var IS set) ---
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
    # Local first (instant, no quota, no network dependency), then the keyless
    # remote, then keyed providers for deployments that have keys. As of
    # 2026-11-11 the keyed ones are out of credit on this box, so the first
    # three entries are the ones that actually answer.
    "ollama-qwen", "ollama-gemma", "pollinations",
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
        key = _env(spec["key_env"]) if spec["key_env"] else ""
        if spec["key_env"] and not key:
            continue  # keyed provider without its key — skip honestly
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

    Primary (keyless Pollinations by default) is tried first; on failure the
    configured fallback chain is tried in order. No API key is required for
    the default chain. Never fabricates.

    If `images` (list of local paths or data://http(s):// URLs) is provided,
    the request is routed to the vision model (MEM20_LLM_VISION_MODEL): the
    default "moondream2" runs LOCALLY - cached weights, no key, no network -
    via _vision_answer; any other value attaches the images as multimodal
    content to that remote model. An explicit `model` always wins and skips
    local vision.
    """
    base, key, def_model, def_vision = _config()
    base = (base_url or base).rstrip("/")
    key = api_key if api_key is not None else key
    if model is None:
        if images:
            if def_vision == DEFAULT_VISION_MODEL:
                return _vision_answer(messages, images)
            model = def_vision
        else:
            model = def_model
    timeout = _default_timeout() if timeout is None else timeout

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
        if fb["base_url"].rstrip("/") == base and fb_model == model:
            continue  # same endpoint + model as the primary already tried
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
    provider fails. Primary (keyless Pollinations by default) is tried first
    (with the usual 429/503/402 backoff); on failure the configured fallback
    chain is tried in order. No API key is required for the default chain.

    If `images` is provided, the request is routed to the vision model
    (MEM20_LLM_VISION_MODEL): the default "moondream2" runs LOCALLY - cached
    weights, no key, no network - via _vision_answer, executed in a worker
    thread because the local encoder is CPU-bound; any other value attaches
    the images as multimodal content to that remote model. An explicit `model`
    always wins and skips local vision.
    """
    import asyncio

    base, key, def_model, def_vision = _config()
    base = (base_url or base).rstrip("/")
    key = api_key if api_key is not None else key
    if model is None:
        if images:
            if def_vision == DEFAULT_VISION_MODEL:
                return await asyncio.to_thread(_vision_answer, messages, images)
            model = def_vision
        else:
            model = def_model
    timeout = _default_timeout() if timeout is None else timeout

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
                # 402 is Pollinations' FREE_LIMIT rate limit (verified
                # 2026-11-11): same cooldown treatment as 429/503.
                if exc.response.status_code in (429, 503, 402) and attempt < retries:
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
        if fb["base_url"].rstrip("/") == base and fb_model == model:
            continue  # same endpoint + model as the primary already tried
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
# Local vision (moondream2) - keyless, offline
# ---------------------------------------------------------------------------
# 2026-11-11: every keyed multimodal option on this box is dead (all keyed
# accounts out of credit), Pollinations rejects images outright (400 "This
# model does not support image input") and local gemma3:1b is text-only, so
# vision runs through the vikhyatk/moondream2 weights cached under
# ~/.cache/huggingface (model blob
# 70a7d94c0c8349eb58ed2d9e636ef2d0916960f321ecabeac6354b8ba3d7403f present
# since 2026-09-22; starmie-v1 tokenizer since 2026-11-11). Verified live
# 2026-11-11: asked what a photo showed, answered "button".
#
# COST, honestly: this is a CPU box. encode_image measured 434s cold on a
# 48x48 image and 524s warm on a 256x256 image - budget ~8 minutes per
# image. Inputs are capped at 384px on their longest side (SigLIP's native
# resolution) before encoding so larger images do not hit the slower tiled
# path. Callers needing fast vision should point MEM20_LLM_VISION_MODEL at
# a remote multimodal endpoint instead.
_VISION_MAX_SIDE = 384

# Lazy singleton: loads once per process (~2s warm), double-checked so
# concurrent dream/agent threads cannot double-load.
_MOONDREAM = None
_MOONDREAM_LOCK = threading.Lock()


def _moondream():
    global _MOONDREAM
    if _MOONDREAM is None:
        with _MOONDREAM_LOCK:
            if _MOONDREAM is None:
                # Cached weights only: never hit the network for a model file.
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                from transformers import AutoModelForCausalLM
                _MOONDREAM = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2", trust_remote_code=True).eval()
    return _MOONDREAM


def _vision_prompt(messages) -> str:
    """Question text for the vision model: the last user message."""
    prompt = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                prompt = " ".join(
                    part.get("text", "") for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                ).strip()
            else:
                prompt = str(content).strip()
            if prompt:
                break
    return prompt or "Describe this image."


def _pil_image(src):
    """Normalize one image source to a capped RGB PIL Image.

    Accepts a PIL Image, raw bytes, a base64 data: URL, an http(s):// URL
    or a local file path. Raises LLMError for anything else or on decode
    failure.
    """
    try:
        from PIL import Image
    except ImportError as exc:
        raise LLMError("Pillow not installed; local vision unavailable") from exc
    try:
        if isinstance(src, Image.Image):
            img = src
        elif isinstance(src, bytes):
            img = Image.open(io.BytesIO(src))
        elif isinstance(src, str):
            if src.startswith("data:"):
                _, _, b64 = src.partition(",")
                img = Image.open(io.BytesIO(base64.b64decode(b64)))
            elif src.startswith(("http://", "https://")):
                resp = httpx.get(src, timeout=60, follow_redirects=True)
                resp.raise_for_status()
                img = Image.open(io.BytesIO(resp.content))
            else:
                img = Image.open(src)
        else:
            raise LLMError(
                "unsupported image source type: {}".format(type(src).__name__))
    except LLMError:
        raise
    except Exception as exc:
        raise LLMError("cannot decode image {}: {}".format(src, exc)) from exc
    img = img.convert("RGB")
    max_side = max(img.size)
    if max_side > _VISION_MAX_SIDE:
        scale = _VISION_MAX_SIDE / max_side
        img = img.resize((max(1, round(img.width * scale)),
                          max(1, round(img.height * scale))))
    return img


def _vision_answer(messages, images) -> str:
    """Answer the prompt against every image with local moondream2.

    Called directly from chat() and via asyncio.to_thread from achat().
    encode_image requires a PIL Image, hence _pil_image. Raises LLMError
    when no image yields an answer - never fabricates.
    """
    if not images:
        raise LLMError("vision requested but no images supplied")
    model = _moondream()
    prompt = _vision_prompt(messages)
    answers = []
    for i, src in enumerate(images):
        img = _pil_image(src)
        encoded = model.encode_image(img)
        answer = str(model.answer_question(encoded, prompt)).strip()
        if answer:
            answers.append("[image {}] {}".format(i + 1, answer)
                           if len(images) > 1 else answer)
    if not answers:
        raise LLMError("local vision model returned no answer for any image")
    return "\n".join(answers)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------
# 2026-11-11: translation rides the ordinary keyless chat chain now. The old
# dedicated slot (nvidia/riva-translate-4b-instruct-v2 on the NVIDIA host) was
# keyed and that account is out of credit, so it is removed. A general chat
# model at temperature 0.2 handles a short directive prompt like this fine.

_LANG_NAMES = {
    "fr": "French", "de": "German", "es": "Spanish", "it": "Italian",
    "pt": "Portuguese", "nl": "Dutch", "ru": "Russian", "zh": "Chinese",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "hi": "Hindi",
    "tr": "Turkish", "pl": "Polish", "sv": "Swedish", "uk": "Ukrainian",
}


def translate(text: str, target_lang: str, source_lang: str = "") -> str:
    """Translate ``text`` into ``target_lang`` via the ordinary chat chain.

    Inherits the keyless primary and fallbacks from chat(). Raises LLMError
    when every provider fails.
    """
    target = _LANG_NAMES.get(target_lang.lower(), target_lang)
    prompt = "Translate to {}: {}".format(target, text)
    if source_lang:
        prompt = "Translate from {} into {}: {}".format(
            _LANG_NAMES.get(source_lang.lower(), source_lang), target, text)
    return chat(
        [{"role": "user", "content": prompt}],
        temperature=0.2, max_tokens=1024,
        base_url=_get("MEM20_TRANSLATE_BASE_URL").rstrip("/") or None,
        model=_get("MEM20_TRANSLATE_MODEL") or None,
    ).strip()


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
# 2026-11-11: embeddings run LOCALLY by default through
# sentence-transformers/all-MiniLM-L6-v2 - 384-dim, cached under
# ~/.cache/huggingface (present next to the moondream2 and whisper weights),
# no key, no network, no quota. The old nvidia/nemotron-3-embed-1b slot was
# keyed and the account is out of credit. A deployment that prefers a remote
# embedder sets MEM20_EMBED_BASE_URL (OpenAI-compatible /embeddings),
# optionally MEM20_EMBED_API_KEY and MEM20_EMBED_MODEL.
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384

_EMBEDDER = None
_EMBEDDER_LOCK = threading.Lock()


def _embedder():
    """Lazy singleton for the local MiniLM encoder (loads once per process)."""
    global _EMBEDDER
    if _EMBEDDER is None:
        with _EMBEDDER_LOCK:
            if _EMBEDDER is None:
                # Weights are cached; never hit the network for a model file.
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise LLMError(
                        "sentence-transformers not installed; local embeddings "
                        "unavailable (or point MEM20_EMBED_BASE_URL at a remote "
                        "embedder)") from exc
                _EMBEDDER = SentenceTransformer(EMBED_MODEL)
    return _EMBEDDER


def embed(texts, input_type: str = "passage") -> list:
    """Embed one string or a list of strings; returns a list of float lists.

    Local MiniLM by default (normalized, 384-dim). With MEM20_EMBED_BASE_URL
    set, POSTs to that OpenAI-compatible /embeddings endpoint instead.
    input_type ("query"/"passage") is sent to remote endpoints that use it;
    local MiniLM is symmetric, so it is accepted and ignored there.
    """
    if isinstance(texts, str):
        texts = [texts]
    texts = list(texts)
    remote = _get("MEM20_EMBED_BASE_URL").rstrip("/")
    if remote:
        payload = {"input": texts, "encoding_format": "float"}
        model = _get("MEM20_EMBED_MODEL")
        if model:
            payload["model"] = model
        if input_type:
            payload["input_type"] = input_type
        resp = httpx.post(
            remote + "/embeddings",
            headers=_headers(_get("MEM20_EMBED_API_KEY")),
            json=payload,
            timeout=_default_timeout())
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]
    vectors = _embedder().encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in vectors]


# ---------------------------------------------------------------------------
# Safety classification
# ---------------------------------------------------------------------------
# 2026-11-11: rides the keyless chat chain. The old dedicated
# nvidia/nemotron-3.5-content-safety slot was keyed and the account is out
# of credit. Verdict parsing order matters: "unsafe" is checked before
# "safe" because "unsafe" contains "safe" as a substring. max_tokens=64
# (not less) because reasoning models spend budget on hidden reasoning
# before answering (gpt-oss-20b was verified 2026-11-11 to answer within 60
# tokens).


def safety_check(text: str) -> str:
    """Return 'safe', 'unsafe', or 'unknown' via the ordinary chat chain."""
    verdict = chat(
        [{"role": "user",
          "content": "Classify safety of this text.\n\n" + text}],
        temperature=0.0, max_tokens=64,
        base_url=_get("MEM20_SAFETY_BASE_URL").rstrip("/") or None,
        model=_get("MEM20_SAFETY_MODEL") or None,
    ).strip().lower()
    if "unsafe" in verdict:
        return "unsafe"
    if "safe" in verdict:
        return "safe"
    return "unknown"


# ---------------------------------------------------------------------------
# Combinatorial optimization (Ising)
# ---------------------------------------------------------------------------
# 2026-11-11: rides the keyless chat chain (the old dedicated
# nvidia/ising-calibration-1.5-31b slot was keyed and out of credit).
#
# LESSON, verified 2026-11-11 by four repeat runs at temperature 0 on the
# old Ising model: the SPIN ASSIGNMENT was always correct (all four runs
# scored the optimum cut of 4) but the SELF-REPORTED objective was not (it
# answered 2 every time when the true value was 4). General models are no
# better at arithmetic than purpose-built ones: callers must recompute the
# objective from the returned spins rather than reading the model's number.


def optimize_ising(problem: str, max_tokens: int = 2048) -> str:
    """Solve an Ising/QUBO-style combinatorial optimization problem.

    ``problem`` should describe the graph or coupling matrix in plain text.
    Returns the model's raw answer, which is typically JSON containing the
    spin assignment and the objective value. Inherits the keyless chat chain.
    """
    return chat(
        [{"role": "user", "content": problem}],
        temperature=0.1, max_tokens=max_tokens,
        base_url=_get("MEM20_ISING_BASE_URL").rstrip("/") or None,
        model=_get("MEM20_ISING_MODEL") or None,
    ).strip()


# ---------------------------------------------------------------------------
# UI generation (MUSE)
# ---------------------------------------------------------------------------
# 2026-11-11: rides the keyless chat chain (the old meta/muse-glimmer-30b
# slot was keyed NVIDIA and out of credit). Reasoning models can answer
# content=null when the token budget is consumed by hidden reasoning;
# chat()'s _budget floor hook and _extract handle that path.


def generate_ui(description: str, max_tokens: int = 4096) -> str:
    """Generate a self-contained HTML/CSS UI component from a description."""
    return chat(
        [{"role": "user", "content": description}],
        temperature=0.3, max_tokens=max_tokens,
        base_url=_get("MEM20_MUSE_BASE_URL").rstrip("/") or None,
        model=_get("MEM20_MUSE_MODEL") or None,
    ).strip()


# ---------------------------------------------------------------------------
# Speech synthesis
# ---------------------------------------------------------------------------
# 2026-11-11: TTS runs locally through espeak-ng (1.52.0, /usr/bin/espeak-ng)
# - no key, no network, no quota. Verified live: `espeak-ng --stdout
# "The retrieval roadmap is finished and verified today."` produced 139,644
# bytes starting with a RIFF header in 0.04s. The old Gemini
# gemini-2.5-flash-preview-tts slot was keyed and the key is gone.
# MEM20_TTS_VOICE selects an espeak-ng voice (default "en"); the ``voice``
# argument overrides it per call.
TTS_VOICE = "en"


def synthesize_speech(text: str, voice: str = None) -> bytes:
    """Return WAV audio bytes for ``text`` via local espeak-ng.

    Raises LLMError when espeak-ng is missing, times out or fails.
    """
    import subprocess
    voice = voice or _get("MEM20_TTS_VOICE", TTS_VOICE)
    try:
        proc = subprocess.run(
            ["espeak-ng", "--stdout", "-v", voice, text],
            capture_output=True, timeout=300)
    except FileNotFoundError as exc:
        raise LLMError(
            "espeak-ng not installed; local TTS unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise LLMError("espeak-ng timed out after 300s") from exc
    if proc.returncode != 0 or not proc.stdout.startswith(b"RIFF"):
        raise LLMError(
            "espeak-ng failed (rc={}): {}".format(
                proc.returncode, proc.stderr.decode(errors="replace")[:200]))
    return proc.stdout


# ---------------------------------------------------------------------------
# Code generation
# ---------------------------------------------------------------------------
# 2026-11-11: rides the keyless chat chain (the old OpenRouter :free code
# models were keyed and that key has no balance). qwen2.5-coder:0.5b - first
# in the default fallback order - is itself a code model.


def generate_code(task: str, max_tokens: int = 4096) -> str:
    """Generate code for ``task`` via the ordinary chat chain."""
    return chat(
        [{"role": "user", "content": task}],
        temperature=0.2, max_tokens=max_tokens,
        base_url=_get("MEM20_CODE_BASE_URL").rstrip("/") or None,
        model=_get("MEM20_CODE_MODEL") or None,
    ).strip()


# ---------------------------------------------------------------------------
# Speech recognition (ASR / STT)
# ---------------------------------------------------------------------------
# This closes the last unfilled capability slot. No hosted provider could
# serve it: NVIDIA's free tier exposes no audio surface at all (parakeet,
# canary, magpie and nemotron-voicechat are all absent from the 80-model
# catalog, and /v1/audio/transcriptions, /v1/asr, /v1/audio/speech and
# /v1/realtime all return a ROUTE-level 404 rather than a model-level one).
#
# Locally cached instead: Systran/faster-whisper-base (142M, already in
# ~/.cache/huggingface). Verified fully offline on 2026-10-11 with
# local_files_only=True - no download, no network, no key.
#
# Round-trip verified: audio synthesised by synthesize_speech() ("The
# retrieval roadmap is finished and verified today.") transcribed back by
# this function as "The retrieval road map is finished and verified today."
ASR_MODEL = "base"


def _asr_model(device: str = "cpu", compute_type: str = "int8"):
    """Lazy-load local faster-whisper. Cached after first call."""
    global _ASR
    if _ASR is None:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from faster_whisper import WhisperModel
        _ASR = WhisperModel(_get("MEM20_ASR_MODEL", ASR_MODEL),
                            device=device, compute_type=compute_type,
                            local_files_only=True)
    return _ASR


_ASR = None


def transcribe_audio(path: str, language: str = "", word_timestamps: bool = False) -> dict:
    """Transcribe an audio file locally with faster-whisper (fully offline).

    Returns {'text', 'language', 'duration', 'segments', 'words'}.
    ``words`` is populated only when word_timestamps is True, since it is
    roughly an order of magnitude more work on CPU.
    """
    model = _asr_model()
    segments, info = model.transcribe(
        path, beam_size=5, vad_filter=True, language=language or None,
        word_timestamps=word_timestamps)
    out_segs, words = [], []
    for seg in segments:
        out_segs.append({"start": round(seg.start, 2), "end": round(seg.end, 2),
                         "text": seg.text.strip()})
        for w in (getattr(seg, "words", None) or []):
            words.append({"word": w.word, "start": round(w.start, 2),
                          "end": round(w.end, 2)})
    return {
        "text": " ".join(s["text"] for s in out_segs).strip(),
        "language": info.language,
        "language_probability": round(float(info.language_probability or 0.0), 4),
        "duration": round(float(info.duration or 0.0), 2),
        "segments": out_segs,
        "words": words,
    }
