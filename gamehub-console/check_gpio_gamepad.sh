#!/bin/bash
set -euo pipefail

SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
BASE_DIR="$(cd "$(dirname "${SCRIPT_PATH}")" && pwd)"
SERVICE_NAME="xiphias-gpio-gamepad.service"

cd "${BASE_DIR}"

echo "== Xiphias GPIO Gamepad Check =="
echo

echo "[1/8] Service state"
systemctl --no-pager --full status "${SERVICE_NAME}" || true
echo

echo "[2/8] Required kernel interfaces"
for module_name in uinput joydev; do
  if lsmod | awk '{print $1}' | grep -qx "${module_name}"; then
    echo "${module_name} module: loaded"
  else
    echo "${module_name} module: not loaded"
  fi
done

if [[ -e /dev/uinput ]]; then
  ls -l /dev/uinput
else
  echo "/dev/uinput: missing"
fi
echo

echo "[3/8] Python dependencies"
python3 - <<'PY'
import importlib.util

for name in ("evdev", "gpiozero", "lgpio"):
    print(f"{name}: {'ok' if importlib.util.find_spec(name) else 'missing'}")
PY
echo

echo "[4/8] Configured GPIO mapping"
python3 - <<'PY'
try:
    from common import load_config
    from gpio_gamepad import DEFAULT_ACTIVE_LOW, config_bool, configured_controls

    config = load_config()
    active_low = config_bool(config, "GPIO_GAMEPAD_ACTIVE_LOW", DEFAULT_ACTIVE_LOW)
    controls = configured_controls(config)
except Exception as exc:
    print(f"Could not read GPIO mapping: {exc}")
else:
    print(f"GPIO_GAMEPAD_ACTIVE_LOW={1 if active_low else 0}")
    for control, pin in controls:
        print(f"{control.name}: BCM{pin} -> {control.kind}")
PY
echo

echo "[5/8] GPIO pin state snapshot"
if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script with sudo to read GPIO pin states directly."
else
  python3 - <<'PY'
import os
import re
import shutil
import subprocess

os.environ.setdefault("GPIOZERO_PIN_FACTORY", "lgpio")

buttons = []


def command_output(args):
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=2, check=False)
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def parse_level(text):
    match = re.search(r"\blevel=([01])\b", text)
    if match:
        return int(match.group(1))
    if re.search(r"(^|[| ])hi([ |]|$)", text):
        return 1
    if re.search(r"(^|[| ])lo([ |]|$)", text):
        return 0
    return None


def read_pin_with_tool(pin):
    if shutil.which("pinctrl"):
        text = command_output(["pinctrl", "get", str(pin)])
        level = parse_level(text)
        if level is not None:
            return level, text
    if shutil.which("raspi-gpio"):
        text = command_output(["raspi-gpio", "get", str(pin)])
        level = parse_level(text)
        if level is not None:
            return level, text
    return None


try:
    from common import load_config
    from gpio_gamepad import DEFAULT_ACTIVE_LOW, config_bool, configured_controls

    config = load_config()
    active_low = config_bool(config, "GPIO_GAMEPAD_ACTIVE_LOW", DEFAULT_ACTIVE_LOW)
    for control, pin in configured_controls(config):
        tool_state = read_pin_with_tool(pin)
        if tool_state is not None:
            level, raw_text = tool_state
            pressed = level == 0 if active_low else level == 1
            state = "pressed" if pressed else "released"
            print(f"{control.name}: BCM{pin} {state} (level={level}; {raw_text})")
            continue

        try:
            from gpiozero import Button

            button = Button(pin, pull_up=active_low, bounce_time=0.02)
            buttons.append(button)
            state = "pressed" if button.is_pressed else "released"
            print(f"{control.name}: BCM{pin} {state}")
        except Exception as exc:
            print(f"{control.name}: BCM{pin} error: {exc}")
except Exception as exc:
    print(f"Could not read GPIO pin states: {exc}")
finally:
    for button in buttons:
        try:
            button.close()
        except Exception:
            pass
PY
fi
echo

echo "[6/8] Input devices"
for name_path in /sys/class/input/event*/device/name; do
  [[ -f "${name_path}" ]] || continue
  event_name="$(basename "$(dirname "$(dirname "${name_path}")")")"
  printf '%s: %s\n' "${event_name}" "$(cat "${name_path}")"
done
if compgen -G "/dev/input/js*" >/dev/null; then
  echo
  echo "Joystick API nodes:"
  ls -l /dev/input/js*
else
  echo
  echo "No /dev/input/js* joystick nodes found."
fi
echo

echo "[7/8] Xiphias gamepad udev tags"
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

echo "[8/8] Recent service logs"
journalctl --no-pager -u "${SERVICE_NAME}" -n 80 || true
