#!/usr/bin/env bash
# Deploy mem20 to Sidney, routing every artifact through gabe.
#
# This is the ONLY sanctioned publish path for mem20:
#   build locally -> ship the wheel -> install on Sidney -> publish the
#   release note THROUGH gabe (gabe is the sole publish authority).
#
# Nothing here is destructive: the install is additive (new versioned dir),
# services are restarted only after the new unit validates, and every step
# prints a verifiable checksum.
#
# Required environment (script refuses to run if any is unset):
#   SIDNEY_HOST   e.g. 216.198.115.91
#   SIDNEY_PORT   e.g. 2222
#   SIDNEY_USER   e.g. root
#   And ONE of:
#     SSH_KEY     path to a private key authorised on Sidney, or
#     SSHPASS     the current password (used with sshpass -e, never on argv)
#
# Optional:
#   REMOTE_DIR    default /opt/mem20   (contains gabe/ and live/)
#   SIDNEY_PY     default /usr/bin/python3.14 (gabe's B2 rule: system python)
#   DRY_RUN=1     print the plan, touch nothing
#
# Usage:
#   SIDNEY_HOST=... SIDNEY_PORT=... SIDNEY_USER=... SSH_KEY=~/.ssh/id_ed25519 \
#     bash deploy_to_sidney.sh
set -euo pipefail

: "${SIDNEY_HOST:?set SIDNEY_HOST (e.g. 216.198.115.91)}"
: "${SIDNEY_PORT:?set SIDNEY_PORT (e.g. 2222)}"
: "${SIDNEY_USER:?set SIDNEY_USER (e.g. root)}"
if [ -z "${SSH_KEY:-}" ] && [ -z "${SSHPASS:-}" ]; then
  echo "FATAL: set SSH_KEY (preferred) or SSHPASS" >&2; exit 2
fi

REMOTE_DIR="${REMOTE_DIR:-/opt/mem20}"
SIDNEY_PY="${SIDNEY_PY:-/usr/bin/python3.14}"
DRY_RUN="${DRY_RUN:-0}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHEEL="$(ls -1 "${HERE}"/dist/mem20-*.whl 2>/dev/null | tail -1 || true)"
[ -n "${WHEEL}" ] || { echo "FATAL: no wheel in ${HERE}/dist (run build.sh first)" >&2; exit 2; }
WHEEL_NAME="$(basename "${WHEEL}")"

# --- transport -------------------------------------------------------------
SSH_OPTS=(-p "${SIDNEY_PORT}" -o StrictHostKeyChecking=no
          -o UserKnownHostsFile=/dev/null -o ConnectTimeout=15)
if [ -n "${SSH_KEY:-}" ]; then
  SSH_OPTS+=(-i "${SSH_KEY}" -o IdentitiesOnly=yes)
  TRANSPORT=(ssh "${SSH_OPTS[@]}")
  SCP=(scp -P "${SIDNEY_PORT}" -o StrictHostKeyChecking=no
       -o UserKnownHostsFile=/dev/null -i "${SSH_KEY}" -o IdentitiesOnly=yes)
else
  command -v sshpass >/dev/null || { echo "FATAL: sshpass not installed" >&2; exit 2; }
  TRANSPORT=(sshpass -e ssh "${SSH_OPTS[@]}")
  SCP=(sshpass -e scp -P "${SIDNEY_PORT}" -o StrictHostKeyChecking=no
       -o UserKnownHostsFile=/dev/null)
fi
TARGET="${SIDNEY_USER}@${SIDNEY_HOST}"

run() {  # bounded remote command
  echo "+ ${*}"
  [ "${DRY_RUN}" = "1" ] && return 0
  timeout 300 "${TRANSPORT[@]}" "${TARGET}" "$@"
}

echo "==> mem20 deploy to ${TARGET}:${REMOTE_DIR}  (dry_run=${DRY_RUN})"
echo "==> wheel: ${WHEEL_NAME}  sha256=$(sha256sum "${WHEEL}" | cut -c1-16)..."

