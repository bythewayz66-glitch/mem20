# `docs/attestations/` — credential and process attestations

**Owner:** mem20-admin · **Status:** append-only, dated

Signed statements from an agent or operator about **how a credential or process was
used** during a specific piece of work. These exist so a token's blast radius is
auditable after the fact: which branch, which base SHA, which invocation paths, and
what was *not* done.

## What lives here

| File | Attests |
|---|---|
| [`2026-11-01-token-attestation-webdev.md`](./2026-11-01-token-attestation-webdev.md) | Webpage Developer's use of a fine-grained PAT on `chore/token-attestation-2026-11-01` (base `main` @ `d99ab5d8`): the three permitted invocation paths (one-off remote URL, `GITHUB_TOKEN`/`GH_TOKEN` env, `Authorization: Bearer` API) and the redaction rule. |

## Rules

1. **One file per attestation, dated in the filename** (`YYYY-MM-DD-<subject>.md`).
2. **Never paste a live secret.** Tokens are referenced redacted (e.g.
   `github_pat_11CO3…`). An attestation that contains a usable credential is a defect,
   not evidence.
3. **State the base SHA and the branch.** An attestation without a 40-char base SHA
   cannot be tied to a tree and is not evidence.
4. **Append-only.** Do not edit a past attestation; write a new one that supersedes it.

## Related

- [`SECURITY.md`](../../SECURITY.md) — repo-wide security policy and disclosure path.
- [`docs/hygiene/`](../hygiene/) — the mechanical gates that back these claims.
