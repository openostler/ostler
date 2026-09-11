#!/bin/bash
# Discovery 2 diagnostics — one-paste Mac installer for non-technical testers.
#
# The tester pastes ONE line into Terminal:
#   curl -fsSL https://raw.githubusercontent.com/Leijoma/discovery2-diag/main/mac/install.sh | bash
# and after that never touches Terminal again — this drops double-clickable
# launchers on the Desktop. No virtualenv, no `pip` (uses `python3 -m pip --user`),
# no `source`/activate — all the steps a novice trips over are removed.
#
# Safe to re-run: it updates an existing checkout instead of failing.
set -e

REPO_URL="https://github.com/Leijoma/discovery2-diag.git"
DEST="$HOME/discovery2-diag"
DESKTOP="$HOME/Desktop"

say()  { printf "\n\033[1m%s\033[0m\n" "$1"; }
ok()   { printf "  \033[32m✓\033[0m %s\n" "$1"; }
warn() { printf "  \033[33m!\033[0m %s\n" "$1"; }

say "Discovery 2 diagnostics — setting up…"

# 1. Python 3 ----------------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1; then
  warn "Python 3 is not installed."
  echo "     Open https://www.python.org/downloads/ , install Python 3,"
  echo "     then run this again. (Click 'macOS 64-bit universal2 installer'.)"
  exit 1
fi
ok "Python 3 found ($(python3 --version 2>&1))"

# 2. Dependencies (no virtualenv — installed into the user's own Python) -----
python3 -m pip install --user --upgrade pip >/dev/null 2>&1 || true
if python3 -m pip install --user --quiet pyserial pytest; then
  ok "Installed pyserial + pytest"
else
  warn "Could not install dependencies automatically."
  echo "     Try once in Terminal:  python3 -m pip install --user pyserial pytest"
  exit 1
fi

# 3. Get / update the code ---------------------------------------------------
if [ -d "$DEST/.git" ]; then
  git -C "$DEST" pull --quiet --ff-only 2>/dev/null || true
  ok "Updated the code in $DEST"
elif command -v git >/dev/null 2>&1; then
  git clone --quiet "$REPO_URL" "$DEST"
  ok "Downloaded the code to $DEST"
else
  warn "git is not installed — opening the Xcode command-line tools installer."
  echo "     Click 'Install', wait for it to finish, then run this again."
  xcode-select --install 2>/dev/null || true
  exit 1
fi

# 4. Double-clickable Desktop launchers --------------------------------------
# Each launcher just cd's into the repo and runs one tool with PYTHONPATH=src,
# so the tester never types anything.
make_launcher() {
  local file="$DESKTOP/$1"
  printf '#!/bin/bash\ncd "%s" || exit 1\n%s\n' "$DEST" "$2" > "$file"
  chmod +x "$file"
  ok "Created: Desktop ▸ $1"
}

make_launcher "1 TEST WITHOUT CAR.command" \
'echo "Starting the test dashboard (no car needed)…"
echo "A browser window will open. Close this black window to stop."
( sleep 3 ; open http://localhost:8080 ) &
PYTHONPATH=src python3 tools/dashboard.py --mock'

make_launcher "2 READ THE CAR.command" \
'echo "Make sure: cable in the car’s OBD socket + USB in the Mac, ignition ON, car stationary."
echo "A browser window will open with live data. Close this black window to stop."
( sleep 3 ; open http://localhost:8080 ) &
PYTHONPATH=src python3 tools/dashboard.py --serial auto'

make_launcher "3 QUICK FAULT CHECK.command" \
'echo "Reading the engine ECU once (read-only). Cable in car + USB in Mac, ignition ON."
echo ""
PYTHONPATH=src python3 tools/verify_ecu.py td5 auto
echo ""
echo "Done. Press Return to close."; read _'

say "All set! Look on your Desktop for three icons:"
echo "   1 TEST WITHOUT CAR   — proves the software works (do this first, no car)"
echo "   2 READ THE CAR       — live dashboard in your browser"
echo "   3 QUICK FAULT CHECK  — one-shot engine fault read"
echo ""
echo "Just double-click an icon. The first time, macOS may say the file is from an"
echo "unknown source — right-click the icon, choose Open, then Open again."
echo ""
