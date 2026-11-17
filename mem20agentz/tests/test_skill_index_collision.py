from __future__ import annotations

from pathlib import Path

from mem20agentz import skill_index


def _write_skill(root: Path, dir_name: str, skill_name: str, desc: str) -> Path:
    skill_dir = root / dir_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {skill_name}\ndescription: {desc}\n---\n\n# {skill_name}\n",
        encoding="utf-8",
    )
    return skill_dir


def test_name_collision_prefers_committed_skill_over_host_copy(tmp_path):
    """When the same skill name exists in committed and host roots, committed wins."""
    committed = tmp_path / "repo" / ".opencode" / "skills"
    host = tmp_path / "host" / "skills"
    _write_skill(committed, "gate-triage", "gate-triage", "committed description")
    _write_skill(host, "gate-triage-copy", "gate-triage", "host description")

    # committed root must come first (repo-preferred)
    idx = skill_index.DiskSkillIndex(roots=(committed, host))
    rows = [r for r in idx.all() if r["name"] == "gate-triage"]
    assert len(rows) == 1
    assert rows[0]["description"] == "committed description"
    assert str(rows[0]["path"]).startswith(str(committed))
