#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
WRAPPER_URL="file://${BASE_DIR}/kiosk-wrapper.html"
BOOT_SPLASH_READY_FILE="${BOOT_SPLASH_READY_FILE:-/tmp/gamehub-boot-ready}"
export DISPLAY="${DISPLAY:-:0}"

GAMEHUB_URL="https://handheld.knfstudios.com/?mode=handheld"
SCREEN_WIDTH=800
SCREEN_HEIGHT=480
HUD_HEIGHT=48
STATUS_BAR_HEIGHT=24
BOTTOM_BAR_HEIGHT=24
REMOTE_DEBUG_PORT=9222

load_console_env() {
  local raw_line line key value

  while IFS= read -r raw_line || [ -n "${raw_line}" ]; do
    line="$(printf '%s' "${raw_line}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    case "${line}" in
      ""|\#*)
        continue
        ;;
    esac

    key="$(printf '%s' "${line%%=*}" | sed 's/[[:space:]]*$//')"
    value="$(printf '%s' "${line#*=}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"

    case "${value}" in
      \"*\")
        value="${value#\"}"
        value="${value%\"}"
        ;;
      \'*\')
        value="${value#\'}"
        value="${value%\'}"
        ;;
    esac

    case "${key}" in
      GAMEHUB_URL|SCREEN_WIDTH|SCREEN_HEIGHT|HUD_HEIGHT|STATUS_BAR_HEIGHT|BOTTOM_BAR_HEIGHT|REMOTE_DEBUG_PORT)
        printf -v "${key}" '%s' "${value}"
        ;;
    esac
  done < "${BASE_DIR}/console.env"
}

load_console_env

WINDOW_X=0
WINDOW_Y="${STATUS_BAR_HEIGHT}"
WINDOW_WIDTH="${SCREEN_WIDTH}"
WINDOW_HEIGHT=$((SCREEN_HEIGHT - STATUS_BAR_HEIGHT - BOTTOM_BAR_HEIGHT))
APP_URL="${WRAPPER_URL}#${GAMEHUB_URL}"

if [ "${WINDOW_HEIGHT}" -lt 1 ]; then
  WINDOW_HEIGHT=1
fi

signal_boot_ready() {
  if [ -n "${BOOT_SPLASH_READY_FILE}" ]; then
    touch "${BOOT_SPLASH_READY_FILE}" 2>/dev/null || true
  fi
}

chromium \
  --app="${APP_URL}" \
  --no-first-run \
  --disable-infobars \
  --noerrdialogs \
  --disable-translate \
  --disable-pinch \
  --disable-session-crashed-bubble \
  --check-for-update-interval=31536000 \
  --enable-gpu-rasterization \
  --enable-accelerated-video-decode \
  --remote-debugging-port="${REMOTE_DEBUG_PORT}" \
  --remote-allow-origins="http://localhost:${REMOTE_DEBUG_PORT}" \
  --hide-scrollbars \
  --window-position="${WINDOW_X}","${WINDOW_Y}" \
  --window-size="${WINDOW_WIDTH}","${WINDOW_HEIGHT}" &

CHROMIUM_PID=$!

for _ in $(seq 1 40); do
  WINDOW_ID="$(xdotool search --onlyvisible --class chromium 2>/dev/null | head -n 1 || true)"
  if [ -n "${WINDOW_ID}" ]; then
    xdotool windowmove "${WINDOW_ID}" "${WINDOW_X}" "${WINDOW_Y}" 2>/dev/null || true
    xdotool windowsize "${WINDOW_ID}" "${WINDOW_WIDTH}" "${WINDOW_HEIGHT}" 2>/dev/null || true
    signal_boot_ready
    break
  fi
  sleep 0.25
done

wait "${CHROMIUM_PID}"
