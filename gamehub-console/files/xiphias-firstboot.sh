#!/bin/bash
set -euo pipefail

STATE_DIR="/var/lib/xiphias"
STATE_FILE="${STATE_DIR}/firstboot-complete"
DEFAULT_HOSTNAME_PREFIX="xiphias"

plymouth_active=0

show_progress() {
  local percent="$1"
  local message="$2"

  echo "${message}"
  if (( plymouth_active )); then
    plymouth display-message --text="${message}" >/dev/null 2>&1 || true
    plymouth system-update --progress="${percent}" >/dev/null 2>&1 || true
  fi
}

start_plymouth_updates() {
  if ! command -v plymouth >/dev/null 2>&1; then
    return 0
  fi
  if ! plymouth --ping >/dev/null 2>&1; then
    return 0
  fi

  plymouth_active=1
  plymouth show-splash >/dev/null 2>&1 || true
  plymouth change-mode --updates >/dev/null 2>&1 || true
}

derive_hostname_suffix() {
  local serial=""
  local mac=""

  serial="$(awk '/^Serial/ {print tolower($3)}' /proc/cpuinfo | tail -n 1)"
  if [[ "${serial}" =~ ^[0-9a-f]{6,}$ ]]; then
    printf '%s\n' "${serial: -6}"
    return 0
  fi

  for mac_path in /sys/class/net/eth0/address /sys/class/net/wlan0/address; do
    if [[ -f "${mac_path}" ]]; then
      mac="$(tr -d ':' < "${mac_path}" | tr '[:upper:]' '[:lower:]')"
      if [[ "${mac}" =~ ^[0-9a-f]{6,}$ ]]; then
        printf '%s\n' "${mac: -6}"
        return 0
      fi
    fi
  done

  printf '001\n'
}

desired_hostname() {
  local current_hostname=""
  local suffix=""

  current_hostname="$(cat /etc/hostname 2>/dev/null | tr -d '[:space:]' || true)"
  if [[ -n "${current_hostname}" && "${current_hostname}" != "raspberrypi" ]]; then
    printf '%s\n' "${current_hostname}"
    return 0
  fi

  suffix="$(derive_hostname_suffix)"
  printf '%s-%s\n' "${DEFAULT_HOSTNAME_PREFIX}" "${suffix}"
}

apply_hostname() {
  local new_hostname="$1"

  printf '%s\n' "${new_hostname}" > /etc/hostname

  if grep -q '^127\.0\.1\.1[[:space:]]' /etc/hosts; then
    sed -i "s/^127\\.0\\.1\\.1[[:space:]].*/127.0.1.1\t${new_hostname}/" /etc/hosts
  else
    printf '127.0.1.1\t%s\n' "${new_hostname}" >> /etc/hosts
  fi

  hostname "${new_hostname}" || true
}

mark_complete() {
  mkdir -p "${STATE_DIR}"
  touch "${STATE_FILE}"
  systemctl disable xiphias-firstboot.service >/dev/null 2>&1 || true
}

start_plymouth_updates

show_progress 10 "Preparing Xiphias first boot..."
target_hostname="$(desired_hostname)"

show_progress 45 "Assigning hostname: ${target_hostname}"
apply_hostname "${target_hostname}"

show_progress 80 "Finalizing kiosk startup..."
mark_complete

show_progress 100 "Starting Xiphias kiosk..."
sleep 0.4
