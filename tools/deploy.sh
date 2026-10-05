#!/usr/bin/env bash
# Deploy the working tree to the Pi and restart the service — so Mac and Pi run
# the SAME version. Stamps the git commit on the Pi (DEPLOYED_VERSION) and checks
# it matches the Mac. Runs a quick test sweep on the Pi before the restart.
#
#   tools/deploy.sh                 # → pi@discopi.local
#   tools/deploy.sh pi@192.168.68.66
#
# The vehicle pack is a separate repo (ADR-0015). PACK_DIR (default: a sibling
# ../discovery2-diag checkout) is mirrored to ${DEST}-pack and pip-installed there in
# editable mode (--no-deps), so the platform finds it through its entry point.
set -euo pipefail
PI="${1:-pi@discopi.local}"
DEST="/home/pi/discovery2-diag"
cd "$(dirname "$0")/.."
PACK_DIR="${PACK_DIR:-../discovery2-diag}"

commit="$(git rev-parse --short HEAD 2>/dev/null || echo nogit)"
dirty=""
if ! git diff --quiet 2>/dev/null || ! git diff --cached --quiet 2>/dev/null; then
  dirty="+dirty"
fi
stamp="${commit}${dirty}"
echo "→ deploying ${stamp} to ${PI}:${DEST}"
[ -n "$dirty" ] && echo "  ⚠ UNCOMMITTED changes are being deployed — commit for a clean version"

# --delete on src so removed modules disappear on the Pi too (exact mirror).
rsync -az --delete src/ "${PI}:${DEST}/src/"
rsync -az tools/ "${PI}:${DEST}/tools/"
rsync -az tests/ "${PI}:${DEST}/tests/"
rsync -az pyproject.toml "${PI}:${DEST}/pyproject.toml" 2>/dev/null || true
if [ -f "${PACK_DIR}/pyproject.toml" ]; then
  echo "→ vehicle pack from ${PACK_DIR}"
  rsync -az --delete --exclude .git --exclude logs "${PACK_DIR}/" "${PI}:${DEST}-pack/"
  ssh "$PI" "python3 -m pip install --user --no-deps -q -e ${DEST}-pack"
else
  echo "  ⚠ no vehicle pack at ${PACK_DIR} (set PACK_DIR) — the Pi keeps the one it has"
fi

# Test on the Pi → stamp the version → restart the service.
ssh "$PI" "set -e
  cd ${DEST}
  OSTLER_REQUIRE_PACK=1 python3 -m pytest tests/test_web.py tests/test_transport.py -q 2>&1 | tail -3
  [ \${PIPESTATUS[0]} -eq 0 ] || { echo 'TESTS RED on the Pi — aborting deploy (no restart)'; exit 1; }
  echo '${stamp}' > DEPLOYED_VERSION
  sudo systemctl restart openostler.service
  sleep 3
  echo \"Pi: \$(cat DEPLOYED_VERSION) · service \$(systemctl is-active openostler.service)\""

remote="$(ssh "$PI" cat "${DEST}/DEPLOYED_VERSION" 2>/dev/null || echo '?')"
if [ "$remote" = "$stamp" ]; then
  echo "✓ Mac ${stamp} = Pi ${remote}"
else
  echo "✗ VERSIONS DIFFER: Mac ${stamp} ≠ Pi ${remote}"; exit 1
fi
