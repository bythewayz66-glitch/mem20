"""The expert panel. Every member is backed by a different model.

The owner's rule, and it is the right one: a single-model panel makes its blind
spot *systematic* rather than random, because every member can be confidently
wrong in the same direction and agreement gets laundered into consensus.
Different training lineages have genuinely different blind spots.

Every provider in ``PROVIDERS`` with ``key_env=None`` is keyless: no API key is
required. The dream engine enforces a per-provider minimum interval
(``KEYLESS_RATE_LIMIT_SECONDS``, 30 seconds) between requests to the same
keyless provider so callers do not hammer free-tier endpoints.

Provider roster (keyless):
  * pollinations      — remote keyless OpenAI-compatible proxy (text.pollinations.ai)
  * llm7              — remote keyless OpenAI-compatible API (api.llm7.io)
  * local-tiny-gpt2   — local transformers pipeline (sshleifer/tiny-gpt2)
  * local-tiny-opt    — local transformers pipeline (tiny-random-OPTForCausalLM)
  * local-tiny-bloom  — local transformers pipeline (tiny-random-BloomForCausalLM)
  * local-tiny-gptneo — local transformers pipeline (tiny-random-GPTNeoForCausalLM)
  * local-tiny-llama  — local transformers pipeline (tiny-random-LlamaForCausalLM)
  * local-tiny-phi    — local transformers pipeline (tiny-random-PhiForCausalLM)

Keyed providers (cohere, groq) remain in PROVIDERS/KEY_ENV so deployments with
real keys can widen the panel without code changes; on this host they are
unfunded and excluded.
"""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass
from typing import Any

from .estate import ESTATE_ROOT
sys.path.insert(0, ESTATE_ROOT)
import llm

POLLINATIONS = "https://text.pollinations.ai/openai"
LLM7 = "https://api.llm7.io/v1"
OLLAMA = "http://localhost:11434/v1"
COHERE = "https://api.cohere.com/compatibility/v1"
GROQ = "https://api.groq.com/openai/v1"

#: Per-provider minimum interval (seconds) enforced for keyless providers.
KEYLESS_RATE_LIMIT_SECONDS = 30.0

# Local transformers-backed providers: provider name -> Hugging Face model id.
# These are served by an in-process OpenAI-compatible shim (local_provider.py)
# started lazily on first use so e2e calls work without external setup.
LOCAL_TRANSFORMERS_MODELS: dict[str, str] = {
    "local-tiny-gpt2": "sshleifer/tiny-gpt2",
    "local-tiny-opt": "hf-internal-testing/tiny-random-OPTForCausalLM",
    "local-tiny-bloom": "hf-internal-testing/tiny-random-BloomForCausalLM",
    "local-tiny-gptneo": "hf-internal-testing/tiny-random-GPTNeoForCausalLM",
    "local-tiny-llama": "hf-internal-testing/tiny-random-LlamaForCausalLM",
    "local-tiny-phi": "hf-internal-testing/tiny-random-PhiForCausalLM",
}

_LOCAL_SERVERS: dict[str, dict[str, Any]] = {}
_LOCAL_SERVERS_LOCK = threading.Lock()


def _local_base_url(provider: str) -> str:
    """Return a running local OpenAI-compatible base URL for a transformers provider."""
    model = LOCAL_TRANSFORMERS_MODELS.get(provider)
    if not model:
        return ""
    with _LOCAL_SERVERS_LOCK:
        entry = _LOCAL_SERVERS.get(provider)
        if entry and entry.get("base_url"):
            return str(entry["base_url"])
        from . import local_provider

        server, thread, base_url = local_provider.start_local_provider(model)
        _LOCAL_SERVERS[provider] = {"server": server, "thread": thread, "base_url": base_url, "model": model}
        return base_url


def stop_local_providers() -> None:
    """Stop any lazily-started local transformers provider servers."""
    with _LOCAL_SERVERS_LOCK:
        entries = list(_LOCAL_SERVERS.values())
        _LOCAL_SERVERS.clear()
    for entry in entries:
        server = entry.get("server")
        if server is None:
            continue
        try:
            from . import local_provider

            local_provider.stop_local_provider(server)
        except Exception:
            pass


