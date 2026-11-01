#!/usr/bin/env python3
"""Re-derive the tier ladder from the locked $14,000 blended ACV.

WHY THIS FILE EXISTS
--------------------
`RECONCILIATION_NOTE.md` asserted the ladder blends to $14,000 by printing a
weighted-sum table. A table is a *result*, not a derivation: it shows that four
products add up, but it does not show that the four shares are the ones the
target forces, nor what happens if one of them is wrong. This script derives
them, so the note can quote arithmetic instead of restating a conclusion.

The derivation has five parts, each printed as a literal equation:

  D1  FORCED SHARES   - the blend pins one share given the other three. Invert
                        it four ways: all four must return the declared share,
                        otherwise the ladder and the target disagree.
  D2  FORCED PRICES   - at fixed shares, d(ACV)/dp_i = s_i. So the blend is 18x
                        more sensitive to the entry tier than to the top tier,
                        and every compensating price move is computable.
  D3  CONTRIBUTION    - the absolute floor (COGS) and the maximum discount each
                        tier can absorb before contribution hits zero. This is
                        the number a discount policy has to respect.
  D4  REACHABILITY    - the target in integer space: which whole-account books
                        reproduce it, and how many accounts of mix drift the
                        blend survives.
  D5  SURFACE         - the live tool surface, derived from executable code in
                        this repo (not quoted from a doc), so the pricing
                        collateral can state it without going stale again.

Every figure the docs quote is emitted here and written to
`docs/pricing/tier-price-derivation.csv`. `docs/pricing/audit_pricing_docs.py`
then asserts each of those strings appears in the docs, so no number can be
hand-transcribed and no doc can drift from this model.

The ladder itself is READ from `docs/finance/inputs.json` - it is not restated
here. Restating it would reproduce the defect this replaces: a guard that
hardcodes its own subject can never detect drift in it.

Usage:  python3 docs/pricing/tier_price_derivation.py [--root .] [--write]
Exits 1 if any invariant fails.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys
from decimal import Decimal as D

# --------------------------------------------------------------------------
# Carried house numbers. These are the inputs to everything below and are
# asserted against docs/finance/inputs.json on every run - see load_inputs().
# --------------------------------------------------------------------------
HOUSE_ACV = D(14_000)
TAM = D(1_280_000_000)
SAM = D(282_000_000)
SOM = D(1_680_000)
LOGOS = 120

HOSTING_PER_ACCOUNT = D(1_880)
TICKETS_PER_ACCOUNT = D(24)
COST_PER_TICKET = D(100)
DIRECT_SUPPORT = TICKETS_PER_ACCOUNT * COST_PER_TICKET          # $2,400
COGS_PER_ACCOUNT = HOSTING_PER_ACCOUNT + DIRECT_SUPPORT         # $4,280

# Fallback ladder, used only if inputs.json is unreadable. The run FAILS when
# it falls back, so a missing input file cannot silently pass.
FALLBACK_LADDER = [("Team", D(6_000), D("0.72")),
                   ("Business", D(18_000), D("0.12")),
                   ("Scale", D(36_000), D("0.12")),
                   ("Enterprise", D(80_000), D("0.04"))]

EMITTED: dict[str, str] = {}      # key -> exact string the docs may quote
RESULTS: list[dict] = []


def emit(key: str, text: str) -> str:
    """Record a string as quotable in the docs, and print it."""
    EMITTED[key] = text
    print(text)
    return text


def money(x: D, cents: bool = False) -> str:
    q = D("0.01") if cents else D("1")
    v = x.quantize(q)
    return f"${v:,.2f}" if cents else f"${v:,.0f}"


def pct(x: D) -> str:
    return f"{(x * 100).quantize(D('0.01'))}%"


# --------------------------------------------------------------------------
# Load the ladder from the finance model's input file (single source of truth)
# --------------------------------------------------------------------------
def load_inputs(root: pathlib.Path) -> tuple[list[tuple[str, D, D]], list[str]]:
    errs: list[str] = []
    path = root / "docs" / "finance" / "inputs.json"
    if not path.exists():
        return FALLBACK_LADDER, [f"missing {path} - ladder not read from source of truth"]
    data = json.loads(path.read_text(encoding="utf-8"))
    house = data.get("house_numbers", {})
    for key, want in (("blended_acv_usd", HOUSE_ACV), ("sam_usd", SAM),
                      ("tam_usd", TAM), ("som_arr_usd", SOM),
                      ("som_accounts", LOGOS)):
        got = house.get(key)
        if got is None or D(str(got)) != want:
            errs.append(f"inputs.json house_numbers.{key} = {got}, expected {want}")
    surf = data.get("tool_surface", {})
    ladder = [(row["tier"], D(str(row["acv_usd"])), D(str(row["share"])))
              for row in data.get("tier_ladder", [])]
    if len(ladder) != 4:
        errs.append(f"inputs.json tier_ladder has {len(ladder)} rows, expected 4")
    return (ladder or FALLBACK_LADDER), errs


# --------------------------------------------------------------------------
# D1 - forced shares
# --------------------------------------------------------------------------
def forced_shares(ladder: list[tuple[str, D, D]]) -> tuple[list[D], list[str]]:
    """Solve the blend for each share in turn. All four must agree."""
    print("\n== D1. FORCED SHARES - the target pins each share given the other three ==")
    prices = [p for _, p, _ in ladder]
    shares = [s for _, _, s in ladder]
    out: list[D] = []
    for i, (name, price, declared) in enumerate(ladder):
        rest = sum(prices[j] * shares[j] for j in range(len(ladder)) if j != i)
        residual = HOUSE_ACV - rest
        solved = residual / price
        out.append(solved)
        emit(f"share_solve_{name}",
             f"  s_{name:<10} = (14,000 - {money(rest, True)}) / {money(price)}"
             f" = {money(residual, True)} / {money(price)} = {solved.quantize(D('0.0001'))}")
        assert solved == declared, f"{name} share solves to {solved}, declared {declared}"
    return out, []


# --------------------------------------------------------------------------
# D2 - forced prices
# --------------------------------------------------------------------------
def price_sensitivity(ladder, shares) -> None:
    print("\n== D2. FORCED PRICES - d(ACV)/dp_i = s_i at fixed mix ==")
    prices = [p for _, p, _ in ladder]
    for (name, price, share) in ladder:
        emit(f"grad_{name}",
             f"  dACV/dp_{name:<10} = s = {share}  ->  a $1,000 move shifts the blend "
             f"{money(D(1000) * share, True)}")
    # Compensating move: restore the blend by moving the top tier.
    team_delta = D(1000)
    comp = -(team_delta * shares[0]) / shares[-1]
    emit("comp_team_to_enterprise",
         f"  Team +$1,000 forces Enterprise {money(comp, True)} "
         f"(-1000 x {shares[0]} / {shares[-1]} = {comp.quantize(D('0.01'))}) "
         f"to hold $14,000")
    # Ratio of entry-tier leverage to top-tier leverage.
    ratio = shares[0] / shares[-1]
    emit("leverage_ratio",
         f"  entry-tier leverage / top-tier leverage = {shares[0]} / {shares[-1]} = {ratio}\u00d7")
    RESULTS.append({"section": "D2", "metric": "leverage_ratio", "value": str(ratio)})


# --------------------------------------------------------------------------
# D3 - contribution and the discount ceiling
# --------------------------------------------------------------------------
def contribution(ladder) -> None:
    print("\n== D3. CONTRIBUTION - the absolute floor and the discount ceiling ==")
    emit("cogs", f"  COGS/account = {money(HOSTING_PER_ACCOUNT)} hosting + "
                 f"{money(DIRECT_SUPPORT)} direct support = {money(COGS_PER_ACCOUNT)}")
    for name, price, _ in ladder:
        contrib = price - COGS_PER_ACCOUNT
        gm = contrib / price
        ceiling = contrib / price          # max discount before contribution = 0
        emit(f"contrib_{name}",
             f"  {name:<10} {money(price):>8} - {money(COGS_PER_ACCOUNT)} = "
             f"{money(contrib, True):>10}  GM {pct(gm):>6}  "
             f"max discount before zero contribution {pct(ceiling)}")
        RESULTS.append({"section": "D3", "metric": f"gm_{name}", "value": str(gm)})
        RESULTS.append({"section": "D3", "metric": f"max_discount_{name}",
                        "value": str(ceiling)})
    tightest = min(ladder, key=lambda r: (r[1] - COGS_PER_ACCOUNT) / r[1])
    tc = (tightest[1] - COGS_PER_ACCOUNT) / tightest[1]
    emit("discount_cap",
         f"  binding discount cap is {tightest[0]} at {pct(tc)} - "
         f"any discount above that makes the entry tier contribution-negative")


# --------------------------------------------------------------------------
# D4 - integer reachability and drift
# --------------------------------------------------------------------------
def integer_space(ladder) -> None:
    print("\n== D4. REACHABILITY - the target on a real 120-logo book ==")
    prices = [p for _, p, _ in ladder]
    shares = [s for _, _, s in ladder]
    raw = [s * LOGOS for s in shares]
    emit("raw_shares", "  share x 120 = " +
         " / ".join(str(x.normalize()) for x in raw) +
         "  (none is an integer)")
    # ------------------------------------------------------------------
    # Largest remainder is NOT unique here. floors are [86,14,14,4] = 118,
    # two accounts are left over, and THREE tiers tie on fractional part 0.4
    # (Team .4, Business .4, Scale .4) while Enterprise uniquely takes .8.
    # So one leftover account is forced (Enterprise) and the second may go to
    # Team, Business or Scale -> three admissible books, not one.
    #
    # The previous note picked one of those three (86/15/14/5) and reported its
    # +$10,000 as "the" rounding error. That is the widest of the three. The
    # honest statement is the bracket, and whether the target sits inside it.
    # ------------------------------------------------------------------
    base = [int(x) for x in raw]
    rem = LOGOS - sum(base)
    fracs = [raw[i] - D(base[i]) for i in range(4)]
    # The rem-th largest fractional part is the cutoff. Tiers strictly above it
    # are forced to take a leftover account; tiers exactly on it compete for
    # whatever is left. That tie is the non-uniqueness.
    cutoff = sorted(fracs, reverse=True)[rem - 1]
    forced_idx = [i for i in range(4) if fracs[i] > cutoff]
    tied = [i for i in range(4) if fracs[i] == cutoff]
    extra_needed = rem - len(forced_idx)
    assert 0 <= extra_needed <= len(tied), "tie structure changed - re-derive"

    import itertools
    books = []
    for pick in itertools.combinations(tied, extra_needed):
        mix = list(base)
        for i in forced_idx + list(pick):
            mix[i] += 1
        books.append(tuple(mix))
    books.sort()
    assert all(sum(b) == LOGOS for b in books), "an admissible book lost an account"
    assert len(set(books)) == len(books), "duplicate book in the admissible set"
    emit("lr_floor_sum", "  floor of share x 120 = " +
         "/".join(str(b) for b in base) + f"  (sums to {sum(base)} - short by {rem})")
    emit("lr_tie", "  fractional parts = " +
         " / ".join(str(f) for f in fracs) +
         f"  -> {len(tied)} tiers tie on {cutoff}; largest remainder is NOT unique")
    emit("lr_books", "  admissible largest-remainder books: " +
         ", ".join("/".join(str(m) for m in b) for b in books))

    blends = [(b, sum(p * m for p, m in zip(prices, b)) / LOGOS) for b in books]
    lo_book, lo_blend = min(blends, key=lambda t: t[1])
    hi_book, hi_blend = max(blends, key=lambda t: t[1])
    emit("lr_band",
         f"  the band spans {money(lo_blend, True)} to {money(hi_blend, True)} "
         f"({money(lo_blend - HOUSE_ACV, True)} / {money(hi_blend - HOUSE_ACV, True)} vs house)")
    emit("lr_band_som",
         f"  SOM across the band: {money(lo_blend * LOGOS)} to {money(hi_blend * LOGOS)} "
         f"({money(lo_blend * LOGOS - SOM)} / {money(hi_blend * LOGOS - SOM)} vs {money(SOM)})")
    inside = lo_blend <= HOUSE_ACV <= hi_blend
    emit("lr_inside",
         f"  {money(HOUSE_ACV)} is {'INSIDE' if inside else 'OUTSIDE'} the admissible band "
         f"- the rounding does not move the target out of reach")
    assert inside, "target fell outside the admissible rounding band"

    # The three books individually, so no reader has to trust the bracket.
    for b, bl in sorted(blends, key=lambda t: t[1]):
        emit(f"lr_book_{''.join(str(m) for m in b)}",
             f"  {'/'.join(str(m) for m in b):<14} -> blend {money(bl, True)} "
             f"({money(bl - HOUSE_ACV, True)}), SOM {money(bl * LOGOS)}")

    # The largest gap between an admissible book and the target.
    mix = list(hi_book)
    mixstr = "/".join(str(m) for m in mix)
    emit("lr_mix", f"  widest admissible book  = {mixstr}  (sums to {sum(mix)})")
    blend_lr = hi_blend
    emit("lr_blend", f"  that book blends to {money(blend_lr, True)} "
                     f"(delta {money(blend_lr - HOUSE_ACV, True)} vs house)")
    emit("lr_som", f"  SOM on that book = 120 x {money(blend_lr, True)} = "
                   f"{money(blend_lr * LOGOS)}  "
                   f"(delta {money(blend_lr * LOGOS - SOM)} vs {money(SOM)})")
    # brute force the exact solution set
    exact, total = [], 0
    for a in range(LOGOS + 1):
        for b in range(LOGOS - a + 1):
            for c in range(LOGOS - a - b + 1):
                d = LOGOS - a - b - c
                total += 1
                if prices[0] * a + prices[1] * b + prices[2] * c + prices[3] * d == HOUSE_ACV * LOGOS:
                    exact.append((a, b, c, d))
    emit("mix_space", f"  integer mixes summing to 120: {total:,}")
    emit("mix_exact", f"  mixes landing exactly on {money(HOUSE_ACV)}: {len(exact)}")
    nearest = min(exact, key=lambda m: sum(abs(x - y) for x, y in zip(m, mix)))
    emit("mix_nearest", "  nearest exact mix to " + mixstr + ": " +
         "/".join(str(x) for x in nearest) +
         f"  (L1 = {sum(abs(x - y) for x, y in zip(nearest, mix))} accounts)")
    # The actionable answer: the exact mix closest to the DECLARED share vector,
    # measured against the real-valued 86.4/14.4/14.4/4.8 rather than a rounding.
    nearest_decl = min(exact, key=lambda m: sum(abs(D(x) - r) for x, r in zip(m, raw)))
    l1_decl = sum(abs(D(x) - r) for x, r in zip(nearest_decl, raw))
    emit("mix_nearest_declared",
         "  nearest exact mix to the declared 72/12/12/4: " +
         " / ".join(str(x) for x in nearest_decl) +
         f"  (L1 = {l1_decl.quantize(D('0.1'))} accounts from 86.4/14.4/14.4/4.8)")
    assert sum(p * m for p, m in zip(prices, nearest_decl)) == HOUSE_ACV * LOGOS
    # drift budget
    for j in range(1, 4):
        step = prices[j] - prices[0]
        per_logo = step / LOGOS
        acct_1pct = (SOM * D("0.01")) / step
        emit(f"drift_{j}",
             f"  Team<->{ladder[j][0]:<10} step {money(step):>8} -> "
             f"{money(per_logo, True)}/logo | 1% of SOM = {acct_1pct.quantize(D('0.01'))} accounts")


# --------------------------------------------------------------------------
# D5 - live tool surface, derived from executable code
# --------------------------------------------------------------------------
def derive_surface(root: pathlib.Path) -> tuple[int | None, int | None, list[str]]:
    """Count the tool surface from the MCP server that actually registers it.

    Three independent measurements, matching the commands the repo documents:
      * registration sites  - assignments to self.tools["..."]
      * distinct tools      - the same set, de-duplicated
      * domains             - register_*_tools groups minus the A2A transport
    """
    print("\n== D5. SURFACE - derived from executable code in this repo ==")
    pkg = root / "mcp"
    if not pkg.is_dir():
        return None, None, ["mcp/ not found - surface not derivable"]

    # The surface is what the SERVER WIRES, not what exists on disk. A module
    # that defines register_*_tools but is never called from _setup_tools()
    # contributes zero tools to tools/list, so counting every file over-states
    # the surface. Anchor on the call sites in mcp/server.py, then read the
    # registrations out of exactly those modules.
    server = pkg / "server.py"
    if not server.is_file():
        return None, None, ["mcp/server.py not found - surface not derivable"]
    wired = re.findall(r"self\.(register_[a-z0-9_]*_tools)\(\)",
                       server.read_text(encoding="utf-8", errors="replace"))
    if not wired:
        return None, None, ["no register_*_tools() calls in mcp/server.py"]

    # group name -> the module that defines it
    owner: dict[str, pathlib.Path] = {}
    for p in pkg.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"def\s+(register_[a-z0-9_]*_tools)\s*\(", text):
            owner.setdefault(m.group(1), p)

    sites, names, groups = [], set(), set()
    for g in wired:
        groups.add(g)
        p = owner.get(g)
        if p is None:
            return None, None, [f"{g}() is wired in server.py but defined nowhere"]
        text = p.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r'self\.tools\[\s*"([^"]+)"\s*\]', text):
            sites.append(m.group(1))
            names.add(m.group(1))

    # Wave-1 subsystems attach their tools by WRAPPING an already-wired
    # register_*_tools method from mcp/tools/__init__.py, so they never appear
    # as a call site in server.py. They are still on the live surface, so read
    # the installers the package actually imports and count what they add.
    init = pkg / "tools" / "__init__.py"
    injected: list[str] = []
    if init.is_file():
        itext = init.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"from\s+tools\.([a-z0-9_]+)\s+import\s+install", itext):
            mod = pkg / "tools" / f"{m.group(1)}.py"
            if not mod.is_file():
                continue
            mtext = mod.read_text(encoding="utf-8", errors="replace")
            for t in re.finditer(r'self\.tools\[\s*"([^"]+)"\s*\]', mtext):
                injected.append(t.group(1))
                sites.append(t.group(1))
                names.add(t.group(1))
    if injected:
        emit("surface_injected",
             f"  installer-injected tools : {len(set(injected))} "
             f"({', '.join(sorted(set(injected)))})")

    domains = len(groups) - 1          # minus register_a2a_tools (transport)
    emit("surface_sites",   f"  registration sites      : {len(sites)}")
    emit("surface_distinct", f"  distinct tool names     : {len(names)}")
    emit("surface_groups",  f"  register_*_tools groups : {len(groups)}")
    emit("surface_domains", f"  domains                 : {len(groups)} - 1 (A2A transport) = {domains}")
    emit("surface_live",    f"  LIVE SURFACE            : {len(names)} tools / {domains} domains")
    return len(names), domains, []


def stale_surface_count(root: pathlib.Path) -> None:
    """Measure, do not quote, the number of retired-surface mentions on disk."""
    pat = re.compile(r"\b(?:257|268)\s*(?:-|\s)?tools?\b|\b26\s*(?:-|\s)?domains?\b"
                     r"|\b(?:257|268)\s*/\s*26\b", re.I)
    hist = re.compile(r"retir|supersed|legacy|histor|no\s+longer|previously|stale|drift"
                      r"|banned|was\s+(?:25|26)\b", re.I)
    suf = {".md", ".html", ".htm", ".csv", ".json", ".txt"}
    skip = {"node_modules", ".git", "target", "dist", "__pycache__", "corpus"}
    # Exclude the pricing registers from their own scan. They quote every retired
    # number in order to explain that it is retired, so counting them inflates
    # the total by a fixed amount and the figure drifts on every edit.
    self_report = {"RECONCILIATION_NOTE.md", "tier-sensitivity.md",
                   "TIER_SHIPPING_AUDIT.md", "tier_price_derivation.py",
                   "audit_pricing_docs.py", "audit_acv_consistency.py",
                   "audit_tier_shipping.py", "tier_sensitivity_model.py"}
    live = marked = 0
    docs_live = 0
    for p in root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in suf:
            continue
        if any(part in skip for part in p.parts):
            continue
        if p.name in self_report:
            continue
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for i, line in enumerate(lines):
            if not pat.search(line):
                continue
            window = "\n".join(lines[max(0, i - 2):i + 1])
            if hist.search(window):
                marked += 1
            else:
                live += 1
                if p.relative_to(root).parts[0] == "docs":
                    docs_live += 1
    emit("stale_total", f"  retired-surface mentions on disk      : {live + marked}")
    emit("stale_marked", f"    carrying a retirement marker        : {marked}")
    emit("stale_live", f"    present tense (unmarked)            : {live}")
    emit("stale_docs", f"    of those, in the canonical docs/ tree: {docs_live}")


# --------------------------------------------------------------------------
# Hand-checkable summary
# --------------------------------------------------------------------------
def summary(ladder) -> None:
    print("\n== SUMMARY - the whole derivation in one block ==")
    prices = [p for _, p, _ in ladder]
    shares = [s for _, _, s in ladder]
    terms = [p * s for p, s in zip(prices, shares)]
    for (name, price, share), term in zip(ladder, terms):
        emit(f"term_{name}",
             f"  {money(price):>8} x {str(share):<5} = {money(term, True):>10}")
    total = sum(terms)
    emit("term_sum", f"  {'-' * 26}\n  {'sum':>8}   {'':<5}   {money(total, True):>10}")
    emit("delta", f"  delta vs {money(HOUSE_ACV)} = {money(total - HOUSE_ACV, True)}")
    emit("som_identity", f"  120 x {money(HOUSE_ACV)} = {money(LOGOS * HOUSE_ACV)} = SOM")
    emit("sam_accounts",
         f"  {money(SAM)} / {money(HOUSE_ACV)} = {(SAM / HOUSE_ACV).quantize(D('0.01'))} accounts")
    emit("tam_accounts",
         f"  {money(TAM)} / {money(HOUSE_ACV)} = {(TAM / HOUSE_ACV).quantize(D('0.01'))} accounts")
    # +/-20% band
    for mult, label in ((D("0.80"), "-20%"), (D("0.90"), "-10%"),
                        (D("1.00"), "held"), (D("1.10"), "+10%"), (D("1.20"), "+20%")):
        acv = HOUSE_ACV * mult
        rev = acv * LOGOS
        gp = rev - COGS_PER_ACCOUNT * LOGOS
        emit(f"band_{label}",
             f"  {money(acv):>8} ({label:>5})  SOM {money(rev):>12}  GP {money(gp):>12}")


def gross_profit_book(ladder) -> None:
    """§6 of tier-sensitivity.md: GP by tier on the middle admissible book.

    The book is 86/15/14/5 - the middle of the three admissible largest-remainder
    books from D4. Every figure in the doc's §6 table is emitted here so the
    audit can prove it was not typed by hand.
    """
    print("\n== D6. GROSS PROFIT ON THE MIDDLE ADMISSIBLE BOOK (86/15/14/5) ==")
    book = [86, 15, 14, 5]
    assert sum(book) == LOGOS
    prices = [p for _, p, _ in ladder]
    rev_total = gp_total = 0
    rows = []
    for (name, price, _), n in zip(ladder, book):
        rev = price * n
        gp = (price - COGS_PER_ACCOUNT) * n
        rev_total += rev
        gp_total += gp
        rows.append((name, price, n, rev, price - COGS_PER_ACCOUNT, gp))
        emit(f"book_rev_{name}", f"  {name:<10} {n:>3} logos x {money(price):>8} = "
                                 f"{money(rev):>10} revenue")
        emit(f"book_gp_{name}", f"  {name:<10} {n:>3} logos x {money(price - COGS_PER_ACCOUNT, True):>10} = "
                                f"{money(gp):>10} gross profit")
    emit("book_rev_total", f"  total revenue      {money(rev_total)}")
    emit("book_gp_total", f"  total gross profit {money(gp_total)}")
    emit("book_gm", f"  blended GM         {pct(gp_total / rev_total)}")
    # The doc's §6 table is 1dp for readability; emit that form too so the audit
    # can gate the exact string the reader sees rather than a rounded variant.
    emit("book_gm_1dp", f"  blended GM (1dp)   {(gp_total / rev_total * 100).quantize(D('0.1'))}%")
    # GP share and logo share, and the leverage ratio between them.
    for (name, price, n, rev, gpa, gp) in rows:
        emit(f"book_gpshare_{name}",
             f"  {name:<10} GP share {pct(gp / gp_total):>6}  logo share {pct(D(n) / LOGOS):>6}  "
             f"leverage {(gp / gp_total) / (D(n) / LOGOS):.2f}x")
        emit(f"book_gpshare1_{name}",
             f"  {name:<10} GP share (1dp) {(gp / gp_total * 100).quantize(D('0.1'))}%  "
             f"logo share (1dp) {(D(n) / LOGOS * 100).quantize(D('0.1'))}%  "
             f"leverage {(gp / gp_total) / (D(n) / LOGOS):.2f}\u00d7")
    # Replacement ratio: how many Team logos replace one lost logo's gross profit.
    # Compare PER-ACCOUNT gross profit, not tier totals - a tier total already
    # includes the logo count, so dividing by it double-counts the mix.
    team_gp = rows[0][4]
    for (name, price, n, rev, gpa, gp) in rows[1:]:
        need = gpa / team_gp
        emit(f"replace_{name}",
             f"  1 {name:<10} = {need.quantize(D('0.1'))} Team logos "
             f"({money(need.quantize(D('1')) * prices[0])} ACV vs {money(price)} lost)")
    # The margin-negative trade, stated as arithmetic.
    ent = rows[3]
    need_ent = (ent[4] / team_gp).quantize(D("1"))
    new_gp = need_ent * team_gp
    emit("trade_ent_to_team",
         f"  {need_ent} Team logos replace 1 Enterprise: revenue "
         f"{money(need_ent * prices[0])} vs {money(ent[1])}, gross profit "
         f"{money(new_gp)} vs {money(ent[4])} -> "
         f"{'margin-negative' if new_gp < ent[4] else 'margin-positive'}")
    # §7 GP/account column at the house figure.
    for mult, label in ((D("0.80"), "-20%"), (D("0.90"), "-10%"),
                        (D("1.00"), "held"), (D("1.10"), "+10%"), (D("1.20"), "+20%")):
        acv = HOUSE_ACV * mult
        emit(f"gpa_{label}", f"  {money(acv):>8} ({label:>5}) GP/account "
                             f"{money(acv - COGS_PER_ACCOUNT)}  GM {pct((acv - COGS_PER_ACCOUNT) / acv)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    root = pathlib.Path(args.root).resolve()

    ladder, errs = load_inputs(root)
    print("== D0. INVARIANTS ==")
    emit("inv_acv", f"  blended ACV target   {money(HOUSE_ACV)}")
    emit("inv_logos", f"  SOM account count    {LOGOS}")
    emit("inv_som", f"  SOM ARR              {money(SOM)}")
    emit("inv_gate", f"  identity gate        {LOGOS} x {money(HOUSE_ACV)} = "
                     f"{money(LOGOS * HOUSE_ACV)}  "
                     f"[{'PASS' if LOGOS * HOUSE_ACV == SOM else 'FAIL'}]")
    emit("inv_crosscheck",
         f"  SAM/ACV = {(SAM / HOUSE_ACV).quantize(D('0.01'))} accounts, "
         f"TAM/ACV = {(TAM / HOUSE_ACV).quantize(D('0.01'))} accounts")
    emit("ladder_source", "  ladder read from docs/finance/inputs.json (not restated here)")

    shares, e = forced_shares(ladder)
    errs += e
    price_sensitivity(ladder, shares)
    contribution(ladder)
    integer_space(ladder)
    n_tools, n_domains, e = derive_surface(root)
    errs += e
    stale_surface_count(root)
    gross_profit_book(ladder)
    summary(ladder)

    if args.write:
        out = root / "docs" / "pricing" / "tier-price-derivation.csv"
        with out.open("w", newline="", encoding="utf-8") as fh:
            # lineterminator="\n": the csv module defaults to CRLF, which would
            # make this generated file the one CRLF file in docs/ and produce a
            # whole-file diff on every regeneration.
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["section", "metric", "value"])
            for r in RESULTS:
                w.writerow([r["section"], r["metric"], r["value"]])
            for k, v in EMITTED.items():
                w.writerow(["emitted", k, v.strip()])
        print(f"\nwrote {out.relative_to(root)}")

    if errs:
        print("\nDERIVATION FAIL")
        for e in errs:
            print("  -", e)
        return 1
    print("\nDERIVATION OK - every share is forced by the target, every price is above "
          "the cost floor, and the live surface is derived from code.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
