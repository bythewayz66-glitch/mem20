"""MCP tools for mem20memorytimemachinez (memory time machine)."""

from __future__ import annotations

from mem20memorytimemachinez.domain import estate_context, snapshot


def memory_time_machine_snapshot(state: dict | None = None, label: str = "", store_path: str | None = None) -> dict:
    return snapshot(state or {}, label=label, store_path=store_path)


def memory_time_machine_context(store_path: str | None = None) -> dict:
    return estate_context(store_path)