#: Every provider the panel knows how to reach, with its base URL and its key
#: requirement. ``key_env=None`` means the provider needs no key at all (keyless).
PROVIDERS: dict[str, dict[str, Any]] = {
    # Remote keyless providers
    "pollinations": {"base": POLLINATIONS, "key_env": None},
    "llm7": {"base": LLM7, "key_env": None},
    # Local transformers-backed keyless providers (base resolved lazily)
    "local-tiny-gpt2": {"base": "", "key_env": None, "local_transformers": True},
    "local-tiny-opt": {"base": "", "key_env": None, "local_transformers": True},
    "local-tiny-bloom": {"base": "", "key_env": None, "local_transformers": True},
    "local-tiny-gptneo": {"base": "", "key_env": None, "local_transformers": True},
    "local-tiny-llama": {"base": "", "key_env": None, "local_transformers": True},
    "local-tiny-phi": {"base": "", "key_env": None, "local_transformers": True},
    # Legacy/local keyed-or-local providers kept for compatibility/widening
    "ollama-qwen": {"base": OLLAMA, "key_env": None},
    "ollama-gemma": {"base": OLLAMA, "key_env": None},
    "cohere": {"base": COHERE, "key_env": "COHERE_API_KEY"},
    "groq": {"base": GROQ, "key_env": "GROQ_API_KEY"},
}

#: Keyed providers only - keyless members never consult this map.
KEY_ENV = {name: spec["key_env"]
           for name, spec in PROVIDERS.items() if spec.get("key_env")}

VERIFIED = "verified"
ESTIMATE = "conservative-estimate"


@dataclass(frozen=True)
class Panelist:
    role: str
    provider: str
    model: str
    context: int
    focus: str
    context_source: str = ESTIMATE
    temperature: float = 0.7
    max_tokens: int = 2400
    notes: str = ""

    def resolved_base(self) -> str:
        spec = PROVIDERS.get(self.provider)
        if spec is None:
            raise PanelConfigError(
                f"unknown provider {self.provider!r}: every panel member must "
                "name a provider that exists in PROVIDERS"
            )
        if spec.get("local_transformers"):
            base = _local_base_url(self.provider)
            if not base:
                raise PanelConfigError(
                    f"local transformers provider {self.provider!r} could not be started"
                )
            return base
        base = spec.get("base", "")
        if not base:
            raise PanelConfigError(
                f"provider {self.provider!r} has no base URL configured"
            )
        return base


# One member per model id. All eight are keyless providers wired into the dream
# engine with a 30-second per-provider rate limit.
PANEL: tuple[Panelist, ...] = (
    Panelist(
        role="systems_inventor",
        provider="pollinations",
        model="gpt-oss-20b",
        context=32_768,
        context_source=ESTIMATE,
        focus=(
            "what capability, tool or runtime this needs that does not exist "
            "yet, and the smallest real version of it"
        ),
        temperature=0.85,
        notes="remote keyless OpenAI-compatible proxy; 30s per-provider rate limit",
    ),
    Panelist(
        role="skeptic",
        provider="llm7",
        model="default",
        context=8_192,
        context_source=ESTIMATE,
        focus=(
            "attack the premise. Is this the right thing to be building? "
            "Argue the opposite."
        ),
        temperature=0.6,
        notes="remote keyless OpenAI-compatible API; 30s per-provider rate limit",
    ),
    Panelist(
        role="product",
        provider="local-tiny-gpt2",
        model="sshleifer/tiny-gpt2",
        context=1_024,
        context_source=ESTIMATE,
        focus=(
            "whether this is the right product, scope discipline, and what is "
            "missing that nobody asked for"
        ),
        temperature=0.7,
        notes="local transformers keyless provider; 30s per-provider rate limit",
    ),
    Panelist(
        role="architect",
        provider="local-tiny-opt",
        model="hf-internal-testing/tiny-random-OPTForCausalLM",
        context=1_024,
        context_source=ESTIMATE,
        focus="system structure, interfaces, and integration boundaries",
        temperature=0.7,
        notes="local transformers keyless provider; 30s per-provider rate limit",
    ),
    Panelist(
        role="researcher",
        provider="local-tiny-bloom",
        model="hf-internal-testing/tiny-random-BloomForCausalLM",
        context=1_024,
        context_source=ESTIMATE,
        focus="prior art, evidence, and what is already known or proven",
        temperature=0.7,
        notes="local transformers keyless provider; 30s per-provider rate limit",
    ),
    Panelist(
        role="implementer",
        provider="local-tiny-gptneo",
        model="hf-internal-testing/tiny-random-GPTNeoForCausalLM",
        context=1_024,
        context_source=ESTIMATE,
        focus="concrete implementation steps and smallest working change",
        temperature=0.7,
        notes="local transformers keyless provider; 30s per-provider rate limit",
    ),
    Panelist(
        role="critic",
        provider="local-tiny-llama",
        model="hf-internal-testing/tiny-random-LlamaForCausalLM",
        context=1_024,
        context_source=ESTIMATE,
        focus="failure modes, edge cases, and what would break in practice",
        temperature=0.6,
        notes="local transformers keyless provider; 30s per-provider rate limit",
    ),
    Panelist(
        role="synthesizer",
        provider="local-tiny-phi",
        model="hf-internal-testing/tiny-random-PhiForCausalLM",
        context=1_024,
        context_source=ESTIMATE,
        focus="synthesize critiques into a coherent, improved revision",
        temperature=0.7,
        notes="local transformers keyless provider; 30s per-provider rate limit",
    ),
)

