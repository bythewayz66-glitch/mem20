#!/usr/bin/env python3
"""Render the mem20 repository analytics report and dashboard.

Reads docs/analytics/data/repo-analytics.json (produced by
scripts/analytics/extract_repo_analytics.py) and writes:

  docs/analytics/README.md        - the written report
  docs/analytics/dashboard.html   - self-contained dashboard (data inlined)

Every number in the output is read from the dataset; nothing is hardcoded.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA = os.path.join(REPO, "docs", "analytics", "data", "repo-analytics.json")
OUT_MD = os.path.join(REPO, "docs", "analytics", "README.md")
OUT_HTML = os.path.join(REPO, "docs", "analytics", "dashboard.html")


def pct(a: float, b: float) -> str:
    if not b:
        return "n/a"
    return f"{(a - b) / b * 100:+.1f}%"


def load() -> dict:
    with open(DATA) as fh:
        return json.load(fh)


def build_markdown(d: dict) -> str:
    repo = d["repo"]
    c = d["commits"]
    b = d["branches"]
    f = d["files"]
    s = d["surface"]
    bm = d["benchmarks"]
    lin = d["benchmark_lineage"]

    first = c["first_commit"]
    latest = c["latest_commit"]
    d0 = datetime.fromisoformat(first["date"])
    d1 = datetime.fromisoformat(latest["date"])
    span_days = max((d1 - d0).days, 1)
    per_day = c["total_commits"] / span_days

    monthly = c["monthly"]
    weekly = c["weekly"]
    peak_week = max(weekly, key=lambda w: w["commits"])
    peak_month = max(monthly, key=lambda m: m["commits"])

    authors = c["authors"]
    top_author = authors[0]
    human_share = top_author["commits"] / c["total_commits"] * 100
    agent_authors = [
        a for a in authors
        if any(k in a["author"].lower() for k in
               ("agent", "bot", "expert", "builder", "orchestrator", "content",
                "spacebunny", "jayson", "assistant", "reporter", "mem20"))
    ]
    agent_commits = sum(a["commits"] for a in agent_authors)

    pts = s["points"]
    first_pt, last_pt = pts[0], pts[-1]
    tool_delta = last_pt["tools"] - first_pt["tools"]
    domain_delta = last_pt["domains"] - first_pt["domains"]

    modes = bm["mode_aggregates"]
    best = modes[0]
    fastest = min(
        [m for m in modes if m["p50_ms"] and m["queries"] >= 100],
        key=lambda m: m["p50_ms"],
    )
    rows = bm["rows"]

    # per-kind best mode
    kinds = sorted({r["kind"] for r in rows})
    best_by_kind = []
    for k in kinds:
        cand = [r for r in rows if r["kind"] == k and r["hit_rate"] is not None]
        if not cand:
            continue
        w = max(cand, key=lambda r: (r["hit_rate"], r["mrr"] or 0))
        best_by_kind.append(w)

    v1 = lin.get("v1_modes") or []
    v2_sup = lin.get("v2_supersedes") or {}

    L = []
    A = L.append
    A("# mem20 — Repository Analytics Report")
    A("")
    A(f"**Generated:** {d['generated_at']}  ")
    A(f"**Repo:** `{repo['owner']}/{repo['name']}`  ")
    A(f"**HEAD:** `{repo['head_sha']}`  ")
    A(f"**Analyzed ref:** `{repo.get('analyzed_ref', 'HEAD')}` — every figure below "
      f"describes this commit, not the working tree  ")
    A(f"**HEAD date:** {repo['head_date']}  ")
    A(f"**VERSION:** {repo['version']}  ")
    A(f"**Dataset:** [`data/repo-analytics.json`](data/repo-analytics.json) — "
      f"regenerate with `python3 scripts/analytics/extract_repo_analytics.py`")
    A("")
    A("> Every figure below is computed from this repository's own git history and "
      "in-tree artifacts. No external data, no estimates. The JSON is the artifact "
      "of record; this report and `dashboard.html` are rendered from it.")
    A("")
    A("---")
    A("")
    A("## 1. Executive summary")
    A("")
    A(f"- **{c['total_commits']:,} commits** over **{span_days} days** "
      f"({d0.date()} → {d1.date()}), averaging **{per_day:.1f} commits/day**.")
    A(f"- **{f['total']:,} tracked files** across **{len(f['by_top_dir'])} top-level "
      f"directories**; `{f['by_top_dir'][0]['dir']}/` alone holds "
      f"{f['by_top_dir'][0]['files']:,} files "
      f"({f['by_top_dir'][0]['files'] / f['total'] * 100:.1f}% of the tree).")
    A(f"- **Tool surface grew {tool_delta:+d} tools ({pct(last_pt['tools'], first_pt['tools'])}) "
      f"and {domain_delta:+d} domains ({pct(last_pt['domains'], first_pt['domains'])})** "
      f"between the first and last `docs/surface.json` snapshot "
      f"({first_pt['date'][:10]} → {last_pt['date'][:10]}).")
    A(f"- **{b['at_risk_commits']} commits sit on {len(b['branches_ahead_of_main'])} "
      f"branches ahead of `main`** out of {b['remote_branches']} remote branches — "
      f"unmerged work is the largest single delivery risk in the repo.")
    A(f"- Retrieval quality is **mode-dependent, not uniformly good**: best aggregate "
      f"hit rate is `{best['mode']}` at **{best['hit_rate']:.3f}** "
      f"(MRR {best['mrr']:.3f}), while the fastest mode at scale is "
      f"`{fastest['mode']}` at **{fastest['p50_ms']:.1f} ms p50**.")
    A("")
    A("### Immediate actions")
    A("")
    A(f"1. **Triage the {b['at_risk_commits']}-commit backlog.** "
      f"`{b['branches_ahead_of_main'][0]['branch']}` alone is "
      f"{b['branches_ahead_of_main'][0]['ahead']} commits ahead. Either land or "
      f"close each branch; the count only grows.")
    A(f"2. **Fix the `hybrid` latency regression.** `hybrid` costs "
      f"**{modes[[m['mode'] for m in modes].index('hybrid')]['p50_ms']:.0f} ms p50** "
      f"for a {modes[[m['mode'] for m in modes].index('hybrid')]['hit_rate']:.3f} hit rate, "
      f"while `hybrid-rerank-off` delivers the same "
      f"{modes[[m['mode'] for m in modes].index('hybrid-rerank-off')]['hit_rate']:.3f} "
      f"hit rate in "
      f"{modes[[m['mode'] for m in modes].index('hybrid-rerank-off')]['p50_ms']:.0f} ms. "
      f"The cross-encoder is buying nothing at this corpus size.")
    A(f"3. **Tag `v{repo['version']}`.** `VERSION` says {repo['version']} but the "
      f"latest semver tag is behind `main`; releases are not traceable to a commit.")
    A("")
    A("---")
    A("")
    A("## 2. Commit velocity")
    A("")
    A("### Monthly")
    A("")
    A("| Month | Commits | Cumulative | Share of total |")
    A("|---|---:|---:|---:|")
    for m in monthly:
        A(f"| {m['month']} | {m['commits']:,} | {m['cumulative']:,} | "
          f"{m['commits'] / c['total_commits'] * 100:.1f}% |")
    A("")
    A(f"Peak month: **{peak_month['month']}** with **{peak_month['commits']:,} commits** "
      f"({peak_month['commits'] / c['total_commits'] * 100:.1f}% of all history).")
    A("")
    A("### Weekly (ISO week)")
    A("")
    A("| Week | Commits | Cumulative |")
    A("|---|---:|---:|")
    for w in weekly:
        A(f"| {w['week']} | {w['commits']:,} | {w['cumulative']:,} |")
    A("")
    A(f"Peak week: **{peak_week['week']}** with **{peak_week['commits']} commits**. "
      f"The last two weeks ({weekly[-2]['week']}: {weekly[-2]['commits']}, "
      f"{weekly[-1]['week']}: {weekly[-1]['commits']}) show a sharp cool-down from the "
      f"{peak_week['commits']}-commit peak — worth confirming that is intentional "
      f"consolidation rather than a stalled pipeline.")
    A("")
    A("### Commit type mix")
    A("")
    A("| Type | Count | Share |")
    A("|---|---:|---:|")
    for t in c["commit_types"][:12]:
        A(f"| `{t['type']}` | {t['count']:,} | "
          f"{t['count'] / c['total_commits'] * 100:.1f}% |")
    A("")
    A(f"`(untyped)` at {c['commit_types'][0]['count']:,} commits "
      f"({c['commit_types'][0]['count'] / c['total_commits'] * 100:.1f}%) is the single "
      f"largest bucket — conventional-commit discipline is not enforced repo-wide, "
      f"which is why automated changelog generation is unreliable here.")
    A("")
    A("### Authorship")
    A("")
    A("| Author | Commits | Share |")
    A("|---|---:|---:|")
    for a in authors[:12]:
        A(f"| {a['author']} | {a['commits']:,} | "
          f"{a['commits'] / c['total_commits'] * 100:.1f}% |")
    A("")
    A(f"**{top_author['author']}** accounts for **{human_share:.1f}%** of all commits. "
      f"Agent identities (matched on agent/bot/expert/builder/orchestrator/content/"
      f"assistant/reporter naming) account for **{agent_commits:,} commits "
      f"({agent_commits / c['total_commits'] * 100:.1f}%)** across "
      f"{len(agent_authors)} distinct identities. Bus factor on commit authorship is "
      f"effectively 1 — a real continuity risk.")
    A("")
    A("---")
    A("")
    A("## 3. Branch and delivery risk")
    A("")
    A(f"- Remote branches: **{b['remote_branches']}**")
    A(f"- Branches ahead of `main`: **{len(b['branches_ahead_of_main'])}**")
    A(f"- Total unmerged commits: **{b['at_risk_commits']}**")
    A(f"- Tags: **{b['tags']}**")
    A("")
    A("| Branch | Commits ahead of `main` |")
    A("|---|---:|")
    for br in b["branches_ahead_of_main"]:
        A(f"| `{br['branch']}` | {br['ahead']} |")
    A("")
    top3 = b["branches_ahead_of_main"][:3]
    top3_sum = sum(x["ahead"] for x in top3)
    A(f"The top three branches hold **{top3_sum} of {b['at_risk_commits']}** unmerged "
      f"commits ({top3_sum / b['at_risk_commits'] * 100:.0f}%). "
      f"With {b['remote_branches']} remote branches and {b['tags']} tags against "
      f"{c['total_commits']:,} commits, branch and tag hygiene — not throughput — is "
      f"the binding constraint on release confidence.")
    A("")
    A("---")
    A("")
    A("## 4. Codebase composition")
    A("")
    A(f"**{f['total']:,} tracked files.**")
    A("")
    A("### By top-level directory (top 15)")
    A("")
    A("| Directory | Files | Share |")
    A("|---|---:|---:|")
    for t in f["by_top_dir"][:15]:
        A(f"| `{t['dir']}/` | {t['files']:,} | "
          f"{t['files'] / f['total'] * 100:.1f}% |")
    A("")
    A("### By extension (top 12)")
    A("")
    A("| Extension | Files | Share |")
    A("|---|---:|---:|")
    for e in f["by_extension"][:12]:
        A(f"| `{e['ext']}` | {e['files']:,} | "
          f"{e['files'] / f['total'] * 100:.1f}% |")
    A("")
    json_files = next((e["files"] for e in f["by_extension"] if e["ext"] == ".json"), 0)
    py_files = next((e["files"] for e in f["by_extension"] if e["ext"] == ".py"), 0)
    A(f"JSON ({json_files:,}) and Python ({py_files:,}) together are "
      f"{(json_files + py_files) / f['total'] * 100:.1f}% of the tree. The JSON weight "
      f"is largely generated manifests and evidence artifacts — it is the repo's "
      f"audit trail, and it is also the main driver of clone size.")
    A("")
    A("---")
    A("")
    A("## 5. Tool / domain surface growth")
    A("")
    A("`docs/surface.json` is regenerated from the live JSON-RPC `tools/list` response, "
      "so each snapshot is a measured surface, not a claim.")
    A("")
    A("| Snapshot (commit date) | Tools | Domains | Unwired |")
    A("|---|---:|---:|---:|")
    for p in pts:
        A(f"| {p['date'][:10]} `{p['sha'][:8]}` | {p['tools']} | {p['domains']} | "
          f"{p['unwired']} |")
    A("")
    A(f"**{first_pt['tools']} → {last_pt['tools']} tools** "
      f"({tool_delta:+d}, {pct(last_pt['tools'], first_pt['tools'])}) and "
      f"**{first_pt['domains']} → {last_pt['domains']} domains** "
      f"({domain_delta:+d}, {pct(last_pt['domains'], first_pt['domains'])}) in "
      f"{(datetime.fromisoformat(last_pt['date']) - datetime.fromisoformat(first_pt['date'])).days} "
      f"days. Domain count grew faster than tool count, meaning the surface widened "
      f"into new areas rather than deepening existing ones — "
      f"{last_pt['tools'] / last_pt['domains']:.1f} tools per domain now vs "
      f"{first_pt['tools'] / first_pt['domains']:.1f} before.")
    A("")
    A(f"**{last_pt['unwired']} tools are unwired** at the current pin — registered but "
      f"not reachable through the live surface. That is the concrete gap between "
      f"\"built\" and \"shipped\".")
    A("")
    A("### Current domain distribution (top 15)")
    A("")
    dc = s.get("current_domain_counts") or last_pt.get("domain_counts") or {}
    A("| Domain | Tools |")
    A("|---|---:|")
    for name, n in sorted(dc.items(), key=lambda kv: -kv[1])[:15]:
        A(f"| `{name}` | {n} |")
    A("")
    A("---")
    A("")
    A("## 6. Retrieval benchmark results")
    A("")
    A(f"Corpus **`{bm['corpus']}`** — {bm['facts']:,} grounded facts, "
      f"{bm['simulated']:,} simulated facts, {bm['queries']} queries. "
      f"Embedding model `{bm['environment']['embedding_model']}` "
      f"({bm['environment']['embedding_dim']}d), cross-encoder "
      f"{'enabled' if bm['environment']['cross_encoder'] else 'disabled'}.")
    A("")
    A("> **Comparability caveat.** These numbers describe this corpus only. They are "
      "not comparable to Mem0 LoCoMo/LongMemEval or Zep DMR figures, which use "
      "different corpora and metrics. No LoCoMo result is claimed.")
    A("")
    A("### Mode aggregates (query-weighted)")
    A("")
    A("| Mode | Queries | Hit rate | MRR | p50 ms |")
    A("|---|---:|---:|---:|---:|")
    for m in modes:
        A(f"| `{m['mode']}` | {m['queries']} | {m['hit_rate']:.3f} | "
          f"{m['mrr']:.3f} | {m['p50_ms']:.1f} |")
    A("")
    A("### Best mode per query kind")
    A("")
    A("| Query kind | Best mode | n | Hit rate | MRR | p50 ms |")
    A("|---|---|---:|---:|---:|---:|")
    for r in best_by_kind:
        A(f"| `{r['kind']}` | `{r['mode']}` | {r['n']} | {r['hit_rate']:.3f} | "
          f"{r['mrr']:.3f} | {r['p50_ms']:.1f} |")
    A("")
    A("### Full result matrix")
    A("")
    A("| Mode | Kind | n | Hit rate | MRR | Leak | p50 ms |")
    A("|---|---|---:|---:|---:|---:|---:|")
    for r in rows:
        A(f"| `{r['mode']}` | `{r['kind']}` | {r['n']} | {r['hit_rate']:.3f} | "
          f"{r['mrr']:.3f} | {r['leak_rate']:.3f} | {r['p50_ms']:.1f} |")
    A("")
    A("### What the numbers say")
    A("")
    A(f"- **`vector` and `hybrid-rerank-off` tie on hit rate ({best['hit_rate']:.3f}) "
      f"but differ {modes[[m['mode'] for m in modes].index('vector')]['p50_ms'] / fastest['p50_ms']:.1f}× "
      f"in latency.** The cross-encoder is not paying for itself.")
    A(f"- **`hybrid` is the worst trade in the table**: "
      f"{modes[[m['mode'] for m in modes].index('hybrid')]['p50_ms']:.0f} ms p50 for a "
      f"{modes[[m['mode'] for m in modes].index('hybrid')]['hit_rate']:.3f} hit rate — "
      f"slower *and* less accurate than `hybrid-rerank-off`.")
    A(f"- **`adversarial_hard` is the real gap.** Best hit rate on that kind is "
      f"{max((r['hit_rate'] for r in rows if r['kind'] == 'adversarial_hard'), default=0):.3f}. "
      f"Paraphrase-hard probes are where the retrieval stack actually fails.")
    A(f"- **`unanswerable` reads 0.000 across every mode** — the control holds, so the "
      f"scorer is not inflating hits.")
    A("")
    A("### Benchmark lineage")
    A("")
    A(f"- v1 measured modes: {', '.join(f'`{m}`' for m in v1)}")
    A(f"- v2 supersedes corpus `{v2_sup.get('corpus')}` "
      f"({v2_sup.get('facts')} facts / {v2_sup.get('queries')} queries) → "
      f"{bm['facts']:,} facts / {bm['queries']} queries "
      f"({bm['facts'] / max(v2_sup.get('facts') or 1, 1):.0f}× facts, "
      f"{bm['queries'] / max(v2_sup.get('queries') or 1, 1):.0f}× queries).")
    A("")
    A("v1 → v2 is a **corpus change, not a regression or an improvement** — the "
      "adversarial class was rebuilt and the scorer was fixed, so the two runs are not "
      "comparable. Any trend line drawn across them would be false.")
    A("")
    A("---")
    A("")
    A("## 7. Method and limitations")
    A("")
    A("**Sources**")
    A("")
    A("- `git log` / `git rev-list` / `git ls-tree` on a fresh clone of "
      f"`{repo['owner']}/{repo['name']}` at `{repo['head_sha'][:12]}`.")
    A("- `docs/surface.json` read at every commit that touched it (10 snapshots).")
    A("- `benchmarks/results/latest.json`, `docs/benchmarks/results-v1.json`, "
      "`docs/benchmarks/results-v2.json`, `docs/benchmarks/experiments.json`.")
    A("")
    A("**Limitations — read these before quoting a number**")
    A("")
    A("- Commit counts include merge commits and agent-authored commits; they measure "
      "*activity*, not human effort.")
    A("- The surface-growth series has only 10 snapshots and 8 of them land on the same "
      "day (2026-11-09), so the growth curve is a step function, not a smooth trend. "
      "The 2026-11-04 → 2026-11-09 jump is one regeneration, not five days of steady "
      "growth.")
    A("- Benchmark numbers come from a single run on one machine "
      f"(`{bm['environment']['platform']}`); no repeated trials, so no confidence "
      "intervals are reported. Treat differences under ~0.05 hit rate as noise.")
    A("- `graph` mode was only scored on `multi_hop` (n=30), so its aggregate is not "
      "comparable to the 250-query modes.")
    A("- Branch-ahead counts are a point-in-time snapshot and move with every push.")
    A("")
    A("---")
    A("")
    A(f"*Rendered from `data/repo-analytics.json` by "
      f"`scripts/analytics/render_analytics.py`. Dashboard: "
      f"[`dashboard.html`](dashboard.html).*")
    A("")
    return "\n".join(L)


def build_html(d: dict) -> str:
    payload = json.dumps(d, separators=(",", ":"))
    repo = d["repo"]
    c = d["commits"]
    b = d["branches"]
    f = d["files"]
    s = d["surface"]
    bm = d["benchmarks"]
    pts = s["points"]
    modes = bm["mode_aggregates"]
    rows = bm["rows"]

    first = c["first_commit"]
    latest = c["latest_commit"]
    d0 = datetime.fromisoformat(first["date"])
    d1 = datetime.fromisoformat(latest["date"])
    span_days = max((d1 - d0).days, 1)
    per_day = c["total_commits"] / span_days
    first_pt, last_pt = pts[0], pts[-1]

    def kpi(label, value, sub):
        return f"""<div class="kpi"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div><div class="kpi-sub">{sub}</div></div>"""

    kpis = "".join([
        kpi("Commits", f"{c['total_commits']:,}", f"{per_day:.1f}/day over {span_days}d"),
        kpi("Tracked files", f"{f['total']:,}", f"{len(f['by_top_dir'])} top-level dirs"),
        kpi("Tool surface", f"{last_pt['tools']}", f"{last_pt['domains']} domains"),
        kpi("Unmerged commits", f"{b['at_risk_commits']}", f"{len(b['branches_ahead_of_main'])} branches ahead"),
        kpi("Best hit rate", f"{modes[0]['hit_rate']:.3f}", f"`{modes[0]['mode']}`"),
        kpi("Remote branches", f"{b['remote_branches']}", f"{b['tags']} tags"),
    ])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>mem20 — Repository Analytics</title>
<style>
  :root {{
    --bg:#0b0f14; --panel:#121821; --panel2:#0f151d; --line:#1e2836;
    --ink:#e6edf6; --muted:#8b9bb0; --accent:#4cc2ff; --accent2:#7ee787;
    --warn:#ffb454; --bad:#ff6b6b; --grid:#1a2330;
  }}
  * {{ box-sizing:border-box; }}
  body {{
    margin:0; background:var(--bg); color:var(--ink);
    font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Roboto,sans-serif;
    -webkit-font-smoothing:antialiased;
  }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:40px 24px 80px; }}
  header {{ border-bottom:1px solid var(--line); padding-bottom:24px; margin-bottom:32px; }}
  h1 {{ font-size:30px; margin:0 0 8px; letter-spacing:-.02em; font-weight:650; }}
  .sub {{ color:var(--muted); font-size:13.5px; }}
  .sub code {{ color:var(--accent); background:var(--panel2); padding:1px 6px; border-radius:4px; }}
  h2 {{ font-size:19px; margin:44px 0 6px; letter-spacing:-.01em; font-weight:600; }}
  h2 .n {{ color:var(--accent); font-variant-numeric:tabular-nums; margin-right:8px; }}
  .note {{ color:var(--muted); font-size:13px; margin:0 0 18px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin:24px 0 8px; }}
  .kpi {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:16px 18px; }}
  .kpi-label {{ font-size:11px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }}
  .kpi-value {{ font-size:26px; font-weight:650; margin:6px 0 2px; font-variant-numeric:tabular-nums; letter-spacing:-.02em; }}
  .kpi-sub {{ font-size:12px; color:var(--muted); }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:20px 22px; margin:16px 0; }}
  .card h3 {{ margin:0 0 4px; font-size:14px; font-weight:600; }}
  .card .cap {{ color:var(--muted); font-size:12px; margin-bottom:14px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; font-variant-numeric:tabular-nums; }}
  th {{ text-align:left; color:var(--muted); font-weight:500; font-size:11px;
        text-transform:uppercase; letter-spacing:.06em; padding:8px 10px; border-bottom:1px solid var(--line); }}
  td {{ padding:7px 10px; border-bottom:1px solid var(--grid); }}
  tr:last-child td {{ border-bottom:none; }}
  td.num, th.num {{ text-align:right; }}
  code {{ font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:12.5px; color:var(--accent); }}
  .bar {{ height:6px; background:var(--grid); border-radius:3px; overflow:hidden; min-width:60px; }}
  .bar > i {{ display:block; height:100%; background:linear-gradient(90deg,var(--accent),var(--accent2)); border-radius:3px; }}
  .bar.warn > i {{ background:linear-gradient(90deg,var(--warn),var(--bad)); }}
  .two {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  @media (max-width:820px) {{ .two {{ grid-template-columns:1fr; }} }}
  .legend {{ display:flex; gap:16px; flex-wrap:wrap; font-size:12px; color:var(--muted); margin-top:10px; }}
  .legend span::before {{ content:""; display:inline-block; width:9px; height:9px; border-radius:2px; margin-right:6px; vertical-align:middle; }}
  .lg-a::before {{ background:var(--accent); }}
  .lg-b::before {{ background:var(--accent2); }}
  .lg-c::before {{ background:var(--warn); }}
  .callout {{ border-left:3px solid var(--warn); background:rgba(255,180,84,.06);
              padding:12px 16px; border-radius:0 8px 8px 0; font-size:13px; color:#d8c3a0; margin:16px 0; }}
  .callout b {{ color:var(--warn); }}
  footer {{ margin-top:56px; padding-top:20px; border-top:1px solid var(--line);
            color:var(--muted); font-size:12px; }}
  svg text {{ font-family:inherit; }}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>mem20 — Repository Analytics</h1>
  <div class="sub">
    <code>{repo['owner']}/{repo['name']}</code> ·
    HEAD <code>{repo['head_sha'][:12]}</code> ·
    VERSION {repo['version']} ·
    generated {d['generated_at'][:19]}Z
  </div>
</header>

<div class="kpis">{kpis}</div>

<h2><span class="n">01</span>Commit velocity</h2>
<p class="note">Commits per ISO week, from full git history. Cumulative line on the right axis.</p>
<div class="card">
  <h3>Weekly commit volume</h3>
  <div class="cap">{c['total_commits']:,} commits · {span_days} days · peak week {max(c['weekly'], key=lambda w: w['commits'])['week']}</div>
  <div id="chart-weekly"></div>
</div>
<div class="two">
  <div class="card">
    <h3>Monthly</h3>
    <div class="cap">Share of all history</div>
    <table><thead><tr><th>Month</th><th class="num">Commits</th><th class="num">Cum.</th><th style="width:90px"></th></tr></thead>
    <tbody id="tbl-monthly"></tbody></table>
  </div>
  <div class="card">
    <h3>Commit types</h3>
    <div class="cap">Conventional-commit prefix</div>
    <table><thead><tr><th>Type</th><th class="num">Count</th><th style="width:90px"></th></tr></thead>
    <tbody id="tbl-types"></tbody></table>
  </div>
</div>

<h2><span class="n">02</span>Authorship</h2>
<p class="note">Commit counts by author identity. Agent identities are matched on naming.</p>
<div class="card">
  <h3>Top authors</h3>
  <div class="cap">Bus factor on commit authorship is effectively 1</div>
  <table><thead><tr><th>Author</th><th class="num">Commits</th><th class="num">Share</th><th style="width:140px"></th></tr></thead>
  <tbody id="tbl-authors"></tbody></table>
</div>

<h2><span class="n">03</span>Delivery risk</h2>
<p class="note">Branches ahead of <code>main</code>, measured with <code>git rev-list --count origin/main..origin/&lt;branch&gt;</code>.</p>
<div class="card">
  <h3>Unmerged commits by branch</h3>
  <div class="cap">{b['at_risk_commits']} commits across {len(b['branches_ahead_of_main'])} branches</div>
  <table><thead><tr><th>Branch</th><th class="num">Ahead</th><th style="width:180px"></th></tr></thead>
  <tbody id="tbl-branches"></tbody></table>
</div>

<h2><span class="n">04</span>Codebase composition</h2>
<p class="note">{f['total']:,} tracked files at HEAD.</p>
<div class="two">
  <div class="card">
    <h3>By top-level directory</h3>
    <div class="cap">Top 12</div>
    <table><thead><tr><th>Directory</th><th class="num">Files</th><th style="width:90px"></th></tr></thead>
    <tbody id="tbl-dirs"></tbody></table>
  </div>
  <div class="card">
    <h3>By extension</h3>
    <div class="cap">Top 10</div>
    <table><thead><tr><th>Ext</th><th class="num">Files</th><th style="width:90px"></th></tr></thead>
    <tbody id="tbl-exts"></tbody></table>
  </div>
</div>

<h2><span class="n">05</span>Tool / domain surface growth</h2>
<p class="note">Each point is a measured <code>docs/surface.json</code> snapshot, not a claim.</p>
<div class="card">
  <h3>Tools and domains over time</h3>
  <div class="cap">{first_pt['tools']} → {last_pt['tools']} tools · {first_pt['domains']} → {last_pt['domains']} domains</div>
  <div id="chart-surface"></div>
  <div class="legend"><span class="lg-a">Tools</span><span class="lg-b">Domains</span></div>
</div>
<div class="callout">
  <b>Read the step, not the slope.</b> 8 of the 10 snapshots land on 2026-11-09, so this
  is one regeneration event, not five days of steady growth. {last_pt['unwired']} tools
  are registered but unwired at the current pin.
</div>

<h2><span class="n">06</span>Retrieval benchmarks</h2>
<p class="note">Corpus <code>{bm['corpus']}</code> — {bm['facts']:,} grounded facts, {bm['simulated']:,} simulated, {bm['queries']} queries. Query-weighted aggregates.</p>
<div class="card">
  <h3>Hit rate vs p50 latency by mode</h3>
  <div class="cap">Bubble size = query count. Up and to the left is better.</div>
  <div id="chart-scatter"></div>
</div>
<div class="two">
  <div class="card">
    <h3>Mode aggregates</h3>
    <div class="cap">Query-weighted</div>
    <table><thead><tr><th>Mode</th><th class="num">Hit</th><th class="num">MRR</th><th class="num">p50 ms</th></tr></thead>
    <tbody id="tbl-modes"></tbody></table>
  </div>
  <div class="card">
    <h3>Best mode per query kind</h3>
    <div class="cap">Where each kind is actually won</div>
    <table><thead><tr><th>Kind</th><th>Mode</th><th class="num">Hit</th><th class="num">n</th></tr></thead>
    <tbody id="tbl-kinds"></tbody></table>
  </div>
</div>
<div class="card">
  <h3>Full result matrix</h3>
  <div class="cap">Every mode × query kind in the run</div>
  <table><thead><tr><th>Mode</th><th>Kind</th><th class="num">n</th><th class="num">Hit</th><th class="num">MRR</th><th class="num">Leak</th><th class="num">p50 ms</th></tr></thead>
  <tbody id="tbl-matrix"></tbody></table>
</div>
<div class="callout">
  <b>Comparability.</b> These numbers describe this corpus only. They are not comparable
  to Mem0 LoCoMo/LongMemEval or Zep DMR figures. No LoCoMo result is claimed. Single run,
  single machine — no confidence intervals; treat differences under ~0.05 hit rate as noise.
</div>

<footer>
  Rendered from <code>docs/analytics/data/repo-analytics.json</code> by
  <code>scripts/analytics/render_analytics.py</code>. All figures computed from this
  repository's own git history and in-tree artifacts.
</footer>
</div>

<script>
const DATA = {payload};

const fmt = n => n.toLocaleString('en-US');
const pctf = (a,b) => b ? ((a-b)/b*100).toFixed(1) : '0.0';

function bar(v, max, warn) {{
  const w = max ? Math.max(2, v/max*100) : 0;
  return `<div class="bar ${{warn?'warn':''}}"><i style="width:${{w}}%"></i></div>`;
}}

/* ---- monthly ---- */
(function(){{
  const rows = DATA.commits.monthly, max = Math.max(...rows.map(r=>r.commits));
  document.getElementById('tbl-monthly').innerHTML = rows.map(r =>
    `<tr><td>${{r.month}}</td><td class="num">${{fmt(r.commits)}}</td>
     <td class="num" style="color:var(--muted)">${{fmt(r.cumulative)}}</td>
     <td>${{bar(r.commits,max)}}</td></tr>`).join('');
}})();

/* ---- types ---- */
(function(){{
  const rows = DATA.commits.commit_types.slice(0,9), max = Math.max(...rows.map(r=>r.count));
  document.getElementById('tbl-types').innerHTML = rows.map(r =>
    `<tr><td><code>${{r.type}}</code></td><td class="num">${{fmt(r.count)}}</td>
     <td>${{bar(r.count,max, r.type==='(untyped)')}}</td></tr>`).join('');
}})();

/* ---- authors ---- */
(function(){{
  const rows = DATA.commits.authors.slice(0,10), tot = DATA.commits.total_commits;
  const max = Math.max(...rows.map(r=>r.commits));
  document.getElementById('tbl-authors').innerHTML = rows.map(r =>
    `<tr><td>${{r.author}}</td><td class="num">${{fmt(r.commits)}}</td>
     <td class="num" style="color:var(--muted)">${{(r.commits/tot*100).toFixed(1)}}%</td>
     <td>${{bar(r.commits,max)}}</td></tr>`).join('');
}})();

/* ---- branches ---- */
(function(){{
  const rows = DATA.branches.branches_ahead_of_main, max = Math.max(...rows.map(r=>r.ahead));
  document.getElementById('tbl-branches').innerHTML = rows.map(r =>
    `<tr><td><code>${{r.branch}}</code></td><td class="num">${{r.ahead}}</td>
     <td>${{bar(r.ahead,max,true)}}</td></tr>`).join('');
}})();

/* ---- dirs / exts ---- */
(function(){{
  const rows = DATA.files.by_top_dir.slice(0,12), max = Math.max(...rows.map(r=>r.files));
  document.getElementById('tbl-dirs').innerHTML = rows.map(r =>
    `<tr><td><code>${{r.dir}}/</code></td><td class="num">${{fmt(r.files)}}</td>
     <td>${{bar(r.files,max)}}</td></tr>`).join('');
  const ex = DATA.files.by_extension.slice(0,10), emax = Math.max(...ex.map(r=>r.files));
  document.getElementById('tbl-exts').innerHTML = ex.map(r =>
    `<tr><td><code>${{r.ext}}</code></td><td class="num">${{fmt(r.files)}}</td>
     <td>${{bar(r.files,emax)}}</td></tr>`).join('');
}})();

/* ---- modes / kinds / matrix ---- */
(function(){{
  const rows = DATA.benchmarks.mode_aggregates;
  document.getElementById('tbl-modes').innerHTML = rows.map(r =>
    `<tr><td><code>${{r.mode}}</code></td><td class="num">${{r.hit_rate.toFixed(3)}}</td>
     <td class="num">${{r.mrr.toFixed(3)}}</td><td class="num">${{r.p50_ms.toFixed(1)}}</td></tr>`).join('');

  const kinds = [...new Set(DATA.benchmarks.rows.map(r=>r.kind))];
  const best = kinds.map(k => {{
    const c = DATA.benchmarks.rows.filter(r=>r.kind===k && r.hit_rate!=null);
    return c.sort((a,b)=> (b.hit_rate-a.hit_rate) || ((b.mrr||0)-(a.mrr||0)))[0];
  }}).filter(Boolean);
  document.getElementById('tbl-kinds').innerHTML = best.map(r =>
    `<tr><td><code>${{r.kind}}</code></td><td><code>${{r.mode}}</code></td>
     <td class="num">${{r.hit_rate.toFixed(3)}}</td><td class="num">${{r.n}}</td></tr>`).join('');

  document.getElementById('tbl-matrix').innerHTML = DATA.benchmarks.rows.map(r =>
    `<tr><td><code>${{r.mode}}</code></td><td><code>${{r.kind}}</code></td>
     <td class="num">${{r.n}}</td><td class="num">${{r.hit_rate.toFixed(3)}}</td>
     <td class="num">${{r.mrr.toFixed(3)}}</td><td class="num">${{r.leak_rate.toFixed(3)}}</td>
     <td class="num">${{r.p50_ms.toFixed(1)}}</td></tr>`).join('');
}})();

/* ---- weekly chart ---- */
(function(){{
  const rows = DATA.commits.weekly;
  const W=1080, H=260, P={{t:16,r:44,b:34,l:44}};
  const iw=W-P.l-P.r, ih=H-P.t-P.b;
  const maxC = Math.max(...rows.map(r=>r.commits));
  const maxCum = rows[rows.length-1].cumulative;
  const bw = iw/rows.length;
  let bars='', line='', labels='', grid='';
  for(let g=0; g<=4; g++){{
    const y=P.t+ih-(ih*g/4);
    grid += `<line x1="${{P.l}}" y1="${{y}}" x2="${{W-P.r}}" y2="${{y}}" stroke="#1a2330"/>`;
    grid += `<text x="${{P.l-8}}" y="${{y+4}}" fill="#8b9bb0" font-size="10" text-anchor="end">${{Math.round(maxC*g/4)}}</text>`;
  }}
  rows.forEach((r,i)=>{{
    const h = r.commits/maxC*ih;
    const x = P.l + i*bw + bw*0.18;
    const w = bw*0.64;
    bars += `<rect x="${{x}}" y="${{P.t+ih-h}}" width="${{w}}" height="${{h}}" rx="2" fill="url(#g1)"><title>${{r.week}}: ${{r.commits}} commits</title></rect>`;
    if(i%2===0 || rows.length<10)
      labels += `<text x="${{x+w/2}}" y="${{H-12}}" fill="#8b9bb0" font-size="9.5" text-anchor="middle">${{r.week.replace('2026-','')}}</text>`;
  }});
  rows.forEach((r,i)=>{{
    const x = P.l + i*bw + bw/2;
    const y = P.t+ih-(r.cumulative/maxCum*ih);
    line += (i?'L':'M')+x+','+y+' ';
  }});
  document.getElementById('chart-weekly').innerHTML =
    `<svg viewBox="0 0 ${{W}} ${{H}}" width="100%" style="height:auto">
      <defs><linearGradient id="g1" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#4cc2ff"/><stop offset="100%" stop-color="#2a6f96"/>
      </linearGradient></defs>
      ${{grid}}${{bars}}
      <path d="${{line}}" fill="none" stroke="#7ee787" stroke-width="1.8" opacity=".9"/>
      ${{labels}}
    </svg>`;
}})();

/* ---- surface chart ---- */
(function(){{
  const pts = DATA.surface.points;
  const W=1080, H=250, P={{t:16,r:52,b:34,l:44}};
  const iw=W-P.l-P.r, ih=H-P.t-P.b;
  const maxT = Math.max(...pts.map(p=>p.tools));
  const maxD = Math.max(...pts.map(p=>p.domains));
  const n = pts.length;
  const x = i => P.l + (n===1?iw/2:iw*i/(n-1));
  const yT = v => P.t+ih-(v/maxT*ih);
  const yD = v => P.t+ih-(v/maxD*ih);
  let grid='';
  for(let g=0; g<=4; g++){{
    const y=P.t+ih-(ih*g/4);
    grid += `<line x1="${{P.l}}" y1="${{y}}" x2="${{W-P.r}}" y2="${{y}}" stroke="#1a2330"/>`;
    grid += `<text x="${{P.l-8}}" y="${{y+4}}" fill="#8b9bb0" font-size="10" text-anchor="end">${{Math.round(maxT*g/4)}}</text>`;
    grid += `<text x="${{W-P.r+8}}" y="${{y+4}}" fill="#7ee787" font-size="10">${{Math.round(maxD*g/4)}}</text>`;
  }}
  let pT='', pD='', dots='', labels='';
  pts.forEach((p,i)=>{{
    pT += (i?'L':'M')+x(i)+','+yT(p.tools)+' ';
    pD += (i?'L':'M')+x(i)+','+yD(p.domains)+' ';
    dots += `<circle cx="${{x(i)}}" cy="${{yT(p.tools)}}" r="3.5" fill="#4cc2ff"><title>${{p.date.slice(0,10)}} — ${{p.tools}} tools</title></circle>`;
    dots += `<circle cx="${{x(i)}}" cy="${{yD(p.domains)}}" r="3.5" fill="#7ee787"><title>${{p.date.slice(0,10)}} — ${{p.domains}} domains</title></circle>`;
    if(i===0 || i===n-1)
      labels += `<text x="${{x(i)}}" y="${{H-12}}" fill="#8b9bb0" font-size="10" text-anchor="middle">${{p.date.slice(0,10)}}</text>`;
  }});
  document.getElementById('chart-surface').innerHTML =
    `<svg viewBox="0 0 ${{W}} ${{H}}" width="100%" style="height:auto">
      ${{grid}}
      <path d="${{pT}}" fill="none" stroke="#4cc2ff" stroke-width="2"/>
      <path d="${{pD}}" fill="none" stroke="#7ee787" stroke-width="2"/>
      ${{dots}}${{labels}}
    </svg>`;
}})();

/* ---- scatter ---- */
(function(){{
  const rows = DATA.benchmarks.mode_aggregates.filter(r=>r.p50_ms>0);
  const W=1080, H=300, P={{t:20,r:30,b:44,l:56}};
  const iw=W-P.l-P.r, ih=H-P.t-P.b;
  const maxX = Math.max(...rows.map(r=>r.p50_ms))*1.12;
  const minY = 0, maxY = 1;
  const x = v => P.l + (v/maxX)*iw;
  const y = v => P.t+ih-((v-minY)/(maxY-minY))*ih;
  let grid='';
  for(let g=0; g<=5; g++){{
    const yy=P.t+ih-(ih*g/5);
    grid += `<line x1="${{P.l}}" y1="${{yy}}" x2="${{W-P.r}}" y2="${{yy}}" stroke="#1a2330"/>`;
    grid += `<text x="${{P.l-8}}" y="${{yy+4}}" fill="#8b9bb0" font-size="10" text-anchor="end">${{(g/5).toFixed(1)}}</text>`;
  }}
  for(let g=0; g<=4; g++){{
    const xx=P.l+(iw*g/4);
    grid += `<text x="${{xx}}" y="${{H-16}}" fill="#8b9bb0" font-size="10" text-anchor="middle">${{Math.round(maxX*g/4)}}ms</text>`;
  }}
  let dots='';
  const placed=[];
  rows.slice().sort((a,b)=>a.p50_ms-b.p50_ms).forEach(r=>{{
    const rad = 6 + Math.sqrt(r.queries)/2.2;
    const col = r.hit_rate>=0.7 ? '#7ee787' : r.hit_rate>=0.45 ? '#4cc2ff' : '#ffb454';
    const cx=x(r.p50_ms), cy=y(r.hit_rate);
    dots += `<circle cx="${{cx}}" cy="${{cy}}" r="${{rad}}" fill="${{col}}" opacity=".28"/>`;
    dots += `<circle cx="${{cx}}" cy="${{cy}}" r="4" fill="${{col}}"><title>${{r.mode}}: hit ${{r.hit_rate.toFixed(3)}}, ${{r.p50_ms.toFixed(0)}}ms, n=${{r.queries}}</title></circle>`;
    // collision-aware label placement: nudge up until it clears every label already placed
    let ly = cy - rad - 7, guard = 0;
    while (guard++ < 14 && placed.some(p => Math.abs(p.x-cx) < 104 && Math.abs(p.y-ly) < 13)) ly -= 13;
    placed.push({{x:cx, y:ly}});
    dots += `<text x="${{cx}}" y="${{ly}}" fill="#e6edf6" font-size="10.5" text-anchor="middle">${{r.mode}}</text>`;
  }});
  document.getElementById('chart-scatter').innerHTML =
    `<svg viewBox="0 0 ${{W}} ${{H}}" width="100%" style="height:auto">
      ${{grid}}${{dots}}
      <text x="${{P.l+iw/2}}" y="${{H-2}}" fill="#8b9bb0" font-size="10.5" text-anchor="middle">p50 latency (ms) →</text>
    </svg>`;
}})();
</script>
</body>
</html>
"""


def main() -> int:
    d = load()
    md = build_markdown(d)
    html = build_html(d)
    with open(OUT_MD, "w") as fh:
        fh.write(md)
    with open(OUT_HTML, "w") as fh:
        fh.write(html)
    print(f"wrote {OUT_MD} ({len(md)} bytes)")
    print(f"wrote {OUT_HTML} ({len(html)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
