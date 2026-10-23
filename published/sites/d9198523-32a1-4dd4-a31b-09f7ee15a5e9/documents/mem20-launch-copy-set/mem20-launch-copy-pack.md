# mem20 — Launch Copy Pack

**Version:** v3 (canonical-repo-corrected)
**Produced by:** Mem20-Content (Content Creator)
**Program:** mem20 launch / repo migration
**Product version of record:** `2.1.0rc2` (`pyproject.toml` on `main`)
**Canonical repository:** https://github.com/bythewayz66-glitch/mem20
**Wedge:** *Auditable agent memory — the memory layer you can prove.*
**Supersedes:** v2 (`documents/mem20-assets-refresh/`), which targeted a repository path that returns 404 and carried an install block that does not work on the canonical tree.

This is one document. Numbered sections are parts of a single copy pack, not separate files.

---

## 1. Canonical reference table — the only references that may appear in copy

| Thing | Canonical value | Verification performed this run |
|---|---|---|
| Repository | `https://github.com/bythewayz66-glitch/mem20` | GitHub API → **HTTP 200**, public, `private: false` |
| Default branch | `main` | GitHub API |
| License | MIT | GitHub API `license.spdx_id = MIT` |
| Language | Python | GitHub API `language = Python` |
| Product version | `2.1.0rc2` | `pyproject.toml` `[project].version` |
| Install | `python3 -m venv .venv` then `.venv/bin/pip install -r requirements.txt` | `requirements.txt` on `main`; also `install.sh`, README, `docs/03-installation.md` |
| Run (stdio) | `MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py` | README "Quick Start", `install.sh` fallback message, `docs/03-installation.md` |
| Run (console script) | `pip install .` then `mem20-mcp` | `pyproject.toml` `[project.scripts]` → `mem20-mcp = "launcher:main"` |
| SDK dependency | `mcp>=2.1.1` | `requirements.txt`, `pyproject.toml` `dependencies` |
| Transport | MCP / JSON-RPC 2.0 over stdio; HTTP health on `:8080` (`/health`, `/ready`, `/metrics`) | README "Transport / protocol" |
| Tool surface (house number) | **268 tools across 26 domains** | README "Tool domains (26)" — stated as counted by instantiating the server |
| Market sizing (house numbers) | TAM **$1.28B** · SAM **$282M** · SOM **$1.68M** · blended ACV **$14,000** | Program brief |
| Distribution status | Not on PyPI | `pypi.org/pypi/mem20/json` → **HTTP 404** |

**Rule:** if a repo, install, or tool-count reference is not in this table, it does not go into an asset.

### 1.1 Stale → canonical ledger

| Item | Was (retired — must not appear in published copy) | Now (canonical) | Why |
|---|---|---|---|
| Repository path | Retired-org path for `mem20` (resolves to 404) | `github.com/bythewayz66-glitch/mem20` | Repo migration; old path returns 404 |
| Install command | `pip install "mcp<2"` + `pip install -e .` | `.venv/bin/pip install -r requirements.txt` | Tree declares `mcp>=2.1.1`; the old pin installs an SDK the tree does not use |
| Run command | `python -m mcp_cognitive_substrate.cli` | `.venv/bin/python mcp/mcp_server.py` | Former module belongs to the older, non-canonical substrate repo; does not exist on this tree |
| Package install | bare `pip install mem20` as a supported command | source install only | PyPI returns 404 |
| Tool count | `~258–260` range | **268** | House number standardised |
| Benchmark framing | unqualified numbers | numbers labelled self-reported on internal harness | Not independently audited; no reproduction script in repo |
| Landing CTA | old-org repo href | canonical repo href | Dead destination |

The exact retired strings are counted per file in `mem20-reference-audit.csv`; they are deliberately not reprinted here.

---

## 2. Positioning lines

**One-liner (primary)**

> mem20 is persistent memory for AI agents — with a hard partition between what an agent actually knows and what it made up.

**Short alt (nav bars, meta descriptions, gallery subtitles)**

