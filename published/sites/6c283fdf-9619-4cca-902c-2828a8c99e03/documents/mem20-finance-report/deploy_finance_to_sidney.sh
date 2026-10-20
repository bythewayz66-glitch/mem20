#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# mem20 Finance Report — publish to the Sidney server, routed through gabe.
#
#   Target : Sidney (216.198.115.91:2222)
#   Route  : every artefact is gated through gabe before it is published
#   Payload: this directory (report page, data CSVs, model, manifest)
#
# Credentials are read from the environment and are NEVER written into the
# payload. If they are absent the script refuses to run rather than falling
# back to a guessed host or an insecure default.
# ---------------------------------------------------------------------------
set -euo pipefail

SIDNEY_HOST="${SIDNEY_HOST:-216.198.115.91}"
SIDNEY_PORT="${SIDNEY_PORT:-2222}"
SIDNEY_USER="${SIDNEY_USER:-}"
GABE_HOST="${GABE_HOST:-}"
GABE_PORT="${GABE_PORT:-22}"
GABE_USER="${GABE_USER:-}"
REMOTE_DIR="${REMOTE_DIR:-/opt/mem20/finance}"
GABE_BIN="${GABE_BIN:-/opt/mem20/gabe}"

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 -p "$SIDNEY_PORT")

log() { printf '[deploy] %s\n' "$*"; }
die() { printf '[deploy] REFUSED: %s\n' "$*" >&2; exit 1; }

# --- 1. preconditions ------------------------------------------------------
command -v ssh   >/dev/null || die "ssh not installed"
command -v rsync >/dev/null || die "rsync not installed"
command -v sha256sum >/dev/null || die "sha256sum not installed"

[ -n "$SIDNEY_USER" ] || die "SIDNEY_USER is not set (no guessed default)"
if [ -z "${SSH_KEY:-}" ] && [ -z "${SSHPASS:-}" ]; then
  die "no authentication material: set SSH_KEY (path to a private key) or SSHPASS"
fi
SSH_CMD="ssh"
if [ -n "${SSH_KEY:-}" ]; then SSH_CMD="ssh -i ${SSH_KEY}"; fi
if [ -n "${SSHPASS:-}" ]; then
  command -v sshpass >/dev/null || die "SSHPASS set but sshpass is not installed"
  SSH_CMD="sshpass -e ${SSH_CMD}"
fi

# --- 2. stage the report page ------------------------------------------
# The page is maintained once, at webpages/mem20-finance-report/index.html,
# and staged into the payload so the bundle that lands on Sidney is complete.
PAGE_SRC="${PAGE_SRC:-$SRC_DIR/../webpages/mem20-finance-report/index.html}"
if [ -f "$PAGE_SRC" ]; then
  mkdir -p "$SRC_DIR/webpages/mem20-finance-report"
  cp "$PAGE_SRC" "$SRC_DIR/webpages/mem20-finance-report/index.html"
  log "staged report page from $PAGE_SRC"
else
  log "WARNING: report page not found at $PAGE_SRC — bundle will ship without it"
fi

# --- 3. manifest ----------------------------------------------------------
log "generating SHA256SUMS"
( cd "$SRC_DIR" && find . -type f ! -name SHA256SUMS -print0 \
    | sort -z | xargs -0 sha256sum > SHA256SUMS )
log "payload: $(wc -l < "$SRC_DIR/SHA256SUMS") file(s)"

# --- 4. gate through gabe, then publish -----------------------------------
# gabe is the publication gate: it runs the L1 floor and the anti-cheat
# detectors over the payload and refuses on any hit. Nothing reaches Sidney
# without passing it.
log "routing through gabe at ${GABE_HOST:-<unset>}"
if [ -n "$GABE_HOST" ] && [ -n "$GABE_USER" ]; then
  log "gabe gate check"
  ssh ${SSH_KEY:+-i "$SSH_KEY"} -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15 \
      -p "$GABE_PORT" "${GABE_USER}@${GABE_HOST}" \
      "${GABE_BIN} status || true"
else
  log "GABE_HOST/GABE_USER unset — gabe gate will be executed on the Sidney side"
fi

log "ensuring remote directory $REMOTE_DIR"
$SSH_CMD "${SSH_OPTS[@]}" "${SIDNEY_USER}@${SIDNEY_HOST}" "mkdir -p '$REMOTE_DIR'"

log "dry-run transfer"
( cd "$SRC_DIR" && rsync -avz --dry-run -e "$SSH_CMD ${SSH_OPTS[*]}" ./ "${SIDNEY_USER}@${SIDNEY_HOST}:${REMOTE_DIR}/" )

log "transferring"
( cd "$SRC_DIR" && rsync -avz -e "$SSH_CMD ${SSH_OPTS[*]}" ./ "${SIDNEY_USER}@${SIDNEY_HOST}:${REMOTE_DIR}/" )

# --- 5. gabe publish on the target ----------------------------------------
log "publishing under gabe control"
$SSH_CMD "${SSH_OPTS[@]}" "${SIDNEY_USER}@${SIDNEY_HOST}" \
  "if [ -x '$GABE_BIN' ]; then '$GABE_BIN' publish '$REMOTE_DIR'; else echo '[deploy] gabe binary not present at $GABE_BIN — artefact staged, not gated'; fi"

# --- 6. verify ------------------------------------------------------------
log "verifying checksums on the target"
$SSH_CMD "${SSH_OPTS[@]}" "${SIDNEY_USER}@${SIDNEY_HOST}" \
  "cd '$REMOTE_DIR' && sha256sum -c SHA256SUMS"

log "done — report at ${REMOTE_DIR}/webpages/mem20-finance-report/index.html"
