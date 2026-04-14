#!/usr/bin/env python3
from array import array
import base64
from functools import lru_cache
from io import BytesIO
import json
import math
import os
import re
import shlex
import shutil
import subprocess
import threading
import time
import tkinter as tk
from tkinter import font as tkfont

import evdev
try:
    import gi

    gi.require_version("GdkPixbuf", "2.0")
    from gi.repository import GdkPixbuf
except Exception:
    GdkPixbuf = None

try:
    from PIL import Image, ImageDraw
except Exception:
    Image = None
    ImageDraw = None

from common import (
    REPO_ROOT,
    WORKSPACE_ROOT,
    TOUCH_TOKENS,
    hud_bar_heights,
    load_config,
    read_workspace_version,
    set_hud_text_input_active,
    set_quick_menu_active,
    touchscreen_present,
)
from audio_output import detect_output_format, get_shared_audio_output


os.environ["DISPLAY"] = ":0"

CONFIG = load_config()
SCREEN_W = int(CONFIG["SCREEN_WIDTH"])
SCREEN_H = int(CONFIG["SCREEN_HEIGHT"])
STATUS_BAR_H, BOTTOM_BAR_H = hud_bar_heights(CONFIG)
APP_Y = STATUS_BAR_H
APP_HEIGHT = max(1, SCREEN_H - STATUS_BAR_H - BOTTOM_BAR_H)
BATTERY_COMMAND = CONFIG.get("BATTERY_COMMAND", "")
BRIGHTNESS_COMMAND = str(CONFIG.get("BRIGHTNESS_COMMAND", "")).strip()
BRIGHTNESS_OUTPUT = str(CONFIG.get("BRIGHTNESS_OUTPUT", "")).strip()
BRIGHTNESS_BACKLIGHT = str(CONFIG.get("BRIGHTNESS_BACKLIGHT", "")).strip()
PROMPT_ICON_DIR = str(REPO_ROOT / "assets" / "input-prompts" / "xbox-series" / "hud")
STATUS_ICON_DIR = str(REPO_ROOT / "assets" / "icons")
RESTART_KIOSK_CMD = ["bash", str(REPO_ROOT / "restart_kiosk.sh")]
OTA_CHECK_AVAILABLE_RC = 10
OTA_CHECK_CMD = ["bash", str(WORKSPACE_ROOT / "release" / "gamehub-console" / "ota_git_update.sh"), "--check-only"]
OTA_UPDATE_CMD = ["bash", str(WORKSPACE_ROOT / "release" / "gamehub-console" / "ota_git_update.sh"), "--no-restart"]
SET_BACKLIGHT_CMD = [str(REPO_ROOT / "set_backlight.sh")]
NMCLI_CMD = ["/usr/bin/nmcli"]
PRIVILEGED_NMCLI_CMD = ["sudo", "-n", "/usr/bin/nmcli"]
STANDARD_TOUCH_CURSOR = touchscreen_present()

BG = "#0a0d12"
STATUS_BG = "#0c1118"
NAV_BG = "#111827"
TEXT = "#ffffff"
TEXT_DIM = "#3a3d4a"
STATUS_ICON = "#c2cad6"
STATUS_ICON_DIM = "#606876"
ACCENT = "#22c55e"
ACCENT_DIM = "#112218"
BLUE = "#3b82f6"
WARN = "#ef4444"
MID = "#f59e0b"
NAV_TEXT = "#c8d1e0"
BATTERY_EMPTY = "#262830"
NAV_HINT_CHIP_BG = "#474b55"
NAV_HINT_CHIP_TEXT = "#f5f7fb"
MENU_BG = "#130b0f"
MENU_PANEL_BG = "#1e1219"
MENU_ROW_BG = "#2a2435"
MENU_ROW_BORDER = "#3d3750"
MENU_CTA_START = "#f0184e"
MENU_CTA_END = "#f5793a"
MENU_HOT_PINK = "#f0197a"
MENU_GOLD = "#f5c53a"
MENU_MUTED = "#b0aabd"
MENU_VALUE = "#b0aabd"
MENU_FOCUS_TEXT = "#ffffff"
MENU_ICON = "#b0aabd"
MENU_ICON_ACTIVE = "#ffffff"
MENU_DESTRUCTIVE = "#f5793a"
VISIBLE_POINTER_CURSOR = "left_ptr"
MENU_TOAST_BG = "#2a2435"
MENU_TOAST_TEXT = "#f5f7fb"
MENU_DETAIL_BG = "#24161e"
MENU_DETAIL_BORDER = "#4a3644"
MENU_DETAIL_TEXT = "#f9eef4"
MENU_DETAIL_SUBTEXT = "#ccbfc7"
MENU_DETAIL_DIM = "#8e7f89"
MENU_DETAIL_ACTIVE = "#331f29"
MENU_CONFIRM_BG = "#3d1621"
MENU_CONFIRM_BORDER = "#f6a46c"
SLIDER_TRACK = "#3d3750"
SLIDER_FILL = "#f0197a"
HUD_ICON_SIZE = 16
MENU_ICON_SIZE = 22
FONT_FAMILY = "FF DIN"
BASE_FONT_SIZE = 10
NAV_FONT = (FONT_FAMILY, BASE_FONT_SIZE, "bold")
CLOCK_FONT = NAV_FONT
MENU_TITLE_FONT = (FONT_FAMILY, 18, "bold")
MENU_ITEM_FONT = (FONT_FAMILY, 13, "bold")
MENU_VALUE_FONT = (FONT_FAMILY, 12, "bold")
MENU_TOAST_FONT = (FONT_FAMILY, 10, "bold")
MENU_WIDTH = 420
MENU_ANIMATION_DURATION_MS = 220
MENU_ANIMATION_STEP_MS = 16
MENU_COLLAPSED_SCALE = 0.92
MENU_COLLAPSED_ALPHA = 0.0
MENU_OPEN_ALPHA = 1.0
MENU_SLIDER_WIDTH = 188
MENU_SIDE_PAD = 18
VOLUME_ADJUST_STEP = 1
VOLUME_ANIMATION_STEP = 1
VOLUME_ANIMATION_INTERVAL_MS = 28
MENU_HEADER_PAD_X = MENU_SIDE_PAD
MENU_HEADER_PAD_Y = 18
MENU_LIST_PAD_X = 4
MENU_ROW_HEIGHT = 56
MENU_ROW_GAP = 12
MENU_ROW_RADIUS = 14
MENU_ROW_ICON_X = 28
MENU_ROW_TEXT_X = 63
MENU_ROW_TRAILING_PAD = 34
MENU_BACK_BUTTON_SIZE = 32
MENU_BACK_BUTTON_BG = "#22242b"
MENU_TOAST_OFFSET_Y = 16
VOLUME_ITEM_KEY = "volume"
WIFI_ITEM_KEY = "wifi"
BLUETOOTH_ITEM_KEY = "bt"
BRIGHTNESS_ITEM_KEY = "brightness"
UPDATE_ITEM_KEY = "update"
RESTART_ITEM_KEY = "restart"
SHUTDOWN_ITEM_KEY = "shutdown"
ADJUSTABLE_ITEM_KEYS = {VOLUME_ITEM_KEY, BRIGHTNESS_ITEM_KEY}
LIST_ITEM_KEYS = {WIFI_ITEM_KEY, BLUETOOTH_ITEM_KEY}
CONFIRM_ITEM_KEYS = {UPDATE_ITEM_KEY, RESTART_ITEM_KEY, SHUTDOWN_ITEM_KEY}
DESTRUCTIVE_ITEM_KEYS = {RESTART_ITEM_KEY, SHUTDOWN_ITEM_KEY}
STATUS_POLL_INTERVAL = 1.0
MENU_GRADIENT_STEPS = 40
ROUNDED_SHAPE_AA_SCALE = 4
BRIGHTNESS_DEFAULT = 80
BRIGHTNESS_MIN_PERCENT = 10
BRIGHTNESS_ADJUST_STEP = 2
XRANDR_BRIGHTNESS_FLOOR = 0.15
DETAIL_PANEL_SIDE_PAD = 18
DETAIL_PANEL_TOP_PAD = 12
DETAIL_PANEL_BOTTOM_PAD = 14
DETAIL_PANEL_ROW_HEIGHT = 28
DETAIL_PANEL_ROW_GAP = 6
DETAIL_PANEL_RADIUS = 14
DETAIL_PANEL_ITEM_RADIUS = 10
DETAIL_LIST_PANEL_OUTER_PAD_X = 22
DETAIL_LIST_PANEL_SIDE_PAD = 16
DETAIL_LIST_PANEL_ITEM_INSET_X = 8
DETAIL_LIST_PANEL_ITEM_TEXT_PAD_X = 12
DETAIL_LIST_PANEL_TITLE_OFFSET_Y = 18
DETAIL_LIST_PANEL_ROWS_TOP_GAP = 30
DETAIL_LIST_PANEL_ROW_HEIGHT = 30
DETAIL_LIST_PANEL_ROW_GAP = 8
DETAIL_LIST_PANEL_BOTTOM_PAD = 10
DETAIL_LIST_PANEL_ITEM_TITLE_OFFSET_Y = 9
DETAIL_LIST_PANEL_ITEM_META_OFFSET_Y = 21
DETAIL_LIST_PANEL_BASE_HEIGHT = (
    DETAIL_PANEL_TOP_PAD
    + DETAIL_LIST_PANEL_TITLE_OFFSET_Y
    + DETAIL_LIST_PANEL_ROWS_TOP_GAP
    + DETAIL_LIST_PANEL_BOTTOM_PAD
    + DETAIL_PANEL_BOTTOM_PAD
)
DETAIL_CONFIRM_PANEL_OUTER_PAD_X = DETAIL_LIST_PANEL_OUTER_PAD_X
DETAIL_CONFIRM_PANEL_SIDE_PAD = DETAIL_LIST_PANEL_SIDE_PAD
DETAIL_CONFIRM_PANEL_ITEM_INSET_X = DETAIL_LIST_PANEL_ITEM_INSET_X
DETAIL_CONFIRM_PANEL_TITLE_OFFSET_Y = 18
DETAIL_CONFIRM_PANEL_NOTE_OFFSET_Y = 18
DETAIL_CONFIRM_PANEL_BUTTON_TOP_GAP = 16
DETAIL_CONFIRM_PANEL_BUTTON_HEIGHT = 32
DETAIL_CONFIRM_PANEL_BOTTOM_PAD = 10
DETAIL_CONFIRM_PANEL_BASE_HEIGHT = (
    DETAIL_PANEL_TOP_PAD
    + DETAIL_CONFIRM_PANEL_TITLE_OFFSET_Y
    + DETAIL_CONFIRM_PANEL_NOTE_OFFSET_Y
    + DETAIL_CONFIRM_PANEL_BUTTON_TOP_GAP
    + DETAIL_CONFIRM_PANEL_BUTTON_HEIGHT
    + DETAIL_CONFIRM_PANEL_BOTTOM_PAD
    + DETAIL_PANEL_BOTTOM_PAD
)
PROMPT_HINT_GAP = 6
MENU_CONFIRM_RADIUS = 10
DETAIL_PANEL_SECTION_GAP = 10
SLIDER_TRACK_HEIGHT = 8
SLIDER_KNOB_RADIUS = 10
SLIDER_THUMB_ICON_SIZE = 20
SLIDER_LABEL_FONT = (FONT_FAMILY, 10, "bold")
SLIDER_TOUCH_PAD_X = 16
SLIDER_TOUCH_PAD_Y = 18
MENU_FOCUS_INSET = 2
MENU_FOCUS_RADIUS = max(0, MENU_ROW_RADIUS - MENU_FOCUS_INSET)
MENU_LIST_MAX_ITEMS = 4
TOUCH_SCROLL_DRAG_THRESHOLD = 10
TOUCH_SCROLL_SETTLE_SEC = 0.35
HOLDABLE_ADJUST_ITEM_KEYS = {VOLUME_ITEM_KEY, BRIGHTNESS_ITEM_KEY}
DPAD_HOLD_INITIAL_DELAY_SEC = 0.28
DPAD_HOLD_REPEAT_SEC = 0.055
DPAD_HOLD_POLL_SEC = 0.01
BLUETOOTH_SCAN_SECONDS = 6
BLUETOOTH_PRE_CONNECT_SCAN_SECONDS = 3
BLUETOOTH_POST_ACTION_SCAN_SECONDS = 1
BLUETOOTH_ACTION_TIMEOUT_SEC = 24
BLUETOOTH_CONNECTION_WAIT_SEC = 8.0
BLUETOOTH_PAIRING_WAIT_SEC = 12.0
BLUETOOTH_DEVICE_LIST_MAX_ITEMS = 10
BLUETOOTH_AGENT_CAPABILITY = "KeyboardDisplay"
BLUETOOTH_OPEN_SCAN_DELAY_MS = 220
WIFI_ACTION_TIMEOUT_SEC = 24
WIFI_CONNECTION_WAIT_SEC = 6.0
WIFI_NETWORK_LIST_MAX_ITEMS = 4
WIFI_SCAN_RETRY_DELAYS_SEC = (0.0, 0.2, 0.55)
WIFI_PASSWORD_MODAL_WIDTH = 360
WIFI_PASSWORD_MODAL_SIDE_PAD = 20
WIFI_PASSWORD_MODAL_TOP_PAD = 18
WIFI_PASSWORD_TOGGLE_ICON_SIZE = 18
TOAST_BG = "#1e1e24"
TOAST_BORDER = "#3a3d4a"
TOAST_TEXT = "#f5f7fb"
TOAST_FONT = (FONT_FAMILY, 10, "bold")
TOAST_PAD_X = 10
TOAST_PAD_Y = 6
TOAST_OFFSET_Y = 12
CONNECTION_TOAST_DURATION_MS = 1100
CONNECTION_TOAST_LABEL_MAX = 18
BATTERY_LOW_PERCENT = 20
BATTERY_LOW_TOAST_DURATION_MS = 1800
BLUETOOTH_ADDR_RE = r"[0-9A-F]{2}(?::[0-9A-F]{2}){5}"
BLUETOOTH_PLACEHOLDER_ADDR_RE = r"[0-9A-F]{2}(?:[:-][0-9A-F]{2}){5}"
ANSI_ESCAPE_RE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
BLUETOOTH_DEVICE_RE = re.compile(rf"^Device\s+({BLUETOOTH_ADDR_RE})(?:\s+(.+))?$", re.IGNORECASE)
SOUND_SAMPLE_RATE = 22050
SOUND_MASTER_GAIN = 0.28
SOUND_ENVELOPE_FLOOR = 0.0008
SOUND_SCROLL_MIN_INTERVAL_SEC = 0.055
SOUND_SLIDER_MIN_INTERVAL_SEC = 0.05
SOUND_RESTART_DELAY_MS = 220
SOUND_SHUTDOWN_DELAY_MS = 340


def run_text(cmd, env=None):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=4, env=env)
        return result.stdout.strip()
    except Exception:
        return ""


def nmcli_text(args, privileged=False, timeout=4):
    base_cmd = PRIVILEGED_NMCLI_CMD if privileged else NMCLI_CMD
    return run_text([*base_cmd, *args], env=display_env())


def strip_ansi(value):
    return ANSI_ESCAPE_RE.sub("", value or "").replace("\r", "")


