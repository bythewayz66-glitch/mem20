#!/usr/bin/env bash
# =============================================================================
# mem20 distributed sync — deploy to Sidney (and server2) THROUGH gabe
# =============================================================================
# Every hop passes through the jump host `gabe`. The live .db is NEVER copied
# file-level; the only database movement is a `sqlite3 .backup` snapshot taken
# ON the target host, which is the rollback artefact for gate G-3.
#
# Required environment (no secrets are stored in this script):
#   SIDNEY_HOST SIDNEY_PORT SIDNEY_USER
#   SERVER2_HOST SERVER2_PORT SERVER2_USER
#   GABE_HOST GABE_PORT GABE_USER
#   SSH_KEY (path)  OR  SSHPASS (password; used via sshpass -e)
#   REMOTE_DIR   (default /opt/mem20-sync)
#   REMOTE_DB    (default /var/lib/mem20/cognitive.db)
#
# Usage:
#   ./deploy_to_sidney.sh stage      # copy the sync layer to both nodes
#   ./deploy_to_sidney.sh snapshot   # G-1: .backup both DBs, verify they open
#   ./deploy_to_sidney.sh backfill   # Phase 2: synthetic events per legacy row
#   ./deploy_to_sidney.sh verify     # G-3 HARD GATE: compare state_hash on both
#   ./deploy_to_sidney.sh schedule   # install + enable the 15-min timer
#   ./deploy_to_sidney.sh all        # stage -> snapshot -> backfill -> verify -> schedule
#   ./deploy_to_sidney.sh rollback   # restore both DBs from their snapshots
# =============================================================================
set -euo pipefail

REMOTE_DIR="${REMOTE_DIR:-/opt/mem20-sync}"
REMOTE_DB="${REMOTE_DB:-/var/lib/mem20/cognitive.db}"
SNAP_DIR="${SNAP_DIR:-/var/lib/mem20/snapshots}"
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

: "${GABE_HOST:?set GABE_HOST}"
: "${SIDNEY_HOST:?set SIDNEY_HOST}"
: "${SERVER2_HOST:?set SERVER2_HOST}"
GABE_PORT="${GABE_PORT:-22}"; GABE_USER="${GABE_USER:-gabe}"
SIDNEY_PORT="${SIDNEY_PORT:-22}"; SIDNEY_USER="${SIDNEY_USER:-root}"
SERVER2_PORT="${SERVER2_PORT:-22}"; SERVER2_USER="${SERVER2_USER:-root}"

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=20)
if [[ -n "${SSH_KEY:-}" ]]; then SSH_OPTS+=(-i "$SSH_KEY"); fi

# ssh/scp wrappers that always jump through gabe
rsh() {  # rsh <host> <port> <user> <cmd...>
  local host="$1" port="$2" user="$3"; shift 3
  if [[ -n "${SSHPASS:-}" ]]; then
    sshpass -e ssh "${SSH_OPTS[@]}" -J "${GABE_USER}@${GABE_HOST}:${GABE_PORT}" -p "$port" "$user@$host" "$@"
  else
    ssh "${SSH_OPTS[@]}" -J "${GABE_USER}@${GABE_HOST}:${GABE_PORT}" -p "$port" "$user@$host" "$@"
  fi
}
rcp() {  # rcp <host> <port> <user> <local> <remote>
  local host="$1" port="$2" user="$3" local_p="$4" remote_p="$5"
  if [[ -n "${SSHPASS:-}" ]]; then
    sshpass -e scp "${SSH_OPTS[@]}" -o "ProxyJump=${GABE_USER}@${GABE_HOST}:${GABE_PORT}" -P "$port" -r "$local_p" "$user@$host:$remote_p"
  else
    scp "${SSH_OPTS[@]}" -o "ProxyJump=${GABE_USER}@${GABE_HOST}:${GABE_PORT}" -P "$port" -r "$local_p" "$user@$host:$remote_p"
  fi
}

sidney() { rsh "$SIDNEY_HOST" "$SIDNEY_PORT" "$SIDNEY_USER" "$@"; }
server2() { rsh "$SERVER2_HOST" "$SERVER2_PORT" "$SERVER2_USER" "$@"; }

stage() {
  echo "-- staging sync layer to both nodes (through gabe) --"
  for pair in "sidney:$SIDNEY_HOST:$SIDNEY_PORT:$SIDNEY_USER" "server2:$SERVER2_HOST:$SERVER2_PORT:$SERVER2_USER"; do
    IFS=: read -r name host port user <<<"$pair"
    rsh "$host" "$port" "$user" "mkdir -p '$REMOTE_DIR' '$SNAP_DIR'"
    rcp "$host" "$port" "$user" "$LOCAL_DIR/mem20_sync.py" "$REMOTE_DIR/"
    rcp "$host" "$port" "$user" "$LOCAL_DIR/backfill.py" "$REMOTE_DIR/"
    rcp "$host" "$port" "$user" "$LOCAL_DIR/sync_cli.py" "$REMOTE_DIR/"
    rcp "$host" "$port" "$user" "$LOCAL_DIR/acceptance_suite.py" "$REMOTE_DIR/"
    rsh "$host" "$port" "$user" "chmod 755 '$REMOTE_DIR'/*.py && ls -la '$REMOTE_DIR'"
    echo "   staged on $name"
  done
}

