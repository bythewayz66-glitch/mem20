"""mem20webgpuz configuration and environment management.

Every tunable is read from the environment with a repo-relative default, so a
clean clone runs with no setup and an operator can override any value without
editing code. The config object is frozen: once the runtime has resolved paths
from it, a later mutation cannot silently desync the two.

Environment variables
---------------------
``MEM20WEBGPUZ_DATA_DIR``   state directory (default ``.rmdata``)
``MEM20WEBGPUZ_HOST``       API bind host (default ``127.0.0.1``)
``MEM20WEBGPUZ_PORT``       API bind port (default ``8767``)
``MEM20WEBGPUZ_MAX_CONCURRENT``  job concurrency ceiling (default ``4``)
``MEM20WEBGPUZ_QUEUE_TIMEOUT``   seconds to wait for a slot (default ``5``)
``MEM20WEBGPUZ_MAX_WORKGROUPS``  workgroup ceiling per dispatch (default ``65535``)
``MEM20WEBGPUZ_MAX_PAYLOAD_BYTES`` request size ceiling (default ``2000000``)
``MEM20WEBGPUZ_LOG_LEVEL``  structured log level (default ``INFO``)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .errors import ConfigurationError

__all__ = ["WebGPUConfig", "DEFAULT_DATA_DIR", "DEFAULT_PORT", "DEFAULT_HOST"]

DEFAULT_DATA_DIR = ".rmdata"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8767


def _parse_int(raw: str, *, name: str, minimum: int) -> int:
    try:
        value = int(str(raw).strip())
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


def _parse_float(raw: str, *, name: str, minimum: float) -> float:
    try:
        value = float(str(raw).strip())
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            f"{name} must be a number, got {raw!r}",
            details={"variable": name, "value": raw},
        ) from exc
    if value < minimum:
        raise ConfigurationError(
            f"{name} must be >= {minimum}, got {value}",
            details={"variable": name, "value": value, "minimum": minimum},
        )
    return value


@dataclass(frozen=True)
class WebGPUConfig:
    """Validated, immutable runtime configuration."""

    data_dir: Path
    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    max_concurrent: int = 4
    queue_timeout: float = 5.0
    max_workgroups: int = 65535
    max_payload_bytes: int = 2_000_000
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "WebGPUConfig":
        source = os.environ if env is None else env
        raw_dir = source.get("MEM20WEBGPUZ_DATA_DIR") or DEFAULT_DATA_DIR
        cfg = cls(
            data_dir=Path(os.path.expanduser(raw_dir)),
            host=(source.get("MEM20WEBGPUZ_HOST") or DEFAULT_HOST).strip(),
            port=_parse_int(
                source.get("MEM20WEBGPUZ_PORT", str(DEFAULT_PORT)),
                name="MEM20WEBGPUZ_PORT",
                minimum=0,
            ),
            max_concurrent=_parse_int(
                source.get("MEM20WEBGPUZ_MAX_CONCURRENT", "4"),
                name="MEM20WEBGPUZ_MAX_CONCURRENT",
                minimum=1,
            ),
            queue_timeout=_parse_float(
                source.get("MEM20WEBGPUZ_QUEUE_TIMEOUT", "5"),
                name="MEM20WEBGPUZ_QUEUE_TIMEOUT",
                minimum=0.0,
            ),
            max_workgroups=_parse_int(
                source.get("MEM20WEBGPUZ_MAX_WORKGROUPS", "65535"),
                name="MEM20WEBGPUZ_MAX_WORKGROUPS",
                minimum=1,
            ),
            max_payload_bytes=_parse_int(
                source.get("MEM20WEBGPUZ_MAX_PAYLOAD_BYTES", "2000000"),
                name="MEM20WEBGPUZ_MAX_PAYLOAD_BYTES",
                minimum=1024,
            ),
            log_level=(source.get("MEM20WEBGPUZ_LOG_LEVEL") or "INFO").strip().upper(),
        )
        cfg.validate()
        return cfg

    def validate(self) -> "WebGPUConfig":
        if not self.host:
            raise ConfigurationError("host must not be empty")
        if not 0 <= self.port <= 65535:
            raise ConfigurationError(
                "port out of range", details={"port": self.port}
            )
        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ConfigurationError(
                "log_level must be a standard level",
                details={"log_level": self.log_level},
            )
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "data_dir": str(self.data_dir),
            "host": self.host,
            "port": self.port,
            "max_concurrent": self.max_concurrent,
            "queue_timeout": self.queue_timeout,
            "max_workgroups": self.max_workgroups,
            "max_payload_bytes": self.max_payload_bytes,
            "log_level": self.log_level,
        }
