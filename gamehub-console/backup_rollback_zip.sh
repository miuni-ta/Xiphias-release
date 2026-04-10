#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
RELEASE_ROOT="$(cd "${BASE_DIR}/.." && pwd)"
BACKUP_ROOT="${RELEASE_ROOT}"
BACKUP_DIR="${BACKUP_ROOT}/backup"
DATE_STAMP="$("/usr/bin/date" '+%Y%m%d')"
TIME_STAMP="$("/usr/bin/date" '+%H%M%S')"
OUTPUT_NAME="console_backup_${DATE_STAMP}_${TIME_STAMP}.zip"
OUTPUT_PATH="${BACKUP_DIR}/${OUTPUT_NAME}"
TMP_PATH="${OUTPUT_PATH}.tmp"

mkdir -p "${BACKUP_DIR}"
cd "${BACKUP_ROOT}"
trap '/usr/bin/rm -f "${TMP_PATH}"' EXIT

INCLUDE_PATHS=(
  "gamehub-console"
  ".icons"
  ".xinitrc"
)

OPTIONAL_PATHS=(
  ".config/openbox"
  ".config/autostart"
  ".config/onboard"
  ".local/share/onboard"
)

for path in "${OPTIONAL_PATHS[@]}"; do
  if [[ -e "${path}" ]]; then
    INCLUDE_PATHS+=("${path}")
  fi
done

/usr/bin/zip -rq "${TMP_PATH}" "${INCLUDE_PATHS[@]}" \
  -x "gamehub-console/logs/*" \
     "gamehub-console/__pycache__/*" \
     "${OUTPUT_NAME}" "${OUTPUT_NAME}.tmp" \
     "console_backup_*.zip" \
     "kiosk-backup-*.zip" \
     "backup/${OUTPUT_NAME}" "backup/${OUTPUT_NAME}.tmp" \
     "backup/console_backup_*.zip" \
     "backup/kiosk-backup-*.zip"

/usr/bin/zip -T "${TMP_PATH}" >/dev/null
/usr/bin/mv -f "${TMP_PATH}" "${OUTPUT_PATH}"

/usr/bin/printf '[%s] Built %s from kiosk paths\n' "$(/usr/bin/date '+%Y-%m-%d %H:%M:%S %z')" "${OUTPUT_PATH}"
/usr/bin/ls -lh "${OUTPUT_PATH}"
