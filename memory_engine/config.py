"""Typed configuration for the memory engine.

Why this module exists
----------------------
Before M0 the engine read ``os.environ`` at import time in six places, with no
validation and no single place to see the full set of knobs. A typo in
``MEM20_SIM_TTL_DAYS`` produced a ``ValueError`` from deep inside a function
call, and ``MEM20_STORE_PATH`` pointing at an unwritable directory was only
discovered on the first write.

``EngineConfig`` makes the whole surface explicit, validates it once, and can
be constructed from an explicit mapping (tests) or the process environment
(deployment).

Ordering constraint
-------------------
``memory_engine.memory`` resolves its paths at import time from
``MEM20_STORE_PATH``. So the environment must be set BEFORE the engine module
is imported. ``EngineConfig`` does not change that; it documents it and gives
you ``EngineConfig.apply()`` to set the environment from a validated object.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

from .errors import ConfigurationError

__all__ = ["EngineConfig", "DEFAULT_STORE_PATH"]

DEFAULT_STORE_PATH = "~/.mem20/store"

_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}


def _parse_bool(raw: str, *, name: str) -> bool:
    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    raise ConfigurationError(
        f"{name} must be one of {sorted(_TRUTHY | _FALSY)}, got {raw!r}",
        details={"variable": name, "value": raw},
    )


def _parse_int(raw: str, *, name: str, minimum: int) -> int:
    try:
        value = int(raw.strip())
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"{name} must be an integer, got {raw!r}",
            details={"variable": name, "value": raw},
        ) from exc
    if value < minimum:
        raise ConfigurationError(
            f"{name} must be >= {minimum}, got {value}",
            details={"variable": name, "value": value, "minimum": minimum},
        )
    return value


@dataclass(frozen=True)
class EngineConfig:
    """Validated, immutable engine configuration.

    Frozen so a config object cannot be mutated after the engine has already
    resolved paths from it — the classic source of "the setting is right but
    the engine used the old value" bugs.
    """

    store_path: Path
    sim_ttl_days: int = 30
    rerank_enabled: bool = True
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    mem_cap: int = 2200
    user_cap: int = 1375

    # -- construction -------------------------------------------------------

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "EngineConfig":
        """Build from a mapping (defaults to ``os.environ``)."""
        source = os.environ if env is None else env

        raw_store = source.get("MEM20_STORE_PATH") or DEFAULT_STORE_PATH
        store = Path(os.path.expanduser(raw_store))

        raw_ttl = source.get("MEM20_SIM_TTL_DAYS", "30")
        ttl = _parse_int(raw_ttl, name="MEM20_SIM_TTL_DAYS", minimum=1)

        raw_rerank = source.get("MEM20_RERANK", "1")
        rerank = _parse_bool(raw_rerank, name="MEM20_RERANK")

        model = source.get(
            "MEM20_RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
        ).strip()
        if not model:
            raise ConfigurationError(
                "MEM20_RERANK_MODEL must not be empty",
                details={"variable": "MEM20_RERANK_MODEL"},
            )

        cfg = cls(
            store_path=store,
            sim_ttl_days=ttl,
            rerank_enabled=rerank,
            rerank_model=model,
        )
        cfg.validate()
        return cfg

    # -- validation ---------------------------------------------------------

    def validate(self) -> "EngineConfig":
        """Raise ``ConfigurationError`` if this config cannot be operated.

        Checks the store path is absolute (a relative path would resolve
        differently depending on the caller's cwd, silently splitting one
        logical store into several) and that its parent is writable.
        """
        if not self.store_path.is_absolute():
            raise ConfigurationError(
                f"store_path must be absolute, got {self.store_path!r}. A relative "
                "path resolves against the caller's cwd and silently splits one "
                "logical store into several.",
                details={"store_path": str(self.store_path)},
            )
        if self.sim_ttl_days < 1:
            raise ConfigurationError(
                f"sim_ttl_days must be >= 1, got {self.sim_ttl_days}"
            )
        if self.mem_cap < 1 or self.user_cap < 1:
            raise ConfigurationError("mem_cap and user_cap must be >= 1")

        parent = self.store_path.parent
        if parent.exists() and not os.access(parent, os.W_OK):
            raise ConfigurationError(
                f"store parent directory is not writable: {parent}",
                details={"store_path": str(self.store_path), "parent": str(parent)},
            )
        return self

    # -- application --------------------------------------------------------

    def to_env(self) -> dict[str, str]:
        """Render back to the environment variables the engine reads."""
        return {
            "MEM20_STORE_PATH": str(self.store_path),
            "MEM20_SIM_TTL_DAYS": str(self.sim_ttl_days),
            "MEM20_RERANK": "1" if self.rerank_enabled else "0",
            "MEM20_RERANK_MODEL": self.rerank_model,
        }

    def apply(self, env: dict[str, str] | None = None) -> None:
        """Write this config into the process environment.

        Must be called BEFORE importing ``memory_engine.memory``, which resolves
        its paths at import time.
        """
        target = os.environ if env is None else env
        target.update(self.to_env())

    def with_store(self, store_path: str | Path) -> "EngineConfig":
        """Return a copy pointing at a different store (used by tests)."""
        return replace(self, store_path=Path(store_path).expanduser().resolve())

    # -- introspection ------------------------------------------------------

    @property
    def ledger_path(self) -> Path:
        return self.store_path / "ledger.jsonl"

    @property
    def entries_path(self) -> Path:
        return self.store_path / "entries"

    @property
    def simulated_ledger_path(self) -> Path:
        return self.store_path / "simulated_ledger.jsonl"

    def describe(self) -> dict[str, object]:
        """Redacted, JSON-safe view for a health/readiness endpoint."""
        return {
            "store_path": str(self.store_path),
            "sim_ttl_days": self.sim_ttl_days,
            "rerank_enabled": self.rerank_enabled,
            "rerank_model": self.rerank_model,
            "mem_cap": self.mem_cap,
            "user_cap": self.user_cap,
        }