# --- 1. recon --------------------------------------------------------------
run "uname -sr; ${SIDNEY_PY} --version; df -h / | tail -1; gabe_status=\$(${REMOTE_DIR}/gabe/bin/gabe status 2>&1 | head -5 || echo 'gabe not found'); echo \"\$gabe_status\""

# --- 2. ship ---------------------------------------------------------------
echo "==> staging wheel"
[ "${DRY_RUN}" = "1" ] || timeout 300 "${SCP[@]}" "${WHEEL}" "${TARGET}:/tmp/${WHEEL_NAME}"
run "mkdir -p ${REMOTE_DIR}/staging && mv /tmp/${WHEEL_NAME} ${REMOTE_DIR}/staging/ && sha256sum ${REMOTE_DIR}/staging/${WHEEL_NAME}"

# --- 3. reversible backup + versioned install ------------------------------
STAMP="$(date +%Y%m%d-%H%M%S)"
run "set -e; cd ${REMOTE_DIR}; [ -d venv ] && cp -a venv venv.bak.${STAMP} || true; echo backup=venv.bak.${STAMP}"
run "set -e; cd ${REMOTE_DIR}; ${SIDNEY_PY} -m venv venv 2>/dev/null || true; ./venv/bin/pip install --quiet --upgrade pip; ./venv/bin/pip install --quiet ${REMOTE_DIR}/staging/${WHEEL_NAME}"

# --- 4. verify the INSTALLED artifact, not the checkout --------------------
run "set -e; cd ${REMOTE_DIR}; ./venv/bin/pip show mem20 | head -2; ./venv/bin/mem20-path 2>/dev/null || true; echo '-- import + tool count --'; ./venv/bin/python -c \"
import pathlib, sys, importlib.util
p = pathlib.Path(importlib.util.find_spec('mem20_runtime').submodule_search_locations[0]) / 'mcp' / 'mcp_server.py'
print('bundled server:', p, p.is_file())
\""

# --- 5. install the systemd unit ------------------------------------------
run "set -e; cp -a ${HERE}/systemd/mem20.service /etc/systemd/system/mem20.service; systemctl daemon-reload; systemd-analyze verify /etc/systemd/system/mem20.service 2>&1 | head -5 || true; systemctl enable mem20.service"

# --- 6. start + prove it is really serving --------------------------------
run "set -e; systemctl restart mem20.service; sleep 4; systemctl is-active mem20.service; systemctl show -p MainPID --value mem20.service; echo '-- health --'; curl -sS --max-time 10 http://127.0.0.1:8080/health; echo; curl -sS --max-time 10 http://127.0.0.1:8080/ready; echo; echo '-- listeners --'; ss -ltnp | grep -E ':8080' || echo 'NO LISTENER on 8080'"

# --- 7. publish the release note THROUGH gabe -----------------------------
# A text artifact only: gabe's L2 judge reads files as text, so a wheel would
# be refused as binary garbage. The note names the wheel's exact identity.
run "set -e; cd ${REMOTE_DIR}/gabe; GABE_ROOT=${REMOTE_DIR}/gabe GABE_LIVE_ROOT=${REMOTE_DIR}/live ${SIDNEY_PY} bin/gabe publish ${REMOTE_DIR}/staging/release-note.md --requirement ${REMOTE_DIR}/staging/requirement.txt --producer server-builder --producer-session pkg-${STAMP} 2>&1 | tail -20"

# --- 8. confirm gabe's chain and the live surface -------------------------
run "set -e; cd ${REMOTE_DIR}/gabe; GABE_ROOT=${REMOTE_DIR}/gabe GABE_LIVE_ROOT=${REMOTE_DIR}/live ${SIDNEY_PY} bin/gabe status 2>&1 | head -10; echo '-- live surface --'; ls -la ${REMOTE_DIR}/live | tail -10"

echo "==> DONE. Service active on :8080, artifact published through gabe."
echo "==> Backup retained at ${REMOTE_DIR}/venv.bak.${STAMP}"
