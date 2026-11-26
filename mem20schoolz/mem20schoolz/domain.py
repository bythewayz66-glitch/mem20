"""mem20schoolz domain — training, certification, and apprenticeship.

The school's records live in a JSON store (default
``~/.mem20/mem20schoolz/state.json``, override with ``MEM20_SCHOOLZ_STORE``).
Courses, exams, credentials, progress, mentorship and evaluations are all
real records: nothing is seeded, nothing is faked. An empty catalog is an
empty school, not a broken one — use :func:`create_course` and
:func:`create_exam` to fill it.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

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
    "create_course",
    "create_exam",
    "register_mentor",
    "log_session",
    "probe",
]

_LOCK = threading.Lock()


def _store_path() -> Path:
    override = os.environ.get("MEM20_SCHOOLZ_STORE")
    if override:
        return Path(override).expanduser().resolve()
    return Path.home() / ".mem20" / "mem20schoolz" / "state.json"


def _empty_state() -> dict:
    return {
        "courses": {},
        "exams": {},
        "paths": {},
        "progress": [],
        "exam_attempts": [],
        "credentials": {},
        "mentors": {},
        "sessions": [],
        "evaluations": [],
        "seq": {"course": 0, "exam": 0, "path": 0, "mentor": 0},
    }


def _load() -> dict:
    p = _store_path()
    if not p.exists():
        return _empty_state()
    try:
        with open(p, "r", encoding="utf-8") as fh:
            state = json.load(fh)
    except Exception:
        return _empty_state()
    base = _empty_state()
    base.update({k: v for k, v in state.items() if k in base})
    return base


def _save(state: dict) -> None:
    p = _store_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, default=str)
    os.replace(tmp, p)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _next_id(state: dict, kind: str) -> str:
    state["seq"][kind] = state["seq"].get(kind, 0) + 1
    return f"{kind}-{state['seq'][kind]}"


def _err(message: str) -> dict:
    return {"ok": False, "error": message}


# ---------------------------------------------------------------- courses
def create_course(title: str, skill: str, lessons: list, description: str = "") -> dict:
    """Add a course with ``lessons`` as [{title, content}] (ids assigned)."""
    if not title or not skill:
        return _err("title and skill are required")
    if not isinstance(lessons, list) or not lessons:
        return _err("lessons must be a non-empty list of {title, content}")
    with _LOCK:
        state = _load()
        course_id = _next_id(state, "course")
        norm = []
        for i, lesson in enumerate(lessons, 1):
            if not isinstance(lesson, dict) or not lesson.get("title"):
                return _err(f"lesson {i} needs a title")
            norm.append(
                {
                    "id": f"lesson-{i}",
                    "title": lesson["title"],
                    "content": lesson.get("content", ""),
                }
            )
        course = {
            "id": course_id,
            "title": title,
            "skill": skill,
            "description": description,
            "lessons": norm,
            "created": _now(),
        }
        state["courses"][course_id] = course
        _save(state)
        return {"ok": True, "course": course}


def list_courses() -> dict:
    """List every course in the catalog (empty when none have been added)."""
    with _LOCK:
        state = _load()
        courses = sorted(state["courses"].values(), key=lambda c: c["id"])
    return {"ok": True, "count": len(courses), "courses": courses}


def get_lesson(course_id: str, lesson_id: str) -> dict:
    """Return one lesson from one course."""
    with _LOCK:
        state = _load()
        course = state["courses"].get(course_id)
        if course is None:
            return _err(f"unknown course: {course_id}")
        for lesson in course["lessons"]:
            if lesson["id"] == lesson_id:
                return {"ok": True, "course_id": course_id, "lesson": lesson}
        return _err(f"unknown lesson {lesson_id} in course {course_id}")


def create_learning_path(learner: str, goal: str, course_ids: list | None = None) -> dict:
    """Build a learning path for ``learner`` toward ``goal`` (a skill).

    When ``course_ids`` is omitted, every course for that skill is used, in
    id order. A path with no matching courses is still recorded, with its
    steps empty — the school has no course for that skill yet.
    """
    if not learner or not goal:
        return _err("learner and goal are required")
    with _LOCK:
        state = _load()
        if course_ids is None:
            course_ids = [
                c["id"] for c in sorted(state["courses"].values(), key=lambda c: c["id"])
                if c["skill"] == goal
            ]
        else:
            missing = [c for c in course_ids if c not in state["courses"]]
            if missing:
                return _err(f"unknown courses: {', '.join(missing)}")
        steps = []
        for cid in course_ids:
            course = state["courses"][cid]
            steps.extend(
                {"course_id": cid, "lesson_id": l["id"], "title": l["title"]}
                for l in course["lessons"]
            )
        path_id = _next_id(state, "path")
        path = {
            "id": path_id,
            "learner": learner,
            "goal": goal,
            "course_ids": list(course_ids),
            "steps": steps,
            "created": _now(),
        }
        state["paths"][path_id] = path
        _save(state)
        return {"ok": True, "path": path}


def track_progress(learner: str, course_id: str, lesson_id: str, status: str = "completed") -> dict:
    """Record ``learner``'s progress on one lesson."""
    if not learner or not course_id or not lesson_id:
        return _err("learner, course_id and lesson_id are required")
    if status not in ("started", "completed"):
        return _err("status must be 'started' or 'completed'")
    lesson = get_lesson(course_id, lesson_id)
    if not lesson.get("ok"):
        return lesson
    with _LOCK:
        state = _load()
        record = {
            "learner": learner,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "status": status,
            "ts": _now(),
        }
        state["progress"].append(record)
        _save(state)
        return {"ok": True, "progress": record}