def run_command_output(cmd, timeout=4, env=None, input_text=None):
    try:
        result = subprocess.run(
            cmd,
            input=input_text,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        output = "\n".join(part for part in (exc.stdout, exc.stderr) if part)
        return False, strip_ansi(output).strip() or "Command timed out"
    except Exception as exc:
        return False, str(exc)
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return result.returncode == 0, strip_ansi(output).strip()


def run_nmcli_output(args, privileged=False, timeout=4):
    base_cmd = PRIVILEGED_NMCLI_CMD if privileged else NMCLI_CMD
    return run_command_output([*base_cmd, *args], timeout=timeout, env=display_env())


def bluetoothctl_text(args, timeout=4):
    try:
        result = subprocess.run(
            ["bluetoothctl", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception:
        return ""
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return strip_ansi(output).strip()


def run_bluetoothctl_script(commands, timeout=8):
    script_lines = [str(command).strip() for command in commands if str(command).strip()]
    if not script_lines:
        return ""
    script = "\n".join([*script_lines, "quit"]) + "\n"
    try:
        result = subprocess.run(
            ["bluetoothctl", "--agent", BLUETOOTH_AGENT_CAPABILITY],
            input=script,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception:
        return ""
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    return strip_ansi(output).strip()


def parse_bluetooth_devices(text):
    devices = {}
    for raw_line in strip_ansi(text).splitlines():
        match = BLUETOOTH_DEVICE_RE.match(raw_line.strip())
        if not match:
            continue
        address = match.group(1).upper()
        name = (match.group(2) or "").strip() or address
        devices[address] = name
    return devices


def bluetooth_devices(filter_name=None):
    args = ["devices"]
    if filter_name:
        args.append(filter_name)
    return parse_bluetooth_devices(bluetoothctl_text(args))


def parse_bluetooth_info(text):
    info = {}
    for raw_line in strip_ansi(text).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = re.match(rf"^Device\s+({BLUETOOTH_ADDR_RE})", line, re.IGNORECASE)
        if match:
            info["address"] = match.group(1).upper()
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        info[key.strip().lower()] = value.strip()
    return {
        "address": info.get("address", ""),
        "name": info.get("alias") or info.get("name") or "",
        "icon": info.get("icon", ""),
        "paired": info.get("paired", "").lower() == "yes",
        "trusted": info.get("trusted", "").lower() == "yes",
        "connected": info.get("connected", "").lower() == "yes",
    }


def bluetooth_device_info(address):
    if not address:
        return {}
    return parse_bluetooth_info(bluetoothctl_text(["info", address], timeout=4))


def bluetooth_scan_results(scan_seconds=BLUETOOTH_SCAN_SECONDS):
    if scan_seconds <= 0:
        return {}
    output = bluetoothctl_text(["--timeout", str(scan_seconds), "scan", "on"], timeout=scan_seconds + 2)
    results = {}
    for raw_line in strip_ansi(output).splitlines():
        if "Device " not in raw_line:
            continue
        match = re.search(rf"Device\s+({BLUETOOTH_ADDR_RE})(?:\s+(.+))?$", raw_line, re.IGNORECASE)
        if not match:
            continue
        address = match.group(1).upper()
        suffix = (match.group(2) or "").strip()
        entry = results.setdefault(address, {"address": address})
        if suffix and not suffix.startswith(("RSSI:", "TxPower:", "ManufacturerData")):
            entry["name"] = suffix
        rssi_match = re.search(r"RSSI:\s+[^\(]*\((-?\d+)\)", raw_line)
        if rssi_match:
            try:
                entry["rssi"] = int(rssi_match.group(1))
            except ValueError:
                pass
    return results


def bluetooth_session_setup_commands():
    return ["default-agent", "pairable on"]


def bluetooth_connect_commands(address, already_paired=False):
    commands = [*bluetooth_session_setup_commands()]
    if not already_paired:
        commands.extend([f"pair {address}", "yes", "yes", "yes"])
    commands.extend([f"trust {address}", f"connect {address}", "yes", "yes"])
    return commands


def bluetooth_type_label(icon_name, device_name):
    icon_map = {
        "audio-card": "Speaker",
        "audio-headphones": "Headphones",
        "audio-headset": "Headset",
        "input-gaming": "Controller",
        "input-gamepad": "Controller",
        "input-keyboard": "Keyboard",
        "input-mouse": "Mouse",
        "input-tablet": "Tablet",
        "multimedia-player": "Player",
        "phone": "Phone",
        "computer": "Computer",
    }
    icon_key = (icon_name or "").strip().lower()
    if icon_key in icon_map:
        return icon_map[icon_key]

    name = (device_name or "").strip().lower()
    if any(token in name for token in ("controller", "gamepad", "xbox", "dualshock", "dualsense", "joy-con")):
        return "Controller"
    if "keyboard" in name:
        return "Keyboard"
    if "mouse" in name:
        return "Mouse"
    if any(token in name for token in ("earbud", "earbuds", "earphone", "earphones", "airpods", "buds")):
        return "Earbuds"
    if any(token in name for token in ("headphone", "headphones")):
        return "Headphones"
    if "headset" in name:
        return "Headset"
    if any(token in name for token in ("speaker", "marshall", "bose", "soundlink", "jbl", "sony wh", "edifier")):
        return "Speaker"
    return "Device"


def normalize_bluetooth_address(value):
    return str(value or "").strip().replace("-", ":").upper()


def bluetooth_name_is_placeholder(name, address=""):
    normalized = (name or "").strip()
    if not normalized:
        return True
    normalized_name_address = normalize_bluetooth_address(normalized)
    normalized_address = normalize_bluetooth_address(address)
    if normalized_address and normalized_name_address == normalized_address:
        return True
    if re.fullmatch(BLUETOOTH_PLACEHOLDER_ADDR_RE, normalized, re.IGNORECASE):
        return True
    if re.fullmatch(r"unknown\s+\[[^\]]+\]", normalized, re.IGNORECASE):
        return True
    return normalized.lower() in {"unknown", "(unknown)", "n/a"}


def bluetooth_display_name(name, icon_name="", address=""):
    normalized = (name or "").strip()
    if not bluetooth_name_is_placeholder(normalized, address):
        return normalized
    type_label = bluetooth_type_label(icon_name, "")
    return f"Unknown [{type_label}]"


def bluetooth_error_message(output, default):
    lines = [line.strip() for line in strip_ansi(output).splitlines() if line.strip()]
    for line in reversed(lines):
        normalized = line.lower()
        if any(
            token in normalized
            for token in (
                "failed",
                "error",
                "not available",
                "not ready",
                "no default controller available",
                "timed out",
                "timeout",
                "authentication",
                "rejected",
                "aborted",
                "le-connection-abort-by-local",
                "org.bluez.error",
            )
        ):
            return line
    return default


def bluetooth_state_snapshot():
    details = bluetoothctl_text(["show"])
    enabled = "Powered: yes" in details
    connected_devices = [
        {"address": address, "name": name}
        for address, name in bluetooth_devices("Connected").items()
    ] if enabled else []
    return enabled, connected_devices


def wait_for_bluetooth_device_state(address, connected=None, paired=None, timeout_sec=3.0):
    deadline = time.monotonic() + max(0.1, timeout_sec)
    last_info = bluetooth_device_info(address)
    while time.monotonic() < deadline:
        info = bluetooth_device_info(address)
        if info:
            last_info = info
        if connected is not None and info.get("connected") != connected:
            time.sleep(0.25)
            continue
        if paired is not None and info.get("paired") != paired:
            time.sleep(0.25)
            continue
        return info or last_info
    return last_info


def display_env():
    release_home = str(WORKSPACE_ROOT / "release")
    env = dict(os.environ)
    env["DISPLAY"] = env.get("DISPLAY", ":0")
    env["HOME"] = release_home
    env["XDG_CONFIG_HOME"] = f"{release_home}/.config"
    env["XDG_DATA_HOME"] = f"{release_home}/.local/share"
    env["XDG_CACHE_HOME"] = f"{release_home}/.cache"
    runtime_dir = f"/run/user/{os.getuid()}"
    if os.path.isdir(runtime_dir):
        env["XDG_RUNTIME_DIR"] = runtime_dir
    xauthority = env.get("XAUTHORITY", "")
    if not xauthority or not os.path.exists(xauthority):
        for candidate in (
            f"{release_home}/.Xauthority",
            os.path.join(release_home, ".cache", ".Xauthority"),
            "/home/pi/.Xauthority",
        ):
            if os.path.exists(candidate):
                env["XAUTHORITY"] = candidate
                break
    return env


def spawn_detached(cmd, extra_env=None):
    env = display_env()
    if extra_env:
        env.update(extra_env)
    try:
        subprocess.Popen(cmd, env=env, start_new_session=True)
        return True
    except Exception:
        return False


def is_running(name):
    return subprocess.run(["pgrep", "-f", name], capture_output=True).returncode == 0


def kill_process(name):
    subprocess.run(["pkill", "-f", name], capture_output=True)


def current_time():
    return time.strftime("%I:%M %p").lower()


def normalize_battery_percent(value):
    try:
        return max(0, min(int(value), 100))
    except (TypeError, ValueError):
        return None


def parse_charging_state(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"charging", "true", "1", "yes", "on", "pending-charge"}:
            return True
        if normalized in {"discharging", "fully-charged", "false", "0", "no", "off", "pending-discharge"}:
            return False
    return None


def parse_battery_output(text):
    text = text.strip()
    if not text:
        return None, None

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        payload = None

    if isinstance(payload, dict):
        percent = normalize_battery_percent(payload.get("percent"))
        charging = parse_charging_state(payload.get("charging", payload.get("state")))
        if percent is not None:
            return percent, charging

    match = re.search(r"(\d+)", text)
    if not match:
        return None, None
    return normalize_battery_percent(match.group(1)), None


def upower_battery():
    devices = run_text(["upower", "-e"])
    for line in devices.splitlines():
        if "battery" not in line.lower():
            continue
        details = run_text(["upower", "-i", line])
        match = re.search(r"percentage:\s+(\d+)%", details)
        if not match:
            continue
        state_match = re.search(r"state:\s+([^\n]+)", details, re.IGNORECASE)
        charging = parse_charging_state(state_match.group(1)) if state_match else None
        return normalize_battery_percent(match.group(1)), charging
    return None, None


def battery_status():
    if BATTERY_COMMAND:
        try:
            percent, charging = parse_battery_output(run_text(shlex.split(BATTERY_COMMAND)))
            if percent is not None:
                return percent, charging
        except Exception:
            pass
    return upower_battery()


def battery_color(percent):
    if percent is None:
        return TEXT_DIM
    if percent >= 60:
        return ACCENT
    if percent >= 30:
        return MID
    return WARN


def unescape_nmcli(value):
    return value.replace("\\:", ":").replace("\\\\", "\\").strip()


def command_error_message(output, default):
    lines = [line.strip() for line in strip_ansi(output).splitlines() if line.strip()]
    if not lines:
        return default
    return lines[-1]


def parse_command_metadata(output, prefix):
    data = {}
    for raw_line in strip_ansi(output).splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key.startswith(prefix):
            continue
        data[key] = value.strip()
    return data


def grayscale_color(value):
    shade = max(0, min(255, int(round((max(0, min(100, value)) / 100.0) * 255))))
    return f"#{shade:02x}{shade:02x}{shade:02x}"


def software_version_label(version_text=None):
    version = str(version_text if version_text is not None else read_workspace_version()).strip()
    if not version:
        return "Unknown"
    if version.lower() == "unknown":
        return "Unknown"
    if version.lower().startswith("v"):
        return version
    return f"v{version}"


def split_nmcli_wifi_line(line):
    match = re.match(r"^(yes|no):([^:]*):([^:]*):(.*)$", line.strip())
    if not match:
        return None
    security = match.group(3).strip()
    if security in {"--", "NONE"}:
        security = ""
    return {
        "active": match.group(1) == "yes",
        "signal": max(0, min(int(match.group(2) or 0), 100)),
        "security": security,
        "ssid": unescape_nmcli(match.group(4)) or "Hidden network",
    }


def wifi_security_requires_password(network):
    return bool(str(network.get("security", "")).strip())


def current_wifi_device():
    text = nmcli_text(["-t", "-f", "DEVICE,TYPE", "device", "status"])
    for line in text.splitlines():
        try:
            device_name, device_type = line.split(":", 1)
        except ValueError:
            continue
        if device_type.strip() != "wifi":
            continue
        if device_name.startswith("p2p-"):
            continue
        return device_name.strip()
    return ""


def saved_wifi_profiles_for_ssid(target_ssid):
    normalized_target = str(target_ssid or "").strip()
    if not normalized_target:
        return []

    profiles = []
    text = nmcli_text(["-t", "-f", "UUID,TYPE", "connection", "show"])
    for line in text.splitlines():
        try:
            profile_uuid, connection_type = line.split(":", 1)
        except ValueError:
            continue
        if connection_type.strip() != "802-11-wireless":
            continue

        details = nmcli_text(
            [
                "-g",
                "connection.id,802-11-wireless.ssid,802-11-wireless-security.key-mgmt,connection.timestamp",
                "connection",
                "show",
                profile_uuid.strip(),
            ]
        )
        detail_lines = [item.strip() for item in details.splitlines()]
        if len(detail_lines) < 2:
            continue

        profile_ssid = detail_lines[1]
        if profile_ssid != normalized_target:
            continue

        try:
            timestamp = int(detail_lines[3]) if len(detail_lines) > 3 and detail_lines[3] else 0
        except ValueError:
            timestamp = 0

        profiles.append(
            {
                "uuid": profile_uuid.strip(),
                "id": detail_lines[0] or profile_uuid.strip(),
                "ssid": profile_ssid,
                "key_mgmt": detail_lines[2] if len(detail_lines) > 2 else "",
                "timestamp": timestamp,
            }
        )
    return profiles


def preferred_wifi_profile(network, password=None):
    ssid = str(network.get("ssid", "")).strip()
    profiles = saved_wifi_profiles_for_ssid(ssid)
    if not profiles:
        return None

    requires_password = wifi_security_requires_password(network) or bool(password)
    profiles.sort(
        key=lambda profile: (
            0 if (bool(profile.get("key_mgmt")) == requires_password) else 1,
            0 if str(profile.get("id", "")).startswith("netplan-") else 1,
            -int(profile.get("timestamp", 0)),
            str(profile.get("id", "")).lower(),
        )
    )
    return profiles[0]


def activate_saved_wifi_profile(profile, device_name="", password=None):
    profile_ref = str(profile.get("uuid") or profile.get("id") or "").strip()
    if not profile_ref:
        return False, "Saved WiFi profile unavailable"

    if password:
        success, output = run_nmcli_output(
            [
                "connection",
                "modify",
                profile_ref,
                "802-11-wireless-security.key-mgmt",
                "wpa-psk",
                "802-11-wireless-security.psk",
                password,
            ],
            privileged=True,
            timeout=8,
        )
        if not success:
            return False, output

    cmd = ["--wait", str(WIFI_ACTION_TIMEOUT_SEC), "connection", "up", profile_ref]
    if device_name:
        cmd.extend(["ifname", device_name])
    return run_nmcli_output(cmd, privileged=True, timeout=WIFI_ACTION_TIMEOUT_SEC + 4)


def nearby_wifi_networks(rescan=True):
    text = nmcli_text(
        [
            "-t",
            "-f",
            "ACTIVE,SIGNAL,SECURITY,SSID",
            "dev",
            "wifi",
            "list",
            "--rescan",
            "yes" if rescan else "no",
        ],
        privileged=True,
    )
    network_map = {}
    for line in text.splitlines():
        network = split_nmcli_wifi_line(line)
        if not network:
            continue
        dedupe_key = (network["ssid"], network["security"])
        existing = network_map.get(dedupe_key)
        if existing is None:
            network_map[dedupe_key] = network
            continue
        if network["active"] and not existing["active"]:
            network_map[dedupe_key] = network
            continue
        if network["signal"] > existing["signal"]:
            network_map[dedupe_key] = network
    networks = list(network_map.values())
    networks.sort(key=lambda item: (0 if item["active"] else 1, -item["signal"], item["ssid"].lower()))
    return networks[:WIFI_NETWORK_LIST_MAX_ITEMS]


def wifi_network_signature(networks):
    return tuple(
        (
            item.get("ssid", ""),
            item.get("security", ""),
            bool(item.get("active")),
            int(item.get("signal", 0)),
        )
        for item in networks
    )


def refresh_wifi_networks(previous_networks=None):
    baseline_networks = previous_networks if previous_networks is not None else nearby_wifi_networks(rescan=False)
    baseline_signature = wifi_network_signature(baseline_networks)
    run_nmcli_output(["device", "wifi", "rescan"], privileged=True, timeout=4)
    latest_networks = list(baseline_networks)
    for delay in WIFI_SCAN_RETRY_DELAYS_SEC:
        if delay > 0:
            time.sleep(delay)
        latest_networks = nearby_wifi_networks(rescan=False)
        if wifi_network_signature(latest_networks) != baseline_signature:
            break
    return latest_networks


def nearby_bluetooth_devices(scan_seconds=BLUETOOTH_SCAN_SECONDS):
    enabled, _connected_devices = bluetooth_state_snapshot()
    if not enabled:
        return []

    paired_map = bluetooth_devices("Paired")
    connected_map = bluetooth_devices("Connected")
    known_map = bluetooth_devices()
    scanned_map = bluetooth_scan_results(scan_seconds=scan_seconds)

    candidate_map = {}
    for address, name in known_map.items():
        candidate_map.setdefault(address, {"address": address, "name": name or address})
        candidate_map[address]["known"] = True
    for address, name in paired_map.items():
        candidate_map.setdefault(address, {"address": address, "name": name or known_map.get(address, address)})
        candidate_map[address]["paired"] = True
    for address, name in connected_map.items():
        candidate_map.setdefault(address, {"address": address, "name": name or known_map.get(address, address)})
        candidate_map[address]["connected"] = True
    for address, payload in scanned_map.items():
        candidate_map.setdefault(
            address,
            {"address": address, "name": payload.get("name") or known_map.get(address, address)},
        )
        candidate_map[address]["scanned"] = True
        if payload.get("name"):
            candidate_map[address]["name"] = payload["name"]
        if payload.get("rssi") is not None:
            candidate_map[address]["rssi"] = payload["rssi"]

    if not scanned_map and not candidate_map:
        return []

    devices = list(candidate_map.values())

    def candidate_sort_key(item):
        rssi = item.get("rssi")
        placeholder_name = bluetooth_name_is_placeholder(item.get("name", ""), item.get("address", ""))
        return (
            0 if not placeholder_name else 1,
            0 if item.get("connected") else 1,
            0 if item.get("paired") else 1,
            0 if item.get("scanned") else 1,
            0 if rssi is not None else 1,
            -rssi if rssi is not None else 999,
            bluetooth_display_name(
                item.get("name", ""),
                item.get("icon", ""),
                item.get("address", ""),
            ).lower(),
        )

    devices.sort(key=candidate_sort_key)
    devices = devices[:BLUETOOTH_DEVICE_LIST_MAX_ITEMS]

    for device in devices:
        info = bluetooth_device_info(device["address"])
        raw_name = device.get("name", "")
        if info.get("name"):
            raw_name = info["name"]
        if info:
            device["paired"] = info.get("paired", device.get("paired", False))
            device["connected"] = info.get("connected", device.get("connected", False))
            device["trusted"] = info.get("trusted", False)
            device["icon"] = info.get("icon", "")
        device["known"] = bool(device.get("known", False))
        device["paired"] = bool(device.get("paired", False))
        device["connected"] = bool(device.get("connected", False))
        device["trusted"] = bool(device.get("trusted", False))
        device["type"] = bluetooth_type_label(device.get("icon", ""), raw_name)
        device["has_custom_name"] = not bluetooth_name_is_placeholder(raw_name, device["address"])
        device["name"] = bluetooth_display_name(raw_name, device.get("icon", ""), device["address"])

    devices.sort(key=candidate_sort_key)
    return devices


def wifi_status():
    if nmcli_text(["-t", "-f", "WIFI", "g"]).strip().lower() != "enabled":
        return 0, "disabled", ""

    text = nmcli_text(["-t", "-f", "ACTIVE,SIGNAL,SSID", "dev", "wifi", "list", "--rescan", "no"])
    for line in text.splitlines():
        match = re.match(r"^yes:([^:]*):(.*)$", line)
        if not match:
            continue
        return max(0, min(int(match.group(1) or 0), 100)), "connected", unescape_nmcli(match.group(2)) or "Hidden network"
    return 0, "offline", ""


def set_wifi_power(enabled):
    command = "on" if enabled else "off"
    success, output = run_nmcli_output(["radio", "wifi", command], privileged=True, timeout=8)
    last_state = wifi_status()[1]
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        state = wifi_status()[1]
        if enabled and state != "disabled":
            return True, ""
        if not enabled and state == "disabled":
            return True, ""
        time.sleep(0.25)
    message = command_error_message(output, f"WiFi stayed {'on' if last_state != 'disabled' else 'off'}")
    return False, message


def wait_for_wifi_connection(target_ssid="", timeout_sec=WIFI_CONNECTION_WAIT_SEC):
    normalized_target = str(target_ssid or "").strip()
    last_state = wifi_status()
    deadline = time.monotonic() + max(0.5, timeout_sec)
    while time.monotonic() < deadline:
        snapshot = wifi_status()
        last_state = snapshot
        signal, state, ssid = snapshot
        if state == "connected" and (not normalized_target or ssid == normalized_target):
            return signal, state, ssid
        time.sleep(0.25)
    return last_state


def wifi_connect_network(network, password=None):
    ssid = str(network.get("ssid", "")).strip()
    if not ssid:
        return False, "WiFi name unavailable"
    if network.get("active"):
        return True, ""

    device_name = current_wifi_device()
    last_error = ""

    saved_profile = preferred_wifi_profile(network, password=password)
    if saved_profile is not None:
        success, output = activate_saved_wifi_profile(saved_profile, device_name=device_name, password=password)
        _signal, state, connected_ssid = wait_for_wifi_connection(ssid)
        if state == "connected" and connected_ssid == ssid:
            return True, ""
        last_error = command_error_message(output, f"Failed to activate saved WiFi profile for {ssid}")

    cmd = ["--wait", str(WIFI_ACTION_TIMEOUT_SEC), "device", "wifi", "connect", ssid]
    if password:
        cmd.extend(["password", password])
    if device_name:
        cmd.extend(["ifname", device_name])
    success, output = run_nmcli_output(cmd, privileged=True, timeout=WIFI_ACTION_TIMEOUT_SEC + 4)
    _signal, state, connected_ssid = wait_for_wifi_connection(ssid)
    if state == "connected" and connected_ssid == ssid:
        return True, ""
    if last_error:
        return False, command_error_message(output, last_error)
    return False, command_error_message(output, f"Failed to connect to {ssid}")


def volume_status():
    text = run_text(["amixer", "get", "Master"])
    if not text:
        return None, True
    level_match = re.search(r"\[(\d+)%\]", text)
    switch_match = re.search(r"\[(on|off)\]", text)
    level = int(level_match.group(1)) if level_match else None
    muted = switch_match.group(1) == "off" if switch_match else level in {None, 0}
    return level, muted


def volume_value(level, muted, default=50):
    if muted:
        return 0
    return level if level is not None else default


def get_volume():
    level, muted = volume_status()
    return volume_value(level, muted)


def set_volume(value):
    value = max(0, min(100, int(value)))
    try:
        cmd = ["amixer", "-q", "-M", "set", "Master", f"{value}%"]
        cmd.append("mute" if value <= 0 else "unmute")
        subprocess.run(cmd, capture_output=True, timeout=4)
    except Exception:
        pass
    return value


def clamp_brightness_percent(value):
    return max(BRIGHTNESS_MIN_PERCENT, min(100, int(value)))


def brightness_fraction_from_percent(value):
    percent = clamp_brightness_percent(value)
    return XRANDR_BRIGHTNESS_FLOOR + ((1.0 - XRANDR_BRIGHTNESS_FLOOR) * (percent / 100.0))


def brightness_percent_from_fraction(value):
    try:
        fraction = float(value)
    except (TypeError, ValueError):
        return None
    fraction = max(XRANDR_BRIGHTNESS_FLOOR, min(1.0, fraction))
    if XRANDR_BRIGHTNESS_FLOOR >= 1.0:
        return 100
    percent = round(((fraction - XRANDR_BRIGHTNESS_FLOOR) * 100.0) / (1.0 - XRANDR_BRIGHTNESS_FLOOR))
    return max(0, min(100, int(percent)))


def read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read().strip()
    except OSError:
        return ""


def backlight_devices():
    root = "/sys/class/backlight"
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return []

    devices = []
    for name in names:
        device_dir = os.path.join(root, name)
        max_text = read_text_file(os.path.join(device_dir, "max_brightness"))
        try:
            max_value = int(max_text)
        except (TypeError, ValueError):
            continue
        devices.append(
            {
                "name": name,
                "dir": device_dir,
                "display_name": read_text_file(os.path.join(device_dir, "display_name")),
                "max_brightness": max(1, max_value),
            }
        )
    return devices


def current_backlight_devices():
    devices = backlight_devices()
    if not devices:
        return []

    if BRIGHTNESS_BACKLIGHT:
        override_matches = [
            device
            for device in devices
            if device["name"] == BRIGHTNESS_BACKLIGHT or device["display_name"] == BRIGHTNESS_BACKLIGHT
        ]
        if override_matches:
            return override_matches

    preferred_output = current_xrandr_output()
    if preferred_output:
        preferred_matches = [device for device in devices if device["display_name"] == preferred_output]
        if preferred_matches:
            return preferred_matches[:1]

    active_outputs = {output["name"] for output in connected_xrandr_outputs()}
    exact_matches = [device for device in devices if device["display_name"] in active_outputs]
    if len(exact_matches) == 1:
        return exact_matches

    for preferred in ("DSI-1", "DSI-2"):
        matches = [device for device in devices if device["display_name"] == preferred]
        if matches:
            return matches[:1]

    return devices[:1]


def brightness_percent_from_backlight(raw_value, max_value):
    try:
        raw_value = int(raw_value)
        max_value = int(max_value)
    except (TypeError, ValueError):
        return None
    if max_value <= 0:
        return None
    return max(0, min(100, int(round((raw_value / float(max_value)) * 100.0))))


def get_backlight_brightness():
    devices = current_backlight_devices()
    if not devices:
        return None
    values = []
    for device in devices:
        raw_value = read_text_file(os.path.join(device["dir"], "actual_brightness")) or read_text_file(
            os.path.join(device["dir"], "brightness")
        )
        brightness = brightness_percent_from_backlight(raw_value, device["max_brightness"])
        if brightness is not None:
            values.append(brightness)
    if not values:
        return None
    return clamp_brightness_percent(min(values))


def set_backlight_brightness(value):
    devices = current_backlight_devices()
    if not devices:
        return False
    percent = clamp_brightness_percent(value)
    success_count = 0
    for device in devices:
        raw_value = int(round((percent / 100.0) * device["max_brightness"]))
        raw_value = max(0, min(device["max_brightness"], raw_value))
        try:
            result = subprocess.run(
                ["sudo", "-n", *SET_BACKLIGHT_CMD, device["name"], str(raw_value)],
                capture_output=True,
                timeout=4,
                env=display_env(),
            )
        except Exception:
            continue
        if result.returncode == 0:
            success_count += 1
    if success_count <= 0:
        return False
    reported_value = get_backlight_brightness()
    if reported_value is None:
        return True
    return abs(reported_value - percent) <= 2


def connected_xrandr_outputs():
    text = run_text(["xrandr", "--query"], env=display_env())
    outputs = []
    for line in text.splitlines():
        match = re.match(r"^(\S+)\s+connected(?:\s+primary)?", line)
        if not match:
            continue
        outputs.append(
            {
                "name": match.group(1),
                "primary": " connected primary" in line,
            }
        )
    return outputs


def current_xrandr_output():
    outputs = connected_xrandr_outputs()
    if not outputs:
        return None
    if BRIGHTNESS_OUTPUT:
        for output in outputs:
            if output["name"] == BRIGHTNESS_OUTPUT:
                return output["name"]
    for output in outputs:
        if output["primary"]:
            return output["name"]
    return outputs[0]["name"]


def get_xrandr_brightness():
    output_name = current_xrandr_output()
    if not output_name:
        return None
    text = run_text(["xrandr", "--verbose", "--current"], env=display_env())
    active_output = None
    for line in text.splitlines():
        output_match = re.match(r"^(\S+)\s+connected(?:\s+primary)?", line)
        if output_match:
            active_output = output_match.group(1)
            continue
        if active_output != output_name:
            continue
        brightness_match = re.search(r"Brightness:\s*([0-9]+(?:\.[0-9]+)?)", line)
        if brightness_match:
            return brightness_percent_from_fraction(brightness_match.group(1))
    return None


def format_brightness_command(value):
    if not BRIGHTNESS_COMMAND:
        return None
    percent = clamp_brightness_percent(value)
    fraction = brightness_fraction_from_percent(percent)
    return BRIGHTNESS_COMMAND.format(value=percent, fraction=f"{fraction:.3f}")


def set_display_brightness(value):
    percent = clamp_brightness_percent(value)
    if set_backlight_brightness(percent):
        return True

    formatted_command = format_brightness_command(percent)
    if formatted_command:
        try:
            result = subprocess.run(
                shlex.split(formatted_command),
                capture_output=True,
                timeout=4,
                env=display_env(),
            )
            return result.returncode == 0
        except Exception:
            return False

    output_name = current_xrandr_output()
    if not output_name:
        return False
    try:
        result = subprocess.run(
            [
                "xrandr",
                "--output",
                output_name,
                "--brightness",
                f"{brightness_fraction_from_percent(percent):.3f}",
            ],
            capture_output=True,
            timeout=4,
            env=display_env(),
        )
        return result.returncode == 0
    except Exception:
        return False


def get_display_brightness(default=BRIGHTNESS_DEFAULT):
    brightness = get_backlight_brightness()
    if brightness is not None:
        return clamp_brightness_percent(brightness)
    brightness = get_xrandr_brightness()
    if brightness is None:
        return clamp_brightness_percent(default)
    return clamp_brightness_percent(brightness)


def bluetooth_status():
    enabled, _connected_devices = bluetooth_state_snapshot()
    return enabled


def set_bluetooth_power(enabled):
    command = "on" if enabled else "off"
    output = bluetoothctl_text(["power", command], timeout=8)
    deadline = time.monotonic() + 2.5
    last_state = bluetooth_status()
    while time.monotonic() < deadline:
        state = bluetooth_status()
        last_state = state
        if state == enabled:
            if enabled:
                run_bluetoothctl_script(bluetooth_session_setup_commands(), timeout=8)
            return True, ""
        time.sleep(0.2)
    message = bluetooth_error_message(output, f"Bluetooth stayed {'on' if last_state else 'off'}")
    return False, message


def bluetooth_connect_device(address, already_paired=False):
    enabled, _connected_devices = bluetooth_state_snapshot()
    if not enabled:
        success, error = set_bluetooth_power(True)
        if not success:
            return False, bluetooth_device_info(address), error

    bluetooth_scan_results(scan_seconds=BLUETOOTH_PRE_CONNECT_SCAN_SECONDS)
    output = run_bluetoothctl_script(
        bluetooth_connect_commands(address, already_paired=already_paired),
        timeout=BLUETOOTH_ACTION_TIMEOUT_SEC,
    )

    info = wait_for_bluetooth_device_state(
        address,
        connected=True,
        paired=True if not already_paired else None,
        timeout_sec=BLUETOOTH_PAIRING_WAIT_SEC if not already_paired else BLUETOOTH_CONNECTION_WAIT_SEC,
    )
    if info.get("connected"):
        return True, info, ""

    retry_output = ""
    if already_paired or info.get("paired"):
        bluetooth_scan_results(scan_seconds=BLUETOOTH_PRE_CONNECT_SCAN_SECONDS)
        retry_output = run_bluetoothctl_script(
            bluetooth_connect_commands(address, already_paired=True),
            timeout=max(12, BLUETOOTH_ACTION_TIMEOUT_SEC // 2),
        )
        info = wait_for_bluetooth_device_state(
            address,
            connected=True,
            timeout_sec=BLUETOOTH_CONNECTION_WAIT_SEC,
        )
        if info.get("connected"):
            return True, info, ""

    combined_output = "\n".join(part for part in (output, retry_output) if part)
    if not already_paired and info.get("paired"):
        return False, info, bluetooth_error_message(combined_output, "Paired, but connection failed")
    return False, info, bluetooth_error_message(combined_output, "Bluetooth connection failed")


def bluetooth_disconnect_device(address):
    output = bluetoothctl_text(["disconnect", address], timeout=12)
    info = wait_for_bluetooth_device_state(address, connected=False, timeout_sec=2.5)
    if not info.get("connected"):
        return True, info, ""
    return False, info, bluetooth_error_message(output, "Bluetooth disconnect failed")


def default_status_snapshot():
    return {
        "wifi_signal": 0,
        "wifi_state": "offline",
        "wifi_name": "",
        "bluetooth_enabled": False,
        "bluetooth_connected_devices": [],
        "volume_level": 50,
        "volume_muted": False,
        "battery_percent": None,
        "battery_charging": None,
    }


def build_status_snapshot():
    wifi_signal, wifi_state, wifi_name = wifi_status()
    bluetooth_enabled, bluetooth_connected_devices = bluetooth_state_snapshot()
    volume_level, volume_muted = volume_status()
    battery_percent, battery_charging = battery_status()
    return {
        "wifi_signal": wifi_signal,
        "wifi_state": wifi_state,
        "wifi_name": wifi_name,
        "bluetooth_enabled": bluetooth_enabled,
        "bluetooth_connected_devices": bluetooth_connected_devices,
        "volume_level": volume_level,
        "volume_muted": volume_muted,
        "battery_percent": battery_percent,
        "battery_charging": battery_charging,
    }


class StatusPoller:
    def __init__(self):
        self.lock = threading.Lock()
        self.snapshot = default_status_snapshot()
        self.refresh_event = threading.Event()
        self.manual_generation = 0
        threading.Thread(target=self.run, daemon=True).start()

    def get_snapshot(self):
        with self.lock:
            return dict(self.snapshot)

    def set_snapshot(self, snapshot, request_refresh=True):
        if not snapshot:
            return False
        with self.lock:
            self.snapshot = dict(snapshot)
            self.manual_generation += 1
        if request_refresh:
            self.refresh_event.set()
        return True

    def run(self):
        while True:
            with self.lock:
                manual_generation = self.manual_generation
            snapshot = build_status_snapshot()
            with self.lock:
                if manual_generation == self.manual_generation:
                    self.snapshot = snapshot
            if self.refresh_event.wait(STATUS_POLL_INTERVAL):
                self.refresh_event.clear()


def create_dock_window(parent, height, y_pos, bg_color):
    window = tk.Toplevel(parent)
    window.geometry(f"{SCREEN_W}x{height}+0+{y_pos}")
    window.configure(bg=bg_color)
    window.overrideredirect(True)
    try:
        window.wm_attributes("-topmost", True)
    except tk.TclError:
        pass
    try:
        window.wm_attributes("-type", "dock")
    except tk.TclError:
        pass
    return window


def configure_default_fonts(root):
    for font_name in (
        "TkDefaultFont",
        "TkTextFont",
        "TkFixedFont",
        "TkMenuFont",
        "TkHeadingFont",
        "TkCaptionFont",
        "TkSmallCaptionFont",
        "TkIconFont",
        "TkTooltipFont",
    ):
        try:
            named_font = tkfont.nametofont(font_name, root=root)
            named_font.configure(family=FONT_FAMILY, size=BASE_FONT_SIZE)
        except tk.TclError:
            continue


def set_widget_cursor(widget, cursor_name):
    try:
        widget.configure(cursor=cursor_name)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        set_widget_cursor(child, cursor_name)


def resolved_cursor_name(hidden):
    if hidden:
        return "none"
    if STANDARD_TOUCH_CURSOR:
        return VISIBLE_POINTER_CURSOR
    return "none"


def ease_in_out_cubic(progress):
    progress = max(0.0, min(1.0, progress))
    if progress < 0.5:
        return 4.0 * progress * progress * progress
    return 1.0 - pow(-2.0 * progress + 2.0, 3) / 2.0


def interpolate_rect(start_rect, end_rect, progress):
    return tuple(
        int(round(start_value + (end_value - start_value) * progress))
        for start_value, end_value in zip(start_rect, end_rect)
    )


@lru_cache(maxsize=None)
def load_prompt_icon(filename):
    path = os.path.join(PROMPT_ICON_DIR, filename)
    try:
        return tk.PhotoImage(file=path)
    except tk.TclError:
        return None


def tint_photo_image(image, color):
    tinted = tk.PhotoImage(width=image.width(), height=image.height())
    for x_pos in range(image.width()):
        for y_pos in range(image.height()):
            transparent = image.transparency_get(x_pos, y_pos)
            if transparent:
                tinted.put("#000000", (x_pos, y_pos))
                tinted.transparency_set(x_pos, y_pos, True)
                continue
            tinted.put(color, (x_pos, y_pos))
            tinted.transparency_set(x_pos, y_pos, False)
    return tinted


def parse_hex_color(color):
    normalized = str(color).strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", normalized):
        raise ValueError(f"unsupported color: {color}")
    return tuple(int(normalized[index:index + 2], 16) for index in (1, 3, 5))


@lru_cache(maxsize=None)
def measure_text_width(font_spec, text):
    try:
        return tkfont.Font(font=font_spec).measure(text)
    except tk.TclError:
        return len(str(text)) * 6


def pixbuf_to_photo_image(pixbuf):
    ok, data = pixbuf.save_to_bufferv("png", [], [])
    if not ok:
        return None
    return tk.PhotoImage(data=base64.b64encode(data).decode("ascii"))


if Image is not None:
    try:
        PIL_LANCZOS = Image.Resampling.LANCZOS
    except AttributeError:
        PIL_LANCZOS = Image.LANCZOS
else:
    PIL_LANCZOS = None


def tint_pixbuf(pixbuf, color):
    red, green, blue = parse_hex_color(color)
    width = pixbuf.get_width()
    height = pixbuf.get_height()
    has_alpha = pixbuf.get_has_alpha()
    rowstride = pixbuf.get_rowstride()
    n_channels = pixbuf.get_n_channels()
    pixels = bytearray(pixbuf.get_pixels())

    for y_pos in range(height):
        row_offset = y_pos * rowstride
        for x_pos in range(width):
            offset = row_offset + (x_pos * n_channels)
            alpha = pixels[offset + 3] if has_alpha and n_channels >= 4 else 255
            if alpha == 0:
                continue
            pixels[offset] = red
            pixels[offset + 1] = green
            pixels[offset + 2] = blue

    tinted = GdkPixbuf.Pixbuf.new_from_data(
        pixels,
        pixbuf.get_colorspace(),
        has_alpha,
        pixbuf.get_bits_per_sample(),
        width,
        height,
        rowstride,
    )
    tinted._pixels = pixels
    return tinted


def photo_image_from_pil(image):
    if image is None:
        return None
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return tk.PhotoImage(data=base64.b64encode(buffer.getvalue()).decode("ascii"))


def retain_canvas_image(canvas, image):
    images = getattr(canvas, "images", None)
    if images is None:
        images = getattr(canvas, "_generated_images", None)
        if images is None:
            images = []
            setattr(canvas, "_generated_images", images)
    images.append(image)


def rounded_shape_bounds(x1, y1, x2, y2):
    left = int(round(min(x1, x2)))
    top = int(round(min(y1, y2)))
    right = int(round(max(x1, x2)))
    bottom = int(round(max(y1, y2)))
    width = max(1, right - left + 1)
    height = max(1, bottom - top + 1)
    return left, top, right, bottom, width, height


def horizontal_gradient_image(width, height, start_color, end_color):
    start_rgb = parse_hex_color(start_color)
    end_rgb = parse_hex_color(end_color)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    for x_pos in range(width):
        progress = 0.0 if width <= 1 else x_pos / float(width - 1)
        color = tuple(
            int(round(start_value + (end_value - start_value) * progress))
            for start_value, end_value in zip(start_rgb, end_rgb)
        )
        draw.line((x_pos, 0, x_pos, height), fill=(*color, 255))
    return image


@lru_cache(maxsize=512)
def antialiased_rounded_shape_image(width, height, radius, fill, border, border_width, start_color="", end_color=""):
    if Image is None or ImageDraw is None or PIL_LANCZOS is None:
        return None
    width = max(1, int(width))
    height = max(1, int(height))
    radius = max(0, int(radius))
    border_width = max(0, int(border_width))
    scale = ROUNDED_SHAPE_AA_SCALE
    scaled_width = max(1, width * scale)
    scaled_height = max(1, height * scale)
    scaled_radius = max(0, min(radius * scale, scaled_width // 2, scaled_height // 2))
    scaled_border = max(0, border_width * scale)

    composed = Image.new("RGBA", (scaled_width, scaled_height), (0, 0, 0, 0))
    outer_mask = Image.new("L", (scaled_width, scaled_height), 0)
    outer_draw = ImageDraw.Draw(outer_mask)
    outer_draw.rounded_rectangle((0, 0, scaled_width - 1, scaled_height - 1), radius=scaled_radius, fill=255)

    if border and scaled_border > 0:
        border_layer = Image.new("RGBA", (scaled_width, scaled_height), (*parse_hex_color(border), 255))
        border_layer.putalpha(outer_mask)
        composed.alpha_composite(border_layer)

    inner_left = scaled_border if border and scaled_border > 0 else 0
    inner_top = scaled_border if border and scaled_border > 0 else 0
    inner_right = scaled_width - 1 - inner_left
    inner_bottom = scaled_height - 1 - inner_top
    if inner_right >= inner_left and inner_bottom >= inner_top and (fill or (start_color and end_color)):
        inner_radius = max(0, min(scaled_radius - scaled_border, (inner_right - inner_left + 1) // 2, (inner_bottom - inner_top + 1) // 2))
        inner_mask = Image.new("L", (scaled_width, scaled_height), 0)
        inner_draw = ImageDraw.Draw(inner_mask)
        inner_draw.rounded_rectangle(
            (inner_left, inner_top, inner_right, inner_bottom),
            radius=inner_radius,
            fill=255,
        )
        if start_color and end_color:
            fill_layer = horizontal_gradient_image(scaled_width, scaled_height, start_color, end_color)
        else:
            fill_layer = Image.new("RGBA", (scaled_width, scaled_height), (*parse_hex_color(fill), 255))
        fill_layer.putalpha(inner_mask)
        composed.alpha_composite(fill_layer)
    elif fill and not border:
        fill_layer = Image.new("RGBA", (scaled_width, scaled_height), (*parse_hex_color(fill), 255))
        fill_layer.putalpha(outer_mask)
        composed.alpha_composite(fill_layer)

    if scale > 1:
        composed = composed.resize((width, height), resample=PIL_LANCZOS)
    return photo_image_from_pil(composed)


def draw_antialiased_rounded_shape(
    canvas,
    x1,
    y1,
    x2,
    y2,
    radius,
    fill,
    border,
    border_width=1,
    start_color="",
    end_color="",
):
    left, top, _right, _bottom, width, height = rounded_shape_bounds(x1, y1, x2, y2)
    image = antialiased_rounded_shape_image(
        width,
        height,
        max(0, int(round(radius))),
        str(fill or ""),
        str(border or ""),
        max(0, int(round(border_width))),
        str(start_color or ""),
        str(end_color or ""),
    )
    if image is None:
        return False
    retain_canvas_image(canvas, image)
    canvas.create_image(left, top, image=image, anchor="nw")
    return True


@lru_cache(maxsize=None)
def load_status_icon(relative_path, color=None, size=None):
    path = os.path.join(STATUS_ICON_DIR, *relative_path.split("/"))
    if GdkPixbuf is not None:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            if size is not None and size > 0 and (pixbuf.get_width() != size or pixbuf.get_height() != size):
                pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
            if color is not None:
                pixbuf = tint_pixbuf(pixbuf, color)
            image = pixbuf_to_photo_image(pixbuf)
            if image is not None:
                return image
        except Exception:
            pass

    try:
        source = tk.PhotoImage(file=path)
    except tk.TclError:
        return None
    if size is not None and size > 0 and source.width() != size and source.height() != size:
        step_x = max(1, source.width() // size)
        step_y = max(1, source.height() // size)
        source = source.subsample(step_x, step_y)
    if color is not None:
        return tint_photo_image(source, color)
    return source


def wifi_icon_path(state):
    if state == "connected":
        return "wifi/wifi_connected.png"
    if state == "disabled":
        return "wifi/wifi_off.png"
    return "wifi/wifi_disconnected.png"


def bluetooth_icon_path(enabled, connected=False):
    if not enabled:
        return "bluetooth/bluetooth_off.png"
    if connected:
        return "bluetooth/bluetooth_paired.png"
    return "bluetooth/bluetooth_on.png"


def volume_icon_path(level, muted):
    if muted:
        return "volume/volume_mute.png"
    if level is None:
        return "volume/volume_half.png"
    if level >= 50:
        return "volume/volume_full.png"
    if level > 0:
        return "volume/volume_half.png"
    return "volume/volume_mute.png"


def battery_icon_path(percent, charging):
    if charging:
        return "battery/battery_charging.png"
    if percent is None:
        return "battery/battery_half.png"
    if percent >= 60:
        return "battery/battery_full.png"
    if percent >= 30:
        return "battery/battery_half.png"
    return "battery/battery_low.png"


def battery_icon_color(percent, charging):
    if percent is None:
        return STATUS_ICON if charging else STATUS_ICON_DIM
    return battery_color(percent)


def find_gamepad():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        caps = dev.capabilities()
        name = dev.name.lower()
        if any(token in name for token in TOUCH_TOKENS):
            continue
        if evdev.ecodes.EV_KEY in caps and evdev.ecodes.EV_ABS in caps:
            return dev
    return None


def restart_kiosk():
    return spawn_detached(RESTART_KIOSK_CMD)


def exit_kiosk():
    try:
        subprocess.Popen(["openbox", "--exit"], env=dict(os.environ, DISPLAY=":0"), start_new_session=True)
        return True
    except Exception:
        return False


class UiSoundPlayer:
    def __init__(self):
        self.sample_rate, self.channel_count, self.default_sink_name = detect_output_format(SOUND_SAMPLE_RATE, 1)
        self.output = get_shared_audio_output(
            sample_rate=self.sample_rate,
            channel_count=self.channel_count,
            client_name="gamehub-console",
            stream_name="gamehub-ui-cues",
        )
        self.backend_name = self.output.backend_name
        self.cache = {}
        self.lock = threading.Lock()
        self.last_played_at = {}

    def available(self):
        return self.output.available()

    def waveform_value(self, waveform, phase):
        if waveform == "triangle":
            return (2.0 / math.pi) * math.asin(math.sin(phase))
        if waveform == "square":
            return 1.0 if math.sin(phase) >= 0 else -1.0
        return math.sin(phase)

    def synthesize(self, segments):
        frames = array("h")
        for segment in segments:
            duration = max(0.0, float(segment.get("duration", 0.0)))
            gap = max(0.0, float(segment.get("gap", 0.0)))
            if duration > 0.0:
                sample_count = max(1, int(round(duration * self.sample_rate)))
                attack = max(0.0, float(segment.get("attack", 0.004)))
                attack_samples = max(1, min(sample_count, int(round(attack * self.sample_rate))))
                start_frequency = float(segment.get("frequency", 440.0))
                end_frequency = float(segment.get("end_frequency", start_frequency))
                waveform = str(segment.get("waveform", "sine") or "sine").strip().lower()
                amplitude = max(0.0, min(1.0, float(segment.get("volume", 0.2)))) * SOUND_MASTER_GAIN
                phase = 0.0
                for index in range(sample_count):
                    progress = index / max(1, sample_count - 1)
                    frequency = start_frequency + ((end_frequency - start_frequency) * progress)
                    phase += (2.0 * math.pi * frequency) / self.sample_rate
                    if index < attack_samples:
                        attack_progress = index / max(1, attack_samples - 1)
                        envelope = SOUND_ENVELOPE_FLOOR + ((1.0 - SOUND_ENVELOPE_FLOOR) * attack_progress)
                    else:
                        decay_progress = (index - attack_samples) / max(1, sample_count - attack_samples - 1)
                        envelope = math.exp(math.log(SOUND_ENVELOPE_FLOOR) * decay_progress)
                    sample = self.waveform_value(waveform, phase) * amplitude * envelope
                    sample_value = int(max(-32767, min(32767, round(sample * 32767))))
                    for _ in range(self.channel_count):
                        frames.append(sample_value)
            if gap > 0.0:
                frames.extend([0] * max(1, int(round(gap * self.sample_rate * self.channel_count))))
        return frames.tobytes()

    def build_soft_click(self, frequency, end_frequency=None, duration=0.045, volume=0.3, waveform="sine"):
        resolved_end_frequency = frequency if end_frequency is None else end_frequency
        return self.synthesize(
            [
                {
                    "frequency": frequency,
                    "end_frequency": resolved_end_frequency,
                    "duration": duration,
                    "waveform": waveform,
                    "volume": volume,
                    "attack": 0.004,
                }
            ]
        )

    def build_tone_run(self, frequencies, duration=0.045, gap=0.016, volume=0.22, waveform="triangle", sweep=-18.0):
        segments = []
        for frequency in frequencies:
            end_frequency = max(120.0, float(frequency) + float(sweep))
            segments.append(
                {
                    "frequency": float(frequency),
                    "end_frequency": end_frequency,
                    "duration": duration,
                    "gap": gap,
                    "waveform": waveform,
                    "volume": volume,
                    "attack": 0.004,
                }
            )
        if segments:
            segments[-1]["gap"] = 0.0
        return self.synthesize(segments)

    def should_skip_family(self, family, min_interval):
        if not family or min_interval <= 0:
            return False
        with self.lock:
            now = time.monotonic()
            last_played_at = self.last_played_at.get(family, 0.0)
            if now - last_played_at < min_interval:
                return True
            self.last_played_at[family] = now
            return False

    def play_cached(self, cache_key, builder, stream_name, family=None, min_interval=0.0, replace_family=False):
        if not self.available():
            return False
        if self.should_skip_family(family, min_interval):
            return False
        with self.lock:
            cached_sound = self.cache.get(cache_key)
            if cached_sound is None:
                data = builder()
                if not data:
                    return False
                cached_sound = self._build_cache_entry(data)
                if cached_sound is None:
                    return False
                self.cache[cache_key] = cached_sound
        if cached_sound is None:
            return False
        return self.output.play(
            cached_sound,
            family=family,
            replace_family=replace_family,
            replace_all=True,
        )

    def _build_cache_entry(self, data):
        return data

    def play_settings_open(self):
        return self.play_cached(
            "settings_open",
            lambda: self.build_soft_click(660, end_frequency=620, duration=0.042, volume=0.28, waveform="sine"),
            "settings-open",
            family="settings-visibility",
            replace_family=True,
        )

    def play_settings_close(self):
        return self.play_cached(
            "settings_close",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 560,
                        "end_frequency": 320,
                        "duration": 0.11,
                        "waveform": "triangle",
                        "volume": 0.3,
                        "attack": 0.006,
                    }
                ]
            ),
            "settings-close",
            family="settings-visibility",
            replace_family=True,
        )

    def play_dropdown_open(self):
        return self.play_cached(
            "dropdown_open",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 480,
                        "end_frequency": 720,
                        "duration": 0.09,
                        "waveform": "triangle",
                        "volume": 0.26,
                        "attack": 0.006,
                    }
                ]
            ),
            "dropdown-open",
            family="settings-dropdown",
            replace_family=True,
        )

    def play_dropdown_close(self):
        return self.play_cached(
            "dropdown_close",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 700,
                        "end_frequency": 430,
                        "duration": 0.09,
                        "waveform": "triangle",
                        "volume": 0.25,
                        "attack": 0.006,
                    }
                ]
            ),
            "dropdown-close",
            family="settings-dropdown",
            replace_family=True,
        )

    def play_scroll(self, direction):
        moving_up = direction < 0
        return self.play_cached(
            "scroll_up" if moving_up else "scroll_down",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 560 if moving_up else 430,
                        "end_frequency": 610 if moving_up else 390,
                        "duration": 0.05,
                        "waveform": "triangle",
                        "volume": 0.22,
                        "attack": 0.003,
                    }
                ]
            ),
            "menu-scroll",
            family="scroll",
            min_interval=SOUND_SCROLL_MIN_INTERVAL_SEC,
            replace_family=True,
        )

    def play_slider(self, direction):
        increasing = direction > 0
        return self.play_cached(
            "slider_up" if increasing else "slider_down",
            lambda: self.build_soft_click(
                720 if increasing else 620,
                end_frequency=770 if increasing else 580,
                duration=0.038,
                volume=0.24,
                waveform="sine",
            ),
            "slider-adjust",
            family="slider",
            min_interval=SOUND_SLIDER_MIN_INTERVAL_SEC,
            replace_family=True,
        )

    def play_refresh(self):
        return self.play_cached(
            "refresh",
            lambda: self.build_tone_run(
                (420, 560, 720),
                duration=0.04,
                gap=0.018,
                volume=0.22,
                waveform="triangle",
                sweep=22.0,
            ),
            "refresh-scan",
            family="refresh",
            replace_family=True,
        )

    def play_confirm(self):
        return self.play_cached(
            "confirm",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 520,
                        "end_frequency": 600,
                        "duration": 0.06,
                        "waveform": "sine",
                        "volume": 0.24,
                        "attack": 0.004,
                    },
                    {
                        "frequency": 780,
                        "end_frequency": 860,
                        "duration": 0.085,
                        "waveform": "sine",
                        "volume": 0.22,
                        "attack": 0.004,
                    },
                ]
            ),
            "connection-confirm",
            family="confirm",
            replace_family=True,
        )

    def play_restart(self):
        return self.play_cached(
            "restart",
            lambda: self.build_tone_run(
                (700, 560, 430),
                duration=0.045,
                gap=0.018,
                volume=0.24,
                waveform="triangle",
                sweep=-28.0,
            ),
            "restart-kiosk",
            family="system-action",
            replace_family=True,
        )

    def play_shutdown(self):
        return self.play_cached(
            "shutdown",
            lambda: self.build_tone_run(
                (760, 660, 560, 460, 360),
                duration=0.04,
                gap=0.014,
                volume=0.25,
                waveform="triangle",
                sweep=-30.0,
            ),
            "shutdown-console",
            family="system-action",
            replace_family=True,
        )


