"""mem20schoolz — unified training, certification, and apprenticeship system."""
from __future__ import annotations

__version__ = "1.0.0"

# The Kiln (Kiln, KilnError, OpFailed, EngineMissing, ValidationFailed) is the
# native mem20kilnz AI 3D modeler, not part of schoolz — it lives in
# mem20kilnz and is exposed by kilnz_tools.py. Do not re-export it here.
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
