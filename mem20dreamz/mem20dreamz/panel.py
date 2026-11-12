"""The expert panel. Every member is backed by a different model.

The owner's rule, and it is the right one: a single-model panel makes its blind
spot *systematic* rather than random, because every member can be confidently
wrong in the same direction and agreement gets laundered into consensus.
Different training lineages have genuinely different blind spots.

Everything in ``PANEL`` was verified to actually answer, on this host, with a
real call. Model ids and context windows were read from provider endpoints
rather than guessed, because a wrong id is an instant 404 and a panelist that
silently never replies is indistinguishable from one with nothing to say.

KEYLESS REALITY, stated plainly (2026-11-11). The estate secrets file is gone
and with it every provider key, so only keyless surfaces can serve a
completion. Verified by calling them, not by reading a catalog:

* Pollinations - ``https://text.pollinations.ai/openai``, ``gpt-oss-20b``;
  answered a real prompt in ~5s. Free tier is rate-limited to roughly one
  reply per 45s per IP (HTTP 402 FREE_LIMIT), so exactly one member rides it.
* Ollama, local - ``http://localhost:11434/v1``; ``qwen2.5-coder:0.5b`` and
  ``gemma3:1b`` both answered. Context 32768 each, read from ``/api/show``,
  not guessed. CPU-bound and slow, but uncapped and free.

Keyed providers (cohere, groq) stay in PROVIDERS/KEY_ENV so a deployment that
obtains real keys can widen the panel without code changes; on this host they
are honestly unfunded and excluded. The distinct-model rule survives the
smaller roster: gpt-oss-20b, gemma3:1b and qwen2.5-coder:0.5b are three
different training lineages across two providers.

Where a context window is an estimate it says so, because that number decides how
much lineage each panelist can actually read.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from .estate import ESTATE_ROOT
sys.path.insert(0, ESTATE_ROOT)
import llm

POLLINATIONS = "https://text.pollinations.ai/openai"
OLLAMA = "http://localhost:11434/v1"
COHERE = "https://api.cohere.com/compatibility/v1"
GROQ = "https://api.groq.com/openai/v1"

#: Every provider the panel knows how to reach, with its base URL and its key
#: requirement. ``key_env=None`` means the provider needs no key at all -
#: that is the whole basis of the 2026-11-11 keyless rewire.
PROVIDERS: dict[str, dict[str, Any]] = {
    "pollinations": {"base": POLLINATIONS, "key_env": None},
    "ollama-qwen": {"base": OLLAMA, "key_env": None},
    "ollama-gemma": {"base": OLLAMA, "key_env": None},
    "cohere": {"base": COHERE, "key_env": "COHERE_API_KEY"},
    "groq": {"base": GROQ, "key_env": "GROQ_API_KEY"},
}

#: Keyed providers only - keyless members never consult this map.
KEY_ENV = {name: spec["key_env"]
           for name, spec in PROVIDERS.items() if spec["key_env"]}

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
        return spec["base"]


# One member per model id. All three verified answering keyless on this host
# on 2026-11-11 (pollinations gpt-oss-20b ~5s; local Ollama models immediately).
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
        notes=(
            "remote keyless proxy; ~1 reply/45s/IP (HTTP 402 FREE_LIMIT), so "
            "exactly one member rides it. Context through the proxy is an "
            "estimate - gpt-oss-20b natively serves 131k, but the free tier "
            "has not been probed for its real cap"
        ),
    ),
    Panelist(
        role="skeptic",
        provider="ollama-gemma",
        model="gemma3:1b",
        context=32_768,
        context_source=VERIFIED,
        focus=(
            "attack the premise. Is this the right thing to be building? "
            "Argue the opposite."
        ),
        temperature=0.6,
        notes=(
            "local CPU, keyless; general lineage, contrarian by instruction. "
            "0.6 not 0.9: verified 2026-11-11 by repeated calls, gemma3:1b at "
            "0.9 drifted into Chinese on ~1/3 of replies ('失望', '了解') - "
            "wrong-language output that the verdict parsers cannot read"
        ),
    ),
    Panelist(
        role="product",
        provider="ollama-qwen",
        model="qwen2.5-coder:0.5b",
        context=32_768,
        context_source=VERIFIED,
        focus=(
            "whether this is the right product, scope discipline, and what is "
            "missing that nobody asked for"
        ),
        temperature=0.8,
        notes="local CPU, keyless; the code lineage, and the smallest writer on the panel",
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
            "keyless reality 2026-11-11: pollinations (remote, ~1 reply/45s/IP) "
            "and local Ollama (qwen2.5-coder:0.5b, gemma3:1b) are the only usable "
            "providers; every keyed provider is unfunded on this host. Family "
            "diversity is narrower than the distinct-model rule deserves - three "
            "lineages across two providers."
        ),
    }
