#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
START_SCRIPT="${BASE_DIR}/start_kiosk_components.sh"
LOCK_FILE="/tmp/gamehub-restart.lock"
LOCK_FD_OPEN=0
export DISPLAY="${DISPLAY:-:0}"

if command -v flock >/dev/null 2>&1; then
  exec 9>"${LOCK_FILE}"
  flock -n 9 || exit 0
  LOCK_FD_OPEN=1
fi

terminate_pattern() {
  local pattern="$1"
  pkill -TERM -f "${pattern}" >/dev/null 2>&1 || true
}

wait_for_pattern_exit() {
  local pattern="$1"
  local attempts=20
  while pgrep -f "${pattern}" >/dev/null 2>&1 && [[ "${attempts}" -gt 0 ]]; do
    sleep 0.1
    attempts=$((attempts - 1))
  done
  if pgrep -f "${pattern}" >/dev/null 2>&1; then
    pkill -KILL -f "${pattern}" >/dev/null 2>&1 || true
  fi
}

sleep 0.15

terminate_pattern "${BASE_DIR}/hud_overlay.py"
terminate_pattern "${BASE_DIR}/gamepad_cursor.py"
terminate_pattern "${BASE_DIR}/launch_chromium.sh"
terminate_pattern "${BASE_DIR}/boot_splash.py"
pkill -TERM -x chromium >/dev/null 2>&1 || true
pkill -TERM -f '[/]usr/bin/onboard' >/dev/null 2>&1 || true
pkill -TERM -f '[/]usr/bin/blueman-applet' >/dev/null 2>&1 || true
pkill -TERM -f '[/]usr/bin/blueman-tray' >/dev/null 2>&1 || true
pkill -TERM -x unclutter >/dev/null 2>&1 || true

wait_for_pattern_exit "${BASE_DIR}/hud_overlay.py"
wait_for_pattern_exit "${BASE_DIR}/gamepad_cursor.py"
wait_for_pattern_exit "${BASE_DIR}/launch_chromium.sh"
wait_for_pattern_exit "${BASE_DIR}/boot_splash.py"

wait_for_pattern_exit "[/]usr/bin/onboard"

for _ in $(seq 1 20); do
  if ! pgrep -x chromium >/dev/null 2>&1; then
    break
  fi
  sleep 0.1
done
if pgrep -x chromium >/dev/null 2>&1; then
  pkill -KILL -x chromium >/dev/null 2>&1 || true
fi

if pgrep -f '[/]usr/bin/onboard' >/dev/null 2>&1; then
  pkill -KILL -f '[/]usr/bin/onboard' >/dev/null 2>&1 || true
fi

if pgrep -f '[/]usr/bin/blueman-applet' >/dev/null 2>&1; then
  pkill -KILL -f '[/]usr/bin/blueman-applet' >/dev/null 2>&1 || true
fi

if pgrep -f '[/]usr/bin/blueman-tray' >/dev/null 2>&1; then
  pkill -KILL -f '[/]usr/bin/blueman-tray' >/dev/null 2>&1 || true
fi

if pgrep -x unclutter >/dev/null 2>&1; then
  pkill -KILL -x unclutter >/dev/null 2>&1 || true
fi

if [[ "${LOCK_FD_OPEN}" -eq 1 ]]; then
  exec 9>&-
fi

exec env SHOW_BOOT_SPLASH=0 bash "${START_SCRIPT}"
