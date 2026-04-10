#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
RELEASE_ROOT="$(cd "${BASE_DIR}/.." && pwd)"
INSTALL_MODE="live"
SKIP_APT_UPDATE="${XIPHIAS_SKIP_APT_UPDATE:-0}"
USER_NAME="${SUDO_USER:-${XIPHIAS_INSTALL_USER:-pi}}"
HOME_DIR="/home/${USER_NAME}"

usage() {
  cat <<EOF
Usage: bash ${BASE_DIR}/install_gamehub_console.sh [options]

Options:
  --image-mode       Provision a mounted image or chroot rootfs as root.
  --skip-apt-update  Skip apt update before installing packages.
  --help             Show this help text.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-mode)
      INSTALL_MODE="image"
      ;;
    --skip-apt-update)
      SKIP_APT_UPDATE=1
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
  shift
done

if [[ ! -d "${BASE_DIR}" ]]; then
  echo "Missing ${BASE_DIR}"
  exit 1
fi

run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  else
    sudo "$@"
  fi
}

run_as_user() {
  local target_user="$1"
  shift

  if [[ "$(id -u)" -eq 0 ]]; then
    runuser -u "${target_user}" -- "$@"
  else
    sudo -u "${target_user}" "$@"
  fi
}

ensure_group() {
  local group_name="$1"

  if getent group "${group_name}" >/dev/null 2>&1; then
    return 0
  fi

  run_root groupadd --system "${group_name}"
}

boot_config_path() {
  local candidate
  for candidate in /boot/firmware/config.txt /boot/config.txt; do
    if [[ -f "${candidate}" ]]; then
      printf '%s\n' "${candidate}"
      return 0
    fi
  done
  return 1
}

maybe_enable_i2c() {
  local config_path battery_command

  battery_command="$(
    sed -n 's/^BATTERY_COMMAND=//p' "${BASE_DIR}/console.env" 2>/dev/null |
      sed -n '1{s/^"//;s/"$//;p;}'
  )"

  if [[ "${battery_command}" != *waveshare_ups_battery.py* ]]; then
    return 0
  fi

  config_path="$(boot_config_path || true)"
  if [[ -z "${config_path}" ]]; then
    return 0
  fi

  if grep -q '^dtparam=i2c_arm=' "${config_path}"; then
    run_root sed -i 's/^dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' "${config_path}"
  else
    printf '\ndtparam=i2c_arm=on\n' | run_root tee -a "${config_path}" >/dev/null
  fi
}

if [[ "${INSTALL_MODE}" == "live" && "$(id -un)" == "root" ]]; then
  echo "Run this script as the regular user, not as root:"
  echo "bash ${BASE_DIR}/install_gamehub_console.sh"
  exit 1
fi

if [[ "${INSTALL_MODE}" == "image" && "$(id -u)" -ne 0 ]]; then
  echo "Run image mode as root inside the image rootfs:"
  echo "bash ${BASE_DIR}/install_gamehub_console.sh --image-mode"
  exit 1
fi

if ! id -u "${USER_NAME}" >/dev/null 2>&1; then
  echo "Missing user: ${USER_NAME}" >&2
  exit 1
fi

sync_dir_if_needed() {
  local src="$1"
  local dst="$2"

  if [[ -d "${src}" && ! -L "${src}" ]]; then
    mkdir -p "${dst}"
    rsync -a "${src}/" "${dst}/"
  fi
}

sync_file_if_needed() {
  local src="$1"
  local dst="$2"

  if [[ -f "${src}" && ! -L "${src}" ]]; then
    mkdir -p "$(dirname "${dst}")"
    rsync -a "${src}" "${dst}"
  fi
}

echo "== GameHub Console installer =="
echo
echo "[1/9] Installing packages..."
if (( ! SKIP_APT_UPDATE )); then
  run_root apt update
fi
run_root apt install -y \
  chromium \
  git \
  openbox \
  unclutter \
  xdotool \
  xinit \
  xserver-xorg \
  python3-evdev \
  python3-gi \
  python3-pygame \
  python3-smbus2 \
  python3-tk \
  python3-websocket \
  onboard \
  network-manager \
  network-manager-gnome \
  bluez \
  blueman \
  plymouth \
  plymouth-themes \
  wireless-tools \
  dbus-x11 \
  lxpolkit \
  upower

echo "[2/9] Ensuring group access..."
for group_name in input video render audio netdev bluetooth i2c; do
  ensure_group "${group_name}"
done
run_root usermod -aG input,video,render,audio,netdev,bluetooth,i2c "${USER_NAME}"

echo "[3/9] Configuring X11 wrapper..."
run_root mkdir -p /etc/X11
cat <<'EOF' | run_root tee /etc/X11/Xwrapper.config >/dev/null
allowed_users=anybody
needs_root_rights=yes
EOF

echo "[4/9] Installing user config..."
mkdir -p "${RELEASE_ROOT}/.config/openbox"
mkdir -p "${RELEASE_ROOT}/.config/autostart"
mkdir -p "${RELEASE_ROOT}/.config/onboard"
mkdir -p "${RELEASE_ROOT}/.icons"
mkdir -p "${RELEASE_ROOT}/.local/share/onboard/layouts"
mkdir -p "${RELEASE_ROOT}/.local/share/onboard/themes"
mkdir -p "${BASE_DIR}/logs"