> Auditable agent memory. Grounded vs simulated, enforced — not hoped for.

**H1 (landing / README)**

> Auditable agent memory — the memory layer you can prove.

**Subhead**

> mem20 is an MIT-licensed MCP server that gives AI agents persistent memory with a hard partition between grounded and simulated content, contamination auditing, evidence-based promotion, and an append-only, origin-tagged ledger. 268 tools across 26 domains. Self-hosted. Zero lock-in.

**Subhead, short**

> Persistent memory for AI agents — with the audit trail that regulated teams need. Grounded vs simulated, enforced in the architecture.

---

## 3. README install block (paste-ready)

````markdown
## Quick Start

mem20 installs from source. It is **not yet published to PyPI**.

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git
cd mem20

# Create venv and install core deps
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run the server (stdio)
MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py
```

`pip install mem20` is not a valid install path today — the package is not on
PyPI. Use the clone command above.
````

### 3.1 Install as a package (console script)

```bash
pip install .        # builds the wheel and installs the `mem20-mcp` command
mem20-mcp            # starts the MCP server + the :8080 health endpoint
```

`mem20-mcp` is a thin launcher (`launcher.py`) that locates the bundled `mcp/` directory and runs it as a script — so `from mcp.server import Server` resolves to the upstream MCP SDK and is never shadowed by the repo's local `mcp/` directory.

### 3.2 Always-on install (systemd)

```bash
git clone https://github.com/bythewayz66-glitch/mem20.git /opt/mem20
sudo /opt/mem20/install.sh --user $USER --dir /opt/mem20

curl http://localhost:8080/health
curl http://localhost:8080/metrics
```

`install.sh` creates the venv, installs `requirements.txt`, generates `/etc/systemd/system/mem20.service` from `systemd/mem20.service.template`, and enables and starts it. `--no-systemd` runs it manually instead.

### 3.3 Other channels

```bash
# Docker
docker build -t mem20 .
docker run -p 8080:8080 -e MEM20_HEALTH_PORT=8080 -v mem20-store:/data mem20

# apt (.deb)
make deb
sudo dpkg -i packaging/deb/mem20_*.deb
mem20-health
```

### 3.4 Register with an MCP client

```bash
claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py
```

```json
{
  "mcpServers": {
    "mem20": {
      "command": "python3",
      "args": ["/path/to/mem20/mcp/mcp_server.py"],
      "env": { "MEM20_STORE_PATH": "/path/to/store" }
    }
  }
}
```

> Requires Python 3.10+ per `pyproject.toml` (`requires-python = ">=3.10"`); the repo's installation guide recommends 3.11+. An API key for an OpenAI-compatible chat-completions endpoint is needed for the cognitive tools only — the memory core runs without one.

---

## 4. Show HN post

**Title (74 characters)**

```
Show HN: mem20 – Auditable memory for AI agents (grounded vs simulated)
```

Alt titles:

```
Show HN: mem20 – Agent memory with contamination auditing and a provenance ledger
Show HN: mem20 – MIT agent-memory server that keeps provenance as its invariant
```

**Body (paste verbatim)**

```
Hi HN — I'm launching mem20, an MCP server that gives AI agents persistent
memory with an audit trail.

The problem I kept hitting: every memory layer competes on retrieval quality,
and none of them let you *prove* what the agent knows. In a regulated context
that's the whole ballgame — you don't need "probably relevant", you need
"here is where this came from and here is the evidence it was allowed in."

What mem20 is:

- An MCP server (JSON-RPC 2.0 over stdio), Python, MIT licensed.
- 268 tools across 26 domains.
- A HARD partition between grounded memory (came from a real source) and
  simulated memory (the agent generated it). These are not the same store with
  a flag — they are separate classes, enforced at the storage layer: the vector
  and BM25 indexes assert grounded-only on write, and a simulated record
  reaching either one raises immediately.
- Contamination auditing, so you can detect when simulated content has bled
  into grounded memory.
