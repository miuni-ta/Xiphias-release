#!/bin/bash
set -euo pipefail

SERVICE_NAME="xiphias-gpio-gamepad.service"

echo "== Xiphias GPIO Gamepad Check =="
echo

echo "[1/6] Service state"
systemctl --no-pager --full status "${SERVICE_NAME}" || true
echo

echo "[2/6] Required kernel interface"
if lsmod | awk '{print $1}' | grep -qx 'uinput'; then
  echo "uinput module: loaded"
else
  echo "uinput module: not loaded"
fi

if [[ -e /dev/uinput ]]; then
  ls -l /dev/uinput
else
  echo "/dev/uinput: missing"
fi
echo

echo "[3/6] Python dependencies"
python3 - <<'PY'
import importlib.util

for name in ("evdev", "gpiozero", "lgpio"):
    print(f"{name}: {'ok' if importlib.util.find_spec(name) else 'missing'}")
PY
echo

echo "[4/6] Input devices"
for name_path in /sys/class/input/event*/device/name; do
  [[ -f "${name_path}" ]] || continue
  event_name="$(basename "$(dirname "$(dirname "${name_path}")")")"
  printf '%s: %s\n' "${event_name}" "$(cat "${name_path}")"
done
echo

echo "[5/6] Xiphias gamepad udev tags"
FOUND_EVENT=""
for name_path in /sys/class/input/event*/device/name; do
  [[ -f "${name_path}" ]] || continue
  if [[ "$(cat "${name_path}")" == "Xiphias GPIO Gamepad" ]]; then
    FOUND_EVENT="$(basename "$(dirname "$(dirname "${name_path}")")")"
    break
  fi
done

if [[ -n "${FOUND_EVENT}" ]]; then
  echo "Found /dev/input/${FOUND_EVENT}"
  udevadm info --query=property --name="/dev/input/${FOUND_EVENT}" |
    grep -E '^(ID_INPUT|ID_INPUT_JOYSTICK|ID_INPUT_GAMEPAD)=' || true
else
  echo "Xiphias GPIO Gamepad input device was not found."
fi
echo

echo "[6/6] Recent service logs"
journalctl --no-pager -u "${SERVICE_NAME}" -n 80 || true