if [[ "${INSTALL_MODE}" == "live" ]]; then
  sync_dir_if_needed "${HOME_DIR}/.config" "${RELEASE_ROOT}/.config"
  sync_dir_if_needed "${HOME_DIR}/.icons" "${RELEASE_ROOT}/.icons"
  sync_dir_if_needed "${HOME_DIR}/.local" "${RELEASE_ROOT}/.local"
  sync_file_if_needed "${HOME_DIR}/.xinitrc" "${RELEASE_ROOT}/.xinitrc"
fi

install -m 755 "${BASE_DIR}/files/xinitrc" "${RELEASE_ROOT}/.xinitrc"
install -m 755 "${BASE_DIR}/files/openbox/autostart" "${RELEASE_ROOT}/.config/openbox/autostart"
install -m 644 "${BASE_DIR}/gamepad_keyboard.onboard" "${RELEASE_ROOT}/.local/share/onboard/layouts/gamepad_keyboard.onboard"
install -m 644 "${BASE_DIR}/gamepad_keyboard.svg" "${RELEASE_ROOT}/.local/share/onboard/layouts/gamepad_keyboard.svg"
install -m 644 "${BASE_DIR}/gamepad_dark.theme" "${RELEASE_ROOT}/.local/share/onboard/themes/gamepad_dark.theme"
install -m 644 "${BASE_DIR}/gamepad_dark.colors" "${RELEASE_ROOT}/.local/share/onboard/themes/gamepad_dark.colors"

cat > "${RELEASE_ROOT}/.config/autostart/nm-applet.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Network
Hidden=true
X-GNOME-Autostart-enabled=false
EOF

cat > "${RELEASE_ROOT}/.config/autostart/blueman.desktop" <<'EOF'
[Desktop Entry]
Type=Application
Name=Blueman Applet
Hidden=true
X-GNOME-Autostart-enabled=false
EOF

cat > "${RELEASE_ROOT}/.config/onboard/onboard.conf" <<'EOF'
[main]
layout=gamepad_keyboard
theme=gamepad_dark
enable-background-transparency=false
EOF

echo "[5/9] Configuring boot splash..."
run_root bash "${BASE_DIR}/configure_boot_splash.sh"
maybe_enable_i2c

echo "[6/9] Installing service..."
run_root install -m 644 "${BASE_DIR}/files/knf-kiosk.service" /etc/systemd/system/knf-kiosk.service
run_root install -d -m 755 /etc/systemd/user-environment-generators
run_root install -m 755 "${BASE_DIR}/files/90-xiphias-release-home" /etc/systemd/user-environment-generators/90-xiphias-release-home
run_root install -m 440 "${BASE_DIR}/files/gamehub-console-sudoers" /etc/sudoers.d/gamehub-console
run_root install -m 644 "${BASE_DIR}/files/gamehub-console-backup.cron" /etc/cron.d/gamehub-console-backup

echo "[7/9] Enabling services..."
if [[ "${INSTALL_MODE}" == "live" ]]; then
  run_root systemctl daemon-reload
  run_root systemctl enable knf-kiosk.service
  run_root systemctl enable NetworkManager
  run_root systemctl disable lightdm.service >/dev/null 2>&1 || true
  XDG_RUNTIME_DIR="/run/user/$(id -u)"
  if [[ -d "${XDG_RUNTIME_DIR}" ]]; then
    run_as_user "${USER_NAME}" env XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR}" systemctl --user daemon-reload || true
  fi
else
  echo "Image mode: service enablement is handled by the image builder."
fi

echo "[8/9] Setting boot target..."
if [[ "${INSTALL_MODE}" == "live" ]]; then
  run_root systemctl set-default multi-user.target
  run_root raspi-config nonint do_boot_behaviour B2 || true
else
  echo "Image mode: boot target is handled by the image builder."
fi

echo "[9/9] Final checks..."
chmod +x \
  "${BASE_DIR}/backup_rollback_zip.sh" \
  "${BASE_DIR}/boot_splash.py" \
  "${BASE_DIR}/configure_boot_splash.sh" \
  "${BASE_DIR}/launch_chromium.sh" \
  "${BASE_DIR}/restart_kiosk.sh" \
  "${BASE_DIR}/start_kiosk_components.sh" \
  "${BASE_DIR}/gamepad_cursor.py" \
  "${BASE_DIR}/hud_overlay.py" \
  "${BASE_DIR}/waveshare_ups_battery.py"

echo
echo "Install complete."
if [[ "${INSTALL_MODE}" == "live" ]]; then
  echo "Next step: sudo reboot"
  echo
  echo "After reboot, the Pi should:"
  echo "- boot straight to kiosk"
  echo "- keep the GameHub splash on-screen during early boot and shutdown"
  echo "- launch Chromium on your GameHub URL"
  echo "- keep touch and gamepad input available in the kiosk"
else
  echo "Image mode complete."
fi
