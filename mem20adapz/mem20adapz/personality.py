"""Adaptive personality runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

AXES = ("formality", "verbosity", "warmth", "directness", "initiative")


@dataclass
class StyleProfile:
    formality: float = 0.5
    verbosity: float = 0.5
    warmth: float = 0.5
    directness: float = 0.5
    initiative: float = 0.5
    tone_label: str = "balanced"
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "formality": round(self.formality, 3),
            "verbosity": round(self.verbosity, 3),
            "warmth": round(self.warmth, 3),
            "directness": round(self.directness, 3),
            "initiative": round(self.initiative, 3),
            "tone_label": self.tone_label,
            "notes": list(self.notes),
        }


def _clamp(v: float) -> float:
    return max(0.0, min(1.0, float(v)))


def derive_style(
    *,
    task_type: str = "general",
    user_preference: dict[str, float] | None = None,
    emotional_valence: float = 0.0,
    urgency: float = 0.5,
    relationship_depth: float = 0.3,
) -> StyleProfile:
    baselines = {
        "general":   {"formality": 0.5, "verbosity": 0.5, "warmth": 0.5, "directness": 0.5, "initiative": 0.4},
        "support":   {"formality": 0.3, "verbosity": 0.6, "warmth": 0.8, "directness": 0.4, "initiative": 0.5},
        "technical": {"formality": 0.6, "verbosity": 0.7, "warmth": 0.3, "directness": 0.8, "initiative": 0.3},
        "crisis":    {"formality": 0.4, "verbosity": 0.3, "warmth": 0.5, "directness": 0.95, "initiative": 0.9},
        "creative":  {"formality": 0.2, "verbosity": 0.7, "warmth": 0.7, "directness": 0.4, "initiative": 0.6},
        "executive": {"formality": 0.8, "verbosity": 0.3, "warmth": 0.3, "directness": 0.9, "initiative": 0.5},
    }
    base = dict(baselines.get(task_type, baselines["general"]))
    notes: list[str] = [f"task_baseline:{task_type}"]
    if urgency > 0.7:
        base["directness"] = _clamp(base["directness"] + 0.25)
        base["verbosity"] = _clamp(base["verbosity"] - 0.2)
        base["initiative"] = _clamp(base["initiative"] + 0.15)
        notes.append("high_urgency_compression")
    if emotional_valence < -0.3:
        base["warmth"] = _clamp(base["warmth"] + 0.2)
        base["formality"] = _clamp(base["formality"] - 0.1)
        notes.append("supportive_shift")
    elif emotional_valence > 0.4:
        base["warmth"] = _clamp(base["warmth"] + 0.1)
        notes.append("positive_match")
    if relationship_depth > 0.6:
        base["formality"] = _clamp(base["formality"] - 0.2)
        base["warmth"] = _clamp(base["warmth"] + 0.15)
        notes.append("familiar_register")
    if user_preference:
        for k, v in user_preference.items():
            if k in base:
                base[k] = _clamp(v)
        notes.append("user_preference_applied")
    if base["directness"] > 0.8 and base["verbosity"] < 0.4:
        label = "terse_direct"
    elif base["warmth"] > 0.7 and base["formality"] < 0.4:
        label = "warm_casual"
    elif base["formality"] > 0.7:
        label = "formal"
    elif base["initiative"] > 0.7:
        label = "proactive"
    else:
        label = "balanced"
    return StyleProfile(
        formality=base["formality"], verbosity=base["verbosity"], warmth=base["warmth"],
        directness=base["directness"], initiative=base["initiative"],
        tone_label=label, notes=notes,
    )


@dataclass
class PersonalityRuntime:
    default_preference: dict[str, float] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def style_for(
        self, *,
        task_type: str = "general",
        emotional_valence: float = 0.0,
        urgency: float = 0.5,
        relationship_depth: float = 0.3,
        user_preference: dict[str, float] | None = None,
    ) -> StyleProfile:
        pref = user_preference if user_preference is not None else self.default_preference
        profile = derive_style(
            task_type=task_type, user_preference=pref or None,
            emotional_valence=emotional_valence, urgency=urgency,
            relationship_depth=relationship_depth,
        )
        self.history.append(profile.to_dict())
        return profile

    def set_preference(self, **kwargs: float) -> None:
        for k, v in kwargs.items():
            if k in AXES:
                self.default_preference[k] = _clamp(v)
