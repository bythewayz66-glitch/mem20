#!/usr/bin/env bash
# Program scoreboard signal collector — mem20
# Every number in docs/ops/program-scoreboard-2026-11-01.md is produced by this script.
# Usage:  bash scripts/ops/scoreboard_signals.sh [MAIN_SHA]
# Requires: git, curl, python3. No GitHub token needed (public repo, unauthenticated API).
set -uo pipefail

OWNER="bythewayz66-glitch"
REPO="mem20"
MAIN_SHA="${1:-2ea4492209dfaae6afb22ca884132a0d1849bfcf}"
API="https://api.github.com/repos/${OWNER}/${REPO}"

# Resolve a local ref for main that exists in ANY clone (shallow, single-branch,
# or full). Falls back to the pinned SHA, which is always present once fetched.
MAIN_REF=""
for cand in origin/main main "${MAIN_SHA}"; do
  if git rev-parse --verify --quiet "${cand}^{commit}" >/dev/null 2>&1; then
    MAIN_REF="${cand}"; break
  fi
done
if [ -z "${MAIN_REF}" ]; then
  # Shallow single-branch clone: pull main and the pinned SHA down, then retry.
  git fetch -q --tags origin main 2>/dev/null || true
  git fetch -q origin "${MAIN_SHA}" 2>/dev/null || true
  for cand in origin/main main "${MAIN_SHA}"; do
    if git rev-parse --verify --quiet "${cand}^{commit}" >/dev/null 2>&1; then
      MAIN_REF="${cand}"; break
    fi
  done
fi
if [ -z "${MAIN_REF}" ]; then
  echo "ERROR: no local ref for main; run: git fetch origin main --tags" >&2
  exit 1
fi
# Tags are needed for section 3; fetch them if absent.
if ! git rev-parse --verify --quiet 'v3.1.1^{commit}' >/dev/null 2>&1; then
  git fetch -q --tags origin 2>/dev/null || true
fi

echo "== 0. baseline ==============================================="
echo "main_sha            : ${MAIN_SHA}"
echo "main_ref_resolved   : ${MAIN_REF}"
echo "main_commit_date    : $(git log -1 --format=%ad --date=iso-strict "${MAIN_SHA}")"
echo "main_commit_subject : $(git log -1 --format=%s "${MAIN_SHA}")"
echo "VERSION             : $(git show "${MAIN_SHA}:VERSION" | tr -d '\n')"
echo "tracked_files       : $(git ls-tree -r --name-only "${MAIN_SHA}" | wc -l)"
echo "commits_on_main     : $(git rev-list --count "${MAIN_SHA}")"

echo
echo "== 1. check-run pass rate on main ============================"
# Command: curl -s "$API/commits/$MAIN_SHA/check-runs?per_page=100"
curl -s -H "Accept: application/vnd.github+json" \
  "${API}/commits/${MAIN_SHA}/check-runs?per_page=100" | python3 -c '
import sys, json
from collections import Counter
d = json.load(sys.stdin)
runs = d["check_runs"]
c = Counter(r["conclusion"] for r in runs)
total = d["total_count"]
ok = c.get("success", 0)
fail = c.get("failure", 0)
print(f"total_check_runs    : {total}")
print(f"success             : {ok}")
print(f"failure             : {fail}")
print(f"other               : {total - ok - fail}")
print(f"pass_rate           : {ok}/{total} = {100.0*ok/total:.2f}%")
print("failing_runs        :")
for r in runs:
    if r["conclusion"] != "success":
        name = r["name"]; rid = r["id"]; concl = r["conclusion"]; url = r["html_url"]
        print("  - %s  id=%s  conclusion=%s" % (name, rid, concl))
        print("    %s" % url)
'

echo
echo "== 2. branch count and merge status =========================="
# Command: git ls-remote --heads origin
# Ensure every remote head is present locally so merge-base can resolve it
# (a shallow single-branch clone has none of them).
git fetch -q origin '+refs/heads/*:refs/remotes/origin/*' 2>/dev/null || true
TOTAL_HEADS=$(git ls-remote --heads origin | wc -l)
NON_MAIN=$(git ls-remote --heads origin | awk '{print $2}' | sed 's#refs/heads/##' | grep -vc '^main$')
echo "remote_heads_total  : ${TOTAL_HEADS}"
echo "non_main_heads      : ${NON_MAIN}"
merged=0; unmerged=0
for b in $(git ls-remote --heads origin | awk '{print $2}' | sed 's#refs/heads/##' | grep -v '^main$'); do
  sha=$(git rev-parse "origin/${b}" 2>/dev/null || echo MISSING)
  ahead=$(git rev-list --count "${MAIN_REF}..${sha}" 2>/dev/null || echo "?")
  if git merge-base --is-ancestor "${sha}" "${MAIN_REF}" 2>/dev/null; then
    st=MERGED; merged=$((merged+1))
  else
    st=UNMERGED; unmerged=$((unmerged+1))
  fi
  printf "  %-9s ahead=%-3s %-52s %s\n" "${st}" "${ahead}" "${b}" "${sha}"
done
echo "merged_non_main     : ${merged}"
echo "unmerged_non_main   : ${unmerged}"

echo
echo "== 3. tag distance to main ==================================="
# Command: git rev-list --left-right --count <tag>...origin/main
for t in v3.1.1 v3.1.0 v3.0.0; do
  read -r ahead behind < <(git rev-list --left-right --count "${t}...${MAIN_REF}")
  printf "  %-8s tag_commit=%s  ahead_by=%s  behind_by=%s\n" \
    "${t}" "$(git rev-parse --short=12 "${t}")" "${ahead}" "${behind}"
done
echo "tags_total          : $(git ls-remote --tags origin | grep -v '\^{}' | wc -l)"
echo "tags_archive_prefix : $(git ls-remote --tags origin | grep -v '\^{}' | grep -c 'archive-')"

echo
echo "== 4. PyPI publication status ================================"
# Command: curl -s -o /dev/null -w '%{http_code}' https://pypi.org/pypi/<pkg>/json
for p in mem20 mem20-mcp mem20-sdk; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/${p}/json")
  printf "  %-12s HTTP %s\n" "${p}" "${code}"
done

echo
echo "== 5. open PR / issue count =================================="
# Command: curl -s "$API/pulls?state=open" ; curl -s "$API"
curl -s "${API}/pulls?state=open&per_page=100" | python3 -c 'import sys,json;print("open_prs            :",len(json.load(sys.stdin)))'
curl -s "${API}" | python3 -c 'import sys,json;d=json.load(sys.stdin);print("open_issues_and_prs :",d["open_issues_count"]);print("repo_pushed_at      :",d["pushed_at"])'

echo
echo "== done ======================================================"
