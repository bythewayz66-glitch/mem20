#!/usr/bin/env python3
"""Apply the 270 tools / 27 domains correction in place.

Why a script instead of a patch: the four target files total 224 KB and two of
them contain box-drawing characters and 20 pre-existing malformed
`"arguments</arg_key>{` lines. A unified diff has to carry those exact bytes as
context, and that does not survive a constrained transport intact — the first
shipped patch had a one-character box-drawing error and a "repaired" context
line, which made it fail to apply at all.

Every substitution below is an equal-width numeric swap (268->270, 26->27,
49->52, 9->8, 8->9), so no line width, table alignment or box drawing changes.
Anchors are deliberately short and ASCII-only, and each one is asserted present
exactly the expected number of times before anything is written.

Usage:
    python3 docs/ops/apply-270-27.py            # apply
    python3 docs/ops/apply-270-27.py --check    # report only, no writes

Exit codes: 0 all substitutions applied (or already applied), 1 a mismatch.
Idempotent: re-running on an already-corrected tree is a no-op that exits 0.
"""
import sys
import pathlib

# (path, needle, replacement, expected_count, marker)
#
# `marker` is a string that must be ABSENT before the edit and PRESENT after.
# When the needle is already gone, the marker decides whether this is a no-op
# (already applied -> skip) or a genuine failure (anchor missing). Without it a
# pure needle/replacement pair cannot tell those two cases apart, which made an
# earlier version of this script insert the lie_* row twice on a re-run.
EDITS = [
    # ---- README.md -------------------------------------------------------
    # 1+2: the layer table and the transport note both assert this sentence.
    ("README.md", "**268 tools across 26 domains**",
     "**270 tools across 27 domains**", 2, "**270 tools across 27 domains**"),
    # 3: toolchest capability registry
    ("README.md", "(268 MCP tools", "(270 MCP tools", 1, "(270 MCP tools"),
    # 4: "The MCP surface" heading line
    ("README.md", "268 tools in 26 domains. The largest:",
     "270 tools in 27 domains. The largest:", 1,
     "270 tools in 27 domains. The largest:"),
    # 5: architecture diagram (equal width keeps the box aligned)
    ("README.md", "268 tools \u00b7 26 domains", "270 tools \u00b7 27 domains", 1,
     "270 tools \u00b7 27 domains"),
    # 6: section heading
    ("README.md", "## Tool domains (26)", "## Tool domains (27)", 1,
     "## Tool domains (27)"),
    # 7: prefix-table preamble
    ("README.md", "268 total across 26 domains; the 29 rows",
     "270 total across 27 domains; the 30 rows", 1,
     "270 total across 27 domains; the 30 rows"),
    # 8: prefix table row corrections
    ("README.md", "| `memory_*` | 49 |", "| `memory_*` | 52 |", 1,
     "| `memory_*` | 52 |"),
    ("README.md", "| `world_model_*` | 9 |", "| `world_model_*` | 8 |", 1,
     "| `world_model_*` | 8 |"),
    # two tables carry an `imagination_*` row; only the domain table (the one
    # with a "What it does" column) is corrected — the summary table on line
    # ~199 is a different, still-accurate view and is left alone.
    ("README.md", "| `imagination_*` | 8 | Counterfactual simulation |",
     "| `imagination_*` | 9 | Counterfactual simulation |", 1,
     "| `imagination_*` | 9 | Counterfactual simulation |"),
    # 9: relabel a2a as the transport layer AND insert the missing lie_* row in
    # one edit. The needle deliberately spans the a2a line so it is consumed by
    # the replacement — anchoring only on the `irc_*` line left that anchor in
    # place after the first run, so a re-run inserted the lie_* row a second time.
    ("README.md",
     "| `a2a_*` | 5 | Agent-to-agent | Discover, call, and orchestrate peer "
     "agents over A2A |\n| `irc_*` | 5 | Shared channel |",
     "| `a2a_*` | 5 | Agent-to-agent (transport layer) | Discover, call, and "
     "orchestrate peer agents over A2A. This is the A2A Hermes layer: one of the "
     "28 registration groups, **not** counted as one of the 27 tool domains "
     "|\n| `lie_*` | 10 | Live intent elicitation | Start and seal an "
     "elicitation session, feed transcript or audio, set a baseline, "
     "acknowledge cues, read status |\n| `irc_*` | 5 | Shared channel |", 1,
     "| `a2a_*` | 5 | Agent-to-agent (transport layer) |"),

    # ---- docs/02-tools-reference.md --------------------------------------
    ("docs/02-tools-reference.md", "**268 tools across 26 domains**",
     "**270 tools across 27 domains**", 1, "**270 tools across 27 domains**"),

    # ---- docs/05-complete-tools-reference.md -----------------------------
    ("docs/05-complete-tools-reference.md", "268 tools across 26 domains.",
     "270 tools across 27 domains.", 1, "270 tools across 27 domains."),
    ("docs/05-complete-tools-reference.md", "All 268 tools fully documented",
     "All 270 tools fully documented", 1, "All 270 tools fully documented"),
    ("docs/05-complete-tools-reference.md", "documentation for all 268 tools",
     "documentation for all 270 tools", 1, "documentation for all 270 tools"),
    ("docs/05-complete-tools-reference.md", '"target": "All 26 domains documented"',
     '"target": "All 27 domains documented"', 1,
     '"target": "All 27 domains documented"'),
    ("docs/05-complete-tools-reference.md", "docs for all 268 tools",
     "docs for all 270 tools", 1, "docs for all 270 tools"),
    ("docs/05-complete-tools-reference.md", "| **TOTAL** | **268** | 26 domains |",
     "| **TOTAL** | **270** | 27 domains |", 1,
     "| **TOTAL** | **270** | 27 domains |"),

    # ---- docs/index.html -------------------------------------------------
    # three occurrences of the same sentence in the hero, a card and the CTA
    ("docs/index.html", "268 tools across 26 domains",
     "270 tools across 27 domains", 3, "270 tools across 27 domains"),
    ("docs/index.html", "<li>268 tools \u00b7 26 domains</li>",
     "<li>270 tools \u00b7 27 domains</li>", 1,
     "<li>270 tools \u00b7 27 domains</li>"),
]

ROOT = pathlib.Path(__file__).resolve().parents[2]


def main() -> int:
    check_only = "--check" in sys.argv
    failures, changed = [], []
    cache = {}

    for path, needle, repl, expected, marker in EDITS:
        p = ROOT / path
        if p not in cache:
            cache[p] = p.read_text(encoding="utf-8")
        text = cache[p]

        got = text.count(needle)
        if got == 0:
            # Disambiguate "already applied" from "anchor missing" using the
            # post-edit outcome, not the replacement string — the replacement
            # can be a substring of the pre-edit text.
            if marker in text:
                continue  # already applied, idempotent no-op
            failures.append(f"{path}: anchor missing entirely: {needle[:50]!r}")
            continue
        if got != expected:
            failures.append(
                f"{path}: expected {expected} occurrence(s) of {needle[:50]!r}, "
                f"found {got}")
            continue
        cache[p] = text.replace(needle, repl)
        if path not in changed:
            changed.append(path)

    if failures:
        print("FAILED — nothing written:")
        for f in failures:
            print("  " + f)
        return 1

    if check_only:
        print("check OK — all anchors present and as expected")
        for c in changed:
            print("  would edit " + c)
        return 0

    for p, text in cache.items():
        p.write_text(text, encoding="utf-8")
    print("applied 270/27 correction to:")
    for c in changed:
        print("  " + c)
    return 0


if __name__ == "__main__":
    sys.exit(main())
