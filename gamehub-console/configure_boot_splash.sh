#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
THEME_NAME="gamehub-console"
THEME_SOURCE_DIR="${BASE_DIR}/files/plymouth-theme/${THEME_NAME}"
THEME_TARGET_DIR="/usr/share/plymouth/themes/${THEME_NAME}"
LOGO_SOURCE="${BASE_DIR}/assets/images/gbl_logo.png"

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

append_unique_token() {
  local line="$1"
  local token="$2"

  case " ${line} " in
    *" ${token} "*) ;;
    *) line="${line} ${token}" ;;
  esac

  printf '%s\n' "${line}"
}

normalize_cmdline() {
  local raw_line="$1"
  local token
  local normalized=""

  for token in ${raw_line}; do
    case "${token}" in
      console=tty0|console=tty1)
        token="console=tty3"
        ;;
      quiet|splash|plymouth.ignore-serial-consoles|logo.nologo)
        continue
        ;;
      loglevel=*|udev.log_priority=*|systemd.show_status=*|rd.systemd.show_status=*|vt.global_cursor_default=*)
        continue
        ;;
    esac

    normalized="$(append_unique_token "${normalized}" "${token}")"
  done

  normalized="$(append_unique_token "${normalized}" "console=tty3")"
  normalized="$(append_unique_token "${normalized}" "quiet")"
  normalized="$(append_unique_token "${normalized}" "splash")"
  normalized="$(append_unique_token "${normalized}" "plymouth.ignore-serial-consoles")"
  normalized="$(append_unique_token "${normalized}" "vt.global_cursor_default=0")"
  normalized="$(append_unique_token "${normalized}" "loglevel=3")"
  normalized="$(append_unique_token "${normalized}" "udev.log_priority=3")"
  normalized="$(append_unique_token "${normalized}" "systemd.show_status=false")"
  normalized="$(append_unique_token "${normalized}" "rd.systemd.show_status=false")"
  normalized="$(append_unique_token "${normalized}" "logo.nologo")"

  printf '%s\n' "${normalized#" "}"
}

ensure_disable_splash() {
  local config_path="$1"

  if grep -q '^disable_splash=' "${config_path}"; then
    sed -i 's/^disable_splash=.*/disable_splash=1/' "${config_path}"
    return 0
  fi

  printf '\ndisable_splash=1\n' >> "${config_path}"
}

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run with sudo: sudo ${BASE_DIR}/configure_boot_splash.sh"
  exit 1
fi

if [[ ! -d "${THEME_SOURCE_DIR}" ]]; then
  echo "Missing theme source directory: ${THEME_SOURCE_DIR}"
  exit 1
fi

if [[ ! -f "${LOGO_SOURCE}" ]]; then
  echo "Missing splash logo: ${LOGO_SOURCE}"
  exit 1
fi

CMDLINE_PATH="$(find_boot_file cmdline.txt || true)"
CONFIG_PATH="$(find_boot_file config.txt || true)"

if [[ -z "${CMDLINE_PATH}" || -z "${CONFIG_PATH}" ]]; then
  echo "Could not locate boot firmware files"
  exit 1
fi

install -d -m 755 "${THEME_TARGET_DIR}"
install -m 644 "${THEME_SOURCE_DIR}/${THEME_NAME}.plymouth" "${THEME_TARGET_DIR}/${THEME_NAME}.plymouth"
install -m 644 "${THEME_SOURCE_DIR}/${THEME_NAME}.script" "${THEME_TARGET_DIR}/${THEME_NAME}.script"
install -m 644 "${LOGO_SOURCE}" "${THEME_TARGET_DIR}/gbl_logo.png"

printf '%s\n' "$(normalize_cmdline "$(cat "${CMDLINE_PATH}")")" > "${CMDLINE_PATH}"
ensure_disable_splash "${CONFIG_PATH}"

plymouth-set-default-theme -R "${THEME_NAME}"
