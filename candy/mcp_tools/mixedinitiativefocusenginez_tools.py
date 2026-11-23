"""MCP tools for mem20mixedinitiativefocusenginez (mixed-initiative focus)."""

from __future__ import annotations

from mem20mixedinitiativefocusenginez.domain import blend, focus_health, focus_score, suggest, take_over


def focus_engine_score(context: dict) -> float:
    return focus_score(context)


def focus_engine_suggest(context: dict, options: list) -> list:
    return suggest(context, options)


def focus_engine_health(context: dict) -> dict:
    return focus_health(context)