class ClockIcon:
    def __init__(self, parent):
        self.image = load_status_icon("hud/clock.png", STATUS_ICON, HUD_ICON_SIZE)
        self.label = tk.Label(parent, bg=STATUS_BG, bd=0, highlightthickness=0, padx=0, pady=0)

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def update(self):
        if self.image is None:
            self.label.config(text="")
            return
        self.label.config(image=self.image)
        self.label.image = self.image


class WifiIcon:
    def __init__(self, parent):
        self.label = tk.Label(parent, bg=STATUS_BG, bd=0, highlightthickness=0, padx=0, pady=0)

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def update(self, _signal, state):
        color = STATUS_ICON if state == "connected" else STATUS_ICON_DIM
        image = load_status_icon(wifi_icon_path(state), color, HUD_ICON_SIZE)
        if image is None:
            self.label.config(text="")
            return
        self.label.config(image=image)
        self.label.image = image


class VolumeIcon:
    def __init__(self, parent):
        self.label = tk.Label(parent, bg=STATUS_BG, bd=0, highlightthickness=0, padx=0, pady=0)

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def update(self, level, muted):
        color = STATUS_ICON if not muted else STATUS_ICON_DIM
        image = load_status_icon(volume_icon_path(level, muted), color, HUD_ICON_SIZE)
        if image is None:
            self.label.config(text="")
            return
        self.label.config(image=image)
        self.label.image = image


