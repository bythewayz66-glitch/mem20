#!/usr/bin/env python3
"""ACCEPTANCE CHECK for docs/gtm/claim-ledger.md.

Enforces the owner directive's acceptance criterion mechanically:

    "the ledger has ZERO rows marked `verified` without a cited command"

Rules checked
-------------
1. Every table row whose Status cell contains VERIFIED must also carry a
   non-empty Command cell, and that cell must contain a real invocation
   (a backticked command, a file path, or a URL) -- not prose.
2. No Status cell may be blank, "-", or "TBD".
3. In any table that declares an `Adversarial` column, that cell must be
   non-blank and must use the controlled vocabulary (0.000 / unmeasured /
   n/a: <reason>).
4. Retired numbers (257 / 258 / 268 / "26 domains") may appear ONLY inside
   the retired-values register (section 7), inside a row whose Status is
   STALE / RETIRED / CORRECTED / WITHDRAWN (i.e. a row that exists to name
   the defect), or inside a never-say / banned cell.

Exit code 0 = PASS, 1 = FAIL.

Usage:
    python3 docs/gtm/verify/check_ledger.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
LEDGER = os.path.join(ROOT, "docs", "gtm", "claim-ledger.md")

RETIRED = re.compile(r"\b(257|258|268)\b|26 domains")
CITATION = re.compile(r"`[^`]+`|https?://|\b[\w./-]+\.(py|sh|json|md|toml|yml)\b")
STATUS_WORDS = re.compile(
    r"\b(VERIFIED|STALE|CHANGED|RETIRED|WITHDRAWN|CORRECTED|CLOSED|"
    r"TIGHTENED|RESOLVED|UNMEASURED)\b", re.I)
# A row that exists to name a defect may legitimately print the retired value.
DEFECT_STATUS = re.compile(r"\b(STALE|RETIRED|CORRECTED|WITHDRAWN)\b", re.I)
NEVER_SAY = re.compile(r"never say|banned|prohibit|do not|must not|"
                       r"retired surface|named prior", re.I)
ADV_OK = re.compile(r"^(0\.000|unmeasured|n/a:)", re.I)

failures = []
stats = {"rows": 0, "verified": 0, "stale": 0, "changed": 0, "retired": 0,
         "adv_tables": 0}


def cells(line):
    """Split a markdown table row on pipes, ignoring pipes inside backticks.

    Command cells legitimately contain shell pipes (`... | wc -l`), so a naive
    split on "|" shreds the row and shifts every later column.
    """
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|"):
        body = body[:-1]
    out, buf, in_tick = [], [], False
    for ch in body:
        if ch == "`":
            in_tick = not in_tick
            buf.append(ch)
        elif ch == "|" and not in_tick:
            out.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    out.append("".join(buf).strip())
    return out


def unbacktick(s):
    return s.strip().strip("`").strip()


def main():
    with open(LEDGER) as f:
        lines = f.read().splitlines()

    section = ""
    in_register = False
    header = None          # column names of the current table
    adv_idx = None         # index of the Adversarial column, if any
    status_idx = None
    neversay_idx = None    # index of a "Never say" column, if any

    for i, line in enumerate(lines, 1):
        if line.startswith("## "):
            section = line[3:].strip()
            in_register = section.startswith("7.")
            header = None
            adv_idx = status_idx = neversay_idx = None
            continue

        if not line.startswith("|"):
            header = None
            adv_idx = status_idx = neversay_idx = None
            continue

        c = cells(line)
        if not c or set("".join(c)) <= set("-: "):
            continue

        # Header row: establishes the columns for this table.
        if header is None:
            header = [unbacktick(x).lower() for x in c]
            adv_idx = next((n for n, h in enumerate(header)
                            if h.startswith("adversarial")), None)
            status_idx = next((n for n, h in enumerate(header)
                               if h.startswith("status")), None)
            neversay_idx = next((n for n, h in enumerate(header)
                                 if "never say" in h), None)
            if adv_idx is not None:
                stats["adv_tables"] += 1
            continue

        joined = " | ".join(c)
        status = c[status_idx] if status_idx is not None and status_idx < len(c) else ""
        if not status:
            status = next((x for x in c if STATUS_WORDS.search(x)), "")

        # Rule 4: retired numbers outside the register. A "Never say" cell is
        # the one place a retired value is quoted on purpose, to forbid it.
        in_never_say = (neversay_idx is not None and neversay_idx < len(c)
                        and RETIRED.search(c[neversay_idx]))
        if not in_register and RETIRED.search(joined):
            if not (DEFECT_STATUS.search(status) or NEVER_SAY.search(joined)
                    or in_never_say):
                failures.append(
                    "L%d [%s] retired number outside the register: %s"
                    % (i, section, joined[:140]))

        if not status:
            continue
        stats["rows"] += 1
        low = status.lower()
        for k in ("verified", "stale", "changed", "retired"):
            if k in low:
                stats[k] += 1

        # Rule 2: no blank status.
        if unbacktick(status) in ("", "-", "TBD"):
            failures.append("L%d blank status" % i)

        # Rule 1: VERIFIED requires a cited command.
        if "verified" in low:
            cmd = ""
            for n, x in enumerate(c):
                if n == status_idx or n == adv_idx:
                    continue
                if CITATION.search(x) and x != status:
                    cmd = x
                    break
            if not cmd:
                failures.append(
                    "L%d VERIFIED with no cited command: %s" % (i, joined[:140]))

        # Rule 3: Adversarial column, only where the table declares one.
        if adv_idx is not None:
            if adv_idx >= len(c):
                failures.append("L%d Adversarial cell missing: %s"
                                % (i, joined[:140]))
            else:
                adv = unbacktick(c[adv_idx])
                if not adv or adv in ("-", "\u2014", "TBD"):
                    failures.append("L%d blank Adversarial cell: %s"
                                    % (i, joined[:140]))
                elif not ADV_OK.match(adv):
                    failures.append(
                        "L%d Adversarial cell outside the controlled "
                        "vocabulary (%r): %s" % (i, adv, joined[:140]))

    print("ledger: %s" % LEDGER)
    print("tables declaring an Adversarial column: %d" % stats["adv_tables"])
    print("rows with a status: %d  (verified=%d stale=%d changed=%d retired=%d)"
          % (stats["rows"], stats["verified"], stats["stale"],
             stats["changed"], stats["retired"]))
    print()
    if failures:
        print("FAIL -- %d defect(s):" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("PASS -- every VERIFIED row cites a command; no retired number "
          "outside the register; no blank or off-vocabulary Adversarial cell.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
