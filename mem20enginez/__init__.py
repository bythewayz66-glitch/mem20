"""Root package shim for estate-root resolution.

Real implementation: `mem20enginez.mem20enginez`.
"""
from __future__ import annotations

# Re-export inner implementation as subpackage content at this package level.
from mem20enginez.mem20enginez import (  # noqa: F401
    MEMBERS, __version__, EngineMember, MemberStatus, RuntimePlan, RuntimeReport,
    EngineRuntimeService, ValidationError, check_member, compatibility,
    dispatch_plan, member_registry, summarize, ecosystem,
)

__all__ = [
    "MEMBERS", "__version__", "EngineMember", "MemberStatus", "RuntimePlan", "RuntimeReport",
    "EngineRuntimeService", "ValidationError", "check_member", "compatibility",
    "dispatch_plan", "member_registry", "summarize", "ecosystem",
]