class BluetoothIcon:
    def __init__(self, parent):
        self.label = tk.Label(parent, bg=STATUS_BG, bd=0, highlightthickness=0, padx=0, pady=0)

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def update(self, enabled, connected=False):
        color = STATUS_ICON if enabled else STATUS_ICON_DIM
        image = load_status_icon(bluetooth_icon_path(enabled, connected), color, HUD_ICON_SIZE)
        if image is None:
            self.label.config(text="")
            return
        self.label.config(image=image)
        self.label.image = image


class BatteryChip:
    def __init__(self, parent):
        self.label = tk.Label(parent, bg=STATUS_BG, bd=0, highlightthickness=0, padx=0, pady=0)

    def pack(self, **kwargs):
        self.label.pack(**kwargs)

    def update(self, percent, charging):
        image = load_status_icon(
            battery_icon_path(percent, charging),
            battery_icon_color(percent, charging),
            HUD_ICON_SIZE,
        )
        if image is None:
            self.label.config(text="")
            return
        self.label.config(image=image)
        self.label.image = image


class NavHint:
    def __init__(
        self,
        parent,
        label,
        icon_image=None,
        draw_icon=None,
        icon_width=18,
        icon_height=18,
        callback=None,
    ):
        self.frame = tk.Frame(parent, bg=NAV_BG)
        self.icon_image = icon_image
        if self.icon_image is not None:
            self.icon = tk.Label(self.frame, image=self.icon_image, bg=NAV_BG, bd=0, highlightthickness=0)
            self.icon.pack(side=tk.LEFT, padx=(0, 6))
        elif draw_icon is not None:
            self.icon = tk.Canvas(self.frame, width=icon_width, height=icon_height, bg=NAV_BG, highlightthickness=0)
            self.icon.pack(side=tk.LEFT, padx=(0, 6))
            draw_icon(self.icon)
        else:
            self.icon = tk.Label(self.frame, width=icon_width, bg=NAV_BG)
            self.icon.pack(side=tk.LEFT, padx=(0, 6))
        self.label = tk.Label(self.frame, text=label, bg=NAV_BG, fg=NAV_TEXT, font=NAV_FONT)
        self.label.pack(side=tk.LEFT)
        self.callback = callback
        if callback is not None:
            for widget in (self.frame, self.icon, self.label):
                widget.bind("<Button-1>", self.handle_click)

    def handle_click(self, _event):
        if self.callback is not None:
            self.callback()

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def show(self, **kwargs):
        if self.frame.winfo_manager():
            return
        self.frame.pack(**kwargs)

    def hide(self):
        if self.frame.winfo_manager():
            self.frame.pack_forget()

    def set_active(self, active):
        self.label.config(fg=ACCENT if active else NAV_TEXT)

    def set_label(self, label):
        self.label.config(text=label)


def draw_a_button_icon(canvas):
    canvas.create_oval(1, 1, 17, 17, fill=ACCENT, outline=ACCENT)
    canvas.create_text(9, 9, text="A", fill=BG, font=(FONT_FAMILY, 9, "bold"))


def draw_gamepad_icon(canvas):
    canvas.create_line(3, 7, 5, 4, 13, 4, 15, 7, fill=TEXT, width=1.6, smooth=True)
    canvas.create_line(2, 7, 5, 11, 13, 11, 16, 7, fill=TEXT, width=1.6, smooth=True)
    canvas.create_line(6, 6, 6, 9, fill=TEXT, width=1.2)
    canvas.create_line(4.5, 7.5, 7.5, 7.5, fill=TEXT, width=1.2)
    canvas.create_oval(11, 6, 12.5, 7.5, fill=TEXT, outline=TEXT)
    canvas.create_oval(13, 8, 14.5, 9.5, fill=TEXT, outline=TEXT)


def draw_menu_button_icon(canvas):
    canvas.create_oval(1, 1, 17, 17, fill=BLUE, outline=BLUE)
    for y_pos in (6, 9, 12):
        canvas.create_line(6, y_pos, 12, y_pos, fill=TEXT, width=1.5, capstyle=tk.ROUND)


def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, fill):
    width = max(0, x2 - x1)
    height = max(0, y2 - y1)
    radius = max(0, min(radius, width // 2, height // 2))
    if radius == 0:
        canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="", width=0)
        return

    canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline="", width=0)
    canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline="", width=0)
    canvas.create_oval(x1, y1, x1 + (radius * 2), y1 + (radius * 2), fill=fill, outline="", width=0)
    canvas.create_oval(x2 - (radius * 2), y1, x2, y1 + (radius * 2), fill=fill, outline="", width=0)
    canvas.create_oval(x1, y2 - (radius * 2), x1 + (radius * 2), y2, fill=fill, outline="", width=0)
    canvas.create_oval(x2 - (radius * 2), y2 - (radius * 2), x2, y2, fill=fill, outline="", width=0)


def draw_rounded_outline(canvas, x1, y1, x2, y2, radius, outline, width=1):
    left = float(min(x1, x2))
    right = float(max(x1, x2))
    top = float(min(y1, y2))
    bottom = float(max(y1, y2))
    width = max(1, float(width))
    radius = max(0.0, min(float(radius), (right - left) / 2.0, (bottom - top) / 2.0))
    inset = width / 2.0
    left_inset = left + inset
    right_inset = right - inset
    top_inset = top + inset
    bottom_inset = bottom - inset

    if right_inset <= left_inset or bottom_inset <= top_inset:
        return

    if radius <= inset:
        canvas.create_rectangle(
            left_inset,
            top_inset,
            right_inset,
            bottom_inset,
            fill="",
            outline=outline,
            width=width,
        )
        return

    canvas.create_line(
        left + radius,
        top_inset,
        right - radius,
        top_inset,
        fill=outline,
        width=width,
        capstyle=tk.ROUND,
    )
    canvas.create_line(
        left + radius,
        bottom_inset,
        right - radius,
        bottom_inset,
        fill=outline,
        width=width,
        capstyle=tk.ROUND,
    )
    canvas.create_line(
        left_inset,
        top + radius,
        left_inset,
        bottom - radius,
        fill=outline,
        width=width,
        capstyle=tk.ROUND,
    )
    canvas.create_line(
        right_inset,
        top + radius,
        right_inset,
        bottom - radius,
        fill=outline,
        width=width,
        capstyle=tk.ROUND,
    )

    arc_right = (radius * 2.0) - inset
    arc_bottom = (radius * 2.0) - inset
    canvas.create_arc(
        left_inset,
        top_inset,
        left + arc_right,
        top + arc_bottom,
        start=90,
        extent=90,
        style=tk.ARC,
        outline=outline,
        width=width,
    )
    canvas.create_arc(
        right - (radius * 2.0) + inset,
        top_inset,
        right_inset,
        top + arc_bottom,
        start=0,
        extent=90,
        style=tk.ARC,
        outline=outline,
        width=width,
    )
    canvas.create_arc(
        left_inset,
        bottom - (radius * 2.0) + inset,
        left + arc_right,
        bottom_inset,
        start=180,
        extent=90,
        style=tk.ARC,
        outline=outline,
        width=width,
    )
    canvas.create_arc(
        right - (radius * 2.0) + inset,
        bottom - (radius * 2.0) + inset,
        right_inset,
        bottom_inset,
        start=270,
        extent=90,
        style=tk.ARC,
        outline=outline,
        width=width,
    )


def interpolate_hex_color(start_color, end_color, progress):
    start_rgb = parse_hex_color(start_color)
    end_rgb = parse_hex_color(end_color)
    blended = tuple(
        int(round(start_value + (end_value - start_value) * progress))
        for start_value, end_value in zip(start_rgb, end_rgb)
    )
    return f"#{blended[0]:02x}{blended[1]:02x}{blended[2]:02x}"


