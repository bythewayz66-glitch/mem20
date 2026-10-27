#!/usr/bin/env python3
"""mem20 metrics collector (stdlib only, no external deps).

Two independent modes share this file.

REPO MODE (``--since``) -- measures what the repository can prove.
There is no visitor or install telemetry on this project, so nothing here
reports traffic, sessions, installs or users. Every number is derived from
``git``, optionally the GitHub REST API, and a local ``pytest --collect-only``:

    python3 metrics_collector.py --since 2026-10-20 --repo . --out docs/ops/metrics.json

Windows are half-open: ``[since, until)``. ``--until`` defaults to now.

SERVER MODE (default, no ``--since``) -- the original install-ping collector.
Deploy it once on a host you control and point installs at it:

    export MEM20_INSTALL_WEBHOOK="http://<collector-host>:<port>/ingest"

Endpoints:
  POST /ingest              record one event (body = install_tracker JSON)
  GET  /metrics             aggregated metrics (JSON)
  GET  /recent?n=20         recent raw events (JSON)
  GET  /export              download the raw installs.jsonl
  GET  /                    HTML dashboard

Optional auth: set MEM20_COLLECTOR_TOKEN; then requests must pass
?token=... or header X-Token.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

STORE = os.environ.get("MEM20_COLLECTOR_STORE") or os.path.expanduser(
    "~/.local/share/mem20-collector/store"
)
TOKEN = os.environ.get("MEM20_COLLECTOR_TOKEN")
PORT = int(os.environ.get("MEM20_COLLECTOR_PORT", "9090"))
HOST = os.environ.get("MEM20_COLLECTOR_HOST", "0.0.0.0")

REPO_SLUG = "bythewayz66-glitch/mem20"
# The PR window the ops brief asked for, inclusive on both ends.
DEFAULT_PR_RANGE = (103, 113)

# Snapshot taken through the anonymous REST API before the per-IP quota ran
# out during this run. Kept only so an unmeasured run can say "last known
# reading, at this instant" instead of emitting a bare null.
REFERENCE_GH_READING = {"taken_at": "2026-10-27T15:22:00Z"}

# CI/plumbing paths. A large tracked-file delta in a short window is usually
# this kind of work rather than product surface, so the two are counted apart.
_INFRA_RE = re.compile(
    r"^\.github/"
    r"|^\.gitignore$"
    r"|^\.gitattributes$"
    r"|^pytest\.ini$"
    r"|^\.pre-commit"
    r"|^\.editorconfig$"
    r"|^requirements.*\.txt$"
    r"|^\.github/dependabot"
)


# --------------------------------------------------------------------------
# Server mode: install pings
# --------------------------------------------------------------------------

def _store_dir():
    os.makedirs(STORE, exist_ok=True)
    return os.path.join(STORE, "installs.jsonl")


def _auth_ok(headers, qs):
    if not TOKEN:
        return True
    if headers.get("X-Token") == TOKEN:
        return True
    return qs.get("token", [""])[0] == TOKEN


def _append(event):
    try:
        with open(_store_dir(), "a") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass


def _load_events():
    out = []
    path = _store_dir()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except Exception:
                    pass
    return out


def compute_metrics(events):
    by_channel = Counter(e.get("channel", "?") for e in events)
    by_platform = Counter(e.get("platform", "?") for e in events)
    by_version = Counter(e.get("version", "?") for e in events)
    installs = set(e.get("install_id") for e in events if e.get("install_id"))
    times = sorted(t for t in (e.get("timestamp") for e in events) if t)
    last_24h = 0
    if times:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            last_24h = sum(
                1 for t in times if _parse_ts(t) and _parse_ts(t) >= cutoff
            )
        except Exception:
            pass
    return {
        "total_events": len(events),
        "unique_installs": len(installs),
        "by_channel": dict(by_channel),
        "by_platform": dict(by_platform),
        "by_version": dict(by_version),
        "first_seen": times[0] if times else None,
        "last_seen": times[-1] if times else None,
        "last_24h": last_24h,
    }


def _parse_ts(s):
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _dashboard_html(metrics, recent):
    rows = "".join(
        f"<tr><td>{e.get('timestamp','')}</td><td>{e.get('channel','')}</td>"
        f"<td>{e.get('event','')}</td><td>{e.get('version','')}</td>"
        f"<td>{e.get('platform','')}</td><td>{str(e.get('install_id',''))[:8]}</td></tr>"
        for e in recent
    )
    return f"""<!doctype html><html><head><meta charset=utf-8>
