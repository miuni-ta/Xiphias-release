#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
TARGET_WIDTH=800
TARGET_HEIGHT=480
TARGET_MODE="${TARGET_WIDTH}x${TARGET_HEIGHT}"
export DISPLAY="${DISPLAY:-:0}"

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
      SCREEN_WIDTH)
        TARGET_WIDTH="${value}"
        ;;
      SCREEN_HEIGHT)
        TARGET_HEIGHT="${value}"
        ;;
    esac
  done < "${BASE_DIR}/console.env"

  TARGET_MODE="${TARGET_WIDTH}x${TARGET_HEIGHT}"
}

find_primary_output() {
  xrandr --query | awk '
    $2 == "connected" && $3 == "primary" { print $1; exit }
    $2 == "connected" { print $1; exit }
  '
}

find_preferred_mode() {
  local output="$1"
  xrandr --query | awk -v output="${output}" '
    $1 == output && $2 == "connected" { in_block = 1; next }
    in_block && $0 !~ /^ / { in_block = 0 }
    in_block && /\+/ { print $1; exit }
    in_block && /\*/ && !fallback { fallback = $1 }
    END {
      if (fallback) {
        print fallback
      }
    }
  '
}

load_console_env

OUTPUT="$(find_primary_output)"
if [ -z "${OUTPUT}" ]; then
  echo "No connected display output found."
  exit 0
fi

PREFERRED_MODE="$(find_preferred_mode "${OUTPUT}")"
if [ -z "${PREFERRED_MODE}" ]; then
  echo "Could not determine preferred mode for ${OUTPUT}."
  exit 0
fi

if [ "${PREFERRED_MODE}" = "${TARGET_MODE}" ]; then
  echo "Applying native mode ${TARGET_MODE} on ${OUTPUT}."
  xrandr --output "${OUTPUT}" --mode "${TARGET_MODE}" --fb "${TARGET_MODE}" --scale 1x1
  exit 0
fi

echo "Applying logical mode ${TARGET_MODE} on ${OUTPUT} using native ${PREFERRED_MODE} scaling."
xrandr --output "${OUTPUT}" --mode "${PREFERRED_MODE}" --fb "${TARGET_MODE}" --scale-from "${TARGET_MODE}"