snapshot() {
  echo "-- G-1: .backup both DBs (never cp) and confirm they open --"
  for pair in "sidney:$SIDNEY_HOST:$SIDNEY_PORT:$SIDNEY_USER" "server2:$SERVER2_HOST:$SERVER2_PORT:$SERVER2_USER"; do
    IFS=: read -r name host port user <<<"$pair"
    rsh "$host" "$port" "$user" \
      "mkdir -p '$SNAP_DIR' && \
       SNAP='$SNAP_DIR/cognitive.db.$name.\$(date -u +%Y%m%dT%H%M%SZ).bak' && \
       sqlite3 '$REMOTE_DB' \".backup '\$SNAP'\" && \
       sqlite3 '\$SNAP' 'PRAGMA integrity_check;' && \
       echo \"snapshot=\$SNAP\""
    echo "   $name snapshot OK"
  done
}

backfill() {
  echo "-- Phase 2: backfill one synthetic upsert per legacy row, per node --"
  sidney "cd '$REMOTE_DIR' && python3 backfill.py --db '$REMOTE_DB' --node sidney --snapshot-dir '$SNAP_DIR'"
  server2 "cd '$REMOTE_DIR' && python3 backfill.py --db '$REMOTE_DB' --node server2 --snapshot-dir '$SNAP_DIR'"
}

verify() {
  echo "-- G-3 HARD GATE: state_hash must be byte-identical on both nodes --"
  # one anti-entropy round, then compare
  sidney "cd '$REMOTE_DIR' && python3 sync_cli.py --db '$REMOTE_DB' --node sidney sync" || true
  HA="$(sidney "cd '$REMOTE_DIR' && python3 sync_cli.py --db '$REMOTE_DB' --node sidney state-hash")"
  HB="$(server2 "cd '$REMOTE_DIR' && python3 sync_cli.py --db '$REMOTE_DB' --node server2 state-hash")"
  echo "   sidney  : $HA"
  echo "   server2 : $HB"
  if [[ "$HA" == "$HB" && -n "$HA" ]]; then
    echo "   G-3 PASS — snapshots may now be archived (keep 30 days per R8)."
    return 0
  fi
  echo "   G-3 FAIL — DO NOT archive snapshots. One debug pass allowed, then roll back." >&2
  return 1
}

schedule() {
  echo "-- installing the 15-minute systemd timer on both nodes --"
  for pair in "sidney:$SIDNEY_HOST:$SIDNEY_PORT:$SIDNEY_USER" "server2:$SERVER2_HOST:$SERVER2_PORT:$SERVER2_USER"; do
    IFS=: read -r name host port user <<<"$pair"
    rcp "$host" "$port" "$user" "$LOCAL_DIR/systemd/mem20-sync.service" "/etc/systemd/system/mem20-sync.service"
    rcp "$host" "$port" "$user" "$LOCAL_DIR/systemd/mem20-sync.timer" "/etc/systemd/system/mem20-sync.timer"
    rsh "$host" "$port" "$user" \
      "mkdir -p /etc/mem20-sync && \
       [ -f /etc/mem20-sync/mem20-sync.env ] || { echo 'FILL /etc/mem20-sync/mem20-sync.env first (see config/mem20-sync.env.example)'; exit 3; } && \
       chmod 600 /etc/mem20-sync/mem20-sync.env && \
       systemctl daemon-reload && \
       systemctl enable --now mem20-sync.timer && \
       systemctl start mem20-sync.service && \
       systemctl is-enabled mem20-sync.timer && \
       journalctl -u mem20-sync.service -n 20 --no-pager"
    echo "   $name timer enabled"
  done
}

rollback() {
  echo "-- ROLLBACK: restore both DBs from their most recent snapshot --"
  for pair in "sidney:$SIDNEY_HOST:$SIDNEY_PORT:$SIDNEY_USER" "server2:$SERVER2_HOST:$SERVER2_PORT:$SERVER2_USER"; do
    IFS=: read -r name host port user <<<"$pair"
    rsh "$host" "$port" "$user" \
      "SNAP=\$(ls -1t '$SNAP_DIR'/cognitive.db.$name.*.bak | head -1) && \
       echo \"restoring \$SNAP -> '$REMOTE_DB'\" && \
       systemctl stop mem20-sync.timer 2>/dev/null || true; \
       sqlite3 '$REMOTE_DB' \".restore '\$SNAP'\" && \
       sqlite3 '$REMOTE_DB' 'PRAGMA integrity_check;'"
    echo "   $name restored"
  done
}

case "${1:-all}" in
  stage) stage ;;
  snapshot) snapshot ;;
  backfill) backfill ;;
  verify) verify ;;
  schedule) schedule ;;
  rollback) rollback ;;
  all) stage; snapshot; backfill; verify; schedule ;;
  *) echo "usage: $0 {stage|snapshot|backfill|verify|schedule|all|rollback}" >&2; exit 2 ;;
esac