- Evidence-based promotion: content moves from simulated to grounded only with
  prediction_error_evidence attached — a linked prior prediction resolved in
  its favour, or a registered external verifier. Not by asserting it.
- An append-only, origin-tagged ledger — every entry carries its origin (user /
  tool / simulated) and store (memory / imaginated), validated at the append
  path.

Self-reported benchmarks on our own harness:
  hit rate  — 1.000 direct | 0.800 multi-hop | 0.000 adversarial
  leak rate — 0.000 on clean stores

I want to be straight about those numbers. The 0.000 adversarial hit rate is a
real weakness, not a marketing smudge: hard adversarial queries defeat the
retrieval path today, and it's on the roadmap. They're self-reported and not
independently audited. And we do not have a published LoCoMo/LongMemEval
comparable to Mem0 or Zep — so I'm not claiming one.

The other honest caveat: the promotion gate is only as strong as its
attestation, and that attestation is currently self-reported rather than
cryptographically enforced. So the accurate claim is "evidence-based promotion
with an append-only audit trail", not tamper-proof.

Why MIT and self-hosted matters here: if your memory layer is the thing you
must audit, you can't audit someone else's black box. Run it on your own
infrastructure, read the code, no lock-in.

Repo: https://github.com/bythewayz66-glitch/mem20

Install (not on PyPI yet — install from source):
  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py

There's also a systemd installer (./install.sh), a Dockerfile, and a .deb
target if you want it always-on with /health and /metrics on :8080.

Happy to answer anything — especially the adversarial hit rate and where the
promotion gate needs hardening. That's the stuff I'd ask about too.
```

**Comment strategy.** Lead with the 0.000 adversarial weakness if it is not already the top comment — owning it first beats defending it. State that benchmarks are self-reported on our harness. For "why not Mem0/Zep?", give the category answer: they optimise retrieval, mem20 optimises provenance; do not disparage their numbers. For "is this a vector DB with a flag?", point at the three enforcement sites. For the 293 `mem20*z` packages, be accurate: it is a monorepo and the sitemap records 632 of 875 registered capabilities `ok`, 142 `unpackaged`, 101 `degraded`.

---

## 5. Product Hunt post

**Tagline (57 characters)**

```
Auditable memory for AI agents — grounded vs simulated
```

**Description**

```
mem20 gives AI agents persistent memory you can actually prove. A hard partition
separates grounded memory from simulated content, contamination auditing catches
bleed between them, and an append-only origin-tagged ledger records where every
memory came from. MIT-licensed MCP server, Python, self-hosted — 268 tools
across 26 domains. Built for teams who need "here's the evidence," not
"probably relevant."
```

**Maker's first comment**

```
Maker here. Every agent-memory tool on the market competes on retrieval quality.
We built mem20 around a different question: can you *prove* what your agent
knows? That's the grounded/simulated partition plus the audit ledger. It's MIT
and self-hosted because you can't audit a black box.

How the partition actually works: it isn't a boolean flag on one store. The
vector and BM25 indexes assert grounded-only on write, so a simulated record
reaching either one raises immediately; the ledger validates origin/store tags
at its lowest append path; and promotion out of the simulated partition
requires prediction_error_evidence attached to the promotion.

Honest caveats, up front:
- Our adversarial hit rate is 0.000 today. That's a known weakness — hard
  adversarial queries defeat the retrieval path. We'd rather tell you than have
  you find it.
- The benchmarks are self-reported on our own harness, not independently audited.
- We don't publish a LoCoMo/LongMemEval comparable to Mem0 or Zep, so we don't
  claim one.
- Promotion is evidence-based with an append-only audit trail; it is not
  tamper-proof, because the evidence attestation is self-reported rather than
  cryptographically enforced.

Install from source today (not on PyPI yet):
  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py
```

**Topic tags.** `Developer Tools` · `Artificial Intelligence` · `Open Source` · `Privacy` · `Software Engineering`

---

## 6. Social copy

### 6.1 X / Twitter — single post (263 characters)

```
Most agent memory competes on retrieval quality.