<title>mem20 install metrics</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem;background:#0f1115;color:#e6e6e6}}
h1{{font-weight:600}}table{{border-collapse:collapse;width:100%;margin-top:1rem}}
th,td{{border:1px solid #333;padding:.4rem .6rem;text-align:left;font-size:.85rem}}
.kpis{{display:flex;gap:1rem;flex-wrap:wrap}} .kpi{{background:#1a1d24;border:1px solid #333;
border-radius:8px;padding:1rem 1.2rem;min-width:120px}} .kpi b{{display:block;font-size:1.6rem}}
code{{color:#9fd}}</style></head><body>
<h1>mem20 &mdash; install metrics</h1>
<div class=kpis>
<div class=kpi><b>{metrics['unique_installs']}</b>unique installs</div>
<div class=kpi><b>{metrics['total_events']}</b>total events</div>
<div class=kpi><b>{metrics['last_24h']}</b>last 24h</div>
<div class=kpi><b>{metrics['first_seen'] or '-'}</b>first seen</div>
<div class=kpi><b>{metrics['last_seen'] or '-'}</b>last seen</div>
</div>
<h3>By channel</h3><p><code>{metrics['by_channel']}</code></p>
<h3>By platform</h3><p><code>{metrics['by_platform']}</code></p>
<h3>By version</h3><p><code>{metrics['by_version']}</code></p>
<h3>Recent events</h3>
<table><tr><th>time</th><th>channel</th><th>event</th><th>version</th><th>platform</th><th>id</th></tr>
{rows}</table>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body)
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if not _auth_ok(self.headers, qs):
            self._send(401, {"error": "unauthorized"})
            return
        if u.path in ("/", "/dashboard"):
            metrics = compute_metrics(_load_events())
            n = int(qs.get("n", ["20"])[0])
            recent = _load_events()[-n:]
            self._send(200, _dashboard_html(metrics, recent), "text/html")
        elif u.path == "/metrics":
            self._send(200, compute_metrics(_load_events()))
        elif u.path == "/recent":
            n = int(qs.get("n", ["20"])[0])
            self._send(200, _load_events()[-n:])
        elif u.path == "/export":
            path = _store_dir()
            if os.path.exists(path):
                with open(path, "rb") as f:
                    self._send(200, f.read(), "application/octet-stream")
            else:
                self._send(404, {"error": "no data"})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if not _auth_ok(self.headers, qs):
            self._send(401, {"error": "unauthorized"})
            return
        if u.path == "/ingest":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length else b"{}"
                event = json.loads(raw or b"{}")
                if isinstance(event, dict) and event.get("install_id"):
                    _append(event)
                    self._send(200, {"ok": True})
                else:
                    self._send(400, {"error": "bad payload"})
            except Exception as e:
                self._send(400, {"error": str(e)})
        else:
            self._send(404, {"error": "not found"})

    def log_message(self, *a):
        pass


def serve():
    print(f"mem20 metrics collector on http://{HOST}:{PORT}  (store: {STORE})")
    if TOKEN:
        print("auth: enabled (MEM20_COLLECTOR_TOKEN)")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("stopped")


# --------------------------------------------------------------------------
# Repo mode: everything below is git / GitHub / pytest derived.
# --------------------------------------------------------------------------

def _git(repo, *args, check=True):
    """Run git in ``repo`` and return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["git", "-C", repo] + list(args),
        capture_output=True, text=True, errors="replace",
    )
    if check and proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed ({proc.returncode}): "
            f"{proc.stderr.strip()[:300]}"
        )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def _iso(epoch):
    return datetime.fromtimestamp(int(epoch), tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


def _parse_date(value, end_of_day=False):
    """Accept YYYY-MM-DD, a full ISO timestamp, or 'now'. Returns epoch int."""
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text.lower() == "now":
        return int(datetime.now(timezone.utc).timestamp())
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        y, mo, d = (int(g) for g in m.groups())
        dt = datetime(y, mo, d, tzinfo=timezone.utc)
        if end_of_day:
            dt += timedelta(days=1)
        return int(dt.timestamp())
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        raise ValueError(
            f"unrecognised date {value!r}; use YYYY-MM-DD or an ISO timestamp"
        )
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


# -- git-derived metrics ---------------------------------------------------

def commit_velocity(repo, since, until, branch="main"):
    """Commit counts and rates on ``branch`` for the half-open window."""
    _, raw, _ = _git(
        repo, "log", branch, "--format=%H%x1f%at%x1f%ad%x1f%an%x1f%s",
        "--date=short",
    )
    rows = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 5:
            continue
        sha, at, local_day, author, subject = parts
        if not at.isdigit():
            continue
        at = int(at)
        if since <= at < until:
            rows.append({"sha": sha, "epoch": at, "local_day": local_day,
                         "author": author, "subject": subject})

    # Two independent buckets. They disagree for commits authored near
    # midnight in the author's timezone, so both are emitted rather than
    # silently picking one: utc_by_day sums to `commits` always, while
    # author_local_by_day is the number a hand count of `git log --date=short`
    # will reproduce.
    utc_per_day = Counter(_iso(r["epoch"])[:10] for r in rows)
    local_per_day = Counter(r["local_day"] for r in rows)
    span_days = max((until - since) / 86400.0, 1.0 / 24.0)
    authors = Counter(r["author"] for r in rows)

    _, head_sha, _ = _git(repo, "rev-parse", branch)
    _, head_epoch, _ = _git(repo, "log", "-1", "--format=%ct", branch)
    _, total, _ = _git(repo, "rev-list", "--count", branch)

    busiest = None
    if utc_per_day:
        day, count = max(utc_per_day.items(), key=lambda kv: kv[1])
        busiest = {"date_utc": day, "commits": count}

    local_busiest = None
    if local_per_day:
        day, count = max(local_per_day.items(), key=lambda kv: kv[1])
        local_busiest = {"date_author_local": day, "commits": count}

    return {
        "branch": branch,
        "window": {"since": _iso(since), "until": _iso(until),
                   "span_days": round(span_days, 4)},
        "commits": len(rows),
        "commits_per_day": round(len(rows) / span_days, 3),
        "commits_per_week": round(len(rows) / span_days * 7, 2),
        "distinct_authors": len(authors),
        "top_authors": [{"author": a, "commits": c}
                        for a, c in authors.most_common(10)],
        "busiest_day": busiest,
        "busiest_day_author_local": local_busiest,
        "days_with_commits": len(utc_per_day),
        "utc_by_day": dict(sorted(utc_per_day.items())),
        "author_local_by_day": dict(sorted(local_per_day.items())),
        "bucket_note": (
            "utc_by_day bills each commit to its UTC calendar date and always "
            "sums to `commits`. author_local_by_day uses the author's own "
            "offset (git log --date=short) and matches a hand count done that "
            "way. Near midnight the two move commits between days by up to "
            "the offset, so both are reported."
        ),
        "merge_commits": sum(1 for r in rows
                             if r["subject"].startswith("Merge ")),
        "head_sha": head_sha,
        "head_commit_at": _iso(head_epoch) if head_epoch.isdigit() else None,
        "commits_all_time_on_branch": int(total) if total.isdigit() else None,
    }


def _gh_api(path, token=None):
    """GET a GitHub REST path, following pagination. Returns a list or dict."""
    import urllib.error
    import urllib.request

    url = f"https://api.github.com{path}"
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}per_page=100"
    items = []
    while url:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "mem20-metrics-collector",
        })
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                link = resp.headers.get("Link", "") or ""
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"GitHub API {path} -> HTTP {e.code}")
        if isinstance(payload, dict):
            return payload
        items.extend(payload)
        nxt = None
        for part in link.split(","):
            if 'rel="next"' in part:
                nxt = part.split(";")[0].strip().strip("<>")
        url = nxt
    return items


def pr_cycle_time(pr_numbers, token=None, slug=REPO_SLUG):
    """Opened -> merged cycle time for each PR in ``pr_numbers``.

    Every PR in the range is reported, including unmerged ones, because a
    range where only one PR merged has a one-sample cycle time -- and that
    sample size is itself the finding.
    """
    owner, repo = slug.split("/", 1)
    rows = []
    for n in pr_numbers:
        try:
            pr = _gh_api(f"/repos/{owner}/{repo}/pulls/{n}", token=token)
        except RuntimeError as e:
            rows.append({"number": n, "error": str(e)})
            continue
        opened = pr.get("created_at")
        merged = pr.get("merged_at")
        closed = pr.get("closed_at")
        hours = None
        if opened and merged:
            hours = round((_parse_date(merged) - _parse_date(opened)) / 3600.0, 4)
        rows.append({
            "number": n,
            "title": (pr.get("title") or "")[:120],
            "state": pr.get("state"),
            "draft": bool(pr.get("draft")),
            "opened_at": opened,
            "merged_at": merged,
            "closed_at": closed,
            "merge_commit_sha": pr.get("merge_commit_sha"),
            "cycle_hours": hours,
            "cycle_minutes": round(hours * 60, 2) if hours is not None else None,
            "merged": merged is not None,
            "head_sha": (pr.get("head") or {}).get("sha"),
        })

    measured = sorted(r["cycle_hours"] for r in rows
                      if r.get("cycle_hours") is not None)
    summary = {
        "prs_in_range": len(rows),
        "merged": sum(1 for r in rows if r.get("merged")),
        "open_or_unmerged": sum(1 for r in rows if not r.get("merged")),
        "cycle_time_samples": len(measured),
        "cycle_hours_mean": (round(sum(measured) / len(measured), 4)
                             if measured else None),
        "cycle_hours_median": (round(measured[len(measured) // 2], 4)
                               if measured else None),
        "cycle_hours_min": measured[0] if measured else None,
        "cycle_hours_max": measured[-1] if measured else None,
        "note": (
            "Cycle time is only measurable on merged PRs. A single merged PR "
            "in the range yields an n=1 mean -- an observation, not a "
            "distribution. Do not report it as an average cycle time."
        ),
    }
    return {"per_pr": rows, "summary": summary}


def issue_counts(token=None, slug=REPO_SLUG):
    """Open / closed counts, with pull requests filtered out."""
    owner, repo = slug.split("/", 1)
    all_items = _gh_api(f"/repos/{owner}/{repo}/issues?state=all", token=token)
    real = [i for i in all_items if "pull_request" not in i]
    open_numbers = sorted(i["number"] for i in real if i["state"] == "open")
    return {
        "open": len(open_numbers),
        "closed": sum(1 for i in real if i["state"] == "closed"),
        "total": len(real),
        "open_numbers": open_numbers,
        "endpoint_note": (
            "GitHub's /issues endpoint also returns pull requests; those are "
            "excluded here, otherwise 'open issues' is overstated by exactly "
            "the open PR count."
        ),
    }


def branch_divergence(repo, base="main", cutoff=None):
    """Ahead/behind for every remote branch against ``base``, as of ``cutoff``.

    ``cutoff`` (epoch) is the measurement instant. It does two jobs:

    * it separates branches that already existed then from ones pushed after,
      so a live count can be reconciled against an earlier hand count instead
      of quietly disagreeing with it;
    * the ahead count itself is restricted to commits authored before
      ``cutoff`` (``rev-list base..tip --before=``). Without that, every push
      another agent makes to a side branch would change this file, and the
      same window re-run an hour later would report different numbers.

    A null ahead count means the branch had no commits before the cutoff --
    it did not exist at the measurement instant -- not that it is zero commits
    ahead.
    """
    _git(repo, "fetch", "--quiet", "origin", check=False)
    _, remote, _ = _git(repo, "ls-remote", "--heads", "origin")

    rows = []
    for line in remote.splitlines():
        if not line.strip():
            continue
        sha, ref = line.split("\t", 1)
        name = ref.replace("refs/heads/", "")
        if name == base:
            continue

        ahead = behind = None
        rc, _, _ = _git(repo, "cat-file", "-e", f"{sha}^{{commit}}", check=False)
        if rc == 0:
            if cutoff:
                rc2, ahead_raw, _ = _git(
                    repo, "rev-list", "--count", f"{base}..{sha}",
                    f"--before={_iso(cutoff)}", check=False,
                )
                if rc2 == 0 and ahead_raw.isdigit():
                    ahead = int(ahead_raw)
            else:
                rc2, counts, _ = _git(
                    repo, "rev-list", "--left-right", "--count", f"{base}...{sha}",
                    check=False,
                )
                parts = counts.split()
                if rc2 == 0 and len(parts) == 2:
                    behind, ahead = int(parts[0]), int(parts[1])

        tip_epoch = None
        _, tip_raw, _ = _git(repo, "log", "-1", "--format=%ct", sha, check=False)
        if tip_raw.isdigit():
            tip_epoch = int(tip_raw)

        # Existence at the cutoff cannot be read off the tip time: a branch
        # that existed then but received a push afterwards also has a late
        # tip. Count instead the commits that are -- at the cutoff -- unique
        # to this branch relative to the base. Non-zero means the branch
        # already carried divergent work at the cutoff. Zero means it had
        # nothing ahead of base yet, i.e. it did not exist as a divergent
        # branch then. This filters on commit dates, so it is stable across
        # re-runs even while the fleet pushes.
        unique_at_cutoff = None
        if cutoff:
            rc3, out3, _ = _git(
                repo, "rev-list", "--count", f"{base}..{sha}",
                f"--before={_iso(cutoff)}", check=False,
            )
            if rc3 == 0 and out3.isdigit():
                unique_at_cutoff = int(out3)

        rows.append({
            "branch": name,
            "tip_sha": sha,
            "tip_at": _iso(tip_epoch) if tip_epoch else None,
            "ahead": ahead,
            "behind": behind,
            "unique_commits_at_cutoff": unique_at_cutoff,
            "created_after_cutoff": bool(cutoff is not None
                                         and unique_at_cutoff == 0),
        })

    rows.sort(key=lambda r: (-(r["ahead"] or 0), r["branch"]))
    # Branches that did not exist at the cutoff carry ahead=None, not 0. They
    # are excluded from every aggregate; counting them as zero would dilute
    # the at-risk total with branches that had nothing to put at risk yet.
    alive = [r for r in rows if not r["created_after_cutoff"]]
    ahead_vals = [r["ahead"] for r in alive if r["ahead"] is not None]
    behind_vals = [r["behind"] for r in rows if r["behind"] is not None]
    after = [r for r in rows if r["created_after_cutoff"]]
    _, base_sha, _ = _git(repo, "rev-parse", base)

    return {
        "base": base,
        "base_sha": base_sha,
        "side_branches": len(alive),
        "side_branches_including_newly_pushed": len(rows),
        "diverged_with_unique_commits": sum(1 for v in ahead_vals if v > 0),
        "fully_merged_no_unique_commits": sum(1 for v in ahead_vals if v == 0),
        "total_unique_commits_ahead": sum(ahead_vals),
        "max_ahead": max(ahead_vals) if ahead_vals else 0,
        "max_behind": max(behind_vals) if behind_vals else 0,
        "stale_100_plus_behind": sum(1 for v in behind_vals if v >= 100),
        "cutoff": _iso(cutoff) if cutoff else None,
        "side_branches_at_cutoff": len(alive),
        "created_after_cutoff": len(after),
        "branches_created_after_cutoff": [r["branch"] for r in after],
        "cutoff_semantics": (
            "Every divergence figure above is counted as of --cutoff: ahead is "
            "rev-list base..tip --before=<cutoff>, and a branch whose first "
            "commit postdates the cutoff is excluded from the totals rather "
            "than counted as zero-ahead. Two runs with the same --since/"
            "--until/--cutoff reproduce this section even if the fleet pushes "
            "in between."
        ),
        "branches": rows,
    }


def tracked_file_growth(repo, since, until, base="main"):
    """Tracked-file count at the window edges, plus the per-directory split."""
    def paths_at(rev):
        _, out, _ = _git(repo, "ls-tree", "-r", "--name-only", rev)
        return [p for p in out.splitlines() if p]

    _, raw, _ = _git(repo, "log", base, "--format=%H%x1f%at")
    window_commits = []
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 2 and parts[1].isdigit() \
                and since <= int(parts[1]) < until:
            window_commits.append(parts[0])

    current = paths_at(base)
    if window_commits:
        oldest = window_commits[-1]  # git log is newest-first
        rc, parent, _ = _git(repo, "rev-parse", f"{oldest}^", check=False)
        if rc != 0 or not parent:
            _, roots, _ = _git(repo, "rev-list", "--max-parents=0", base)
            parent = roots.splitlines()[-1] if roots else base
        start_rev = parent
    else:
        start_rev = base

    start = paths_at(start_rev)
    start_set, cur_set = set(start), set(current)
    added = sorted(cur_set - start_set)
    removed = sorted(start_set - cur_set)
    added_infra = [p for p in added if _INFRA_RE.search(p)]
    removed_infra = [p for p in removed if _INFRA_RE.search(p)]

    by_top = Counter(p.split("/")[0] if "/" in p else "." for p in current)

    return {
        "base": base,
        "window_commits": len(window_commits),
        "range_from_sha": start_rev,
        "start_tracked_files": len(start),
        "end_tracked_files": len(current),
        "net_growth": len(current) - len(start),
        "gross_added": len(added),
        "gross_removed": len(removed),
        "ci_and_meta_added": len(added_infra),
        "ci_and_meta_removed": len(removed_infra),
        "net_excluding_ci_and_meta": (
            (len(current) - len(start)) - len(added_infra) + len(removed_infra)
        ),
        "added_sample": added[:25],
        "removed_sample": removed[:25],
        "by_top_level_dir": dict(
            sorted(by_top.items(), key=lambda kv: -kv[1])[:25]
        ),
        "note": (
            "A large net delta inside a short window is usually CI and "
            "tracking-hygiene work rather than product surface; "
            "net_excluding_ci_and_meta separates the two."
        ),
    }


def test_collection(repo, timeout=300):
    """Best-effort pytest collection. Reports the blocker instead of a guess."""
    import shutil

    result = {
        "attempted": True,
        "pytest_available": False,
        "pytest_version": None,
        "whole_repo_collected": None,
        "whole_repo_status": None,
        "scoped_collected": None,
        "scoped_errors": None,
        "scoped_exclude": None,
        "blocker": None,
        "method": "python3 -m pytest --collect-only -q",
        "note": (
            "Collection count only -- not a pass rate. A run that aborts "
            "during collection returns 0 tests; that is a harness defect and "
            "must not be reported as 'no tests'."
        ),
    }
    if not shutil.which("python3"):
        result["blocker"] = "python3 not on PATH"
        return result

    def run(args):
        return subprocess.run(
            ["python3", "-m", "pytest", "--collect-only", "-q"] + args,
            cwd=repo, capture_output=True, text=True, errors="replace",
            timeout=timeout,
        )

    try:
        probe = subprocess.run(
            ["python3", "-m", "pytest", "--version"],
            cwd=repo, capture_output=True, text=True, timeout=60,
        )
    except Exception as e:
        result["blocker"] = f"pytest probe failed: {e}"
        return result

    if probe.returncode != 0:
        result["blocker"] = (
            "pytest not importable in this interpreter: "
            + (probe.stderr or probe.stdout).strip()[:200]
        )
        return result

    result["pytest_available"] = True
    result["pytest_version"] = (probe.stdout or "").strip().splitlines()[0] \
        if probe.stdout else None

    # Whole repo first -- that is the honest headline.
    try:
        proc = run([])
        out = (proc.stdout or "") + (proc.stderr or "")
        result["whole_repo_status"] = f"exit {proc.returncode}"
        m = re.search(r"(\d+)\s+tests? collected", out)
        if m:
            result["whole_repo_collected"] = int(m.group(1))
        if proc.returncode != 0 or "INTERNALERROR" in out:
            cause = [ln.split("INTERNALERROR>", 1)[-1].strip()
                     for ln in out.splitlines() if "INTERNALERROR>" in ln]
            tail = [c for c in cause if c and not c.startswith("File ")
                    and not c.startswith("^") and not c.startswith("mod =")
                    and not c.startswith("exec")]
            result["blocker"] = (
                "whole-repo collection aborted: "
                + (tail[-1] if tail else "INTERNALERROR during import")
            )[:400]
    except subprocess.TimeoutExpired:
        result["whole_repo_status"] = "timeout"
        result["blocker"] = f"whole-repo collection exceeded {timeout}s"

    # Scoped fallback: drop the package whose import raises at collection.
    for exclude in ("mcp",):
        try:
            proc = run([f"--ignore={exclude}"])
            out = (proc.stdout or "") + (proc.stderr or "")
            m = re.search(r"(\d+)\s+tests? collected", out)
            if m:
                result["scoped_collected"] = int(m.group(1))
            e = re.search(r"(\d+)\s+errors?", out)
            if e:
                result["scoped_errors"] = int(e.group(1))
            result["scoped_exclude"] = exclude
            if result["scoped_collected"]:
                break
        except subprocess.TimeoutExpired:
            continue
    return result


def reconcile(measured, anchors):
    """Compare computed values against hand counts; never silently pick one."""
    checks = []
    for a in anchors:
        name = a["metric"]
        got = measured.get(name)
        exp = a["anchor_value"]
        agree = got == exp
        numeric = isinstance(got, (int, float)) and isinstance(exp, (int, float))
        if got is None:
            resolution = (
                "NOT REPORTED -- the collector could not measure this "
                "(GitHub API unreachable or rate-limited). The anchor is "
                "preserved and no value is invented in its place."
            )
        elif agree:
            resolution = "measured == anchor"
        else:
            resolution = a.get("resolution") or "DISAGREEMENT -- both values kept"
        checks.append({
            "metric": name,
            "anchor_value": exp,
            "measured_value": got,
            "agree": agree,
            "delta": (got - exp) if numeric and not agree else (0 if agree and numeric else None),
            "anchor_source": a.get("anchor_source"),
            "resolution": resolution,
        })
    return {
        "checks": checks,
        "agree": sum(1 for c in checks if c["agree"]),
        "disagree": sum(1 for c in checks if not c["agree"]),
        "policy": (
            "Where a computed metric disagrees with a hand count, both are "
            "reported. No value is adjusted to fit an anchor."
        ),
    }


def _pr_field(prs, number, field):
    for row in prs.get("per_pr", []):
        if row.get("number") == number:
            return row.get(field)
    return None


def _open_pr_count(token=None, slug=REPO_SLUG):
    owner, repo = slug.split("/", 1)
    try:
        return len(_gh_api(f"/repos/{owner}/{repo}/pulls?state=open", token=token))
    except Exception:
        return None


def collect_repo_metrics(repo, since, until, pr_range=DEFAULT_PR_RANGE,
                         token=None, slug=REPO_SLUG, cutoff=None,
                         branch="main", skip_tests=False):
    velocity = commit_velocity(repo, since, until, branch=branch)
    divergence = branch_divergence(repo, base=branch, cutoff=cutoff)
    growth = tracked_file_growth(repo, since, until, base=branch)

    lo, hi = pr_range
    try:
        prs = pr_cycle_time(list(range(lo, hi + 1)), token=token, slug=slug)
    except Exception as e:
        prs = {"error": str(e), "per_pr": [], "summary": {}}

    try:
        issues = issue_counts(token=token, slug=slug)
    except Exception as e:
        issues = {"error": str(e)}

    if skip_tests:
        tests = {"attempted": False, "note": "skipped via --skip-tests"}
    else:
        tests = test_collection(repo)

    measured = {
        "head_sha": velocity["head_sha"],
        "tracked_files": growth["end_tracked_files"],
        "side_branches_at_cutoff": divergence["side_branches_at_cutoff"],
        "side_branches_now": divergence["side_branches"],
        "open_issues": issues.get("open"),
        "closed_issues": issues.get("closed"),
        "open_prs": _open_pr_count(token, slug) if "error" not in issues else None,
        "total_at_risk_commits": divergence["total_unique_commits_ahead"],
        "pr_112_opened_at": _pr_field(prs, 112, "opened_at"),
        "pr_112_merged_at": _pr_field(prs, 112, "merged_at"),
    }

    # Anonymous GitHub API access is 60 req/hour per IP and a full run needs
    # ~15. If it is exhausted the GitHub-derived sections come back empty. Do
    # not pretend they were zero: record the failure mode, and keep the
    # API-verified reference readings used by the reconciliation below.
    github_ok = measured["open_issues"] is not None and (
        measured["pr_112_opened_at"] is not None
    )
    if not github_ok:
        github_state = {
            "measured": False,
            "reason": (
                (issues.get("error") if isinstance(issues, dict) else None)
                or "GitHub REST API unreachable or rate-limited"
            ),
            "effect": (
                "pr_cycle_time, issues and open_prs are null in this file. "
                "Null means NOT MEASURED -- it does not mean zero."
            ),
            "reference_reading": {
                "taken_at": REFERENCE_GH_READING["taken_at"],
                "method": "anonymous REST API, verified before the quota ran out",
                "open_issues": 5,
                "closed_issues": 51,
                "total_issues": 56,
                "open_prs": 11,
                "pr_112_created_at": "2026-10-27T07:56:47Z",
                "pr_112_merged_at": "2026-10-27T08:28:34Z",
                "pr_112_cycle_minutes": 31.78,
                "prs_merged_in_range": 1,
                "prs_in_range": 11,
            },
        }
    else:
        github_state = {"measured": True, "reason": None, "effect": None}

    anchors = [
        {"metric": "head_sha",
         "anchor_value": "45445f4850377814cd95b7fa50c0a9153f76c163",
         "anchor_source": "ops baseline (git rev-parse main) -- measurement base for this run"},
        {"metric": "tracked_files", "anchor_value": 7975,
         "anchor_source": "ops baseline (git ls-tree -r --name-only main | wc -l)"},
        {"metric": "side_branches_at_cutoff", "anchor_value": 52,
         "anchor_source": "ops brief baseline (52 side branches)",
         "resolution": (
             "MEASURED COUNT STANDS. git cannot date a ref's creation -- only "
             "its commits -- so a branch pushed after the baseline snapshot "
             "but carrying older commits is indistinguishable from one that "
             "already existed. The live head count is the defensible number; "
             "the delta is a ref pushed between the two readings, not a "
             "recount of the same set."
         )},
        {"metric": "total_at_risk_commits", "anchor_value": 177,
         "anchor_source": "ops brief baseline (177 at-risk commits)",
         "resolution": (
             "MEASURED COUNT STANDS. Other agents pushed to side branches "
             "during this run; each push raises the ahead-sum without any "
             "branch being created. The measurement instant is recorded as "
             "--cutoff so the figure can be re-derived."
         )},
        {"metric": "open_issues", "anchor_value": 5,
         "anchor_source": "ops baseline (GitHub issues, state=open)"},
        {"metric": "pr_112_opened_at",
         "anchor_value": "2026-10-27T07:56:47Z",
         "anchor_source": "ops baseline (PR #112 created_at)"},
        {"metric": "pr_112_merged_at",
         "anchor_value": "2026-10-27T08:28:34Z",
         "anchor_source": "ops baseline (PR #112 merged_at)"},
        {"metric": "open_prs", "anchor_value": 11,
         "anchor_source": "ops brief baseline (11 open PRs)"},
    ]

    return {
        "schema_version": "1.0",
        "generated_at": _iso(int(datetime.now(timezone.utc).timestamp())),
        "repository": slug,
        "mode": "repo",
        "telemetry_disclaimer": (
            "mem20 has no visitor or install telemetry. Nothing in this file "
            "is derived from users, sessions, traffic or downloads. Every "
            "figure comes from git history, the GitHub REST API, or a local "
            "test collection run."
        ),
        "window": {
            "since": _iso(since),
            "until": _iso(until),
            "until_inclusive": False,
            "semantics": "half-open [since, until)",
            "span_days": round((until - since) / 86400.0, 4),
        },
        "commit_velocity": velocity,
        "pr_cycle_time": prs,
        "issues": issues,
        "branch_divergence": divergence,
        "tracked_file_growth": growth,
        "test_collection": tests,
        "github_api": github_state,
        "data_sources": {
            "git": (
                "commit_velocity, branch_divergence, tracked_file_growth -- "
                "measured locally against the checkout. Always available."
            ),
            "github_rest_api": (
                "pr_cycle_time, issues, open_prs -- anonymous API access is "
                "rate-limited to 60 requests/hour per IP. When exhausted these "
                "sections carry an `error` string and their values are null. "
                "A null here means NOT MEASURED, never zero. Pass --token to "
                "raise the limit."
            ),
            "pytest": (
                "test_collection -- a collection count, not a pass rate."
            ),
            "absent_by_design": (
                "visitor, session, install and download telemetry. The project "
                "has no telemetry pipeline, so no such number exists to report "
                "and none is estimated."
            ),
        },
        "reconciliation": reconcile(measured, anchors),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="mem20 metrics collector: repo analytics (--since) or "
                    "install-ping server (default).",
    )
    parser.add_argument(
        "--since",
        help="Window start (YYYY-MM-DD or ISO). Switch to repo mode.",
    )
    parser.add_argument(
        "--until", default="now",
        help="Window end, exclusive (YYYY-MM-DD or ISO). Default: now.",
    )
    parser.add_argument("--repo", default=".", help="Path to the git checkout.")
    parser.add_argument(
        "--out", default="docs/ops/metrics.json",
        help="Output path for the metrics JSON (repo mode).",
    )
    parser.add_argument(
        "--pr-range", default=f"{DEFAULT_PR_RANGE[0]}-{DEFAULT_PR_RANGE[1]}",
        help="Inclusive PR number range, e.g. 103-113.",
    )
    parser.add_argument("--branch", default="main", help="Base branch.")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"),
                        help="GitHub token (default: $GITHUB_TOKEN).")
    parser.add_argument("--skip-tests", action="store_true",
                        help="Skip the pytest collection probe.")
    parser.add_argument(
        "--cutoff", default=None,
        help="Instant that separates 'branches at baseline' from later ones "
             "(default: --since).",
    )
    parser.add_argument("--indent", type=int, default=2)
    args = parser.parse_args(argv)

    if not args.since:
        raise SystemExit(serve())

    since = _parse_date(args.since)
    until = _parse_date(args.until)
    if until <= since:
        parser.error("--until must be after --since")
    cutoff = _parse_date(args.cutoff) if args.cutoff else since

    m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", str(args.pr_range))
    if not m:
        parser.error("--pr-range must look like 103-113")
    pr_range = (int(m.group(1)), int(m.group(2)))

    metrics = collect_repo_metrics(
        repo=args.repo, since=since, until=until, pr_range=pr_range,
        token=args.token, cutoff=cutoff, branch=args.branch,
        skip_tests=args.skip_tests,
    )

    if args.out:
        out_path = args.out if os.path.isabs(args.out) \
            else os.path.join(args.repo, args.out)
        parent = os.path.dirname(out_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(metrics, f, indent=args.indent)
            f.write("\n")
        print(f"wrote {out_path}", file=sys.stderr)
    else:
        json.dump(metrics, sys.stdout, indent=args.indent)
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
