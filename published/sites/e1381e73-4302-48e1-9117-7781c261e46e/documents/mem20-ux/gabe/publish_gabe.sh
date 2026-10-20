#!/usr/bin/env bash
# mem20 UX lane — gabe publish on Sidney.
#
# Sidney credentials are the only blocker: this runs the whole publish in one
# command as soon as a working credential is supplied.
#
#   SIDNEY_PASS='<password>' ./publish_gabe.sh
#   SIDNEY_KEY=~/.ssh/sidney_ed25519 ./publish_gabe.sh
#
# Exit codes: 0 published (pass verdict), 2 credential refused, 3 gabe refused,
#             4 could not land the bundle.
set -uo pipefail

HOST="${SIDNEY_HOST:-216.198.115.91}"
PORT="${SIDNEY_PORT:-2222}"
USER_="${SIDNEY_USER:-root}"
LEG="ux"
LANDING="/opt/mem20/${LEG}-landing"
STAGING="/opt/mem20/staging/payload"

here="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -n "${SIDNEY_KEY:-}" ]]; then
  AUTH=(-i "$SIDNEY_KEY")
elif [[ -n "${SIDNEY_PASS:-}" ]]; then
  export SSHPASS="$SIDNEY_PASS"
  AUTH=(-o PreferredAuthentications=password -o PubkeyAuthentication=no)
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "sshpass is required for password auth" >&2; exit 4
  fi
  SSH=(sshpass -e)
else
  echo "set SIDNEY_PASS or SIDNEY_KEY" >&2; exit 4
fi

SSH_OPTS=(-p "$PORT" -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
          -o ConnectTimeout=15 -o NumberOfPasswordPrompts=1 "${AUTH[@]}")

remote() { timeout 60 "${SSH[@]}" ssh "${SSH_OPTS[@]}" "${USER_}@${HOST}" "$@" </dev/null; }

echo "== 1. connectivity and gate presence =="
if ! remote 'echo LOGIN_OK; test -x /opt/mem20/gabe/bin/gabe && echo GATE_PRESENT'; then
  echo "REFUSED: Sidney credential rejected or unreachable" >&2
  exit 2
fi

echo "== 2. land the bundle in a private scratch dir =="
timeout 120 tar -C "$here" -cf - \
  gabe/mem20_ux_artifact.py gabe/mem20_ux_requirement.txt \
  gabe/evidence/evidence.txt memory_surface.json prototype.html \
  | timeout 120 "${SSH[@]}" ssh "${SSH_OPTS[@]}" "${USER_}@${HOST}" \
      "mkdir -p ${LANDING}/gabe/evidence && tar -C ${LANDING} -xf - && ls -la ${LANDING}" </dev/null || {
  echo "REFUSED: bundle did not land" >&2; exit 4; }

echo "== 3. publish, re-copying staging inside the same command =="
# The staging area is shared between producers, so staging is refreshed here
# immediately before the publish call rather than earlier.
remote "set -e
  mkdir -p ${STAGING}
  cp -r ${LANDING}/. ${STAGING}/
  cd /opt/mem20/gabe
  export GABE_ROOT=/opt/mem20/gabe
  export GABE_LIVE_ROOT=/opt/mem20/live
  /usr/bin/python3.14 bin/gabe publish ${LANDING}/prototype.html \\
    --requirement ${LANDING}/gabe/mem20_ux_requirement.txt \\
    --producer ux-researcher \\
    --producer-session mem20-ux-\$(date -u +%Y%m%dT%H%M%SZ) \\
    --claims 'ranked memory surface with 49 of 257 tools grouped and ranked=prototype.html' \\
    --evidence ${LANDING}/gabe/evidence/evidence.txt
  echo PUBLISH_RC=\$?
"
rc=$?

echo "== 4. independent confirmation =="
remote "cd /opt/mem20/gabe && /usr/bin/python3.14 bin/gabe status; ls -la /opt/mem20/live/prototype.html" || true

[[ $rc -eq 0 ]] || exit 3
echo "published"
