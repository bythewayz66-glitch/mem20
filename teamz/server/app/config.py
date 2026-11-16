from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off", ""}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _csv(name: str, default: List[str]) -> List[str]:
    raw = os.getenv(name)
    if raw is None:
        return list(default)
    items = [p.strip() for p in raw.split(",")]
    return [p for p in items if p]


@dataclass
class Settings:
    # Server
    host: str = field(default_factory=lambda: os.getenv("TEAMZ_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: _env_int("TEAMZ_PORT", 8787))
    cors_origins: List[str] = field(
        default_factory=lambda: _csv(
            "TEAMZ_CORS_ORIGINS",
            [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:4173",
                "http://127.0.0.1:4173",
            ],
        )
    )

    # Provider routing
    keyless_first: bool = field(default_factory=lambda: _env_bool("TEAMZ_KEYLESS_FIRST", True))
    request_timeout_s: float = field(default_factory=lambda: _env_float("TEAMZ_REQUEST_TIMEOUT_S", 60.0))
    connect_timeout_s: float = field(default_factory=lambda: _env_float("TEAMZ_CONNECT_TIMEOUT_S", 10.0))
    probe_timeout_s: float = field(default_factory=lambda: _env_float("TEAMZ_PROBE_TIMEOUT_S", 3.0))
    max_attempts: int = field(default_factory=lambda: _env_int("TEAMZ_MAX_ATTEMPTS", 6))
    dead_runtime_timeout_s: float = field(
        default_factory=lambda: _env_float("TEAMZ_DEAD_RUNTIME_TIMEOUT_S", 0.6)
    )

    # Provider endpoints/keys (keyless-first: keys optional)
    pollinations_base_url: str = field(
        default_factory=lambda: os.getenv("POLLINATIONS_BASE_URL", "https://text.pollinations.ai/openai").rstrip("/")
    )
    pollinations_keyed_base_url: str = field(
        default_factory=lambda: os.getenv(
            "POLLINATIONS_KEYED_BASE_URL", "https://gen.pollinations.ai/v1"
        ).rstrip("/")
    )
    pollinations_api_key: str = field(default_factory=lambda: os.getenv("POLLINATIONS_API_KEY", ""))

    llm7_base_url: str = field(
        default_factory=lambda: os.getenv("LLM7_BASE_URL", "https://api.llm7.io/v1").rstrip("/")
    )
    llm7_api_key: str = field(default_factory=lambda: os.getenv("LLM7_API_KEY", ""))

    ovh_base_url: str = field(
        default_factory=lambda: os.getenv(
            "OVH_BASE_URL", "https://oai.endpoints.kepler.ai.cloud.ovh.net/v1"
        ).rstrip("/")
    )
    ovh_api_key: str = field(default_factory=lambda: os.getenv("OVH_API_KEY", ""))

    # Optional local runtimes (probed quickly; dead ones must not consume attempt budget)
    local_openai_base_urls: List[str] = field(
        default_factory=lambda: _csv(
            "TEAMZ_LOCAL_OPENAI_BASE_URLS",
            [],
        )
    )

    # Mem20 integration
    mem20_enabled: bool = field(default_factory=lambda: _env_bool("MEM20_ENABLED", True))
    mem20_mcp_command: str = field(
        default_factory=lambda: os.getenv("MEM20_MCP_COMMAND", "python3")
    )
    mem20_mcp_args: List[str] = field(
        default_factory=lambda: _csv(
            "MEM20_MCP_ARGS",
            ["/opt/mem20/mcp/mcp_server.py"],
        )
    )
    mem20_timeout_s: float = field(default_factory=lambda: _env_float("MEM20_TIMEOUT_S", 30.0))

    # Fleetwide Mem20 integration (Step 6: isolated namespaces)
    fleet_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_FLEET_ENABLED", True))
    fleet_gateway_url: str = field(default_factory=lambda: os.getenv("TEAMZ_FLEET_GATEWAY_URL", "http://localhost:8788"))
    fleet_agent_name: str = field(default_factory=lambda: os.getenv("TEAMZ_FLEET_AGENT_NAME", "teamz-orchestrator"))
    fleet_namespace_auto_create: bool = field(default_factory=lambda: _env_bool("TEAMZ_FLEET_NS_AUTO_CREATE", True))

    # Kanban integration (Step 7)
    kanban_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_KANBAN_ENABLED", False))
    kanban_mcp_url: str = field(default_factory=lambda: os.getenv("TEAMZ_KANBAN_MCP_URL", "http://localhost:8789"))

    # A2A setup (Step 8)
    a2a_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_A2A_ENABLED", True))
    a2a_port: int = field(default_factory=lambda: _env_int("TEAMZ_A2A_PORT", 8790))
    a2a_peer_config: str = field(default_factory=lambda: os.getenv("TEAMZ_A2A_PEER_CONFIG", ""))

    # Fleetwide rules enforcement (Step 9)
    fleet_rules_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_FLEET_RULES_ENABLED", True))
    fleet_decision_persistence: bool = field(default_factory=lambda: _env_bool("TEAMZ_FLEET_DECISION_PERSISTENCE", True))
    fleet_fail_log_review: bool = field(default_factory=lambda: _env_bool("TEAMZ_FLEET_FAIL_LOG_REVIEW", True))

    # Persistent workspace/session storage (survives browser restarts + server restarts)
    persist_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_PERSIST_ENABLED", True))
    state_file: str = field(
        default_factory=lambda: os.getenv("TEAMZ_STATE_FILE", str(_REPO_ROOT / "server" / "data" / "workspace.json"))
    )

    # Autonomous goal worker (agents keep working toward a channel goal)
    goal_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_GOAL_ENABLED", True))
    goal_worker_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_GOAL_WORKER_ENABLED", True))
    goal_tick_s: float = field(default_factory=lambda: _env_float("TEAMZ_GOAL_TICK_S", 60.0))
    goal_turn_timeout_s: float = field(default_factory=lambda: _env_float("TEAMZ_GOAL_TURN_TIMEOUT_S", 120.0))
    goal_max_steps: int = field(default_factory=lambda: _env_int("TEAMZ_GOAL_MAX_STEPS", 200))

    # Terminal access (real shell, run server-side)
    terminal_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_TERMINAL_ENABLED", True))
    terminal_workdir: str = field(
        default_factory=lambda: os.getenv("TEAMZ_TERMINAL_WORKDIR", str(_REPO_ROOT))
    )
    terminal_timeout_s: float = field(default_factory=lambda: _env_float("TEAMZ_TERMINAL_TIMEOUT_S", 60.0))
    terminal_allow_all: bool = field(default_factory=lambda: _env_bool("TEAMZ_TERMINAL_ALLOW_ALL", True))
    terminal_allow_prefixes: List[str] = field(
        default_factory=lambda: _csv(
            "TEAMZ_TERMINAL_ALLOW_PREFIXES",
            [
                "git", "gh", "npm", "yarn", "node", "python", "python3", "pip", "pip3",
                "ls", "cat", "pwd", "echo", "grep", "find", "rg", "make", "docker",
                "curl", "wget", "mkdir", "cp", "mv", "rm", "touch", "head", "tail",
                "wc", "jq", "go", "cargo", "rustc", "java", "mvn", "gradle",
                "pytest", "tsc", "vite", "sed", "awk", "bash", "sh", "zsh",
            ],
        )
    )

    # File tools (agents read/write/edit real files themselves)
    files_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_FILES_ENABLED", True))
    files_root: str = field(default_factory=lambda: os.getenv("TEAMZ_FILES_ROOT", str(_REPO_ROOT)))
    files_max_bytes: int = field(default_factory=lambda: _env_int("TEAMZ_FILES_MAX_BYTES", 1_048_576))

    # GitHub / gh access for agents
    github_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_GITHUB_ENABLED", True))
    gh_enabled: bool = field(default_factory=lambda: _env_bool("TEAMZ_GH_ENABLED", True))


settings = Settings()