def draw_gradient_rounded_rect(canvas, x1, y1, x2, y2, radius, start_color, end_color, steps=MENU_GRADIENT_STEPS):
    left = int(round(min(x1, x2)))
    right = int(round(max(x1, x2)))
    top = float(min(y1, y2))
    bottom = float(max(y1, y2))
    radius = max(0, min(int(round(radius)), (right - left) // 2, int((bottom - top) // 2)))
    total_width = max(1, right - left)
    steps = max(2, min(steps, total_width))

    for step_index in range(steps):
        band_left = left + int(round((step_index * total_width) / steps))
        band_right = left + int(round(((step_index + 1) * total_width) / steps))
        if band_right <= band_left:
            band_right = min(right, band_left + 1)
        progress = step_index / max(1, steps - 1)
        color = interpolate_hex_color(start_color, end_color, progress)
        band_center = (band_left + band_right) / 2.0
        line_top = top
        line_bottom = bottom
        if radius > 0:
            if band_center < left + radius:
                center_x = left + radius
                distance = center_x - band_center
                offset = radius - max(0.0, (radius * radius - distance * distance) ** 0.5)
                line_top = top + offset
                line_bottom = bottom - offset
            elif band_center > right - radius:
                center_x = right - radius
                distance = band_center - center_x
                offset = radius - max(0.0, (radius * radius - distance * distance) ** 0.5)
                line_top = top + offset
                line_bottom = bottom - offset
        canvas.create_rectangle(
            band_left,
            line_top,
            band_right,
            line_bottom,
            fill=color,
            outline="",
            width=0,
        )


def inset_rounded_bounds(x1, y1, x2, y2, radius, inset):
    left = float(min(x1, x2)) + inset
    right = float(max(x1, x2)) - inset
    top = float(min(y1, y2)) + inset
    bottom = float(max(y1, y2)) - inset
    if right <= left or bottom <= top:
        return None
    inner_radius = max(0.0, min(float(radius) - inset, (right - left) / 2.0, (bottom - top) / 2.0))
    return left, top, right, bottom, inner_radius


def draw_bordered_rounded_rect(canvas, x1, y1, x2, y2, radius, fill, border, border_width=1):
    border_width = max(0.0, float(border_width))
    if draw_antialiased_rounded_shape(canvas, x1, y1, x2, y2, radius, fill, border, border_width=border_width):
        return
    if border and border_width > 0:
        draw_rounded_rect(canvas, x1, y1, x2, y2, radius, border)
        inner_bounds = inset_rounded_bounds(x1, y1, x2, y2, radius, border_width)
        if fill and inner_bounds is not None:
            inner_x1, inner_y1, inner_x2, inner_y2, inner_radius = inner_bounds
            draw_rounded_rect(canvas, inner_x1, inner_y1, inner_x2, inner_y2, inner_radius, fill)
        return
    if fill:
        draw_rounded_rect(canvas, x1, y1, x2, y2, radius, fill)
    if border:
        draw_rounded_outline(canvas, x1, y1, x2, y2, radius, border, width=border_width or 1)


def draw_bordered_gradient_rounded_rect(
    canvas,
    x1,
    y1,
    x2,
    y2,
    radius,
    start_color,
    end_color,
    border,
    border_width=1,
    steps=MENU_GRADIENT_STEPS,
):
    border_width = max(0.0, float(border_width))
    if draw_antialiased_rounded_shape(
        canvas,
        x1,
        y1,
        x2,
        y2,
        radius,
        "",
        border,
        border_width=border_width,
        start_color=start_color,
        end_color=end_color,
    ):
        return
    if border and border_width > 0:
        draw_rounded_rect(canvas, x1, y1, x2, y2, radius, border)
        inner_bounds = inset_rounded_bounds(x1, y1, x2, y2, radius, border_width)
        if inner_bounds is None:
            return
        inner_x1, inner_y1, inner_x2, inner_y2, inner_radius = inner_bounds
        draw_gradient_rounded_rect(
            canvas,
            inner_x1,
            inner_y1,
            inner_x2,
            inner_y2,
            inner_radius,
            start_color,
            end_color,
            steps=steps,
        )
        return
    draw_gradient_rounded_rect(canvas, x1, y1, x2, y2, radius, start_color, end_color, steps=steps)
    if border:
        draw_rounded_outline(canvas, x1, y1, x2, y2, radius, border, width=border_width or 1)


def draw_footer_button_chip(canvas, label):
    canvas.delete("all")
    draw_rounded_rect(canvas, 1, 1, 17, 17, 4, NAV_HINT_CHIP_BG)
    canvas.create_text(9, 9, text=label, fill=NAV_HINT_CHIP_TEXT, font=(FONT_FAMILY, 8, "bold"))


def draw_footer_a_button_icon(canvas):
    draw_footer_button_chip(canvas, "A")


def draw_footer_b_button_icon(canvas):
    draw_footer_button_chip(canvas, "B")


def draw_footer_dpad_icon(canvas):
    canvas.delete("all")
    draw_rounded_rect(canvas, 1, 1, 17, 17, 4, NAV_HINT_CHIP_BG)
    canvas.create_line(9, 5, 9, 13, fill=NAV_HINT_CHIP_TEXT, width=1.5, capstyle=tk.ROUND)
    canvas.create_line(5, 9, 13, 9, fill=NAV_HINT_CHIP_TEXT, width=1.5, capstyle=tk.ROUND)


class WifiPasswordDialog:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Frame(parent, bg=MENU_BG, bd=0, highlightthickness=0)
        self.window.place_forget()
        for sequence in ("<ButtonPress-1>", "<B1-Motion>", "<ButtonRelease-1>"):
            self.window.bind(sequence, lambda _event: "break")

        self.panel_border = tk.Frame(self.window, bg=MENU_DETAIL_BORDER, bd=0, highlightthickness=0)
        frame = tk.Frame(self.panel_border, bg=MENU_PANEL_BG, bd=0, highlightthickness=0, padx=16, pady=14)
        frame.pack(padx=1, pady=1)

        self.password_visible = False
        self.password_hidden_icon = load_status_icon(
            "wifi/wifi_password_visible_off.png",
            MENU_MUTED,
            WIFI_PASSWORD_TOGGLE_ICON_SIZE,
        )
        self.password_visible_icon = load_status_icon(
            "wifi/wifi_password_visible_on.png",
            TEXT,
            WIFI_PASSWORD_TOGGLE_ICON_SIZE,
        )

        self.title_label = tk.Label(frame, text="WiFi Password", bg=MENU_PANEL_BG, fg=TEXT, font=MENU_ITEM_FONT, anchor="w")
        self.title_label.pack(fill=tk.X)

        self.ssid_label = tk.Label(
            frame,
            text="",
            bg=MENU_PANEL_BG,
            fg=MENU_MUTED,
            font=SLIDER_LABEL_FONT,
            justify=tk.LEFT,
            anchor="w",
            wraplength=300,
        )
        self.ssid_label.pack(fill=tk.X, pady=(4, 10))

        entry_frame = tk.Frame(frame, bg=MENU_ROW_BORDER, bd=0, highlightthickness=0)
        entry_frame.pack(fill=tk.X)
        entry_inner = tk.Frame(entry_frame, bg=MENU_ROW_BG, bd=0, highlightthickness=0)
        entry_inner.pack(fill=tk.X, padx=1, pady=1)
        self.password_var = tk.StringVar()
        self.entry = tk.Entry(
            entry_inner,
            textvariable=self.password_var,
            bg=MENU_ROW_BG,
            fg=TEXT,
            insertbackground=TEXT,
            relief=tk.FLAT,
            bd=0,
            font=MENU_VALUE_FONT,
            show="*",
        )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), pady=0, ipady=8)
        self.visibility_button = tk.Button(
            entry_inner,
            text="Show",
            command=self.toggle_password_visibility,
            bg=MENU_ROW_BG,
            fg=TEXT,
            activebackground=MENU_ROW_BORDER,
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            padx=10,
            pady=8,
            font=(FONT_FAMILY, 9, "bold"),
            compound=tk.LEFT,
        )
        self.visibility_button.pack(side=tk.RIGHT, padx=(8, 4), pady=0)
        self.update_password_visibility_button()

        self.hint_label = tk.Label(
            frame,
            text="Use the current OSK, tap Show if needed, then press A or Connect",
            bg=MENU_PANEL_BG,
            fg=MENU_DETAIL_SUBTEXT,
            font=(FONT_FAMILY, 9, "bold"),
            justify=tk.LEFT,
            anchor="w",
        )
        self.hint_label.pack(fill=tk.X, pady=(8, 0))

        self.error_label = tk.Label(
            frame,
            text="",
            bg=MENU_PANEL_BG,
            fg=MENU_DESTRUCTIVE,
            font=(FONT_FAMILY, 9, "bold"),
            justify=tk.LEFT,
            anchor="w",
        )
        self.error_label.pack(fill=tk.X, pady=(6, 0))

        button_row = tk.Frame(frame, bg=MENU_PANEL_BG)
        button_row.pack(fill=tk.X, pady=(12, 0))
        self.cancel_button = tk.Button(
            button_row,
            text="Cancel",
            command=self.cancel,
            bg=MENU_ROW_BG,
            fg=TEXT,
            activebackground=MENU_ROW_BORDER,
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=8,
            font=SLIDER_LABEL_FONT,
        )
        self.cancel_button.pack(side=tk.LEFT)
        self.connect_button = tk.Button(
            button_row,
            text="Connect",
            command=self.submit,
            bg=MENU_CONFIRM_BG,
            fg=TEXT,
            activebackground=MENU_CTA_END,
            activeforeground=TEXT,
            relief=tk.FLAT,
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=8,
            font=SLIDER_LABEL_FONT,
        )
        self.connect_button.pack(side=tk.RIGHT)

        self.window.bind("<Escape>", lambda _event: self.cancel())
        self.entry.bind("<Return>", lambda _event: self.submit())
        self.entry.bind("<Escape>", lambda _event: self.cancel())
        self.submit_callback = None
        self.cancel_callback = None
        self.network = None

    def is_visible(self):
        return bool(self.window.winfo_manager())

    def show(self, network, submit_callback=None, cancel_callback=None):
        self.network = dict(network or {})
        self.submit_callback = submit_callback
        self.cancel_callback = cancel_callback
        self.set_password_visible(False)
        self.password_var.set("")
        self.error_label.config(text="")
        ssid = self.network.get("ssid") or "Hidden network"
        self.ssid_label.config(text=f"Enter the password for {ssid}")
        try:
            self.window.place(x=0, y=0, relwidth=1.0, relheight=1.0)
            self.parent.update_idletasks()
            panel_width = min(
                max(WIFI_PASSWORD_MODAL_WIDTH, self.panel_border.winfo_reqwidth()),
                max(1, self.parent.winfo_width() - (WIFI_PASSWORD_MODAL_SIDE_PAD * 2)),
            )
            center_x = max(
                WIFI_PASSWORD_MODAL_SIDE_PAD + (panel_width // 2),
                min(
                    self.parent.winfo_width() - WIFI_PASSWORD_MODAL_SIDE_PAD - (panel_width // 2),
                    self.parent.winfo_width() // 2,
                ),
            )
            self.panel_border.place(
                x=center_x,
                y=WIFI_PASSWORD_MODAL_TOP_PAD,
                width=panel_width,
                anchor="n",
            )
            self.parent.lift()
            self.window.lift()
            self.panel_border.lift()
        except tk.TclError:
            return False
        self.activate()
        for delay in (0, 60, 180, 320):
            try:
                self.parent.after(delay, self.activate)
            except tk.TclError:
                break
        return True

    def activate(self):
        self.activate_window()
        self.focus_entry()

    def activate_window(self):
        try:
            self.parent.update_idletasks()
            window_id = self.parent.winfo_id()
        except tk.TclError:
            return
        if not window_id:
            return
        try:
            subprocess.run(
                ["xdotool", "windowraise", str(window_id)],
                capture_output=True,
                timeout=1,
                env=display_env(),
            )
            subprocess.run(
                ["xdotool", "windowfocus", str(window_id)],
                capture_output=True,
                timeout=1,
                env=display_env(),
            )
        except Exception:
            pass

    def update_password_visibility_button(self):
        icon_image = self.password_visible_icon if self.password_visible else self.password_hidden_icon
        label = "Hide" if self.password_visible else "Show"
        self.visibility_button.config(
            text=label,
            image=icon_image if icon_image is not None else "",
        )

    def set_password_visible(self, visible):
        self.password_visible = bool(visible)
        self.entry.config(show="" if self.password_visible else "*")
        self.update_password_visibility_button()

    def toggle_password_visibility(self):
        try:
            cursor_index = self.entry.index(tk.INSERT)
        except tk.TclError:
            cursor_index = None
        self.set_password_visible(not self.password_visible)
        self.focus_entry(cursor_index=cursor_index)

    def focus_entry(self, cursor_index=None):
        try:
            self.parent.focus_force()
            self.window.lift()
            self.panel_border.lift()
            self.entry.focus_force()
            self.entry.focus_set()
            self.entry.icursor(cursor_index if cursor_index is not None else tk.END)
        except tk.TclError:
            pass

    def set_error(self, text):
        self.error_label.config(text=str(text or ""))

    def password(self):
        return self.password_var.get()

    def hide(self):
        self.submit_callback = None
        self.cancel_callback = None
        self.network = None
        self.set_password_visible(False)
        self.password_var.set("")
        self.error_label.config(text="")
        self.window.place_forget()

    def submit(self):
        if self.submit_callback is None:
            return
        try:
            self.submit_callback(self.password())
        except Exception:
            pass

    def cancel(self):
        callback = self.cancel_callback
        self.hide()
        if callback is None:
            return
        try:
            callback()
        except Exception:
            pass


class QuickMenuOverlay:
    def __init__(
        self,
        parent,
        snapshot_getter=None,
        on_visibility_change=None,
        on_snapshot_change=None,
        on_bluetooth_connected=None,
        on_wifi_connected=None,
        sound_player=None,
    ):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=MENU_BG)
        try:
            self.window.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

        self.snapshot_getter = snapshot_getter
        self.on_visibility_change = on_visibility_change
        self.on_snapshot_change = on_snapshot_change
        self.on_bluetooth_connected = on_bluetooth_connected
        self.on_wifi_connected = on_wifi_connected
        self.sound_player = sound_player
        self.snapshot = default_status_snapshot()
        self.visible = False
        self.target_visible = False
        self.expanded_key = None
        self.adjusting_key = None
        self.detail_selection_key = None
        self.detail_selection_index = 0
        self.selected_index = 0
        self.volume_value = 50
        self.volume_target_value = 50
        self.brightness_value = get_display_brightness()
        self.wifi_networks = []
        self.bluetooth_devices = []
        self.wifi_scan_in_progress = False
        self.wifi_action_in_progress = False
        self.bluetooth_scan_in_progress = False
        self.bluetooth_action_in_progress = False
        self.bluetooth_open_refresh_job = None
        self.software_update_check_in_progress = False
        self.software_update_in_progress = False
        self.software_update_available = False
        self.software_remote_version = None
        self.message_job = None
        self.animation_job = None
        self.volume_animation_job = None
        self.animation_started_at = 0.0
        self.animation_start_rect = (0, APP_Y, SCREEN_W, APP_HEIGHT)
        self.animation_end_rect = self.animation_start_rect
        self.current_alpha = MENU_COLLAPSED_ALPHA
        self.alpha_supported = True
        self.animation_in_progress = False
        self.render_job = None
        self.system_action_job = None
        self.cursor_widgets = [self.window]
        self.cursor_hidden = not STANDARD_TOUCH_CURSOR
        set_widget_cursor(self.window, resolved_cursor_name(self.cursor_hidden))
        self.wifi_password_dialog = WifiPasswordDialog(self.window)
        self.register_cursor_windows(
            self.wifi_password_dialog.window,
            self.wifi_password_dialog.entry,
            self.wifi_password_dialog.visibility_button,
            self.wifi_password_dialog.cancel_button,
            self.wifi_password_dialog.connect_button,
        )
        self.volume_write_event = threading.Event()
        self.volume_write_lock = threading.Lock()
        self.pending_volume_write = None
        self.selection_visibility_pending = True
        self.touch_press_active = False
        self.touch_drag_active = False
        self.touch_press_y_root = 0
        self.touch_press_scroll_top = 0.0
        self.touch_press_index = None
        self.touch_slider_index = None
        self.touch_slider_key = None
        self.touch_scroll_suppress_until = 0.0
        self.software_version = read_workspace_version()
        self.items = [
            {"key": VOLUME_ITEM_KEY, "label": "Volume"},
            {"key": WIFI_ITEM_KEY, "label": "WiFi"},
            {"key": BLUETOOTH_ITEM_KEY, "label": "Bluetooth"},
            {"key": BRIGHTNESS_ITEM_KEY, "label": "Brightness"},
            {"key": UPDATE_ITEM_KEY, "label": "Check for Updates"},
            {"key": RESTART_ITEM_KEY, "label": "Restart Kiosk"},
            {"key": SHUTDOWN_ITEM_KEY, "label": "Shutdown"},
        ]
        self.item_labels = {item["key"]: item["label"] for item in self.items}
        self.rows = []
        threading.Thread(target=self.volume_write_loop, daemon=True).start()

        outer = tk.Frame(self.window, bg=MENU_BG, bd=0, highlightthickness=0)
        outer.pack(fill=tk.BOTH, expand=True)
        self.outer = outer

        header = tk.Frame(outer, bg=MENU_BG)
        header.pack(fill=tk.X, padx=MENU_HEADER_PAD_X, pady=(MENU_HEADER_PAD_Y, 16))

        tk.Label(header, text="Settings", bg=MENU_BG, fg=TEXT, font=MENU_TITLE_FONT).pack(side=tk.LEFT)

        self.list_canvas = tk.Canvas(
            outer,
            bg=MENU_BG,
            bd=0,
            highlightthickness=0,
            relief=tk.FLAT,
        )
        self.list_canvas.pack(fill=tk.BOTH, expand=True, padx=MENU_SIDE_PAD)

        self.list_frame = tk.Frame(self.list_canvas, bg=MENU_BG)
        self.list_window = self.list_canvas.create_window(0, 0, anchor="nw", window=self.list_frame)
        self.list_frame.bind("<Configure>", self.handle_list_frame_configure)
        self.list_canvas.bind("<Configure>", self.handle_list_canvas_configure)
        self.bind_touch_scroll(self.list_canvas)
        self.bind_touch_scroll(self.list_frame)

        for index, item in enumerate(self.items):
            row = self.build_row(item, index)
            self.rows.append(row)

        self.status_label = tk.Label(
            outer,
            text="",
            bg=MENU_TOAST_BG,
            fg=MENU_TOAST_TEXT,
            font=MENU_TOAST_FONT,
            anchor="center",
            padx=12,
            pady=6,
        )
        self.status_label.place_forget()

        self.render()
        self.apply_rect(self.collapsed_rect())
        self.set_window_alpha(MENU_COLLAPSED_ALPHA)

    def is_active(self):
        return self.visible or self.target_visible

    def notify_visibility_change(self, active):
        if self.on_visibility_change is None:
            return
        try:
            self.on_visibility_change(bool(active))
        except Exception:
            pass

    def build_row(self, item, index):
        card = tk.Canvas(
            self.list_frame,
            bd=0,
            bg=MENU_BG,
            highlightthickness=0,
            relief=tk.FLAT,
            height=MENU_ROW_HEIGHT,
        )
        card.pack(fill=tk.X, padx=MENU_LIST_PAD_X, pady=(0, MENU_ROW_GAP))
        self.bind_touch_scroll(card, index=index)

        return {
            "item": item,
            "card": card,
        }

    def bind_touch_scroll(self, widget, index=None):
        widget.bind("<ButtonPress-1>", lambda event, selected=index: self.on_touch_press(event, selected))
        widget.bind("<B1-Motion>", self.on_touch_drag)
        widget.bind("<ButtonRelease-1>", lambda event, selected=index: self.on_touch_release(event, selected))

    def handle_list_frame_configure(self, _event=None):
        bbox = self.list_canvas.bbox(self.list_window)
        if bbox is not None:
            self.list_canvas.config(scrollregion=bbox)

    def handle_list_canvas_configure(self, event):
        self.list_canvas.itemconfigure(self.list_window, width=event.width)
        if not self.animation_in_progress:
            self.schedule_render()
        self.ensure_selected_visible()

    def open_rect(self):
        return (0, APP_Y, SCREEN_W, APP_HEIGHT)

    def collapsed_rect(self):
        open_x, open_y, open_width, open_height = self.open_rect()
        width = max(MENU_WIDTH, int(round(open_width * MENU_COLLAPSED_SCALE)))
        height = max(220, int(round(open_height * MENU_COLLAPSED_SCALE)))
        x_pos = open_x + max(0, (open_width - width) // 2)
        y_pos = open_y + max(0, (open_height - height) // 2)
        return (x_pos, y_pos, width, height)

    def current_rect(self):
        if not self.window.winfo_ismapped():
            return self.collapsed_rect()
        self.window.update_idletasks()
        return (
            self.window.winfo_x(),
            self.window.winfo_y(),
            max(1, self.window.winfo_width()),
            max(1, self.window.winfo_height()),
        )

    def apply_rect(self, rect):
        x_pos, y_pos, width, height = rect
        self.window.geometry(f"{max(1, width)}x{max(1, height)}+{x_pos}+{y_pos}")
        self.ensure_selected_visible(force=True)

    def set_window_alpha(self, alpha):
        alpha = max(MENU_COLLAPSED_ALPHA, min(MENU_OPEN_ALPHA, alpha))
        self.current_alpha = alpha
        if not self.alpha_supported:
            return
        try:
            self.window.wm_attributes("-alpha", alpha)
        except tk.TclError:
            self.alpha_supported = False

    def register_cursor_windows(self, *widgets):
        for widget in widgets:
            if widget not in self.cursor_widgets:
                self.cursor_widgets.append(widget)
            set_widget_cursor(widget, resolved_cursor_name(self.cursor_hidden))

    def set_cursor_hidden(self, hidden):
        self.cursor_hidden = bool(hidden)
        cursor_name = resolved_cursor_name(self.cursor_hidden)
        for widget in self.cursor_widgets:
            set_widget_cursor(widget, cursor_name)

    def cancel_animation(self):
        if self.animation_job is not None:
            self.window.after_cancel(self.animation_job)
            self.animation_job = None
        self.animation_in_progress = False

    def cancel_volume_animation(self):
        if self.volume_animation_job is not None:
            self.window.after_cancel(self.volume_animation_job)
            self.volume_animation_job = None

    def schedule_render(self):
        if self.render_job is not None:
            return
        self.render_job = self.window.after_idle(self.perform_scheduled_render)

    def perform_scheduled_render(self):
        self.render_job = None
        self.render()

    def queue_volume_write(self, value):
        with self.volume_write_lock:
            self.pending_volume_write = int(value)
        self.volume_write_event.set()

    def volume_write_loop(self):
        while True:
            self.volume_write_event.wait()
            while True:
                with self.volume_write_lock:
                    next_value = self.pending_volume_write
                    self.pending_volume_write = None
                    if next_value is None:
                        self.volume_write_event.clear()
                        break
                set_volume(next_value)
                with self.volume_write_lock:
                    if self.pending_volume_write is None:
                        self.volume_write_event.clear()
                        break

    def step_volume_animation(self):
        self.volume_animation_job = None
        if self.volume_value == self.volume_target_value:
            return
        direction = 1 if self.volume_target_value > self.volume_value else -1
        step = min(VOLUME_ANIMATION_STEP, abs(self.volume_target_value - self.volume_value))
        self.volume_value += direction * step
        self.queue_volume_write(self.volume_value)
        self.push_snapshot(
            self.optimistic_snapshot(
                volume_level=self.volume_value,
                volume_muted=self.volume_value <= 0,
            )
        )
        self.render()
        if self.volume_value != self.volume_target_value:
            self.volume_animation_job = self.window.after(VOLUME_ANIMATION_INTERVAL_MS, self.step_volume_animation)

    def begin_animation(self, opening):
        self.cancel_animation()
        self.animation_in_progress = True
        self.animation_started_at = time.monotonic()
        self.animation_start_rect = self.current_rect()
        self.animation_end_rect = self.open_rect() if opening else self.collapsed_rect()
        self.animation_start_alpha = self.current_alpha
        self.animation_end_alpha = MENU_OPEN_ALPHA if opening else MENU_COLLAPSED_ALPHA
        self.step_animation(opening)

    def step_animation(self, opening):
        elapsed_ms = (time.monotonic() - self.animation_started_at) * 1000.0
        progress = min(1.0, elapsed_ms / MENU_ANIMATION_DURATION_MS)
        eased = ease_in_out_cubic(progress)
        self.apply_rect(interpolate_rect(self.animation_start_rect, self.animation_end_rect, eased))
        self.set_window_alpha(
            self.animation_start_alpha + (self.animation_end_alpha - self.animation_start_alpha) * eased
        )
        self.window.lift()
        if progress >= 1.0:
            self.animation_job = None
            self.finish_animation(opening)
            return
        self.animation_job = self.window.after(MENU_ANIMATION_STEP_MS, lambda: self.step_animation(opening))

    def finish_animation(self, opening):
        self.animation_in_progress = False
        self.apply_rect(self.open_rect() if opening else self.collapsed_rect())
        self.set_window_alpha(MENU_OPEN_ALPHA if opening else MENU_COLLAPSED_ALPHA)
        if opening:
            self.visible = True
            self.window.lift()
            self.render()
            return
        self.visible = False
        self.window.withdraw()
        self.set_cursor_hidden(False)
        set_quick_menu_active(False)
        self.clear_message()
        self.render()

    def ensure_selected_visible(self, force=False):
        if not force and not self.selection_visibility_pending:
            return
        if not force and self.touch_scroll_suppressed():
            return
        if not self.rows:
            return
        viewport_height = self.list_canvas.winfo_height()
        if viewport_height <= 1:
            return
        content_height = self.list_frame.winfo_reqheight()
        if content_height <= viewport_height:
            self.list_canvas.yview_moveto(0)
            self.selection_visibility_pending = False
            return
        row_top, row_bottom = self.selected_content_bounds()
        row_height = max(MENU_ROW_HEIGHT, row_bottom - row_top)
        max_offset = max(0, content_height - viewport_height)
        target_top = self.selection_scroll_target(row_top, row_bottom, viewport_height, max_offset)
        if row_height <= viewport_height:
            target_top = max(target_top, row_bottom - viewport_height)
            target_top = min(target_top, row_top)
        target_top = max(0, min(target_top, max_offset))
        self.scroll_to_top(target_top, content_height=content_height)
        self.selection_visibility_pending = False

    def selected_content_bounds(self):
        row = self.rows[self.selected_index]["card"]
        row_top = row.winfo_y()
        row_height = max(MENU_ROW_HEIGHT, row.winfo_height())
        row_bottom = row_top + row_height
        if self.detail_selection_key in LIST_ITEM_KEYS and self.expanded_key == self.detail_selection_key:
            detail_bounds = self.detail_entry_bounds(self.detail_selection_index)
            if detail_bounds is not None:
                detail_top, detail_bottom = detail_bounds
                return row_top + detail_top, row_top + detail_bottom
        return row_top, row_bottom

    def selection_scroll_target(self, row_top, row_bottom, viewport_height, max_offset):
        highlight_center = row_top + ((row_bottom - row_top) / 2.0)
        midpoint = viewport_height / 2.0
        return max(0, min(highlight_center - midpoint, max_offset))

    def detail_entry_bounds(self, index, key=None):
        resolved_key = self.detail_selection_key if key is None else key
        entries = self.detail_entries(resolved_key)
        if index < 0 or index >= len(entries):
            return None
        panel_top = MENU_ROW_HEIGHT + DETAIL_PANEL_TOP_PAD
        title_y = panel_top + DETAIL_LIST_PANEL_TITLE_OFFSET_Y
        row_top = title_y + DETAIL_LIST_PANEL_ROWS_TOP_GAP
        entry_y1 = row_top + index * (DETAIL_LIST_PANEL_ROW_HEIGHT + DETAIL_LIST_PANEL_ROW_GAP)
        entry_y2 = entry_y1 + DETAIL_LIST_PANEL_ROW_HEIGHT
        return entry_y1, entry_y2

    def row_card_width(self, row_index):
        if row_index < 0 or row_index >= len(self.rows):
            return 0
        card = self.rows[row_index]["card"]
        width = max(1, card.winfo_width())
        if width <= 1:
            width = max(1, self.list_canvas.winfo_width() - (MENU_LIST_PAD_X * 2))
        if width <= 1:
            width = SCREEN_W - (MENU_LIST_PAD_X * 2)
        return width

    def row_card_height(self, row_index):
        if row_index < 0 or row_index >= len(self.rows):
            return MENU_ROW_HEIGHT
        key = self.item_key_at_index(row_index)
        card = self.rows[row_index]["card"]
        height = max(MENU_ROW_HEIGHT, card.winfo_height())
        if key == self.expanded_key:
            height = max(height, MENU_ROW_HEIGHT + self.detail_panel_height(key))
        return height

    def touch_slider_geometry(self, row_index):
        if row_index is None or row_index < 0 or row_index >= len(self.rows):
            return None
        key = self.item_key_at_index(row_index)
        if key not in ADJUSTABLE_ITEM_KEYS or key != self.expanded_key:
            return None
        width = self.row_card_width(row_index)
        card_height = self.row_card_height(row_index)
        return self.slider_panel_geometry(key, width, card_height)

    def touch_slider_hit_target(self, row_index, x_pos, y_pos):
        geometry = self.touch_slider_geometry(row_index)
        if geometry is None:
            return None
        if x_pos < geometry["slider_left"] - SLIDER_TOUCH_PAD_X or x_pos > geometry["slider_right"] + SLIDER_TOUCH_PAD_X:
            return None
        slider_top = geometry["slider_y"] - SLIDER_KNOB_RADIUS - SLIDER_TOUCH_PAD_Y
        slider_bottom = geometry["slider_y"] + SLIDER_KNOB_RADIUS + SLIDER_TOUCH_PAD_Y
        if y_pos < slider_top or y_pos > slider_bottom:
            return None
        return geometry

    def slider_value_from_touch(self, geometry, x_pos):
        slider_left = geometry["slider_left"]
        slider_right = geometry["slider_right"]
        width = max(1, slider_right - slider_left)
        ratio = max(0.0, min(1.0, (x_pos - slider_left) / float(width)))
        value = int(round(ratio * 100.0))
        if geometry["key"] == BRIGHTNESS_ITEM_KEY:
            return clamp_brightness_percent(value)
        return max(0, min(100, value))

    def update_touch_slider(self, row_index, x_pos):
        geometry = self.touch_slider_geometry(row_index)
        if geometry is None:
            return False
        value = self.slider_value_from_touch(geometry, x_pos)
        return self.set_slider_value(geometry["key"], value, animate=False)

    def detail_entry_hit_index(self, row_index, x_pos, y_pos):
        if row_index is None or row_index < 0 or row_index >= len(self.rows):
            return None
        key = self.item_key_at_index(row_index)
        if key not in LIST_ITEM_KEYS or key != self.expanded_key:
            return None
        entries = self.detail_entries(key)
        if not entries:
            return None

        width = self.row_card_width(row_index)
        entry_x1 = DETAIL_LIST_PANEL_OUTER_PAD_X + DETAIL_LIST_PANEL_SIDE_PAD + DETAIL_LIST_PANEL_ITEM_INSET_X
        entry_x2 = width - DETAIL_LIST_PANEL_OUTER_PAD_X - DETAIL_LIST_PANEL_SIDE_PAD - DETAIL_LIST_PANEL_ITEM_INSET_X
        if x_pos < entry_x1 or x_pos > entry_x2:
            return None

        for entry_index in range(len(entries)):
            bounds = self.detail_entry_bounds(entry_index, key=key)
            if bounds is None:
                continue
            entry_y1, entry_y2 = bounds
            if entry_y1 <= y_pos <= entry_y2:
                return entry_index
        return None

    def activate_touch_detail_entry(self, row_index, detail_index):
        key = self.item_key_at_index(row_index)
        self.selected_index = row_index
        self.detail_selection_key = key
        self.detail_selection_index = detail_index
        self.selection_visibility_pending = False
        self.render()
        if key == WIFI_ITEM_KEY:
            self.activate_wifi_detail_entry()
            return
        if key == BLUETOOTH_ITEM_KEY:
            self.activate_bluetooth_detail_entry()

    def center_selected_row(self):
        if not self.rows:
            return
        try:
            self.window.update_idletasks()
        except tk.TclError:
            return
        self.handle_list_frame_configure()
        self.ensure_selected_visible(force=True)

    def touch_scroll_suppressed(self):
        return self.touch_press_active or self.touch_drag_active or time.monotonic() < self.touch_scroll_suppress_until

    def current_scroll_top(self):
        return self.list_canvas.canvasy(0)

    def scroll_to_top(self, target_top, content_height=None):
        viewport_height = self.list_canvas.winfo_height()
        if viewport_height <= 1:
            return
        if content_height is None:
            content_height = self.list_frame.winfo_reqheight()
        if content_height <= viewport_height:
            self.list_canvas.yview_moveto(0)
            return
        max_offset = max(0, content_height - viewport_height)
        target_top = max(0, min(target_top, max_offset))
        if content_height > 0:
            self.list_canvas.yview_moveto(target_top / content_height)

    def on_touch_press(self, event, index=None):
        if not self.is_active():
            return None
        self.touch_press_active = True
        self.touch_drag_active = False
        self.touch_press_y_root = event.y_root
        self.touch_press_scroll_top = self.current_scroll_top()
        self.touch_press_index = index
        self.touch_slider_index = None
        self.touch_slider_key = None
        slider_target = self.touch_slider_hit_target(index, event.x, event.y)
        if slider_target is not None:
            self.selected_index = index
            self.selection_visibility_pending = False
            self.touch_slider_index = index
            self.touch_slider_key = slider_target["key"]
            self.update_touch_slider(index, event.x)
        return "break"

    def on_touch_drag(self, event):
        if not self.touch_press_active:
            return None
        if self.touch_slider_key is not None and self.touch_slider_index is not None:
            self.touch_drag_active = True
            self.touch_scroll_suppress_until = time.monotonic() + TOUCH_SCROLL_SETTLE_SEC
            self.update_touch_slider(self.touch_slider_index, event.x)
            return "break"
        delta_y = event.y_root - self.touch_press_y_root
        if not self.touch_drag_active and abs(delta_y) < TOUCH_SCROLL_DRAG_THRESHOLD:
            return "break"
        self.touch_drag_active = True
        self.selection_visibility_pending = False
        self.touch_scroll_suppress_until = time.monotonic() + TOUCH_SCROLL_SETTLE_SEC
        self.scroll_to_top(self.touch_press_scroll_top - delta_y)
        return "break"

    def on_touch_release(self, event, index=None):
        if not self.touch_press_active:
            return None
        tapped_index = self.touch_press_index if index is None else index
        dragged = self.touch_drag_active
        self.touch_press_active = False
        self.touch_drag_active = False
        self.touch_press_index = None
        slider_index = self.touch_slider_index
        slider_key = self.touch_slider_key
        self.touch_slider_index = None
        self.touch_slider_key = None
        if slider_key is not None and slider_index is not None:
            self.touch_scroll_suppress_until = time.monotonic() + TOUCH_SCROLL_SETTLE_SEC
            self.update_touch_slider(slider_index, event.x)
            return "break"
        if dragged:
            self.touch_scroll_suppress_until = time.monotonic() + TOUCH_SCROLL_SETTLE_SEC
            return "break"
        if tapped_index is not None:
            detail_index = self.detail_entry_hit_index(tapped_index, event.x, event.y)
            if detail_index is not None:
                self.activate_touch_detail_entry(tapped_index, detail_index)
                return "break"
            key = self.item_key_at_index(tapped_index)
            if key in LIST_ITEM_KEYS and key == self.expanded_key and event.y > MENU_ROW_HEIGHT:
                return "break"
            self.on_row_click(tapped_index)
        return "break"

    def set_message(self, text, color=MENU_MUTED, timeout_ms=2200):
        self.status_label.config(text=text, fg=color)
        self.status_label.place(relx=0.5, rely=1.0, anchor="s", y=-MENU_TOAST_OFFSET_Y)
        self.status_label.lift()
        if self.message_job is not None:
            self.window.after_cancel(self.message_job)
            self.message_job = None
        if timeout_ms:
            self.message_job = self.window.after(timeout_ms, self.clear_message)

    def clear_message(self):
        self.message_job = None
        self.status_label.config(text="")
        self.status_label.place_forget()

    def item_key_at_index(self, index=None):
        resolved_index = self.selected_index if index is None else index
        return self.items[resolved_index]["key"]

    def detail_entries(self, key=None):
        resolved_key = self.detail_selection_key if key is None else key
        if resolved_key == WIFI_ITEM_KEY:
            return self.wifi_detail_entries()
        if resolved_key == BLUETOOTH_ITEM_KEY:
            return self.bluetooth_detail_entries()
        return []

    def clamp_detail_selection(self):
        if self.detail_selection_key not in LIST_ITEM_KEYS or self.expanded_key != self.detail_selection_key:
            self.detail_selection_index = 0
            return
        entries = self.detail_entries(self.detail_selection_key)
        if not entries:
            self.detail_selection_index = 0
            return
        self.detail_selection_index = max(0, min(self.detail_selection_index, len(entries) - 1))

    def wifi_detail_selected_entry(self):
        if self.detail_selection_key != WIFI_ITEM_KEY or self.expanded_key != WIFI_ITEM_KEY:
            return None
        entries = self.wifi_detail_entries()
        if not entries:
            return None
        self.clamp_detail_selection()
        return entries[self.detail_selection_index]

    def bluetooth_detail_selected_entry(self):
        if self.detail_selection_key != BLUETOOTH_ITEM_KEY or self.expanded_key != BLUETOOTH_ITEM_KEY:
            return None
        entries = self.bluetooth_detail_entries()
        if not entries:
            return None
        self.clamp_detail_selection()
        return entries[self.detail_selection_index]

    def wifi_detail_header_text(self):
        if self.wifi_action_in_progress:
            return "Working..."
        return "Select"

    def bluetooth_detail_header_text(self):
        if self.bluetooth_action_in_progress:
            return "Working..."
        return "Select"

    def short_wifi_label(self, name):
        label = str(name or "").strip()
        if not label:
            return "Connected"
        if len(label) > 14:
            return f"{label[:11]}..."
        return label

    def short_connected_device_label(self, devices):
        if not devices:
            return "On"
        if len(devices) > 1:
            return f"{len(devices)} connected"
        name = (devices[0].get("name") or "Connected").strip()
        if len(name) > 14:
            return f"{name[:11]}..."
        return name

    def wifi_password_prompt_open(self):
        return self.wifi_password_dialog.is_visible()

    def open_wifi_password_dialog(self, network):
        set_hud_text_input_active(True)
        opened = self.wifi_password_dialog.show(
            network,
            submit_callback=lambda password: self.submit_wifi_password(password),
            cancel_callback=self.handle_wifi_password_cancel,
        )
        if not opened:
            set_hud_text_input_active(False)
            self.set_message("Could not open WiFi password dialog", MENU_DESTRUCTIVE)
            return
        self.wifi_password_dialog.focus_entry()

    def close_wifi_password_dialog(self):
        set_hud_text_input_active(False)
        if self.wifi_password_dialog.is_visible():
            self.wifi_password_dialog.hide()
        try:
            self.window.lift()
        except tk.TclError:
            pass

    def handle_wifi_password_cancel(self):
        set_hud_text_input_active(False)
        try:
            self.window.lift()
        except tk.TclError:
            pass

    def submit_wifi_password(self, password):
        if self.wifi_action_in_progress:
            return
        network = dict(self.wifi_password_dialog.network or {})
        if not str(password or ""):
            self.wifi_password_dialog.set_error("Password required")
            self.wifi_password_dialog.focus_entry()
            return
        self.close_wifi_password_dialog()
        self.start_wifi_network_action(network, password=password)

    def collapse_expanded(self, play_sound=False):
        was_expanded = self.expanded_key is not None or self.adjusting_key is not None or self.detail_selection_key is not None
        if self.expanded_key == UPDATE_ITEM_KEY and not self.software_update_in_progress:
            self.software_update_available = False
            self.software_remote_version = None
        self.cancel_bluetooth_open_refresh()
        self.touch_slider_index = None
        self.touch_slider_key = None
        self.adjusting_key = None
        self.expanded_key = None
        self.detail_selection_key = None
        self.detail_selection_index = 0
        if play_sound and was_expanded and self.sound_player is not None:
            self.sound_player.play_dropdown_close()

    def system_action_pending(self):
        return (
            self.system_action_job is not None
            or self.software_update_check_in_progress
            or self.software_update_in_progress
        )

    def show(self):
        if self.target_visible or self.system_action_pending():
            return
        self.close_wifi_password_dialog()
        self.target_visible = True
        self.notify_visibility_change(True)
        self.software_version = read_workspace_version()
        self.software_update_available = False
        self.software_remote_version = None
        self.sync_snapshot()
        self.sync_brightness_value()
        self.collapse_expanded()
        self.selected_index = max(0, min(self.selected_index, len(self.items) - 1))
        self.selection_visibility_pending = True
        self.clear_message()
        self.render()
        set_quick_menu_active(True)
        self.visible = True
        self.set_cursor_hidden(True)
        was_mapped = self.window.winfo_ismapped()
        self.window.deiconify()
        if not was_mapped:
            self.apply_rect(self.collapsed_rect())
            self.set_window_alpha(MENU_COLLAPSED_ALPHA)
        self.window.lift()
        if self.sound_player is not None:
            self.sound_player.play_settings_open()
        self.begin_animation(True)

    def hide(self, play_sound=True):
        if self.system_action_pending() and play_sound:
            return
        if not self.target_visible and not self.visible:
            return
        self.close_wifi_password_dialog()
        self.target_visible = False
        self.notify_visibility_change(False)
        self.collapse_expanded()
        if self.message_job is not None:
            self.window.after_cancel(self.message_job)
            self.message_job = None
        if not self.window.winfo_ismapped():
            self.visible = False
            self.set_cursor_hidden(False)
            set_quick_menu_active(False)
            self.clear_message()
            self.render()
            return
        if play_sound and self.sound_player is not None:
            self.sound_player.play_settings_close()
        self.begin_animation(False)

    def toggle(self):
        if self.system_action_pending():
            return
        if self.target_visible:
            self.hide()
        else:
            self.show()

    def sync_snapshot(self, snapshot=None):
        if snapshot is None and self.snapshot_getter is not None:
            snapshot = self.snapshot_getter()
        if not snapshot:
            return False
        snapshot_changed = snapshot != self.snapshot
        if snapshot_changed:
            self.snapshot = dict(snapshot)
        next_value = volume_value(
            snapshot.get("volume_level"),
            snapshot.get("volume_muted"),
            default=self.volume_value,
        )
        volume_changed = False
        if self.adjusting_key != VOLUME_ITEM_KEY and self.volume_animation_job is None:
            if next_value != self.volume_value or next_value != self.volume_target_value:
                self.volume_value = next_value
                self.volume_target_value = next_value
                volume_changed = True
        return snapshot_changed or volume_changed

    def notify_snapshot_change(self, snapshot=None):
        if self.on_snapshot_change is None:
            return
        resolved_snapshot = self.snapshot if snapshot is None else snapshot
        if not resolved_snapshot:
            return
        try:
            self.on_snapshot_change(dict(resolved_snapshot))
        except Exception:
            pass

    def push_snapshot(self, snapshot):
        if not snapshot:
            return False
        changed = self.sync_snapshot(snapshot)
        self.notify_snapshot_change(snapshot)
        return changed

    def optimistic_snapshot(self, **updates):
        snapshot = dict(self.snapshot)
        snapshot.update(updates)
        return snapshot

    def sync_brightness_value(self):
        if self.adjusting_key == BRIGHTNESS_ITEM_KEY:
            return False
        next_value = get_display_brightness(default=self.brightness_value)
        if next_value == self.brightness_value:
            return False
        self.brightness_value = next_value
        return True

    def describe_item(self, key):
        if key == WIFI_ITEM_KEY:
            state = self.snapshot.get("wifi_state", "offline")
            if state == "connected":
                return self.short_wifi_label(self.snapshot.get("wifi_name", ""))
            if state == "disabled":
                return "Off"
            return "Offline"

        if key == BLUETOOTH_ITEM_KEY:
            if not self.snapshot.get("bluetooth_enabled", False):
                return "Off"
            return self.short_connected_device_label(self.snapshot.get("bluetooth_connected_devices", []))

        if key == VOLUME_ITEM_KEY:
            return f"{self.volume_value}%"

        if key == BRIGHTNESS_ITEM_KEY:
            return f"{self.brightness_value}%"

        if key == UPDATE_ITEM_KEY:
            return software_version_label(self.software_version)

        return ""

    def on_row_click(self, index):
        if self.wifi_password_prompt_open() or self.system_action_pending():
            return
        self.selected_index = index
        self.selection_visibility_pending = False
        self.render()
        self.on_a()

    def request_list_refresh(self, key, force=False):
        if key == WIFI_ITEM_KEY:
            if self.wifi_action_in_progress:
                return
            if self.wifi_scan_in_progress:
                return
            self.wifi_scan_in_progress = True
            self.render()
            threading.Thread(target=self.scan_wifi_networks, daemon=True).start()
            return

        if key == BLUETOOTH_ITEM_KEY:
            self.cancel_bluetooth_open_refresh()
            if self.bluetooth_action_in_progress:
                return
            if self.bluetooth_scan_in_progress:
                return
            self.bluetooth_scan_in_progress = True
            if force:
                self.bluetooth_devices = []
            self.render()
            threading.Thread(target=self.scan_bluetooth_devices, daemon=True).start()

    def scan_wifi_networks(self):
        baseline_networks = list(self.wifi_networks)
        networks = refresh_wifi_networks(previous_networks=baseline_networks)
        try:
            self.window.after(0, lambda: self.finish_wifi_scan(networks))
        except tk.TclError:
            pass

    def finish_wifi_scan(self, networks):
        self.wifi_scan_in_progress = False
        self.wifi_networks = networks
        if self.expanded_key == WIFI_ITEM_KEY:
            self.clamp_detail_selection()
            self.render()

    def scan_bluetooth_devices(self):
        devices = nearby_bluetooth_devices()
        try:
            self.window.after(0, lambda: self.finish_bluetooth_scan(devices))
        except tk.TclError:
            pass

    def finish_bluetooth_scan(self, devices):
        self.bluetooth_scan_in_progress = False
        self.bluetooth_devices = devices
        if self.expanded_key == BLUETOOTH_ITEM_KEY:
            self.clamp_detail_selection()
            self.render()

    def cancel_bluetooth_open_refresh(self):
        if self.bluetooth_open_refresh_job is None:
            return
        try:
            self.window.after_cancel(self.bluetooth_open_refresh_job)
        except tk.TclError:
            pass
        self.bluetooth_open_refresh_job = None

    def run_bluetooth_open_refresh(self):
        self.bluetooth_open_refresh_job = None
        if self.expanded_key != BLUETOOTH_ITEM_KEY or self.detail_selection_key != BLUETOOTH_ITEM_KEY:
            return
        if not self.snapshot.get("bluetooth_enabled", False):
            return
        self.request_list_refresh(BLUETOOTH_ITEM_KEY, force=False)

    def schedule_bluetooth_open_refresh(self):
        self.cancel_bluetooth_open_refresh()
        try:
            self.bluetooth_open_refresh_job = self.window.after(
                BLUETOOTH_OPEN_SCAN_DELAY_MS,
                self.run_bluetooth_open_refresh,
            )
        except tk.TclError:
            self.bluetooth_open_refresh_job = None

    def move_selection(self, delta):
        if not self.is_active() or self.system_action_pending():
            return
        if self.wifi_password_prompt_open():
            return
        if self.adjusting_key in ADJUSTABLE_ITEM_KEYS:
            self.adjust_active_slider(-delta)
            return
        if self.detail_selection_key in LIST_ITEM_KEYS and self.expanded_key == self.detail_selection_key:
            entries = self.detail_entries(self.detail_selection_key)
            if not entries:
                return
            self.detail_selection_index = (self.detail_selection_index + delta) % len(entries)
            self.selection_visibility_pending = True
            if self.sound_player is not None:
                self.sound_player.play_scroll(delta)
            self.render()
            return
        self.selected_index = (self.selected_index + delta) % len(self.items)
        self.selection_visibility_pending = True
        selected_key = self.item_key_at_index()
        if self.expanded_key is not None and self.expanded_key != selected_key:
            self.clear_message()
            self.collapse_expanded(play_sound=True)
        if self.sound_player is not None:
            self.sound_player.play_scroll(delta)
        self.render()

    def move_horizontal(self, delta):
        if not self.is_active() or self.system_action_pending():
            return
        if self.wifi_password_prompt_open():
            return
        if self.adjusting_key in ADJUSTABLE_ITEM_KEYS:
            self.adjust_active_slider(delta)

    def adjust_active_slider(self, direction):
        if self.adjusting_key == VOLUME_ITEM_KEY:
            self.adjust_volume(direction * VOLUME_ADJUST_STEP)
            return
        if self.adjusting_key == BRIGHTNESS_ITEM_KEY:
            self.adjust_brightness(direction * BRIGHTNESS_ADJUST_STEP)

    def set_slider_value(self, key, value, animate=True):
        if key == VOLUME_ITEM_KEY:
            return self.set_volume_absolute(value, animate=animate)
        if key == BRIGHTNESS_ITEM_KEY:
            return self.set_brightness_absolute(value)
        return False

    def set_volume_absolute(self, value, animate=True):
        next_target = max(0, min(100, int(round(value))))
        if next_target == self.volume_target_value and next_target == self.volume_value:
            return False
        delta = next_target - (self.volume_target_value if animate else self.volume_value)
        self.volume_target_value = next_target
        if delta != 0 and self.sound_player is not None:
            self.sound_player.play_slider(delta)
        if animate:
            if self.volume_animation_job is None:
                self.step_volume_animation()
            return True
        self.cancel_volume_animation()
        self.volume_value = next_target
        self.queue_volume_write(self.volume_value)
        self.push_snapshot(
            self.optimistic_snapshot(
                volume_level=self.volume_value,
                volume_muted=self.volume_value <= 0,
            )
        )
        self.render()
        return True

    def adjust_volume(self, delta):
        self.set_volume_absolute(self.volume_target_value + delta)

    def set_brightness_absolute(self, value):
        next_value = clamp_brightness_percent(value)
        if next_value == self.brightness_value:
            return False
        if not set_display_brightness(next_value):
            self.set_message("Brightness control unavailable", MENU_DESTRUCTIVE)
            return False
        delta = next_value - self.brightness_value
        self.brightness_value = next_value
        if delta != 0 and self.sound_player is not None:
            self.sound_player.play_slider(delta)
        self.render()
        return True

    def adjust_brightness(self, delta):
        self.set_brightness_absolute(self.brightness_value + delta)

    def open_adjustable(self, key):
        self.expanded_key = key
        self.adjusting_key = key
        self.clear_message()
        if self.sound_player is not None:
            self.sound_player.play_dropdown_open()
        if key == VOLUME_ITEM_KEY:
            self.sync_snapshot()
            self.volume_target_value = self.volume_value
        elif key == BRIGHTNESS_ITEM_KEY:
            self.sync_brightness_value()
        self.render()
        self.center_selected_row()

    def open_wifi_detail(self):
        self.clear_message()
        self.adjusting_key = None
        self.expanded_key = WIFI_ITEM_KEY
        self.detail_selection_key = WIFI_ITEM_KEY
        self.detail_selection_index = 0
        if self.sound_player is not None:
            self.sound_player.play_dropdown_open()
        if self.snapshot.get("wifi_state", "offline") != "disabled":
            self.request_list_refresh(WIFI_ITEM_KEY, force=True)
        self.render()
        self.center_selected_row()

    def set_wifi_action_state(self, active):
        self.wifi_action_in_progress = bool(active)
        self.render()

    def finish_wifi_action(self, success, message, snapshot, networks=None):
        self.wifi_action_in_progress = False
        self.wifi_scan_in_progress = False
        self.push_snapshot(snapshot)
        if networks is not None:
            self.wifi_networks = networks
        self.clamp_detail_selection()
        if message:
            self.set_message(message, MENU_TOAST_TEXT if success else MENU_DESTRUCTIVE)
        else:
            self.clear_message()
        self.render()
        self.center_selected_row()

    def run_wifi_power_action(self, enable):
        success, error = set_wifi_power(enable)
        snapshot = build_status_snapshot()
        networks = [] if not enable else None
        if success and enable:
            try:
                self.window.after(
                    0,
                    lambda: (
                        self.finish_wifi_action(True, "WiFi is on", snapshot, networks=None),
                        self.request_list_refresh(WIFI_ITEM_KEY, force=True),
                    ),
                )
                return
            except tk.TclError:
                return
        message = "WiFi is off" if success and not enable else error
        try:
            self.window.after(0, lambda: self.finish_wifi_action(success, message, snapshot, networks=networks))
        except tk.TclError:
            pass

    def toggle_wifi_power(self):
        if self.wifi_action_in_progress:
            self.set_message("WiFi action already running", MENU_DESTRUCTIVE)
            return
        enable = self.snapshot.get("wifi_state", "offline") == "disabled"
        self.set_wifi_action_state(True)
        self.set_message(f"Turning WiFi {'on' if enable else 'off'}...", MENU_TOAST_TEXT, timeout_ms=0)
        self.push_snapshot(
            self.optimistic_snapshot(
                wifi_signal=0,
                wifi_state="offline" if enable else "disabled",
                wifi_name="",
            )
        )
        threading.Thread(target=self.run_wifi_power_action, args=(enable,), daemon=True).start()

    def run_wifi_network_action(self, network, password=None):
        if network.get("active"):
            success = True
            error = ""
            success_message = f"{network['ssid']} already connected"
        else:
            success, error = wifi_connect_network(network, password=password)
            success_message = ""
        snapshot = build_status_snapshot()
        networks = nearby_wifi_networks(rescan=False) if snapshot.get("wifi_state") != "disabled" else []
        if success and not network.get("active") and self.on_wifi_connected is not None:
            try:
                self.on_wifi_connected(snapshot.get("wifi_name") or network.get("ssid") or "WiFi")
            except Exception:
                pass
        message = success_message if success else error
        try:
            self.window.after(0, lambda: self.finish_wifi_action(success, message, snapshot, networks=networks))
        except tk.TclError:
            pass

    def start_wifi_network_action(self, network, password=None):
        self.set_wifi_action_state(True)
        self.set_message(f"Connecting {network['ssid']}...", MENU_TOAST_TEXT, timeout_ms=0)
        threading.Thread(target=self.run_wifi_network_action, args=(dict(network), password), daemon=True).start()

    def activate_wifi_detail_entry(self):
        if self.wifi_action_in_progress or self.system_action_pending():
            self.set_message("WiFi action already running", MENU_DESTRUCTIVE)
            return
        entry = self.wifi_detail_selected_entry()
        if not entry:
            return
        kind = entry.get("kind")
        if kind == "power":
            self.toggle_wifi_power()
            return
        if kind == "scan":
            if self.sound_player is not None:
                self.sound_player.play_refresh()
            self.request_list_refresh(WIFI_ITEM_KEY, force=True)
            self.render()
            return
        if kind != "network":
            return
        network = dict(entry["network"])
        if network.get("active"):
            self.set_message(f"{network['ssid']} already connected", MENU_TOAST_TEXT)
            return
        if wifi_security_requires_password(network):
            self.clear_message()
            self.open_wifi_password_dialog(network)
            return
        self.start_wifi_network_action(network)

    def open_bluetooth_detail(self):
        self.clear_message()
        self.adjusting_key = None
        self.expanded_key = BLUETOOTH_ITEM_KEY
        self.detail_selection_key = BLUETOOTH_ITEM_KEY
        self.detail_selection_index = 0
        self.cancel_bluetooth_open_refresh()
        if self.sound_player is not None:
            self.sound_player.play_dropdown_open()
        if self.snapshot.get("bluetooth_enabled", False):
            self.schedule_bluetooth_open_refresh()
        self.render()
        self.center_selected_row()

    def set_bluetooth_action_state(self, active):
        self.bluetooth_action_in_progress = bool(active)
        self.render()

    def finish_bluetooth_action(self, success, message, snapshot, devices=None):
        self.cancel_bluetooth_open_refresh()
        self.bluetooth_action_in_progress = False
        self.bluetooth_scan_in_progress = False
        self.push_snapshot(snapshot)
        if devices is not None:
            self.bluetooth_devices = devices
        self.clamp_detail_selection()
        if message:
            self.set_message(message, MENU_TOAST_TEXT if success else MENU_DESTRUCTIVE)
        else:
            self.clear_message()
        self.render()
        self.center_selected_row()

    def run_bluetooth_power_action(self, enable):
        success, error = set_bluetooth_power(enable)
        snapshot = build_status_snapshot()
        devices = [] if not enable else None
        if success and enable:
            try:
                self.window.after(
                    0,
                    lambda: (
                        self.finish_bluetooth_action(True, "Bluetooth is on", snapshot, devices=None),
                        self.request_list_refresh(BLUETOOTH_ITEM_KEY, force=True),
                    ),
                )
                return
            except tk.TclError:
                return
        message = "Bluetooth is off" if success and not enable else error
        try:
            self.window.after(0, lambda: self.finish_bluetooth_action(success, message, snapshot, devices=devices))
        except tk.TclError:
            pass

    def toggle_bluetooth_power(self):
        if self.bluetooth_action_in_progress:
            self.set_message("Bluetooth action already running", MENU_DESTRUCTIVE)
            return
        enable = not self.snapshot.get("bluetooth_enabled", False)
        self.set_bluetooth_action_state(True)
        self.set_message(f"Turning Bluetooth {'on' if enable else 'off'}...", MENU_TOAST_TEXT, timeout_ms=0)
        self.push_snapshot(
            self.optimistic_snapshot(
                bluetooth_enabled=enable,
                bluetooth_connected_devices=[],
            )
        )
        threading.Thread(target=self.run_bluetooth_power_action, args=(enable,), daemon=True).start()

    def run_bluetooth_device_action(self, device):
        if device.get("connected"):
            success, info, error = bluetooth_disconnect_device(device["address"])
            success_message = f"{device['name']} disconnected"
            refresh_scan_seconds = 0
        else:
            success, info, error = bluetooth_connect_device(device["address"], already_paired=device.get("paired", False))
            success_message = ""
            refresh_scan_seconds = BLUETOOTH_POST_ACTION_SCAN_SECONDS
        snapshot = build_status_snapshot()
        devices = (
            nearby_bluetooth_devices(scan_seconds=refresh_scan_seconds)
            if snapshot.get("bluetooth_enabled", False)
            else []
        )
        if success and not device.get("connected") and info.get("connected") and self.on_bluetooth_connected is not None:
            try:
                self.on_bluetooth_connected(device["address"], info.get("name") or device["name"])
            except Exception:
                pass
        message = success_message if success else error
        try:
            self.window.after(0, lambda: self.finish_bluetooth_action(success, message, snapshot, devices=devices))
        except tk.TclError:
            pass

    def activate_bluetooth_detail_entry(self):
        if self.bluetooth_action_in_progress or self.system_action_pending():
            self.set_message("Bluetooth action already running", MENU_DESTRUCTIVE)
            return
        entry = self.bluetooth_detail_selected_entry()
        if not entry:
            return
        kind = entry.get("kind")
        if kind == "power":
            self.toggle_bluetooth_power()
            return
        if kind == "scan":
            if self.sound_player is not None:
                self.sound_player.play_refresh()
            self.request_list_refresh(BLUETOOTH_ITEM_KEY, force=True)
            self.render()
            return
        if kind != "device":
            return
        device = dict(entry["device"])
        verb = "Disconnecting" if device.get("connected") else ("Connecting" if device.get("paired") else "Pairing")
        self.set_bluetooth_action_state(True)
        self.set_message(f"{verb} {device['name']}...", MENU_TOAST_TEXT, timeout_ms=0)
        threading.Thread(target=self.run_bluetooth_device_action, args=(device,), daemon=True).start()

    def on_a(self):
        if not self.is_active() or self.system_action_pending():
            return
        if self.wifi_password_prompt_open():
            self.submit_wifi_password(self.wifi_password_dialog.password())
            return
        item = self.items[self.selected_index]
        key = item["key"]

        if key in ADJUSTABLE_ITEM_KEYS:
            if self.adjusting_key == key:
                self.clear_message()
                self.collapse_expanded(play_sound=True)
                self.render()
                self.center_selected_row()
                return
            self.open_adjustable(key)
            return

        if key in LIST_ITEM_KEYS:
            if self.expanded_key == key and self.detail_selection_key == key:
                if key == WIFI_ITEM_KEY:
                    self.activate_wifi_detail_entry()
                else:
                    self.activate_bluetooth_detail_entry()
                return
            if self.expanded_key == key:
                self.clear_message()
                self.collapse_expanded(play_sound=True)
            else:
                if key == WIFI_ITEM_KEY:
                    self.open_wifi_detail()
                    return
                if key == BLUETOOTH_ITEM_KEY:
                    self.open_bluetooth_detail()
                    return
                self.clear_message()
                self.adjusting_key = None
                self.expanded_key = key
                self.request_list_refresh(key, force=True)
            self.render()
            self.center_selected_row()
            return

        if key in CONFIRM_ITEM_KEYS:
            if key == UPDATE_ITEM_KEY:
                if self.expanded_key == key and self.software_update_available:
                    self.execute_item(key)
                else:
                    self.start_software_update_check()
                return
            if self.expanded_key == key:
                self.execute_item(key)
                return
            self.adjusting_key = None
            self.expanded_key = key
            if self.sound_player is not None:
                self.sound_player.play_dropdown_open()
            self.set_message("Press A again to confirm", MENU_TOAST_TEXT)
            self.render()
            self.center_selected_row()
            return

        self.execute_item(key)

    def on_b(self):
        if not self.is_active() or self.system_action_pending():
            return
        if self.wifi_password_prompt_open():
            self.close_wifi_password_dialog()
            return
        if self.expanded_key is not None or self.adjusting_key is not None:
            self.clear_message()
            self.collapse_expanded(play_sound=True)
            self.render()
            return
        self.hide()

    def finish_system_action(self, key):
        self.system_action_job = None
        if key == RESTART_ITEM_KEY:
            if restart_kiosk():
                self.hide(play_sound=False)
                return
            self.set_message("Restart failed to start", MENU_DESTRUCTIVE)
            return

        if key == SHUTDOWN_ITEM_KEY:
            if spawn_detached(["sudo", "-n", "systemctl", "poweroff"]):
                self.hide(play_sound=False)
                return
            self.set_message("Shutdown failed to start", MENU_DESTRUCTIVE)

    def schedule_system_action(self, key):
        if self.system_action_pending():
            return
        if key == RESTART_ITEM_KEY:
            message = "Restarting kiosk..."
            delay_ms = SOUND_RESTART_DELAY_MS
            if self.sound_player is not None:
                self.sound_player.play_restart()
        else:
            message = "Shutting down system..."
            delay_ms = SOUND_SHUTDOWN_DELAY_MS
            if self.sound_player is not None:
                self.sound_player.play_shutdown()
        self.set_message(message, MENU_TOAST_TEXT, timeout_ms=0)
        self.system_action_job = self.window.after(delay_ms, lambda resolved_key=key: self.finish_system_action(resolved_key))

    def set_software_update_state(self, active):
        self.software_update_in_progress = bool(active)
        self.render()

    def set_software_update_check_state(self, active):
        self.software_update_check_in_progress = bool(active)
        self.render()

    def finish_software_update_check(self, available, current_version=None, remote_version=None, message=None):
        self.software_update_check_in_progress = False
        resolved_current_version = str(current_version or read_workspace_version()).strip()
        self.software_version = resolved_current_version or read_workspace_version()
        self.software_update_available = bool(available)
        self.software_remote_version = str(remote_version).strip() if remote_version else None

        if self.software_update_available:
            self.adjusting_key = None
            self.expanded_key = UPDATE_ITEM_KEY
            if self.sound_player is not None:
                self.sound_player.play_dropdown_open()
            self.clear_message()
            self.render()
            self.center_selected_row()
            return

        self.software_remote_version = None
        if self.expanded_key == UPDATE_ITEM_KEY:
            self.collapse_expanded()
        if message:
            self.set_message(message, MENU_DESTRUCTIVE)
            return
        self.set_message("Updated to latest version", MENU_TOAST_TEXT)

    def finish_software_update(self, success, message):
        self.software_update_in_progress = False
        self.software_version = read_workspace_version()
        if success:
            self.software_update_available = False
            self.software_remote_version = None
            self.set_message("Restarting kiosk...", MENU_TOAST_TEXT, timeout_ms=0)
            if restart_kiosk():
                self.hide(play_sound=False)
                return
            self.set_message("Restart failed to start", MENU_DESTRUCTIVE)
            self.render()
            self.center_selected_row()
            return
        self.set_message(message, MENU_DESTRUCTIVE)
        self.render()
        self.center_selected_row()

    def run_software_update_check(self):
        if not os.path.exists(OTA_CHECK_CMD[1]):
            try:
                self.window.after(0, lambda: self.finish_software_update_check(False, message="Update script unavailable"))
            except tk.TclError:
                pass
            return
        try:
            result = subprocess.run(
                OTA_CHECK_CMD,
                capture_output=True,
                text=True,
                env=display_env(),
                cwd=str(WORKSPACE_ROOT),
            )
            output = "\n".join(part for part in (result.stdout, result.stderr) if part)
            metadata = parse_command_metadata(output, "CHECK_")
            current_version = metadata.get("CHECK_CURRENT_VERSION") or read_workspace_version()
            remote_version = metadata.get("CHECK_REMOTE_VERSION") or None
            if result.returncode == OTA_CHECK_AVAILABLE_RC:
                callback = lambda: self.finish_software_update_check(
                    True,
                    current_version=current_version,
                    remote_version=remote_version,
                )
            elif result.returncode == 0:
                callback = lambda: self.finish_software_update_check(
                    False,
                    current_version=current_version,
                    remote_version=remote_version,
                )
            else:
                message = command_error_message(output, "Update check failed")
                callback = lambda resolved_message=message: self.finish_software_update_check(
                    False,
                    current_version=current_version,
                    message=resolved_message,
                )
            self.window.after(0, callback)
        except Exception:
            try:
                self.window.after(0, lambda: self.finish_software_update_check(False, message="Update check failed"))
            except tk.TclError:
                pass

    def run_software_update(self):
        if not os.path.exists(OTA_UPDATE_CMD[1]):
            try:
                self.window.after(0, lambda: self.finish_software_update(False, "Update script unavailable"))
            except tk.TclError:
                pass
            return
        try:
            result = subprocess.run(
                OTA_UPDATE_CMD,
                capture_output=True,
                text=True,
                env=display_env(),
                cwd=str(WORKSPACE_ROOT),
            )
            output = "\n".join(part for part in (result.stdout, result.stderr) if part)
            if result.returncode == 0:
                callback = lambda: self.finish_software_update(True, "Software updated")
            else:
                message = command_error_message(output, "Software update failed")
                callback = lambda resolved_message=message: self.finish_software_update(False, resolved_message)
            self.window.after(0, callback)
        except Exception:
            try:
                self.window.after(0, lambda: self.finish_software_update(False, "Software update failed"))
            except tk.TclError:
                pass

    def start_software_update_check(self):
        if self.software_update_check_in_progress or self.software_update_in_progress:
            self.set_message("Update check already running", MENU_DESTRUCTIVE)
            return
        self.software_version = read_workspace_version()
        self.software_update_available = False
        self.software_remote_version = None
        if self.expanded_key == UPDATE_ITEM_KEY:
            self.collapse_expanded()
        self.set_software_update_check_state(True)
        if self.sound_player is not None:
            self.sound_player.play_refresh()
        self.set_message("Checking for updates...", MENU_TOAST_TEXT, timeout_ms=0)
        threading.Thread(target=self.run_software_update_check, daemon=True).start()
        self.render()
        self.center_selected_row()

    def start_software_update(self):
        if self.software_update_in_progress:
            self.set_message("Software update already running", MENU_DESTRUCTIVE)
            return
        self.software_version = read_workspace_version()
        self.set_software_update_state(True)
        if self.sound_player is not None:
            self.sound_player.play_refresh()
        self.set_message("Updating software...", MENU_TOAST_TEXT, timeout_ms=0)
        threading.Thread(target=self.run_software_update, daemon=True).start()
        self.render()
        self.center_selected_row()

    def execute_item(self, key):
        if key == UPDATE_ITEM_KEY:
            self.start_software_update()
            return

        if key == RESTART_ITEM_KEY:
            self.schedule_system_action(key)
            return

        if key == SHUTDOWN_ITEM_KEY:
            self.schedule_system_action(key)
            return

        label = self.item_labels.get(key, "Setting")
        self.set_message(f"{label} is layout-only for now", MENU_TOAST_TEXT)

    def refresh_dynamic(self, snapshot=None):
        if not self.is_active():
            return
        if self.sync_snapshot(snapshot):
            self.render()

    def menu_icon_path(self, key):
        if key == WIFI_ITEM_KEY:
            return wifi_icon_path(self.snapshot.get("wifi_state", "offline"))
        if key == BLUETOOTH_ITEM_KEY:
            return bluetooth_icon_path(self.snapshot.get("bluetooth_enabled", False))
        if key == VOLUME_ITEM_KEY:
            preview_level = self.volume_value if self.adjusting_key == VOLUME_ITEM_KEY else self.snapshot.get("volume_level")
            preview_muted = (
                self.volume_value <= 0 if self.adjusting_key == VOLUME_ITEM_KEY else self.snapshot.get("volume_muted", False)
            )
            return volume_icon_path(preview_level, preview_muted)
        if key == BRIGHTNESS_ITEM_KEY:
            return "hud/brightness.png"
        if key == UPDATE_ITEM_KEY:
            return "hud/cursor_settings.png"
        if key == RESTART_ITEM_KEY:
            return "hud/restart.png"
        if key == SHUTDOWN_ITEM_KEY:
            return "hud/shutdown.png"
        return None

    def load_menu_icon(self, key, focused):
        relative_path = self.menu_icon_path(key)
        if relative_path is None:
            return None
        color = MENU_ICON_ACTIVE if focused else MENU_ICON
        return load_status_icon(relative_path, color, MENU_ICON_SIZE)

    def detail_panel_height(self, key):
        if key in ADJUSTABLE_ITEM_KEYS:
            return 98
        if key == WIFI_ITEM_KEY:
            row_count = max(1, len(self.wifi_detail_entries()))
            return DETAIL_LIST_PANEL_BASE_HEIGHT + (row_count * DETAIL_LIST_PANEL_ROW_HEIGHT) + (
                max(0, row_count - 1) * DETAIL_LIST_PANEL_ROW_GAP
            )
        if key == BLUETOOTH_ITEM_KEY:
            row_count = max(1, len(self.bluetooth_detail_entries()))
            return DETAIL_LIST_PANEL_BASE_HEIGHT + (row_count * DETAIL_LIST_PANEL_ROW_HEIGHT) + (
                max(0, row_count - 1) * DETAIL_LIST_PANEL_ROW_GAP
            )
        if key in CONFIRM_ITEM_KEYS:
            return DETAIL_CONFIRM_PANEL_BASE_HEIGHT
        return 0

    def wifi_detail_entries(self):
        state = self.snapshot.get("wifi_state", "offline")
        connected_name = self.snapshot.get("wifi_name", "")
        entries = [
            {
                "kind": "power",
                "title": "Turn WiFi Off" if state != "disabled" else "Turn WiFi On",
                "meta": (
                    f"Connected to {connected_name}"
                    if state == "connected" and connected_name
                    else ("Ready for nearby WiFi" if state != "disabled" else "Enable WiFi to scan and connect")
                ),
                "accent": False,
            }
        ]

        if state == "disabled":
            entries.append(
                {
                    "kind": "empty",
                    "title": "WiFi is turned off",
                    "meta": "Turn it on to find nearby networks",
                    "accent": False,
                }
            )
            return entries

        entries.append(
            {
                "kind": "scan",
                "title": "Scanning nearby networks..." if self.wifi_scan_in_progress else "Refresh nearby networks",
                "meta": (
                    "Looking for nearby access points"
                    if self.wifi_scan_in_progress
                    else "Run a fresh WiFi scan"
                ),
                "accent": self.wifi_scan_in_progress,
            }
        )

        if not self.wifi_networks:
            entries.append(
                {
                    "kind": "empty",
                    "title": "Looking for nearby networks..." if self.wifi_scan_in_progress else "No nearby networks found",
                    "meta": (
                        "Refresh is running now"
                        if self.wifi_scan_in_progress
                        else "Try Refresh nearby networks again"
                    ),
                    "accent": False,
                }
            )
            return entries

        for network in self.wifi_networks[:WIFI_NETWORK_LIST_MAX_ITEMS]:
            security = network["security"] or "Open"
            status = "Connected" if network["active"] else ("Password required" if wifi_security_requires_password(network) else "Open")
            meta = f"{network['signal']}% | {security} | {status}"
            if network["active"]:
                meta = f"Connected | {network['signal']}% | {security}"
            entries.append(
                {
                    "kind": "network",
                    "title": network["ssid"],
                    "meta": meta,
                    "accent": network["active"],
                    "network": network,
                }
            )
        return entries

    def bluetooth_detail_entries(self):
        enabled = self.snapshot.get("bluetooth_enabled", False)
        connected_devices = self.snapshot.get("bluetooth_connected_devices", [])
        entries = [
            {
                "kind": "power",
                "title": "Turn Bluetooth Off" if enabled else "Turn Bluetooth On",
                "meta": (
                    f"{len(connected_devices)} connected"
                    if enabled and connected_devices
                    else ("Ready for pairing" if enabled else "Enable nearby pairing and scans")
                ),
                "accent": False,
            }
        ]

        if not enabled:
            entries.append(
                {
                    "kind": "empty",
                    "title": "Bluetooth is turned off",
                    "meta": "Turn it on to find nearby devices",
                    "accent": False,
                }
            )
            return entries

        entries.append(
            {
                "kind": "scan",
                "title": "Scanning nearby devices..." if self.bluetooth_scan_in_progress else "Refresh nearby devices",
                "meta": (
                    "Looking for mouse, keyboard, controller, speaker"
                    if self.bluetooth_scan_in_progress
                    else "Run a fresh nearby Bluetooth scan"
                ),
                "accent": self.bluetooth_scan_in_progress,
            }
        )

        if not self.bluetooth_devices:
            entries.append(
                {
                    "kind": "empty",
                    "title": "No nearby devices found",
                    "meta": "Try Refresh nearby devices again",
                    "accent": False,
                }
            )
            return entries

        for device in self.bluetooth_devices[:BLUETOOTH_DEVICE_LIST_MAX_ITEMS]:
            if device.get("connected"):
                status = "Connected"
            elif device.get("paired"):
                status = "Paired"
            elif device.get("known"):
                status = "Known"
            else:
                status = "Found"
            entries.append(
                {
                    "kind": "device",
                    "title": device["name"],
                    "meta": f"{device.get('type', 'Device')} | {status}",
                    "accent": device.get("connected") or device.get("paired"),
                    "device": device,
                }
            )
        return entries

    def draw_slider(self, canvas, x1, x2, y_pos, value):
        track_y1 = y_pos - (SLIDER_TRACK_HEIGHT // 2)
        track_y2 = track_y1 + SLIDER_TRACK_HEIGHT
        fill_x = x1 + int(round((x2 - x1) * max(0, min(100, value)) / 100.0))
        draw_rounded_rect(canvas, x1, track_y1, x2, track_y2, SLIDER_TRACK_HEIGHT // 2, SLIDER_TRACK)
        if fill_x > x1:
            draw_gradient_rounded_rect(
                canvas,
                x1,
                track_y1,
                fill_x,
                track_y2,
                SLIDER_TRACK_HEIGHT // 2,
                MENU_CTA_START,
                MENU_CTA_END,
            )
        knob_center_x = max(x1, min(x2, fill_x))
        knob_image = load_status_icon("hud/slider_dot.png", TEXT, SLIDER_THUMB_ICON_SIZE)
        if knob_image is not None:
            if hasattr(canvas, "images"):
                canvas.images.append(knob_image)
            canvas.create_image(knob_center_x, y_pos, image=knob_image, anchor="c")
            return
        canvas.create_oval(
            knob_center_x - SLIDER_KNOB_RADIUS,
            y_pos - SLIDER_KNOB_RADIUS,
            knob_center_x + SLIDER_KNOB_RADIUS,
            y_pos + SLIDER_KNOB_RADIUS,
            fill=TEXT,
            outline="",
            width=0,
        )
        canvas.create_oval(
            knob_center_x - 4,
            y_pos - 4,
            knob_center_x + 4,
            y_pos + 4,
            fill=MENU_HOT_PINK,
            outline="",
            width=0,
        )

    def detail_container_bounds(self, width, card_height, left_inset=MENU_ROW_TEXT_X, right_inset=MENU_ROW_TRAILING_PAD):
        x1 = left_inset
        x2 = max(x1 + 1, width - right_inset)
        y1 = MENU_ROW_HEIGHT + DETAIL_PANEL_TOP_PAD
        y2 = max(y1 + 1, card_height - DETAIL_PANEL_BOTTOM_PAD)
        return x1, y1, x2, y2

    def draw_detail_container(self, card, width, card_height, left_inset=MENU_ROW_TEXT_X, right_inset=MENU_ROW_TRAILING_PAD):
        x1, y1, x2, y2 = self.detail_container_bounds(width, card_height, left_inset=left_inset, right_inset=right_inset)
        draw_bordered_rounded_rect(card, x1, y1, x2, y2, DETAIL_PANEL_RADIUS, MENU_DETAIL_BG, MENU_DETAIL_BORDER)
        return x1, y1, x2, y2

    def slider_panel_geometry(self, key, width, card_height):
        x1, y1, x2, y2 = self.detail_container_bounds(width, card_height)
        inner_left = x1 + DETAIL_PANEL_SIDE_PAD
        inner_right = x2 - DETAIL_PANEL_SIDE_PAD
        icon_padding = 34 if key == BRIGHTNESS_ITEM_KEY else 0
        slider_right = inner_right - icon_padding
        title_y = y1 + 18
        note_y = title_y + 18
        slider_y = note_y + 24
        return {
            "key": key,
            "panel_x1": x1,
            "panel_y1": y1,
            "panel_x2": x2,
            "panel_y2": y2,
            "inner_left": inner_left,
            "inner_right": inner_right,
            "slider_left": inner_left,
            "slider_right": slider_right,
            "title_y": title_y,
            "note_y": note_y,
            "slider_y": slider_y,
        }

    def draw_prompt_hint(self, card, x_pos, y_pos, icon_filename, text, fill, font, anchor="w"):
        label = str(text or "").strip()
        icon_image = load_prompt_icon(icon_filename) if icon_filename else None
        icon_width = icon_image.width() if icon_image is not None else 0
        gap = PROMPT_HINT_GAP if icon_width and label else 0
        total_width = icon_width + gap + (measure_text_width(font, label) if label else 0)
        if anchor == "e":
            left = x_pos - total_width
        elif anchor in {"c", "center"}:
            left = x_pos - (total_width / 2.0)
        else:
            left = x_pos

        if icon_image is not None:
            card.images.append(icon_image)
            card.create_image(left, y_pos, image=icon_image, anchor="w")

        if label:
            text_x = left + icon_width + gap
            card.create_text(text_x, y_pos, text=label, fill=fill, font=font, anchor="w")

    def draw_slider_panel(self, card, key, width, card_height):
        geometry = self.slider_panel_geometry(key, width, card_height)
        x1 = geometry["panel_x1"]
        y1 = geometry["panel_y1"]
        x2 = geometry["panel_x2"]
        inner_left = geometry["inner_left"]
        inner_right = geometry["inner_right"]
        slider_right = geometry["slider_right"]
        title_y = geometry["title_y"]
        note_y = geometry["note_y"]
        slider_y = geometry["slider_y"]
        draw_bordered_rounded_rect(card, x1, y1, x2, geometry["panel_y2"], DETAIL_PANEL_RADIUS, MENU_DETAIL_BG, MENU_DETAIL_BORDER)

        if key == VOLUME_ITEM_KEY:
            title = "Live system volume"
            value_text = f"{self.volume_value}%"
            adjust_hint = "to adjust volume"
            slider_value = self.volume_value
        else:
            title = "Display brightness"
            value_text = f"{self.brightness_value}%"
            adjust_hint = "to adjust brightness"
            slider_value = self.brightness_value

        card.create_text(inner_left, title_y, text=title, fill=MENU_DETAIL_TEXT, font=SLIDER_LABEL_FONT, anchor="w")
        card.create_text(inner_right, title_y, text=value_text, fill=MENU_DETAIL_TEXT, font=SLIDER_LABEL_FONT, anchor="e")

        self.draw_prompt_hint(card, inner_left, note_y, "dpad.png", adjust_hint, MENU_DETAIL_SUBTEXT, SLIDER_LABEL_FONT)
        self.draw_slider(card, inner_left, slider_right, slider_y, slider_value)

        if key == BRIGHTNESS_ITEM_KEY:
            preview_icon = load_status_icon("hud/brightness.png", grayscale_color(self.brightness_value), 28)
            if preview_icon is not None:
                card.images.append(preview_icon)
                card.create_image(inner_right - 8, slider_y - 10, image=preview_icon)

    def draw_list_panel(self, card, key, width, card_height):
        x1, y1, x2, y2 = self.draw_detail_container(
            card,
            width,
            card_height,
            left_inset=DETAIL_LIST_PANEL_OUTER_PAD_X,
            right_inset=DETAIL_LIST_PANEL_OUTER_PAD_X,
        )
        inner_left = x1 + DETAIL_LIST_PANEL_SIDE_PAD
        inner_right = x2 - DETAIL_LIST_PANEL_SIDE_PAD
        header_left = inner_left + DETAIL_LIST_PANEL_ITEM_INSET_X
        header_right = inner_right - DETAIL_LIST_PANEL_ITEM_INSET_X
        title = "Nearby WiFi" if key == WIFI_ITEM_KEY else "Bluetooth Devices"
        entries = self.wifi_detail_entries() if key == WIFI_ITEM_KEY else self.bluetooth_detail_entries()

        title_y = y1 + DETAIL_LIST_PANEL_TITLE_OFFSET_Y
        card.create_text(header_left, title_y, text=title, fill=MENU_DETAIL_TEXT, font=SLIDER_LABEL_FONT, anchor="w")
        if key == WIFI_ITEM_KEY:
            header_text = self.wifi_detail_header_text()
            if self.wifi_action_in_progress:
                card.create_text(
                    header_right,
                    title_y,
                    text=header_text,
                    fill=MENU_DETAIL_SUBTEXT,
                    font=SLIDER_LABEL_FONT,
                    anchor="e",
                )
            else:
                self.draw_prompt_hint(
                    card,
                    header_right,
                    title_y,
                    "a.png",
                    header_text,
                    MENU_DETAIL_SUBTEXT,
                    SLIDER_LABEL_FONT,
                    anchor="e",
                )
        else:
            header_text = self.bluetooth_detail_header_text()
            if self.bluetooth_action_in_progress:
                card.create_text(
                    header_right,
                    title_y,
                    text=header_text,
                    fill=MENU_DETAIL_SUBTEXT,
                    font=SLIDER_LABEL_FONT,
                    anchor="e",
                )
            else:
                self.draw_prompt_hint(
                    card,
                    header_right,
                    title_y,
                    "a.png",
                    header_text,
                    MENU_DETAIL_SUBTEXT,
                    SLIDER_LABEL_FONT,
                    anchor="e",
                )

        row_top = title_y + DETAIL_LIST_PANEL_ROWS_TOP_GAP
        for index, entry in enumerate(entries):
            entry_y1 = row_top + index * (DETAIL_LIST_PANEL_ROW_HEIGHT + DETAIL_LIST_PANEL_ROW_GAP)
            entry_y2 = entry_y1 + DETAIL_LIST_PANEL_ROW_HEIGHT
            entry_x1 = inner_left + DETAIL_LIST_PANEL_ITEM_INSET_X
            entry_x2 = inner_right - DETAIL_LIST_PANEL_ITEM_INSET_X
            selected = key in LIST_ITEM_KEYS and self.detail_selection_key == key and index == self.detail_selection_index
            entry_fill = MENU_DETAIL_ACTIVE if entry.get("accent") else MENU_BG
            entry_border = MENU_HOT_PINK if selected else MENU_DETAIL_BORDER
            if selected:
                entry_fill = MENU_CONFIRM_BG
            draw_bordered_rounded_rect(
                card,
                entry_x1,
                entry_y1,
                entry_x2,
                entry_y2,
                DETAIL_PANEL_ITEM_RADIUS,
                entry_fill,
                entry_border,
            )
            card.create_text(
                entry_x1 + DETAIL_LIST_PANEL_ITEM_TEXT_PAD_X,
                entry_y1 + DETAIL_LIST_PANEL_ITEM_TITLE_OFFSET_Y,
                text=entry["title"],
                fill=MENU_FOCUS_TEXT if selected else MENU_DETAIL_TEXT,
                font=SLIDER_LABEL_FONT,
                anchor="w",
            )
            card.create_text(
                entry_x1 + DETAIL_LIST_PANEL_ITEM_TEXT_PAD_X,
                entry_y1 + DETAIL_LIST_PANEL_ITEM_META_OFFSET_Y,
                text=entry["meta"],
                fill=MENU_FOCUS_TEXT if selected else MENU_DETAIL_SUBTEXT,
                font=(FONT_FAMILY, 9, "bold"),
                anchor="w",
            )
    def draw_confirm_panel(self, card, key, width, card_height):
        x1, y1, x2, y2 = self.draw_detail_container(
            card,
            width,
            card_height,
            left_inset=DETAIL_CONFIRM_PANEL_OUTER_PAD_X,
            right_inset=DETAIL_CONFIRM_PANEL_OUTER_PAD_X,
        )
        inner_left = x1 + DETAIL_CONFIRM_PANEL_SIDE_PAD
        inner_right = x2 - DETAIL_CONFIRM_PANEL_SIDE_PAD
        content_left = inner_left + DETAIL_CONFIRM_PANEL_ITEM_INSET_X
        content_right = inner_right - DETAIL_CONFIRM_PANEL_ITEM_INSET_X

        if key == UPDATE_ITEM_KEY:
            current_label = software_version_label(self.software_version)
            remote_label = software_version_label(self.software_remote_version) if self.software_remote_version else None
            action_text = "Install available update?" if not self.software_update_in_progress else "Installing update from GitHub..."
            note_text = (
                f"{current_label} -> {remote_label}"
                if remote_label and remote_label != current_label
                else f"Current version {current_label}"
            )
            prompt_icon = None if self.software_update_in_progress else "a.png"
            prompt_text = "Please wait while installing" if self.software_update_in_progress else "to update and restart"
            button_text = "Installing..." if self.software_update_in_progress else "Install update?"
            button_fill = MENU_ROW_BG
            button_border = MENU_HOT_PINK
        else:
            action_text = "Restart the kiosk now?" if key == RESTART_ITEM_KEY else "Shut the console down now?"
            note_text = "to confirm"
            prompt_icon = "a.png"
            prompt_text = note_text
            button_text = "Confirm?"
            button_fill = MENU_CONFIRM_BG
            button_border = MENU_CONFIRM_BORDER

        title_y = y1 + DETAIL_CONFIRM_PANEL_TITLE_OFFSET_Y
        card.create_text(content_left, title_y, text=action_text, fill=MENU_DETAIL_TEXT, font=SLIDER_LABEL_FONT, anchor="w")
        if prompt_icon is None:
            card.create_text(
                content_left,
                title_y + DETAIL_CONFIRM_PANEL_NOTE_OFFSET_Y,
                text=prompt_text,
                fill=MENU_DETAIL_SUBTEXT,
                font=SLIDER_LABEL_FONT,
                anchor="w",
            )
        else:
            self.draw_prompt_hint(
                card,
                content_left,
                title_y + DETAIL_CONFIRM_PANEL_NOTE_OFFSET_Y,
                prompt_icon,
                prompt_text,
                MENU_DETAIL_SUBTEXT,
                SLIDER_LABEL_FONT,
            )
        if key == UPDATE_ITEM_KEY:
            card.create_text(
                content_right,
                title_y + DETAIL_CONFIRM_PANEL_NOTE_OFFSET_Y,
                text=note_text,
                fill=MENU_DETAIL_SUBTEXT,
                font=SLIDER_LABEL_FONT,
                anchor="e",
            )

        button_x1 = content_left
        button_x2 = content_right
        button_y1 = title_y + DETAIL_CONFIRM_PANEL_NOTE_OFFSET_Y + DETAIL_CONFIRM_PANEL_BUTTON_TOP_GAP
        button_y2 = button_y1 + DETAIL_CONFIRM_PANEL_BUTTON_HEIGHT
        draw_bordered_rounded_rect(
            card,
            button_x1,
            button_y1,
            button_x2,
            button_y2,
            MENU_CONFIRM_RADIUS,
            button_fill,
            button_border,
        )
        card.create_text(
            (button_x1 + button_x2) / 2,
            (button_y1 + button_y2) / 2,
            text=button_text,
            fill=MENU_FOCUS_TEXT,
            font=MENU_ITEM_FONT,
            anchor="c",
        )

    def render_detail_panel(self, card, key, width, card_height):
        if key in ADJUSTABLE_ITEM_KEYS:
            self.draw_slider_panel(card, key, width, card_height)
            return
        if key in LIST_ITEM_KEYS:
            self.draw_list_panel(card, key, width, card_height)
            return
        if key in CONFIRM_ITEM_KEYS:
            self.draw_confirm_panel(card, key, width, card_height)

    def render(self):
        if self.render_job is not None:
            try:
                self.window.after_cancel(self.render_job)
            except tk.TclError:
                pass
            self.render_job = None
        self.clamp_detail_selection()
        for index, row in enumerate(self.rows):
            item = row["item"]
            key = item["key"]
            focused = index == self.selected_index
            expanded = key == self.expanded_key
            destructive = key in DESTRUCTIVE_ITEM_KEYS
            card = row["card"]
            card_height = MENU_ROW_HEIGHT + (self.detail_panel_height(key) if expanded else 0)
            card.config(height=card_height, bg=MENU_BG)
            card.delete("all")
            card.images = []

            width = max(1, card.winfo_width())
            if width <= 1:
                width = max(1, self.list_canvas.winfo_width() - (MENU_LIST_PAD_X * 2))
            if width <= 1:
                width = SCREEN_W - (MENU_LIST_PAD_X * 2)

            text_color = MENU_FOCUS_TEXT if focused else (MENU_DESTRUCTIVE if destructive else TEXT)
            trailing_color = MENU_FOCUS_TEXT if focused else MENU_VALUE
            center_y = MENU_ROW_HEIGHT // 2
            trailing_text = self.describe_item(key)
            icon_image = self.load_menu_icon(key, focused)

            draw_bordered_rounded_rect(card, 0, 0, width - 1, card_height - 1, MENU_ROW_RADIUS, MENU_ROW_BG, MENU_ROW_BORDER)
            if focused:
                highlight_left = MENU_FOCUS_INSET
                highlight_top = MENU_FOCUS_INSET
                highlight_right = max(highlight_left + 1, width - 1 - MENU_FOCUS_INSET)
                highlight_bottom = min(card_height - 1 - MENU_FOCUS_INSET, MENU_ROW_HEIGHT - MENU_FOCUS_INSET)
                draw_gradient_rounded_rect(
                    card,
                    highlight_left,
                    highlight_top,
                    highlight_right,
                    highlight_bottom,
                    MENU_FOCUS_RADIUS,
                    MENU_CTA_START,
                    MENU_CTA_END,
                )

            if icon_image is not None:
                card.images.append(icon_image)
                card.create_image(MENU_ROW_ICON_X, center_y, image=icon_image)

            card.create_text(
                MENU_ROW_TEXT_X,
                center_y,
                text=item["label"],
                fill=text_color,
                font=MENU_ITEM_FONT,
                anchor="w",
            )

            if trailing_text:
                card.create_text(
                    width - MENU_ROW_TRAILING_PAD,
                    center_y,
                    text=trailing_text,
                    fill=trailing_color,
                    font=MENU_VALUE_FONT,
                    anchor="e",
                )

            if expanded:
                self.render_detail_panel(card, key, width, card_height)

        self.handle_list_frame_configure()
        self.ensure_selected_visible()


class ToastPopup:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.withdraw()
        self.window.overrideredirect(True)
        self.window.configure(bg=TOAST_BORDER)
        try:
            self.window.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

        frame = tk.Frame(
            self.window,
            bg=TOAST_BG,
            bd=0,
            highlightthickness=0,
            padx=TOAST_PAD_X,
            pady=TOAST_PAD_Y,
        )
        frame.pack(padx=1, pady=1)
        self.label = tk.Label(frame, text="", bg=TOAST_BG, fg=TOAST_TEXT, font=TOAST_FONT)
        self.label.pack()
        self.hide_job = None

    def show(self, text, duration_ms=CONNECTION_TOAST_DURATION_MS):
        if self.hide_job is not None:
            try:
                self.window.after_cancel(self.hide_job)
            except tk.TclError:
                pass
            self.hide_job = None
        self.label.config(text=text)
        self.window.update_idletasks()
        width = max(1, self.window.winfo_reqwidth())
        height = max(1, self.window.winfo_reqheight())
        x_pos = max(0, (SCREEN_W - width) // 2)
        y_pos = max(STATUS_BAR_H, SCREEN_H - BOTTOM_BAR_H - height - TOAST_OFFSET_Y)
        self.window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        self.window.deiconify()
        self.window.lift()
        if duration_ms:
            self.hide_job = self.window.after(duration_ms, self.hide)

    def hide(self):
        self.hide_job = None
        self.window.withdraw()


class StatusDock:
    def __init__(self, parent):
        self.window = create_dock_window(parent, STATUS_BAR_H, 0, STATUS_BG)
        container = tk.Frame(self.window, bg=STATUS_BG)
        container.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(container, bg=STATUS_BG)
        left_frame.pack(side=tk.LEFT, padx=10)

        self.clock_icon = ClockIcon(left_frame)
        self.clock_icon.pack(side=tk.LEFT, padx=(0, 4))

        self.clock_label = tk.Label(left_frame, text="", bg=STATUS_BG, fg=TEXT, font=CLOCK_FONT)
        self.clock_label.pack(side=tk.LEFT)

        right_frame = tk.Frame(container, bg=STATUS_BG)
        right_frame.pack(side=tk.RIGHT, padx=10)

        self.wifi_icon = WifiIcon(right_frame)
        self.wifi_icon.pack(side=tk.LEFT)

        self.bluetooth_icon = BluetoothIcon(right_frame)
        self.bluetooth_icon.pack(side=tk.LEFT, padx=(10, 0))

        self.volume_icon = VolumeIcon(right_frame)
        self.volume_icon.pack(side=tk.LEFT, padx=(10, 0))

        self.battery_chip = BatteryChip(right_frame)
        self.battery_chip.pack(side=tk.LEFT, padx=(10, 0))

    def update(self, snapshot):
        self.clock_icon.update()
        self.wifi_icon.update(snapshot.get("wifi_signal", 0), snapshot.get("wifi_state", "offline"))
        self.bluetooth_icon.update(
            snapshot.get("bluetooth_enabled", False),
            bool(snapshot.get("bluetooth_connected_devices", [])),
        )
        self.volume_icon.update(snapshot.get("volume_level"), snapshot.get("volume_muted", False))
        self.clock_label.config(text=current_time())
        self.battery_chip.update(snapshot.get("battery_percent"), snapshot.get("battery_charging"))


class BottomNavDock:
    def __init__(self, parent, on_settings):
        self.window = create_dock_window(parent, BOTTOM_BAR_H, SCREEN_H - BOTTOM_BAR_H, NAV_BG)
        container = tk.Frame(self.window, bg=NAV_BG)
        container.pack(fill=tk.BOTH, expand=True)

        self.select_icon = load_prompt_icon("a.png")
        self.navigate_icon = load_prompt_icon("dpad.png")
        self.bookmark_icon = load_prompt_icon("x.png")
        self.search_icon = load_prompt_icon("y.png")
        self.settings_icon = load_prompt_icon("start.png")

        left_frame = tk.Frame(container, bg=NAV_BG)
        left_frame.pack(side=tk.LEFT, padx=14)
        NavHint(
            left_frame,
            "Select",
            icon_image=self.select_icon,
            draw_icon=draw_a_button_icon,
        ).pack(side=tk.LEFT)
        NavHint(left_frame, "Navigate", icon_image=self.navigate_icon, draw_icon=draw_gamepad_icon).pack(
            side=tk.LEFT,
            padx=(14, 0),
        )
        NavHint(
            left_frame,
            "Bookmark",
            icon_image=self.bookmark_icon,
        ).pack(side=tk.LEFT, padx=(14, 0))
        NavHint(
            left_frame,
            "Search",
            icon_image=self.search_icon,
        ).pack(side=tk.LEFT, padx=(14, 0))

        right_frame = tk.Frame(container, bg=NAV_BG)
        right_frame.pack(side=tk.RIGHT, padx=14)
        self.quick_menu_hint = NavHint(
            right_frame,
            "Settings",
            icon_image=self.settings_icon,
            draw_icon=draw_menu_button_icon,
            callback=on_settings,
        )
        self.quick_menu_hint.pack(side=tk.LEFT)

    def set_quick_menu_active(self, active):
        if active:
            self.quick_menu_hint.set_label("Back")
            self.quick_menu_hint.label.config(fg=MENU_HOT_PINK)
            return
        self.quick_menu_hint.set_label("Settings")
        self.quick_menu_hint.label.config(fg=NAV_TEXT)


class Hud:
    def __init__(self, root):
        self.root = root
        root.withdraw()
        configure_default_fonts(root)
        set_quick_menu_active(False)
        self.sound_player = UiSoundPlayer()
        self.status_poller = StatusPoller()
        initial_snapshot = build_status_snapshot()
        self.status_poller.set_snapshot(initial_snapshot, request_refresh=False)
        self.last_status_snapshot = dict(initial_snapshot)
        self.connection_toast = ToastPopup(root)
        self.status_dock = StatusDock(root)
        self.quick_menu = QuickMenuOverlay(
            root,
            snapshot_getter=self.status_poller.get_snapshot,
            on_visibility_change=self.handle_quick_menu_visibility,
            on_snapshot_change=self.handle_status_snapshot_change,
            on_bluetooth_connected=self.handle_bluetooth_connected,
            on_wifi_connected=self.handle_wifi_connected,
            sound_player=self.sound_player,
        )
        self.dpad_hold_lock = threading.Lock()
        self.dpad_vertical_hold = 0
        self.dpad_horizontal_hold = 0
        self.dpad_vertical_next_repeat_at = 0.0
        self.dpad_horizontal_next_repeat_at = 0.0
        self.bottom_dock = BottomNavDock(root, self.handle_quick_menu_button)
        self.bottom_dock.set_quick_menu_active(False)
        self.quick_menu.register_cursor_windows(
            self.status_dock.window,
            self.bottom_dock.window,
            self.connection_toast.window,
        )
        self.status_dock.update(self.last_status_snapshot)
        threading.Thread(target=self.dpad_hold_loop, daemon=True).start()
        threading.Thread(target=self.gamepad_loop, daemon=True).start()
        self.refresh()

    def safe_after(self, delay, callback):
        try:
            self.root.after(delay, callback)
        except tk.TclError:
            pass

    def handle_quick_menu_visibility(self, active):
        self.bottom_dock.set_quick_menu_active(active)
        if not active:
            self.clear_dpad_holds()

    def handle_quick_menu_button(self):
        self.quick_menu.toggle()

    def handle_status_snapshot_change(self, snapshot):
        if not snapshot:
            return
        self.apply_status_snapshot(snapshot, update_poller=True)

    def connected_wifi_name(self, snapshot):
        if snapshot.get("wifi_state") != "connected":
            return ""
        return str(snapshot.get("wifi_name") or "").strip()

    def connected_bluetooth_devices(self, snapshot):
        devices = {}
        for device in snapshot.get("bluetooth_connected_devices", []) or []:
            if not isinstance(device, dict):
                continue
            address = str(device.get("address") or "").strip()
            if not address:
                continue
            devices[address] = str(device.get("name") or "").strip()
        return devices

    def low_battery_percent(self, snapshot):
        percent = normalize_battery_percent(snapshot.get("battery_percent"))
        if percent is None or snapshot.get("battery_charging"):
            return None
        if percent > BATTERY_LOW_PERCENT:
            return None
        return percent

    def show_notification_toast(self, text, duration_ms=CONNECTION_TOAST_DURATION_MS):
        self.connection_toast.show(text, duration_ms=duration_ms)

    def show_connection_toast(self, name, fallback_label):
        label = str(name or "").strip() or fallback_label
        if len(label) > CONNECTION_TOAST_LABEL_MAX:
            label = f"{label[:CONNECTION_TOAST_LABEL_MAX - 3]}..."
        self.show_notification_toast(f"{label} Connected")

    def show_battery_low_toast(self, percent):
        self.show_notification_toast(f"Battery Low ({percent}%)", duration_ms=BATTERY_LOW_TOAST_DURATION_MS)

    def maybe_notify_status_transitions(self, previous_snapshot, snapshot):
        previous_wifi_connected = previous_snapshot.get("wifi_state") == "connected"
        current_wifi_connected = snapshot.get("wifi_state") == "connected"
        previous_wifi_name = self.connected_wifi_name(previous_snapshot)
        current_wifi_name = self.connected_wifi_name(snapshot)
        if current_wifi_connected and (not previous_wifi_connected or current_wifi_name != previous_wifi_name):
            if self.sound_player is not None:
                self.sound_player.play_confirm()
            self.show_connection_toast(current_wifi_name, "WiFi")

        previous_bluetooth = self.connected_bluetooth_devices(previous_snapshot)
        current_bluetooth = self.connected_bluetooth_devices(snapshot)
        new_addresses = [address for address in current_bluetooth if address not in previous_bluetooth]
        if new_addresses:
            address = new_addresses[0]
            device_name = current_bluetooth.get(address, "")
            if bluetooth_name_is_placeholder(device_name, address):
                device_name = "Bluetooth"
            if self.sound_player is not None:
                self.sound_player.play_confirm()
            self.show_connection_toast(device_name, "Bluetooth")

        previous_battery_low = self.low_battery_percent(previous_snapshot)
        current_battery_low = self.low_battery_percent(snapshot)
        if current_battery_low is not None and previous_battery_low is None:
            self.show_battery_low_toast(current_battery_low)

    def apply_status_snapshot(self, snapshot, update_poller=False):
        if not snapshot:
            return
        resolved_snapshot = dict(snapshot)
        previous_snapshot = dict(self.last_status_snapshot)
        self.last_status_snapshot = resolved_snapshot
        if update_poller:
            self.status_poller.set_snapshot(resolved_snapshot, request_refresh=False)
        self.status_dock.update(resolved_snapshot)
        self.quick_menu.refresh_dynamic(resolved_snapshot)
        self.maybe_notify_status_transitions(previous_snapshot, resolved_snapshot)

    def handle_wifi_connected(self, _name):
        return

    def handle_bluetooth_connected(self, _address, _name):
        return

    def handle_dpad(self, delta):
        self.quick_menu.move_selection(delta)

    def handle_dpad_horizontal(self, delta):
        self.quick_menu.move_horizontal(delta)

    def handle_confirm(self):
        self.quick_menu.on_a()

    def handle_back(self):
        self.quick_menu.on_b()

    def set_dpad_hold(self, axis, delta):
        next_repeat_at = time.monotonic() + DPAD_HOLD_INITIAL_DELAY_SEC if delta else 0.0
        with self.dpad_hold_lock:
            if axis == "vertical":
                self.dpad_vertical_hold = delta
                self.dpad_vertical_next_repeat_at = next_repeat_at
                return
            self.dpad_horizontal_hold = delta
            self.dpad_horizontal_next_repeat_at = next_repeat_at

    def clear_dpad_holds(self):
        with self.dpad_hold_lock:
            self.dpad_vertical_hold = 0
            self.dpad_horizontal_hold = 0
            self.dpad_vertical_next_repeat_at = 0.0
            self.dpad_horizontal_next_repeat_at = 0.0

    def dpad_hold_loop(self):
        while True:
            time.sleep(DPAD_HOLD_POLL_SEC)
            if not self.quick_menu.is_active():
                continue
            if self.quick_menu.adjusting_key not in HOLDABLE_ADJUST_ITEM_KEYS:
                continue

            now = time.monotonic()
            vertical_delta = 0
            horizontal_delta = 0
            with self.dpad_hold_lock:
                if self.dpad_vertical_hold and now >= self.dpad_vertical_next_repeat_at:
                    vertical_delta = self.dpad_vertical_hold
                    self.dpad_vertical_next_repeat_at = now + DPAD_HOLD_REPEAT_SEC
                if self.dpad_horizontal_hold and now >= self.dpad_horizontal_next_repeat_at:
                    horizontal_delta = self.dpad_horizontal_hold
                    self.dpad_horizontal_next_repeat_at = now + DPAD_HOLD_REPEAT_SEC

            if vertical_delta:
                self.safe_after(0, lambda delta=vertical_delta: self.handle_dpad(delta))
            if horizontal_delta:
                self.safe_after(0, lambda delta=horizontal_delta: self.handle_dpad_horizontal(delta))

    def refresh(self):
        snapshot = self.status_poller.get_snapshot()
        self.apply_status_snapshot(snapshot)
        self.root.after(1000, self.refresh)

    def gamepad_loop(self):
        while True:
            dev = find_gamepad()
            if not dev:
                time.sleep(5)
                continue
            try:
                for event in dev.read_loop():
                    if event.type == evdev.ecodes.EV_ABS:
                        if event.code == evdev.ecodes.ABS_HAT0Y:
                            if event.value == -1:
                                self.set_dpad_hold("vertical", -1)
                                self.safe_after(0, lambda delta=-1: self.handle_dpad(delta))
                            elif event.value == 1:
                                self.set_dpad_hold("vertical", 1)
                                self.safe_after(0, lambda delta=1: self.handle_dpad(delta))
                            elif event.value == 0:
                                self.set_dpad_hold("vertical", 0)
                        elif event.code == evdev.ecodes.ABS_HAT0X:
                            if event.value == -1:
                                self.set_dpad_hold("horizontal", -1)
                                self.safe_after(0, lambda delta=-1: self.handle_dpad_horizontal(delta))
                            elif event.value == 1:
                                self.set_dpad_hold("horizontal", 1)
                                self.safe_after(0, lambda delta=1: self.handle_dpad_horizontal(delta))
                            elif event.value == 0:
                                self.set_dpad_hold("horizontal", 0)
                    elif event.type == evdev.ecodes.EV_KEY and event.value == 1:
                        if event.code in {evdev.ecodes.BTN_MODE, evdev.ecodes.BTN_START}:
                            self.safe_after(0, self.handle_quick_menu_button)
                        elif event.code == evdev.ecodes.BTN_SOUTH:
                            self.safe_after(0, self.handle_confirm)
                        elif event.code == evdev.ecodes.BTN_EAST:
                            self.safe_after(0, self.handle_back)
            except OSError:
                self.clear_dpad_holds()
                time.sleep(2)


if __name__ == "__main__":
    app = tk.Tk()
    Hud(app)
    app.mainloop()