#: Roles that gate the revision. Skeptic and inventor inform but do not gate.
CRITIC_ROLES = tuple(p.role for p in PANEL if p.role not in {"skeptic", "systems_inventor"})
GATING_ROLES = CRITIC_ROLES + ("skeptic",)


def _key_for(provider: str) -> str:
    """Whether a KEYED provider is funded, resolved through llm.

    This used to read ``os.environ`` directly, which worked only by accident:
    ``llm`` published the entire secrets file into the process environment at
    import time, so COHERE_API_KEY and GROQ_API_KEY happened to be there. When
    llm stopped doing that - because it was handing every process that imported it
    the control-plane admin password, the sudo password and every cloud key in
    the estate - this function found nothing and ``panel()`` returned an empty
    list. A funded check that silently reports "nobody" is the worst possible
    failure for a panel whose whole job is to notice it has lost a member.

    Keyless providers (``key_env=None``) have no key to find and return "".
    """
    env = PROVIDERS.get(provider, {}).get("key_env")
    if not env:
        return ""
    return llm.env_value(env)


def _usable(provider: str) -> bool:
    """A provider is usable when it needs no key, or its key is funded.

    An unknown provider is never usable - the roster validation exists so
    that case fails loudly instead of silently dropping a member.
    """
    spec = PROVIDERS.get(provider)
    if spec is None:
        return False
    return not spec["key_env"] or bool(_key_for(provider))


class PanelConfigError(RuntimeError):
    """The roster itself is wrong. Never silently drop a role."""


def assert_roster_valid() -> None:
    """Fail loudly on a duplicated model or an unresolvable provider.

    This previously deduplicated silently, which quietly removed
    ``systems_inventor`` from the panel because it shared a model with
    ``performance`` - the invention register stayed empty and nothing said why.
    A missing panelist is indistinguishable from one with nothing to say, which
    is the exact failure this engine is supposed to avoid, so it raises. The
    provider check exists for the same reason: a provider typo would otherwise
    drop the member at call time instead of at config time.
    """
    ids = [m.model for m in PANEL]
    dupes = sorted({m for m in ids if ids.count(m) > 1})
    if dupes:
        roles = sorted({m.role for m in PANEL if m.model in dupes})
        raise PanelConfigError(
            f"distinct-model rule violated: {', '.join(dupes)} assigned to multiple "
            f"roles ({', '.join(roles)}). Every panel member needs its own model."
        )
    unknown = sorted({m.provider for m in PANEL if m.provider not in PROVIDERS})
    if unknown:
        raise PanelConfigError(
            f"unknown provider(s): {', '.join(unknown)}. Every panel member "
            "must name a provider that exists in PROVIDERS."
        )


def panel() -> list[Panelist]:
    """Usable panelists: keyless providers always, keyed providers when funded.

    The roster is validated, never quietly trimmed."""
    assert_roster_valid()
    return [m for m in PANEL if _usable(m.provider)]


def by_role(role: str) -> Panelist | None:
    return next((m for m in panel() if m.role == role), None)


def smallest_context() -> int:
    members = panel()
    return min((m.context for m in members), default=32_768)


def roster_status() -> dict[str, Any]:
    """What the panel will actually be, and honestly why anything is missing."""
    assert_roster_valid()
    members = panel()
    providers = {m.provider for m in members}
    return {
        "panel_size": len(members),
        "distinct_models": len({m.model for m in members}),
        "distinct_providers": len(providers),
        "distinct_model_rule": "enforced: one member per model id",
        "keyless_rate_limit_s": KEYLESS_RATE_LIMIT_SECONDS,
        "members": [
            {
                "role": m.role,
                "provider": m.provider,
                "model": m.model,
                "context": m.context,
                "context_source": m.context_source,
                "focus": m.focus,
                "notes": m.notes,
            }
            for m in members
        ],
        "unfunded_providers": {
            name: "keyed; no key in the estate (secrets file removed 2026-11-11)"
            for name in KEY_ENV if not _key_for(name)
        },
        "caveat": (
            f"keyless providers wired: {len(members)} members across {len(providers)} "
            f"providers, each enforced with a {int(KEYLESS_RATE_LIMIT_SECONDS)}s "
            "per-provider rate limit. Keyed providers remain unfunded on this host."
        ),
    }
