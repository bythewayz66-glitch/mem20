"""mem20enginez: first-class crew runtime for 30 engine members (RM/#305).

Real member registry, probing, compatibility checks, dispatch planning,
durable state, service/CLI/HTTP API, and 6 unique cross-subsystem peers.
"""
from __future__ import annotations

import importlib

from .domain import (
    MEMBERS, EngineMember, MemberStatus, RuntimePlan, RuntimeReport,
    check_member, compatibility, dispatch_plan, member_registry, summarize,
)

__version__ = "1.0.0"

__all__ = [
    "MEMBERS", "EngineMember", "MemberStatus", "RuntimePlan", "RuntimeReport",
    "EngineRuntimeService", "ValidationError",
    "check_member", "compatibility", "dispatch_plan", "member_registry", "summarize",
    "ecosystem", "__version__",
]


def __getattr__(name):
    if name in ("EngineRuntimeService", "ValidationError"):
        return getattr(importlib.import_module(".service", __name__), name)
    if name == "ecosystem":
        return importlib.import_module(".ecosystem", __name__)
    raise AttributeError(name)