mem20 competes on proof.

Hard grounded/simulated partition. Contamination auditing. Evidence-based
promotion. Append-only origin ledger.

MIT. Self-hosted. 268 tools over MCP.
https://github.com/bythewayz66-glitch/mem20
```

### 6.2 X / Twitter — thread (6 posts)

**1/**
```
Agent memory has a trust problem nobody's selling a fix for.

Every tool answers "what's relevant?" None answer "can you prove what this
agent knows?"

We built mem20 for the second question. 🧵
```

**2/**
```
The core idea: a HARD partition between grounded memory (real source) and
simulated memory (agent-generated).

Not a flag on one store. Two classes, enforced on write — the vector and BM25
indexes reject simulated records outright.

"The agent made this up" becomes structurally visible.
```

**3/**
```
Around that: contamination auditing (catch simulated content bleeding into
grounded), evidence-based promotion (nothing graduates without
prediction_error_evidence attached), and an append-only origin-tagged ledger.

Every memory carries its origin. History can't be quietly rewritten.
```

**4/**
```
Why MIT + self-hosted: you can't audit a black box. If your memory layer is the
thing under audit, run it yourself.

Python, MCP-native (JSON-RPC 2.0 over stdio), 268 tools across 26 domains.
Installs with a clone, a venv and requirements.txt.
```

**5/**
```
Straight talk: our adversarial hit rate is 0.000 today. Real weakness, not a
footnote. Benchmarks are self-reported on our harness and not independently
audited.

We also don't have a published LoCoMo/LongMemEval comparable to Mem0 or Zep —
so we're not claiming one. And promotion is evidence-based, not tamper-proof.
```

**6/**
```
The wedge is auditability, and it's genuinely unoccupied. If you're building
production agents in a regulated context and "probably relevant" isn't good
enough:

https://github.com/bythewayz66-glitch/mem20
```

### 6.3 LinkedIn — regulated / enterprise angle

```
Most agent-memory systems answer "what is relevant?"

Regulated AI teams have to answer a harder question: "what does this agent
actually know, and can you show me where it learned it?"

mem20 is persistent memory for AI agents built around that second question:

— A hard partition between grounded memory and simulated content, enforced at
  the storage layer rather than by convention
— Contamination auditing to catch simulated content leaking into grounded stores
— Evidence-based promotion — nothing becomes "known" without evidence attached
— An append-only, origin-tagged ledger for every memory
— MIT licensed, Python, self-hosted — no lock-in, no black box

268 tools across 26 domains, delivered over MCP (JSON-RPC 2.0 over stdio).

It's not a retrieval-quality race. It's a trust and provenance race.

To be precise about the claim: this is evidence-based promotion with an
append-only audit trail — not tamper-proof. The promotion gate's attestation is
self-reported today, and we say so.

github.com/bythewayz66-glitch/mem20

#AgenticAI #AIGovernance #MLOps #AIInfrastructure #Auditability
```

### 6.4 Reddit — r/LocalLLaMA

**Title:** `mem20 – MIT, self-hosted agent memory with a grounded/simulated partition (auditable, no black box)`

```
I've been frustrated that most agent-memory tooling is a black box you can't
self-host end to end. mem20 is an MIT-licensed Python MCP server you run in your
own VPC: JSON-RPC 2.0 over stdio, 268 tools across 26 domains.

The interesting architectural bit is a HARD partition between grounded memory
(real source) and simulated memory (agent-generated) — two classes, not a flag.
The vector and BM25 indexes assert grounded-only on write, so simulated records
can't reach them; the ledger validates origin/store tags at the append path.

Honest limits: adversarial hit rate is 0.000 today (real weakness, on the
roadmap), the benchmarks are self-reported on our own harness rather than
independently audited, and there's no published LoCoMo/LongMemEval comparable to
Mem0/Zep, so I'm not claiming one. Promotion is evidence-based, not tamper-proof.

