"""mem20schoolz — unified training, certification, and apprenticeship system."""
from __future__ import annotations

__version__ = "1.0.0"

# Re-export from all three subsystems
from mem20schoolz import (
    Kiln,
    KilnError,
    OpFailed,
    EngineMissing,
    ValidationFailed,
)
from mem20schoolz.domain import (
    skill_level,
    mentor_match,
    evaluate_task,
    progression_plan,
    mentorship_hours,
    estate_context,
)
from mem20schoolz.domain import (
    list_courses,
    get_lesson,
    create_learning_path,
    track_progress,
)
from mem20schoolz.domain import (
    list_exams,
    take_exam,
    issue_credential,
    verify_credential,
)

__all__ = [
    "Kiln",
    "KilnError",
    "OpFailed",
    "EngineMissing",
    "ValidationFailed",
    "skill_level",
    "mentor_match",
    "evaluate_task",
    "progression_plan",
    "mentorship_hours",
    "estate_context",
    "list_courses",
    "get_lesson",
    "create_learning_path",
    "track_progress",
    "list_exams",
    "take_exam",
    "issue_credential",
    "verify_credential",
    "__version__",
]
