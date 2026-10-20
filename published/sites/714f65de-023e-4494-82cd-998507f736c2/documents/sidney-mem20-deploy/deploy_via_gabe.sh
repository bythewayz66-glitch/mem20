#!/usr/bin/env bash
# deploy_via_gabe.sh — stage the mem20 payload to sidney and hand the commit to gabe.
#
# Does NOT push straight into the live tree: GABE_SPEC.md §8 requires that no code
# reaches sidney except through Gabe (G1 / G10 / G11). This script stages only.
#
# Usage:
#   export SIDNEY_HOST=216.198.115.91
#   export SIDNEY_PORT=2222
#   export SIDNEY_USER=root
#   export SSHPASS='...'          # password auth, OR leave unset to use a key
#   ./deploy_via_gabe.sh /workspace/mem20_clone
set -euo pipefail

CLONE="${1:-/workspace/mem20_clone}"
HOST="${SIDNEY_HOST:-216.198.115.91}"
PORT="${SIDNEY_PORT:-2222}"
USER="${SIDNEY_USER:-root}"
STAGE="${SIDNEY_STAGE:-/tmp/gabe-ingress}"
EXPECTED_SHA="ac645714ee2120a93d4669044e519c6889aee231b9e79876a857a4f315226680"
TARBALL="mem20-c274404.tar.gz"

SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=12 -p "$PORT")

say() { printf '\n[deploy] %s\n' "$*"; }

# --- 0. credential check -----------------------------------------------------
if [ -z "${SSHPASS:-}" ] && [ ! -f "$HOME/.ssh/id_ed25519" ] && [ ! -f "$HOME/.ssh/id_rsa" ]; then
  echo "[deploy] FATAL: no password (SSHPASS) and no SSH key found." >&2
  echo "[deploy] Provide one; see DEPLOY_RUNBOOK.md." >&2
  exit 2
fi

run_ssh() {
  if [ -n "${SSHPASS:-}" ]; then
    command -v sshpass >/dev/null || { echo "[deploy] sshpass not installed" >&2; exit 2; }
    timeout 300 sshpass -e ssh "${SSH_OPTS[@]}" "$USER@$HOST" "$@"
  else
    timeout 300 ssh "${SSH_OPTS[@]}" "$USER@$HOST" "$@"
  fi
}

run_scp_rsync() {
  # $@ = rsync args after the -e
  local RSYNC_SSH="ssh -p $PORT -o StrictHostKeyChecking=accept-new -o ConnectTimeout=12"
  if [ -n "${SSHPASS:-}" ]; then
    timeout 900 sshpass -e rsync -e "$RSYNC_SSH" "$@"
  else
    timeout 900 rsync -e "$RSYNC_SSH" "$@"
  fi
}

# --- 1. verify the local clone ----------------------------------------------
say "verifying local clone"
cd "$CLONE"
HEAD_SHA=$(git rev-parse HEAD)
[ "$HEAD_SHA" = "c274404a116f203b0ed99ab7156e3752f0953ea8" ] \
  || { echo "[deploy] FATAL: HEAD is $HEAD_SHA, expected c274404a..." >&2; exit 2; }
echo "[deploy] HEAD ok: $HEAD_SHA"

# --- 2. build the payload ---------------------------------------------------
say "building payload"
tar czf "/tmp/$TARBALL" --exclude=.git .
GOT_SHA=$(sha256sum "/tmp/$TARBALL" | cut -d' ' -f1)
[ "$GOT_SHA" = "$EXPECTED_SHA" ] || echo "[deploy] NOTE: payload sha256 $GOT_SHA differs from recorded $EXPECTED_SHA (repo may have changed)"
echo "[deploy] payload sha256=$GOT_SHA bytes=$(stat -c%s "/tmp/$TARBALL")"

# --- 3. stage (NOT the live tree) -------------------------------------------
say "staging to $USER@$HOST:$STAGE"
run_ssh "mkdir -p '$STAGE'"
run_scp_rsync --partial --inplace "/tmp/$TARBALL" "$USER@$HOST:$STAGE/"

# --- 4. verify the payload landed intact ------------------------------------
say "verifying staged payload"
REMOTE_SHA=$(run_ssh "sha256sum '$STAGE/$TARBALL' | cut -d' ' -f1")
if [ "$REMOTE_SHA" != "$GOT_SHA" ]; then
  echo "[deploy] FATAL: remote sha256 $REMOTE_SHA != local $GOT_SHA — transfer corrupted" >&2
  exit 3
fi
echo "[deploy] staged payload verified: $REMOTE_SHA"

# --- 5. recon before touching anything --------------------------------------
say "recon"
run_ssh 'uname -a; cat /etc/os-release | head -3; df -h / | tail -1; python3 --version; ls -d /opt/mem20 /opt/mem20/gabe 2>/dev/null; systemctl is-active mem20 2>/dev/null || true'

cat <<'EOF'

[deploy] STAGED. The commit into the live surface is gabe's call, not this script's:

    /opt/mem20/gabe/bin/gabe publish --producer mem20 \
        --artifact /tmp/gabe-ingress/mem20-c274404.tar.gz
    /opt/mem20/gabe/bin/gabe status

[deploy] Then build/verify: see DEPLOY_RUNBOOK.md steps 3-4.
EOF