Install is from source right now (not on PyPI):

  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20 && python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  MEM20_STORE_PATH=~/.mem20/store .venv/bin/python mcp/mcp_server.py

Repo: https://github.com/bythewayz66-glitch/mem20
Happy to hear where this breaks — especially the promotion gate.
```

### 6.5 Reddit — r/MachineLearning

**Title:** `[P] mem20: an agent memory substrate with provenance as the primary invariant (MIT, MCP)`

```
Most memory systems for LLM agents optimise retrieval. mem20 inverts the design
goal: the primary invariant is provenance.

- Grounded and simulated memory are distinct classes, enforced at the write path
  (_assert_grounded() on both the vector and BM25 index writers).
- The ledger is append-only and origin/store tagged, validated by
  _validate_partition_tags() at the lowest append.
- Promotion between partitions requires prediction_error_evidence — a linked
  prior prediction resolved in the item's favour, or a registered external
  verifier.

Self-reported benchmarks on our own harness: hit rate 1.000 direct / 0.800
multi-hop / 0.000 adversarial; leak rate 0.000 on clean stores. The adversarial
0.000 is disclosed as a known limitation — hard adversarial queries defeat the
retrieval path today. These are not independently audited and there is no
reproduction script in the repo, so treat them as vendor-reported.

We have no LoCoMo/LongMemEval result comparable to Mem0 or Zep and don't claim
one. Would value critique on the promotion gate, which currently relies on
self-attestation rather than cryptographic enforcement.

Repo: https://github.com/bythewayz66-glitch/mem20
```

### 6.6 Reddit — r/LangChain

**Title:** `mem20 — MCP-native agent memory (268 tools, grounded/simulated partition)`

```
For anyone wiring memory into LangGraph / CrewAI / Pydantic AI: mem20 is an MCP
server (JSON-RPC 2.0 over stdio) that adds persistent memory with an audit trail
— a hard grounded/simulated partition, contamination auditing, evidence-based
promotion, and an append-only origin-tagged ledger. 268 tools across 26 domains,
MIT, Python.

Because it speaks MCP, it registers like any other stdio server:

  claude mcp add mem20 -- python3 /path/to/mem20/mcp/mcp_server.py

Install from source for now (not on PyPI yet):

  git clone https://github.com/bythewayz66-glitch/mem20.git
  cd mem20 && python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt

