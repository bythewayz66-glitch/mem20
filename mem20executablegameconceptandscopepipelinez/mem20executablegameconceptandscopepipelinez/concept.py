"""Pipeline 1 — Game Concept, GDD & Scope.

Real domain logic for turning a raw game idea into a controlled, reviewable
concept brief and Game Design Document.

Spec authority: package docs / game-maker pipelines (pipeline 1) — not a
machine-local absolute path.
pipeline 1 — "Game Concept, GDD & Scope Pipeline":

    Turns a raw game idea into a structured concept brief, core loop, audience
    definition, platform targets, feature list, risks, milestones, and a
    controlled Game Design Document. It should detect contradictions,
    uncontrolled scope, missing success criteria, and features that do not
    support the core experience.

This module owns that behaviour. It depends only on the standard library, so
it runs standalone with the other nineteen pipelines absent from the path.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable

__all__ = [
    "ConceptBrief", "CoreLoop", "Feature", "Risk", "Milestone",
    "Contradiction", "ScopeFinding", "ConceptError",
    "build_brief", "detect_contradictions", "assess_scope",
    "core_loop_support", "render_gdd", "analyse",
]