# ------------------------------------------------------------------ exams
def create_exam(
    title: str,
    skill: str,
    questions: list,
    course_id: str | None = None,
    passing_score: float = 70.0,
) -> dict:
    """Add an exam. ``questions`` are [{prompt, choices, answer}] where
    ``answer`` is the index of the correct choice (or the exact text)."""
    if not title or not skill:
        return _err("title and skill are required")
    if not isinstance(questions, list) or not questions:
        return _err("questions must be a non-empty list")
    with _LOCK:
        state = _load()
        if course_id is not None and course_id not in state["courses"]:
            return _err(f"unknown course: {course_id}")
        norm = []
        for i, q in enumerate(questions, 1):
            if not isinstance(q, dict) or not q.get("prompt") or "answer" not in q:
                return _err(f"question {i} needs a prompt and an answer")
            norm.append(
                {
                    "id": f"q{i}",
                    "prompt": q["prompt"],
                    "choices": list(q.get("choices", [])),
                    "answer": q["answer"],
                }
            )
        exam_id = _next_id(state, "exam")
        exam = {
            "id": exam_id,
            "title": title,
            "skill": skill,
            "course_id": course_id,
            "passing_score": float(passing_score),
            "questions": norm,
            "created": _now(),
        }
        state["exams"][exam_id] = exam
        _save(state)
        return {"ok": True, "exam": exam}


def list_exams() -> dict:
    """List every exam (empty when none have been added)."""
    with _LOCK:
        state = _load()
        exams = sorted(state["exams"].values(), key=lambda e: e["id"])
    return {"ok": True, "count": len(exams), "exams": exams}


def take_exam(learner: str, exam_id: str, answers: dict) -> dict:
    """Score ``answers`` ({question_id: answer}) against the exam key."""
    if not learner or not exam_id:
        return _err("learner and exam_id are required")
    if not isinstance(answers, dict):
        return _err("answers must be an object mapping question id to answer")
    with _LOCK:
        state = _load()
        exam = state["exams"].get(exam_id)
        if exam is None:
            return _err(f"unknown exam: {exam_id}")
        correct = 0
        detail = {}
        for q in exam["questions"]:
            given = answers.get(q["id"])
            expected = q["answer"]
            if isinstance(expected, int) and q["choices"]:
                hit = given == expected or given == q["choices"][expected]
            else:
                hit = str(given) == str(expected)
            detail[q["id"]] = bool(hit)
            correct += int(bool(hit))
        total = len(exam["questions"])
        score = round(100.0 * correct / total, 1) if total else 0.0
        passed = score >= exam["passing_score"]
        attempt = {
            "learner": learner,
            "exam_id": exam_id,
            "score": score,
            "passed": passed,
            "correct": correct,
            "total": total,
            "ts": _now(),
        }
        state["exam_attempts"].append(attempt)
        _save(state)
        return {"ok": True, "attempt": attempt, "detail": detail}


def issue_credential(learner: str, exam_id: str) -> dict:
    """Issue a credential to ``learner`` for ``exam_id``.

    Requires a passing attempt on that exam. The credential id is a hash of
    learner + exam + issue time, so it can be verified later.
    """
    if not learner or not exam_id:
        return _err("learner and exam_id are required")
    with _LOCK:
        state = _load()
        exam = state["exams"].get(exam_id)
        if exam is None:
            return _err(f"unknown exam: {exam_id}")
        passed = any(
            a["learner"] == learner and a["exam_id"] == exam_id and a["passed"]
            for a in state["exam_attempts"]
        )
        if not passed:
            return _err(f"{learner} has no passing attempt on {exam_id}")
        issued = _now()
        digest = hashlib.sha256(f"{learner}|{exam_id}|{issued}".encode()).hexdigest()[:16]
        credential_id = f"cred-{digest}"
        credential = {
            "id": credential_id,
            "learner": learner,
            "exam_id": exam_id,
            "title": exam["title"],
            "skill": exam["skill"],
            "issued": issued,
            "hash": digest,
        }
        state["credentials"][credential_id] = credential
        _save(state)
        return {"ok": True, "credential": credential}


