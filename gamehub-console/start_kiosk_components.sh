#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
LOG_DIR="${BASE_DIR}/logs"
BOOT_SPLASH_READY_FILE="${BOOT_SPLASH_READY_FILE:-/tmp/gamehub-boot-ready}"
export DISPLAY="${DISPLAY:-:0}"
SHOW_BOOT_SPLASH="${SHOW_BOOT_SPLASH:-auto}"

find_boot_file() {
  local candidate
  for candidate in "/boot/firmware/$1" "/boot/$1"; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

boot_cmdline_has_token() {
  local token="$1"
  local cmdline_path

  cmdline_path="$(find_boot_file cmdline.txt || true)"
  [[ -n "${cmdline_path}" ]] || return 1
  grep -Eq "(^| )${token}( |$)" "${cmdline_path}"
}

has_early_boot_splash() {
  command -v plymouth-set-default-theme >/dev/null 2>&1 || return 1
  boot_cmdline_has_token "splash" || return 1
  return 0
}

resolve_x_boot_splash_mode() {
  case "${SHOW_BOOT_SPLASH}" in
    0|false|no)
      printf 'none\n'
      ;;
    handoff)
      printf 'handoff\n'
      ;;
    full|1|true|yes)
      printf 'full\n'
      ;;
    auto)
      if has_early_boot_splash; then
        printf 'handoff\n'
      else
        printf 'full\n'
      fi
      ;;
    *)
      printf 'full\n'
      ;;
  esac
}

mkdir -p "${LOG_DIR}"
rm -f "${BOOT_SPLASH_READY_FILE}"

bash "${BASE_DIR}/display_mode.sh" >> "${LOG_DIR}/display_mode.log" 2>&1 || true

pkill -f "${BASE_DIR}/boot_splash.py" >/dev/null 2>&1 || true
pkill -x unclutter >/dev/null 2>&1 || true
pkill -f '[/]usr/bin/onboard' >/dev/null 2>&1 || true
pkill -f '[/]usr/bin/blueman-applet' >/dev/null 2>&1 || true
pkill -f '[/]usr/bin/blueman-tray' >/dev/null 2>&1 || true

BOOT_SPLASH_MODE="$(resolve_x_boot_splash_mode)"

if [[ "${BOOT_SPLASH_MODE}" != "none" ]]; then
  setsid -f bash -lc "export DISPLAY='${DISPLAY}'; export BOOT_SPLASH_MODE='${BOOT_SPLASH_MODE}'; export BOOT_SPLASH_READY_FILE='${BOOT_SPLASH_READY_FILE}'; exec python3 '${BASE_DIR}/boot_splash.py' >> '${LOG_DIR}/splash.log' 2>&1"
fi

setsid -f bash -lc "sleep 0.1; export DISPLAY='${DISPLAY}'; exec unclutter -idle 0 -root >> '${LOG_DIR}/cursor.log' 2>&1"
setsid -f bash -lc "sleep 0.2; export DISPLAY='${DISPLAY}'; exec python3 '${BASE_DIR}/hud_overlay.py' >> '${LOG_DIR}/hud.log' 2>&1"
setsid -f bash -lc "sleep 0.2; export DISPLAY='${DISPLAY}'; exec python3 '${BASE_DIR}/gamepad_cursor.py' >> '${LOG_DIR}/gamepad.log' 2>&1"
setsid -f bash -lc "sleep 0.35; export DISPLAY='${DISPLAY}'; export BOOT_SPLASH_READY_FILE='${BOOT_SPLASH_READY_FILE}'; exec bash '${BASE_DIR}/launch_chromium.sh' >> '${LOG_DIR}/chromium.log' 2>&1"
