# mem20 — Finance Report: Canonical Repo Rebase

**As of:** 2026-10-14 · commit `c274404` · prepared by the Finance Assistant
**Source of truth:** https://github.com/bythewayz66-glitch/mem20

---

## What this is

The mem20 finance report, re-pointed at the newly designated canonical repository and with every
figure that depended on the old repository reference re-derived. House numbers — TAM `$1.28B`,
SAM `$282M`, SOM `$1.68M`, blended ACV `$14,000` — are **preserved exactly**; only repo-dependent
inputs move.

## What changed

The repository previously cited throughout the finance model,
`github.com/JaysonAIOnline/mem20`, returns **HTTP 404** and does not exist. Its version string
(`v2.1.0rc2`) had no supporting location, and its install path (`pip install mem20`) is not
serviceable — the package is not on PyPI. Every reference is now anchored to
`bythewayz66-glitch/mem20` at `c274404`.

**26 corrections logged · 14 of them move a number in the model.**

Two are material:

| | Effect |
|---|---|
| **Acquisition** | Blended CAC `$8,000 → $16,800`. The canonical repo carries 0 stars, 0 forks, 0 releases and no package index entry, so the OSS-led inbound path has no support. Acquiring the full SOM book costs `$1,056,000` more. |
| **Support** | Cost per account `$1,200 → $2,400`. The issue tracker and discussions are both disabled (`has_issues=false`, `has_discussions=false`), removing the community-deflection channel. Gross margin compresses `78.0% → 69.4%`. |

Net effect: 3-yr LTV:CAC falls `4.74× → 2.01×`, below the 3.0× institutional hurdle.

## Headline position

| Metric | Value | vs retired basis |
|---|---|---|
| Blended ACV | $14,000 | held exactly |
| SOM (3-yr ARR) | $1.68M | held exactly |
| Gross margin | 69.4% | ▼ 8.6 pts |
| CAC payback | 1.73 yr | ▲ 1.00 yr |
| 3-yr LTV:CAC | 2.01× | ▼ 2.73× |

## Contents

| Path | What |
|---|---|
| `webpages/mem20-finance-report/index.html` | The report page (self-contained; no external assets) — published separately and staged into this bundle by the deploy script |
| `data/corrections_register.csv` | All 26 corrections: legacy value → canonical value, with source |
| `data/repo_dependencies.csv` | The 14 model lines conditional on the repository, with the signal that moved each |
| `data/unit_economics.csv` | Full cost stack, ACV tier ladder, acquisition metrics |
| `data/market_sizing.csv` | TAM → SAM → SOM bridge with account counts |
| `model/compute_model.py` | Deterministic model that generates every figure above |
| `deploy_finance_to_sidney.sh` | Publish script (Sidney via ssh/rsync, gated through gabe) |
| `SHA256SUMS` | Checksum manifest for the payload |

Regenerate all numbers with:

```bash
python3 model/compute_model.py
```

The model asserts its own invariants: the tier shares must sum to 1 and the weighted tier mix must
land on `$14,000` exactly. If either drifts, the script fails rather than emitting a wrong figure.

## Publishing to Sidney

Standing programme instruction: publish to the Sidney server via ssh/sftp/rsync, all work routed
through gabe.

- **Sidney** `216.198.115.91:2222` — reachable; SSH is open and accepts publickey/password.
- **Credentials** are not present in the sandbox, so the remote leg cannot be executed from here.
  The bundle and script are staged and ready.
- **gabe** gates the payload before publication. Nothing reaches Sidney without passing it.

```bash
export SIDNEY_HOST=216.198.115.91 SIDNEY_PORT=2222 SIDNEY_USER=<user>
export SSHPASS=<secret>            # or SSH_KEY=/path/to/key
bash deploy_finance_to_sidney.sh
```

The script refuses to run without authentication material — it never falls back to a guessed host
or an insecure default — and it never writes a secret into the payload it publishes. Verify the
transfer with `sha256sum -c SHA256SUMS` on the target (step 3 of the script does this).

## Guardrails honoured

- No LoCoMo or LongMemEval comparability is claimed against Mem0 or Zep.
- The adversarial hit rate of `0.000` is retained visibly, not omitted.
- The promotion mechanism is described as evidence-based with an append-only audit trail — never
  as tamper-proof or unfakeable.
- MIT licensing is stated as a fact about the repository, not as a moat.

---

**Disclaimer.** As an AI Agent, I cannot provide legally protected, personalized investment advice.
This analysis is for informational purposes only and does not constitute investment advice or
recommendations. Consult a licensed financial advisor before making investment decisions.