def verify_credential(credential_id: str) -> dict:
    """Check a credential id against the store and its hash."""
    if not credential_id:
        return _err("credential_id is required")
    with _LOCK:
        state = _load()
        credential = state["credentials"].get(credential_id)
        if credential is None:
            return {"ok": True, "valid": False, "credential_id": credential_id}
        expected = hashlib.sha256(
            f"{credential['learner']}|{credential['exam_id']}|{credential['issued']}".encode()
        ).hexdigest()[:16]
        valid = expected == credential["hash"] and credential_id == f"cred-{expected}"
        return {"ok": True, "valid": valid, "credential": credential}


# ------------------------------------------------------------- mentorship
def register_mentor(name: str, skills: list) -> dict:
    """Register a mentor and the skills they can teach."""
    if not name or not skills:
        return _err("name and skills are required")
    with _LOCK:
        state = _load()
        mentor_id = _next_id(state, "mentor")
        mentor = {"id": mentor_id, "name": name, "skills": list(skills), "created": _now()}
        state["mentors"][mentor_id] = mentor
        _save(state)
        return {"ok": True, "mentor": mentor}


def mentor_match(learner: str, skill: str) -> dict:
    """Find mentors who teach ``skill``, most experienced first."""
    if not learner or not skill:
        return _err("learner and skill are required")
    with _LOCK:
        state = _load()
        hours = {}
        for s in state["sessions"]:
            hours[s["mentor"]] = hours.get(s["mentor"], 0.0) + float(s.get("hours", 0))
        matches = [
            {**m, "hours_taught": hours.get(m["id"], 0.0)}
            for m in state["mentors"].values()
            if skill in m["skills"]
        ]
        matches.sort(key=lambda m: m["hours_taught"], reverse=True)
    return {"ok": True, "learner": learner, "skill": skill, "count": len(matches), "mentors": matches}


def log_session(learner: str, mentor: str, skill: str, hours: float) -> dict:
    """Log a mentorship session of ``hours`` with mentor ``mentor``."""
    if not learner or not mentor or not skill:
        return _err("learner, mentor and skill are required")
    try:
        hours = float(hours)
    except (TypeError, ValueError):
        return _err("hours must be a number")
    if hours <= 0:
        return _err("hours must be positive")
    with _LOCK:
        state = _load()
        if mentor not in state["mentors"]:
            return _err(f"unknown mentor: {mentor}")
        record = {
            "learner": learner,
            "mentor": mentor,
            "skill": skill,
            "hours": hours,
            "ts": _now(),
        }
        state["sessions"].append(record)
        _save(state)
        return {"ok": True, "session": record}


def mentorship_hours(learner: str | None = None, mentor: str | None = None) -> dict:
    """Total mentorship hours, optionally filtered by learner or mentor."""
    with _LOCK:
        state = _load()
        total = 0.0
        count = 0
        for s in state["sessions"]:
            if learner is not None and s["learner"] != learner:
                continue
            if mentor is not None and s["mentor"] != mentor:
                continue
            total += float(s.get("hours", 0))
            count += 1
    return {"ok": True, "learner": learner, "mentor": mentor, "hours": total, "sessions": count}


def evaluate_task(learner: str, task: str, score: float, notes: str = "") -> dict:
    """Record an evaluation of ``learner`` on ``task`` (score 0-100)."""
    if not learner or not task:
        return _err("learner and task are required")
    try:
        score = float(score)
    except (TypeError, ValueError):
        return _err("score must be a number")
    if not 0 <= score <= 100:
        return _err("score must be between 0 and 100")
    with _LOCK:
        state = _load()
        record = {
            "learner": learner,
            "task": task,
            "score": score,
            "notes": notes,
            "ts": _now(),
        }
        state["evaluations"].append(record)
        _save(state)
        return {"ok": True, "evaluation": record}


