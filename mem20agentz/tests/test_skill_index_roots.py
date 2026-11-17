"""Regression tests for repo-relative agent-skill discovery.

``mem20agentz.skill_index`` used to resolve its scan roots from two absolute
host paths only (``/root/.config/opencode/skills`` and
``/opt/mem20-skills/skills``). On a clean clone neither exists, so the catalog
reported an empty inventory even though ``.opencode/skills/`` is committed to
this repository. These tests pin the fix: the repository's own skill tree is a
default root, and discovery works without any host tree present.
"""

from __future__ import annotations

import os
from unittest import mock

from mem20agentz import skill_index


def test_repo_skill_tree_is_a_default_root():
    """A skill committed to this checkout is discoverable without setup."""
    assert skill_index.repo_skill_root() in skill_index.DEFAULT_ROOTS
    assert skill_index.repo_skill_root().is_dir()


def test_repo_root_is_the_checkout_holding_the_package():
    """``repo_root`` resolves to the tree that holds both the package and skills."""
    root = skill_index.repo_root()
    assert (root / "mem20agentz").is_dir()
    assert (root / ".opencode" / "skills").is_dir()


def test_discovery_does_not_depend_on_host_paths():
    """The committed skills resolve even when no host tree exists.

    ``MEM20_SKILL_ROOTS`` is honoured verbatim, so pointing it at the repo tree
    alone proves the repo tree is sufficient on its own.
    """
    root = skill_index.repo_skill_root()
    with mock.patch.dict(os.environ, {"MEM20_SKILL_ROOTS": str(root)}):
        roots = skill_index.default_roots()
    assert roots == (root,)
    names = {row["name"] for row in skill_index.DiskSkillIndex(roots).all()}
    assert "register-subsystem" in names


def test_committed_skills_are_indexed_with_frontmatter():
    """Every committed skill is indexed with a name and a description."""
    rows = skill_index.DiskSkillIndex().all()
    by_name = {row["name"]: row for row in rows}
    assert "register-subsystem" in by_name
    assert by_name["register-subsystem"]["description"]
    assert by_name["register-subsystem"]["source"] == "skill"
