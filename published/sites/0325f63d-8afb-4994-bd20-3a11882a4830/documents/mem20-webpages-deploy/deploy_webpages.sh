#!/usr/bin/env bash
# Publish the mem20 v2 webpages to the Sidney server via rsync-over-ssh,
# routed through the 'gabe' jump host.
#
# Requires (export before running):
#   SIDNEY_HOST  SIDNEY_PORT(22)  SIDNEY_USER
#   GABE_HOST    GABE_PORT(22)    GABE_USER        # jump host — all traffic goes through gabe
#   SIDNEY_SSH_KEY (path to key)  OR  SSHPASS      # auth
#   REMOTE_WEBROOT (e.g. /var/www/mem20)
#
# Usage:  bash deploy_webpages.sh
set -euo pipefail

: "${SIDNEY_HOST:?set SIDNEY_HOST}"
: "${SIDNEY_USER:?set SIDNEY_USER}"
: "${GABE_HOST:?set GABE_HOST}"
: "${GABE_USER:?set GABE_USER}"
: "${REMOTE_WEBROOT:?set REMOTE_WEBROOT}"

SIDNEY_PORT="${SIDNEY_PORT:-22}"
GABE_PORT="${GABE_PORT:-22}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$HERE/payload"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
JUMP="-J ${GABE_USER}@${GABE_HOST}:${GABE_PORT}"
if [ -n "${SIDNEY_SSH_KEY:-}" ]; then
  SSH_OPTS+=(-i "$SIDNEY_SSH_KEY")
fi

# Optional password auth via sshpass
if [ -n "${SSHPASS:-}" ]; then
  command -v sshpass >/dev/null || { echo "sshpass not installed; use a key instead"; exit 1; }
  SSH_WRAP="sshpass -e ssh"
else
  SSH_WRAP="ssh"
fi

echo "==> Routing through gabe: ${GABE_USER}@${GABE_HOST}:${GABE_PORT}"
echo "==> Target:             ${SIDNEY_USER}@${SIDNEY_HOST}:${SIDNEY_PORT}  → ${REMOTE_WEBROOT}"

# 0. Sanity: reach Sidney through gabe
${SSH_WRAP} "${SSH_OPTS[@]}" "$JUMP" -p "$SIDNEY_PORT" \
  "${SIDNEY_USER}@${SIDNEY_HOST}" 'echo "reachable as $(whoami)@$(hostname)"'

# 1. Ensure remote dirs exist
${SSH_WRAP} "${SSH_OPTS[@]}" "$JUMP" -p "$SIDNEY_PORT" \
  "${SIDNEY_USER}@${SIDNEY_HOST}" \
  "mkdir -p '${REMOTE_WEBROOT}/webpages/mem20-launch' '${REMOTE_WEBROOT}/webpages/mem20-launch-dashboard'"

# 2. Rsync the payload through gabe
RSYNC_RSH="${SSH_WRAP} ${SSH_OPTS[*]} $JUMP -p $SIDNEY_PORT"
rsync -avz --no-perms --omit-dir-times -e "$RSYNC_RSH" \
  "$PAYLOAD/webpages/mem20-launch/"          "${SIDNEY_USER}@${SIDNEY_HOST}:${REMOTE_WEBROOT}/webpages/mem20-launch/" \
  "$PAYLOAD/webpages/mem20-launch-dashboard/" "${SIDNEY_USER}@${SIDNEY_HOST}:${REMOTE_WEBROOT}/webpages/mem20-launch-dashboard/"

# 3. Verify: new repo present, old repo gone
echo "==> Verifying on Sidney"
${SSH_WRAP} "${SSH_OPTS[@]}" "$JUMP" -p "$SIDNEY_PORT" \
  "${SIDNEY_USER}@${SIDNEY_HOST}" bash -s <<EOF
set -e
cd "${REMOTE_WEBROOT}/webpages"
echo "--- files ---"; ls -l mem20-launch/index.html mem20-launch-dashboard/index.html
echo "--- new repo refs ---"; grep -c bythewayz66-glitch mem20-launch/index.html mem20-launch-dashboard/index.html || true
echo "--- stale old-repo refs (expect 0) ---"; grep -rc JaysonAIOnline mem20-launch/index.html mem20-launch-dashboard/index.html || echo 0
EOF

echo "==> Done. Both pages published with bythewayz66-glitch/mem20, routed through gabe."