def _skill_points(state: dict, learner: str, skill: str) -> tuple[int, int]:
    """(completed lessons, passed exams) for ``learner`` on ``skill``."""
    lessons = 0
    for p in state["progress"]:
        if p["learner"] != learner or p["status"] != "completed":
            continue
        course = state["courses"].get(p["course_id"])
        if course and course["skill"] == skill:
            lessons += 1
    exams = 0
    for a in state["exam_attempts"]:
        if a["learner"] != learner or not a["passed"]:
            continue
        exam = state["exams"].get(a["exam_id"])
        if exam and exam["skill"] == skill:
            exams += 1
    return lessons, exams


def skill_level(skill: str, learner: str | None = None) -> dict:
    """Level 0-5 for ``skill``.

    With a learner, the level is computed from their real records:
    points = completed lessons + 2 x passed exams (0 -> 0, 1-2 -> 1,
    3-4 -> 2, 5-7 -> 3, 8-11 -> 4, 12+ -> 5). Without a learner, returns
    the level scale itself.
    """
    if not skill:
        return _err("skill is required")
    scale = {
        0: "no activity",
        1: "1-2 points",
        2: "3-4 points",
        3: "5-7 points",
        4: "8-11 points",
        5: "12+ points",
    }
    if learner is None:
        return {"ok": True, "skill": skill, "scale": scale}
    with _LOCK:
        state = _load()
        lessons, exams = _skill_points(state, learner, skill)
    points = lessons + 2 * exams
    if points == 0:
        level = 0
    elif points <= 2:
        level = 1
    elif points <= 4:
        level = 2
    elif points <= 7:
        level = 3
    elif points <= 11:
        level = 4
    else:
        level = 5
    return {
        "ok": True,
        "skill": skill,
        "learner": learner,
        "level": level,
        "description": scale[level],
        "points": points,
        "lessons_completed": lessons,
        "exams_passed": exams,
    }


def progression_plan(learner: str, goal: str) -> dict:
    """A plan for ``learner`` to reach ``goal`` (a skill).

    Built from the learner's real level plus the courses and exams that
    exist for that skill, in order. When nothing exists for the skill yet,
    the plan says so instead of inventing steps.
    """
    if not learner or not goal:
        return _err("learner and goal are required")
    level = skill_level(goal, learner)
    if not level.get("ok"):
        return level
    with _LOCK:
        state = _load()
        courses = [
            {"id": c["id"], "title": c["title"], "lessons": len(c["lessons"])}
            for c in sorted(state["courses"].values(), key=lambda c: c["id"])
            if c["skill"] == goal
        ]
        exams = [
            {"id": e["id"], "title": e["title"], "passing_score": e["passing_score"]}
            for e in sorted(state["exams"].values(), key=lambda e: e["id"])
            if e["skill"] == goal
        ]
        mentors = [m for m in state["mentors"].values() if goal in m["skills"]]
    steps = []
    for c in courses:
        steps.append(f"Complete course {c['id']}: {c['title']} ({c['lessons']} lessons)")
    for e in exams:
        steps.append(f"Pass exam {e['id']}: {e['title']} (needs {e['passing_score']}%)")
    if mentors:
        steps.append(f"Book a mentor: {', '.join(m['name'] for m in mentors)}")
    if not steps:
        steps = [f"No courses, exams, or mentors exist for {goal} yet — add some first."]
    return {
        "ok": True,
        "learner": learner,
        "goal": goal,
        "current_level": level["level"],
        "points": level["points"],
        "courses": courses,
        "exams": exams,
        "mentors": [m["name"] for m in mentors],
        "steps": steps,
    }


# ------------------------------------------------------------------ status
def estate_context(store_path: str | Path | None = None) -> dict:
    """Real counts from the school store."""
    with _LOCK:
        state = _load()
        learners = sorted(
            {p["learner"] for p in state["progress"]}
            | {a["learner"] for a in state["exam_attempts"]}
            | {e["learner"] for e in state["evaluations"]}
        )
        ctx = {
            "ok": True,
            "store": str(store_path or _store_path()),
            "courses": len(state["courses"]),
            "exams": len(state["exams"]),
            "paths": len(state["paths"]),
            "credentials": len(state["credentials"]),
            "mentors": len(state["mentors"]),
            "sessions": len(state["sessions"]),
            "evaluations": len(state["evaluations"]),
            "learners": len(learners),
        }
    return ctx


def probe() -> dict:
    """Check the school store loads and the directory is writable."""
    p = _store_path()
    try:
        state = _load()
        p.parent.mkdir(parents=True, exist_ok=True)
        writable = os.access(p.parent, os.W_OK)
        return {
            "ok": writable,
            "store": str(p),
            "exists": p.exists(),
            "writable": writable,
            "courses": len(state["courses"]),
            "exams": len(state["exams"]),
            "credentials": len(state["credentials"]),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "store": str(p), "error": f"{type(exc).__name__}: {exc}"}
