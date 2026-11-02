# Publication note — serial 2026-11-01

**Applies to:** `serial-2026-11-01.md` and `serial-2026-11-01b.md`
**Note written:** 2026-11-01, after both parts were committed
**Frontier the two posts are pinned to:** `2ea4492209dfaae6afb22ca884132a0d1849bfcf`

This note exists because `main` moved while the instalment was being written, and one of the figures in
it is now out of date in a way a reader would otherwise read as an error.

## What moved

When the two parts were drafted, `main` was at `2ea44922` and `VERSION` read `3.1.0`. By the time the
second part was committed, `main` had advanced:

```
$ git fetch origin main
$ git rev-parse origin/main
48c241a1edff1fdc9f0d0b38f51796c3c8b88b2b

$ git log -1 --format='%h %aI %s' origin/main
48c241a1 2026-11-01T10:33:30-07:00 chore(release): cut 3.1.2 and land the owner directive

$ git show origin/main:VERSION
3.1.2
```

So `VERSION` on `main` is now **3.1.2**, not 3.1.0. The posts say 3.1.0, and they are right to: every
figure in them is stated at the frontier they name, `2ea44922`, and at that commit `VERSION` is 3.1.0.

```
$ git show 2ea44922:VERSION
3.1.0
```

## What this does and does not change

**It does not change the finding.** The `v3.1.1`-before-`v3.1.0` ordering described in part two §5 is a
property of the tag graph, and the graph has not changed. `52ffe13d` (tag `v3.1.1`) is still an ancestor
of `73343f68` (tag `v3.1.0`). Cutting 3.1.2 on top of both does not reorder them.

**It does change one number.** The "63 commits behind" figure for `v3.1.1` was measured against
`2ea44922`. Against `48c241a1` it is larger, because `main` gained commits. A reader re-running the
verifier in part two §11 will get a mismatch on that assertion, and the mismatch is correct: the script
pins `FRONT=2ea44922` and checks out whatever `HEAD` is, so it will fail on a moved `main` by design.
That is the script doing its job — a figure is a fact about the moment it was measured.

**It also closes the thread part two left open.** Part two §12 asked whether the repository has a check
that `VERSION` is monotonic across its release tags. `48c241a1` cuts 3.1.2, which is higher than both
3.1.0 and 3.1.1, so the *current* state is monotonic. Whether a *check* now exists is a separate
question this note does not answer, and the next instalment should.

## Why this is a note and not an edit

The two posts are pinned to a named baseline and every figure in them is reproducible at that baseline.
Rewriting them to track a moving `main` would make them unpinnable — the next commit would invalidate
them again. The discipline the serial follows is: state the frontier, measure at the frontier, and
record the movement separately. This note is that record.

It is also the honest form of a correction. Nothing in the two posts was wrong when written. A figure
that was right at its baseline and is stale at a later one is not an error; it is a measurement with a
date on it, and the date is in the header of both parts.
