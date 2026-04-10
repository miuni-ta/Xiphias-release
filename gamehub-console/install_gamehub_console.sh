#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
RELEASE_ROOT="$(cd "${BASE_DIR}/.." && pwd)"
USER_NAME="${SUDO_USER:-pi}"
HOME_DIR="/home/${USER_NAME}"

if [[ ! -d "${BASE_DIR}" ]]; then
  echo "Missing ${BASE_DIR}"
  exit 1
fi

if [[ "$(id -un)" == "root" ]]; then
  echo "Run this script as the regular user, not as root:"
  echo "bash ${BASE_DIR}/install_gamehub_console.sh"
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
sudo apt update
sudo apt install -y \
  chromium \
  openbox \
  xdotool \
  xinit \
  xserver-xorg \
  python3-evdev \
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
sudo usermod -aG input,video,render,audio,netdev,bluetooth,i2c "${USER_NAME}"

echo "[3/9] Configuring X11 wrapper..."
sudo mkdir -p /etc/X11
cat <<'EOF' | sudo tee /etc/X11/Xwrapper.config >/dev/null
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

sync_dir_if_needed "${HOME_DIR}/.config" "${RELEASE_ROOT}/.config"
sync_dir_if_needed "${HOME_DIR}/.icons" "${RELEASE_ROOT}/.icons"
sync_dir_if_needed "${HOME_DIR}/.local" "${RELEASE_ROOT}/.local"
sync_file_if_needed "${HOME_DIR}/.xinitrc" "${RELEASE_ROOT}/.xinitrc"

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
sudo bash "${BASE_DIR}/configure_boot_splash.sh"

echo "[6/9] Installing service..."
sudo install -m 644 "${BASE_DIR}/files/knf-kiosk.service" /etc/systemd/system/knf-kiosk.service
sudo install -d -m 755 /etc/systemd/user-environment-generators
sudo install -m 755 "${BASE_DIR}/files/90-xiphias-release-home" /etc/systemd/user-environment-generators/90-xiphias-release-home
sudo install -m 440 "${BASE_DIR}/files/gamehub-console-sudoers" /etc/sudoers.d/gamehub-console
sudo install -m 644 "${BASE_DIR}/files/gamehub-console-backup.cron" /etc/cron.d/gamehub-console-backup

echo "[7/9] Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable knf-kiosk.service
sudo systemctl enable NetworkManager
sudo systemctl disable lightdm.service >/dev/null 2>&1 || true
XDG_RUNTIME_DIR="/run/user/$(id -u)"
if [[ -d "${XDG_RUNTIME_DIR}" ]]; then
  sudo -u "${USER_NAME}" XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR}" systemctl --user daemon-reload || true
fi

echo "[8/9] Setting boot target..."
sudo systemctl set-default multi-user.target
sudo raspi-config nonint do_boot_behaviour B2 || true

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
echo "Next step: sudo reboot"
echo
echo "After reboot, the Pi should:"
echo "- boot straight to kiosk"
echo "- keep the GameHub splash on-screen during early boot and shutdown"
echo "- launch Chromium on your GameHub URL"
echo "- keep touch and gamepad input available in the kiosk"