Repo: https://github.com/bythewayz66-glitch/mem20
```

---

## 7. Value propositions

**Short form (3 bullets — landing page, PH gallery)**

- **Prove it, don't just retrieve it.** A hard grounded/simulated partition plus an append-only origin-tagged ledger tells you where every memory came from.
- **Catch contamination before it ships.** Auditing detects simulated content bleeding into grounded memory — `contamination_rate` 0.0 on a clean store, checkable on demand.
- **Own your memory layer.** MIT licensed, Python, self-hosted. No lock-in, no black box, no vendor holding your audit trail.

**Long form (6 bullets — README, deep-dive posts)**

1. **Hard grounded/simulated partition, enforced on write.** Not a boolean flag on one store — the vector and BM25 index writers assert grounded-only and raise on a simulated record.
2. **Contamination auditing.** `memory_audit_contamination()` inspects the grounded store and the BM25 corpus and returns `contamination_rate`, `violations`, and `violations_simulated_in_bm25_corpus`.
3. **Evidence-based promotion.** `promote_simulated_to_grounded()` requires `prediction_error_evidence` — a resolved prior prediction or a registered external verifier.
4. **Append-only, origin-tagged ledger.** Every entry carries `origin` and `store`, validated at the lowest append path. History is appended, not rewritten.
5. **MCP-native and broad.** JSON-RPC 2.0 over stdio, 268 tools across 26 domains — registers with any MCP host, including Claude Code, Cursor and Hermes.
6. **MIT, self-hosted, Python.** Audit the code you depend on. Run it in your own VPC.

---

## 8. Claim ledger — every number, with its source

| Claim in copy | Value | Source / status |
|---|---|---|
| Tools / domains | **268 tools, 26 domains** | House number; corroborated by README "Tool domains (26)" counted from the live server |
| License / language | MIT · Python | GitHub API, verified this run |
| Product version | `2.1.0rc2` | `pyproject.toml` on `main` |
| Install path | clone + `pip install -r requirements.txt` | `requirements.txt`, `install.sh`, README, `docs/03-installation.md` |
| Run path | `mcp/mcp_server.py`; console script `mem20-mcp` | README, `pyproject.toml` `[project.scripts]` |
| SDK dependency | `mcp>=2.1.1` | `requirements.txt`, `pyproject.toml` |
| Transport | JSON-RPC 2.0 over stdio; health on `:8080` | README "Transport / protocol" |
| Python floor | `>=3.10` (`pyproject.toml`); 3.11+ recommended (installation guide) | `pyproject.toml`, `docs/03-installation.md` |
| Hit rate | 1.000 direct · 0.800 multi-hop · 0.000 adversarial | Self-reported, internal harness — **not independently audited** |
| Leak rate | 0.000 on clean stores | Self-reported; checkable via `memory_audit_contamination()` |
| Monorepo subsystems | 293 `mem20*z` packages | README "Repository layout" |
| Capability health | 632 of 875 `ok` · 142 `unpackaged` · 101 `degraded` | README, per the repo sitemap |
| Market sizing | TAM $1.28B · SAM $282M · SOM $1.68M · blended ACV $14,000 | Program brief (house numbers) |
| PyPI status | 404 | `pypi.org/pypi/mem20/json`, verified this run |

**Rule for downstream assets:** if it is not in this table, it does not go in the asset.

---

## 9. Guardrails — do not overclaim

1. **No LoCoMo/LongMemEval claim.** mem20 has no published benchmark comparable to Mem0 or Zep. Never imply parity; never cite their numbers as ours.
2. **Adversarial hit rate 0.000 must be disclosed** in any asset that shows the benchmark table. Frame it as a known weakness with a roadmap entry — never omit it from the HN post or the maker comment.
3. **Evidence-based promotion, not tamper-proof.** Describe promotion as *evidence-based with an append-only audit trail*. Use "auditable", never "unfakeable".
4. **Benchmarks are self-reported.** Label them as measured on our own internal harness and not independently audited. Do not imply independent validation, and do not present a reproduction script that does not exist.
5. **No stale references.** No retired repo path; no bare `pip install mem20`; no `mcp<2` pin; no non-existent module path.
6. **No competitor disparagement.** Compare positions, not their numbers.

**Banned phrasings:** "provably secure", "tamper-proof memory", "matches Mem0", "beats Zep", "industry-leading retrieval", any unqualified superlative.

---

## 10. Open blockers — not copy problems

| Blocker | Status | Owner |
|---|---|---|
| `pip install mem20` → PyPI 404 | OPEN — source install published instead | GitHub Repo Assistant / release owner |
| Launch page 403 to anonymous visitors | OPEN — blocks external launch traffic | Webpage Developer / hosting |
| `mem20.jaysonai.online` did not respond this run, yet is the Website badge target in the canonical README | OPEN — repo defect | GitHub Repo Assistant |
| Publish through gabe on Sidney | Not completed from this sandbox — see publish report | Orchestrator / Server Builder |

Do not describe the launch as unblocked while the first three rows are open.

---

## 11. Next actions

1. **GitHub Repo Assistant:** re-point the canonical README's Website badge (currently `mem20.jaysonai.online`, which did not respond) and confirm the LICENSE/Releases badges resolve to the canonical repo.
2. **Webpage Developer:** apply the ten string replacements in `landing-page-copy-update.md` and resolve the anonymous-403 on the launch page.
3. **Release owner:** cut the PyPI release; when `pypi.org/pypi/mem20/json` returns 200, swap the install block for `pip install mem20` in all seven assets.
4. **Orchestrator:** hand the Sidney publish bundle to a lane with a working gabe credential.
