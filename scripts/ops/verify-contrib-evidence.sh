#!/usr/bin/env bash
# verify-contrib-evidence.sh — contribution-evidence gate for bythewayz66-glitch/mem20.
#
# A contribution is a commit on a pushed branch. Nothing else counts. This gate
# reads a pull-request body and fails unless the body carries at least one of:
#
#   (a) a 40-character commit SHA, or
#   (b) a URL that answers HTTP 200.
#
# It is deliberately body-only and network-light: it never inspects the diff, so
# it cannot be satisfied by the change itself, and it never needs a token.
#
# Usage:
#   scripts/ops/verify-contrib-evidence.sh --body-file <path> [--body <text>]
#                                          [--require-sha] [--require-url]
#                                          [--timeout <seconds>] [--json]
#
# Exit codes:
#   0  evidence present (and every required kind present)
#   1  no evidence found, or a required kind missing
#   2  usage error
#
# Environment:
#   CONTRIB_EVIDENCE_TIMEOUT   per-URL curl timeout in seconds (default 10)
#   CONTRIB_EVIDENCE_OFFLINE   when "1", skip the network probe and accept any
#                              well-formed http(s) URL (used by the self-test)

set -euo pipefail

BODY_FILE=""
BODY_TEXT=""
REQUIRE_SHA=0
REQUIRE_URL=0
TIMEOUT="${CONTRIB_EVIDENCE_TIMEOUT:-10}"
JSON=0

usage() {
  sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --body-file) BODY_FILE="${2:-}"; shift 2 ;;
    --body)      BODY_TEXT="${2:-}"; shift 2 ;;
    --require-sha) REQUIRE_SHA=1; shift ;;
    --require-url) REQUIRE_URL=1; shift ;;
    --timeout)   TIMEOUT="${2:-10}"; shift 2 ;;
    --json)      JSON=1; shift ;;
    -h|--help)   usage ;;
    *) echo "unknown argument: $1" >&2; usage ;;
  esac
done

if [ -n "$BODY_FILE" ]; then
  [ -f "$BODY_FILE" ] || { echo "body file not found: $BODY_FILE" >&2; exit 2; }
  BODY_TEXT="$(cat "$BODY_FILE")"
fi

if [ -z "$BODY_TEXT" ] && [ -z "$BODY_FILE" ]; then
  # Fall back to stdin when nothing was supplied on the command line.
  if [ ! -t 0 ]; then
    BODY_TEXT="$(cat)"
  fi
fi

# ---------------------------------------------------------------------------
# 1. 40-character commit SHA
# ---------------------------------------------------------------------------
# A bare 40-hex token, or a github.com/<owner>/<repo>/commit/<sha> URL.
# The lookarounds keep us from matching a 40-hex slice of a longer hex run
# (e.g. a 64-char blob digest) and from matching inside a longer word.
SHA_RE='(^|[^0-9a-fA-F])([0-9a-fA-F]{40})([^0-9a-fA-F]|$)'
SHA_URL_RE='github\.com/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+/commit/([0-9a-fA-F]{40})'

FOUND_SHA=""
if printf '%s' "$BODY_TEXT" | grep -Eq "$SHA_URL_RE"; then
  FOUND_SHA="$(printf '%s' "$BODY_TEXT" | grep -Eo "$SHA_URL_RE" | head -1 | grep -Eo '[0-9a-fA-F]{40}$')"
elif printf '%s' "$BODY_TEXT" | grep -Eq "$SHA_RE"; then
  FOUND_SHA="$(printf '%s' "$BODY_TEXT" | grep -Eo "$SHA_RE" | head -1 | grep -Eo '[0-9a-fA-F]{40}')"
fi

# ---------------------------------------------------------------------------
# 2. A URL that answers HTTP 200
# ---------------------------------------------------------------------------
URL_RE='https?://[^][[:space:]<>"'"'"'`]+'
FOUND_URL=""
FOUND_URL_STATUS=""

probe_url() {
  # $1 = url. Prints the HTTP status code, or 000 on any failure.
  local url="$1" code
  code="$(curl -sS -o /dev/null -w '%{http_code}' \
            --max-time "$TIMEOUT" --retry 1 --retry-delay 1 \
            -L -A 'mem20-contrib-evidence-gate/1.0' \
            "$url" 2>/dev/null || true)"
  printf '%s' "${code:-000}"
}

if [ "${CONTRIB_EVIDENCE_OFFLINE:-0}" = "1" ]; then
  # Offline self-test mode: accept the first well-formed http(s) URL.
  FOUND_URL="$(printf '%s' "$BODY_TEXT" | grep -Eo "$URL_RE" | head -1 || true)"
  [ -n "$FOUND_URL" ] && FOUND_URL_STATUS="200"
else
  while IFS= read -r url; do
    [ -n "$url" ] || continue
    # Strip a trailing punctuation run that is almost never part of a URL.
    url="$(printf '%s' "$url" | sed -E 's/[.,;:!?)]+$//')"
    code="$(probe_url "$url")"
    if [ "$code" = "200" ]; then
      FOUND_URL="$url"
      FOUND_URL_STATUS="$code"
      break
    fi
  done < <(printf '%s' "$BODY_TEXT" | grep -Eo "$URL_RE" || true)
fi

# ---------------------------------------------------------------------------
# 3. Verdict
# ---------------------------------------------------------------------------
ok=1
reasons=()

if [ -n "$FOUND_SHA" ]; then
  reasons+=("40-char commit SHA: $FOUND_SHA")
else
  reasons+=("no 40-character commit SHA in the PR body")
fi

if [ -n "$FOUND_URL" ]; then
  reasons+=("200-verified URL: $FOUND_URL (HTTP $FOUND_URL_STATUS)")
else
  reasons+=("no URL in the PR body answered HTTP 200")
fi

if [ -z "$FOUND_SHA" ] && [ -z "$FOUND_URL" ]; then
  ok=0
fi
if [ "$REQUIRE_SHA" = "1" ] && [ -z "$FOUND_SHA" ]; then ok=0; fi
if [ "$REQUIRE_URL" = "1" ] && [ -z "$FOUND_URL" ]; then ok=0; fi

if [ "$JSON" = "1" ]; then
  printf '{"ok":%s,"sha":"%s","url":"%s","url_status":"%s"}\n' \
    "$([ "$ok" = 1 ] && echo true || echo false)" \
    "$FOUND_SHA" "$FOUND_URL" "$FOUND_URL_STATUS"
else
  echo "contribution-evidence gate"
  echo "--------------------------"
  for r in "${reasons[@]}"; do echo "  - $r"; done
  echo
  if [ "$ok" = 1 ]; then
    echo "PASS: the PR body carries contribution evidence."
  else
    echo "FAIL: the PR body carries neither a 40-character commit SHA nor a 200-verified URL."
    echo "      A contribution is a commit on a pushed branch. Add the branch head SHA"
    echo "      (40 hex chars) or a URL that answers HTTP 200 to the PR body."
  fi
fi

[ "$ok" = 1 ] || exit 1
exit 0
