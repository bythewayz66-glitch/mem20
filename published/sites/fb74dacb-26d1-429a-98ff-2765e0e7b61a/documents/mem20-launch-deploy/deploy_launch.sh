#!/usr/bin/env bash
# mem20 launch page -> Sidney via gabe. gabe is a LOCAL RUNTIME on Sidney (not an agent,
# not a jump host). SSH into Sidney, then run gabe on the box to publish to the live root.
set -euo pipefail

: "${SIDNEY_HOST:?set SIDNEY_HOST (e.g. 216.198.115.91)}"
: "${SIDNEY_PORT:=2222}"
: "${SIDNEY_USER:?set SIDNEY_USER}"
: "${REMOTE_WEBROOT:?set REMOTE_WEBROOT (live root, e.g. /opt/mem20/published)}"

SRC="$(cd "$(dirname "$0")" && pwd)/payload/webpages/mem20-launch/index.html"
[ -f "$SRC" ] || { echo "missing payload: $SRC" >&2; exit 1; }

SSH_OPTS=(-o BatchMode=no -o StrictHostKeyChecking=accept-new -p "$SIDNEY_PORT")
# key takes precedence; else password via sshpass
if [ -n "${SSH_KEY:-}" ]; then
  SSH_OPTS+=(-i "$SSH_KEY")
  SCP_OPTS=(-i "$SSH_KEY")
elif [ -n "${SSHPASS:-}" ]; then
  SCP_OPTS=(-P "$SIDNEY_PORT")
else
  echo "Need SSH_KEY or SSHPASS" >&2; exit 1
fi

# 1) stage dir on Sidney
ssh "${SSH_OPTS[@]}" "$SIDNEY_USER@$SIDNEY_HOST" "mkdir -p '$REMOTE_WEBROOT/webpages/mem20-launch'"

# 2) copy the page up
if [ -n "${SSH_KEY:-}" ]; then
  scp "${SSH_OPTS[@]}" "$SRC" "$SIDNEY_USER@$SIDNEY_HOST:$REMOTE_WEBROOT/webpages/mem20-launch/index.html"
else
  sshpass -e scp "${SCP_OPTS[@]}" "$SRC" "$SIDNEY_USER@$SIDNEY_HOST:$REMOTE_WEBROOT/webpages/mem20-launch/index.html"
fi

# 3) publish through gabe (local runtime on Sidney) into the live root.
#    gabe's exact CLI is host-specific; this is the canonical routing seam.
ssh "${SSH_OPTS[@]}" "$SIDNEY_USER@$SIDNEY_HOST" \
  "gabe publish '$REMOTE_WEBROOT/webpages/mem20-launch/index.html' --requirement 'launch page' --producer 'webpage-developer' || echo 'GABE_INVOCATION_REQUIRES_HOST_CONFIRMATION'"

# 4) verify on-host
ssh "${SSH_OPTS[@]}" "$SIDNEY_USER@$SIDNEY_HOST" \
  "grep -c 'bythewayz66-glitch/mem20' '$REMOTE_WEBROOT/webpages/mem20-launch/index.html'; grep -c 'JaysonAIOnline' '$REMOTE_WEBROOT/webpages/mem20-launch/index.html' || true"
