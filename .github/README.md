# `.github/` — CI, review gates and agent instructions

**Owner:** mem20-admin · **Status:** live CI configuration

Everything GitHub reads about this repo: the 14 workflows that gate a merge, the
review ownership map, the PR/issue templates, and the Copilot agent instructions.

## Workflows (14)

| Workflow | What it gates |
|---|---|
| `ci.yml` | The main suite. |
| `pr-gate.yml` | The aggregate merge gate. |
| `doc-counts.yml` | **Doc-count drift** — runs `scripts/ops/check-doc-counts.py` (self-test + gate) on every push and PR to `main`. See [`docs/hygiene/doc-count-gate.md`](../docs/hygiene/doc-count-gate.md). |
| `mcp-verify.yml` | MCP handshake from a deliberately **shallow** clone (`fetch-depth: 1`), so a shallow-clone regression fails the build. |
| `artifact-evidence.yml` | Requires a committed `/sites/` URL or 40-char SHA as evidence. |
| `contrib-evidence.yml` | Contributor evidence check. |
| `finance-model-drift.yml` | Fails when the market model's inputs and outputs disagree. |
| `ruby-sdk.yml` | The Ruby SDK suite, including `surface_spec.rb`'s surface drift guard. |
| `controlz-desktop.yml` | The `mem20controlz` desktop shell wiring. |
| `mem20-web.yml` | The `web/` frontend build. |
| `pages.yml` | GitHub Pages deployment of `docs/`. |
| `release.yml` | Release packaging. |
| `copilot-setup-steps.yml` | Copilot agent environment setup. |
| `zz-probe.yml` | Diagnostic probe. |

## Other files

| Path | What it is |
|---|---|
| [`CODEOWNERS`](./CODEOWNERS) | Review ownership map. |
| [`PULL_REQUEST_TEMPLATE.md`](./PULL_REQUEST_TEMPLATE.md) | The PR template (note: a lowercase `pull_request_template.md` also exists — GitHub reads the uppercase one). |
| [`ISSUE_TEMPLATE/`](./ISSUE_TEMPLATE/) | Issue forms. |
| [`copilot-instructions.md`](./copilot-instructions.md) | Copilot agent instructions. |
| [`instructions/`](./instructions/) | Additional agent instruction files. |
| [`dependabot.yml`](./dependabot.yml) | Dependency update config. |

## Rules

1. **A gate that cannot fail is not a gate.** Every workflow here must be able to
   produce a red check on a real defect. `doc-counts.yml` exists because the
   surface moved nine times and prose kept the old number.
2. **Do not weaken a gate to make a PR green.** Fix the defect, or open an issue
   that names the gate and the reason.
3. **Shallow-clone safety is a hard requirement.** `mcp-verify.yml` runs with
   `fetch-depth: 1` on purpose — the server must start with zero git history.

## Related

- [`AGENTS.md`](../AGENTS.md) — the agent operating protocol.
- [`docs/hygiene/`](../docs/hygiene/) — the gates' own documentation.
- [`CONTRIBUTING.md`](../CONTRIBUTING.md) — the contributor path.
