#!/usr/bin/env python3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
RELEASE_ROOT = REPO_ROOT.parent
WORKSPACE_ROOT = RELEASE_ROOT.parent if RELEASE_ROOT.name == "release" else RELEASE_ROOT
VERSION_PATH = WORKSPACE_ROOT / "version.txt"
CONFIG_PATH = REPO_ROOT / "console.env"
TOUCH_TOKENS = ("touch", "touchscreen", "touchpad", "ft5x06", "edt-ft")
ONBOARD_KEY_SYNTH = "XTest"
ONBOARD_FORCE_TO_TOP = True
ONBOARD_USE_SYSTEM_DEFAULTS = False
ONBOARD_SHOW_STATUS_ICON = False
ONBOARD_ICON_PALETTE_IN_USE = False
ONBOARD_WINDOW_HANDLES = ""
ONBOARD_ICON_PALETTE_WINDOW_HANDLES = ""
DEFAULT_STATUS_BAR_HEIGHT = 24
DEFAULT_BOTTOM_BAR_HEIGHT = 24
QUICK_MENU_ACTIVE_PATH = Path("/tmp/gamehub-quick-menu-active")
HUD_TEXT_INPUT_ACTIVE_PATH = Path("/tmp/gamehub-hud-text-input-active")


def load_config():
    config = {
        "GAMEHUB_URL": "https://handheld.knfstudios.com/?mode=handheld",
        "SCREEN_WIDTH": "800",
        "SCREEN_HEIGHT": "480",
        "HUD_HEIGHT": str(DEFAULT_STATUS_BAR_HEIGHT + DEFAULT_BOTTOM_BAR_HEIGHT),
        "STATUS_BAR_HEIGHT": str(DEFAULT_STATUS_BAR_HEIGHT),
        "BOTTOM_BAR_HEIGHT": str(DEFAULT_BOTTOM_BAR_HEIGHT),
        "REMOTE_DEBUG_PORT": "9222",
        "BATTERY_COMMAND": "",
    }

    if CONFIG_PATH.exists():
        for raw_line in CONFIG_PATH.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip('"').strip("'")

    return config


def read_workspace_version(default="Unknown"):
    try:
        version = VERSION_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return default
    return version or default


def touchscreen_present():
    try:
        import evdev

        for path in evdev.list_devices():
            try:
                name = evdev.InputDevice(path).name.lower()
            except OSError:
                continue
            if any(token in name for token in TOUCH_TOKENS):
                return True
    except Exception:
        pass

    try:
        devices_text = Path("/proc/bus/input/devices").read_text(encoding="utf-8", errors="ignore").lower()
    except OSError:
        return False
    return any(token in devices_text for token in TOUCH_TOKENS)


def config_int(config, key, default):
    try:
        return int(str(config.get(key, default)).strip())
    except (TypeError, ValueError, AttributeError):
        return default


def hud_bar_heights(config):
    screen_h = max(1, config_int(config, "SCREEN_HEIGHT", 480))
    status_h = max(0, config_int(config, "STATUS_BAR_HEIGHT", DEFAULT_STATUS_BAR_HEIGHT))
    bottom_h = max(0, config_int(config, "BOTTOM_BAR_HEIGHT", DEFAULT_BOTTOM_BAR_HEIGHT))
    if status_h + bottom_h > screen_h:
        bottom_h = max(0, screen_h - status_h)
    return status_h, bottom_h


def ensure_onboard_xtest():
    try:
        from gi.repository import Gio
    except Exception:
        return False

    try:
        root_settings = Gio.Settings.new("org.onboard")
        keyboard_settings = Gio.Settings.new("org.onboard.keyboard")
        window_settings = Gio.Settings.new("org.onboard.window")
        icon_palette_settings = Gio.Settings.new("org.onboard.icon-palette")

        if root_settings.get_boolean("use-system-defaults") != ONBOARD_USE_SYSTEM_DEFAULTS:
            root_settings.set_boolean("use-system-defaults", ONBOARD_USE_SYSTEM_DEFAULTS)
        if keyboard_settings.get_string("key-synth") != ONBOARD_KEY_SYNTH:
            keyboard_settings.set_string("key-synth", ONBOARD_KEY_SYNTH)
        if window_settings.get_boolean("force-to-top") != ONBOARD_FORCE_TO_TOP:
            window_settings.set_boolean("force-to-top", ONBOARD_FORCE_TO_TOP)
        if root_settings.get_boolean("show-status-icon") != ONBOARD_SHOW_STATUS_ICON:
            root_settings.set_boolean("show-status-icon", ONBOARD_SHOW_STATUS_ICON)
        if icon_palette_settings.get_boolean("in-use") != ONBOARD_ICON_PALETTE_IN_USE:
            icon_palette_settings.set_boolean("in-use", ONBOARD_ICON_PALETTE_IN_USE)
        if window_settings.get_string("window-handles") != ONBOARD_WINDOW_HANDLES:
            window_settings.set_string("window-handles", ONBOARD_WINDOW_HANDLES)
        if icon_palette_settings.get_string("window-handles") != ONBOARD_ICON_PALETTE_WINDOW_HANDLES:
            icon_palette_settings.set_string("window-handles", ONBOARD_ICON_PALETTE_WINDOW_HANDLES)

        root_settings.apply()
        keyboard_settings.apply()
        window_settings.apply()
        icon_palette_settings.apply()
        return True
    except Exception:
        return False


def quick_menu_active():
    return QUICK_MENU_ACTIVE_PATH.exists()


def hud_text_input_active():
    return HUD_TEXT_INPUT_ACTIVE_PATH.exists()


def set_hud_text_input_active(active):
    try:
        if active:
            HUD_TEXT_INPUT_ACTIVE_PATH.write_text("1")
        elif HUD_TEXT_INPUT_ACTIVE_PATH.exists():
            HUD_TEXT_INPUT_ACTIVE_PATH.unlink()
    except OSError:
        pass


def set_quick_menu_active(active):
    try:
        if active:
            QUICK_MENU_ACTIVE_PATH.write_text("1")
        else:
            if QUICK_MENU_ACTIVE_PATH.exists():
                QUICK_MENU_ACTIVE_PATH.unlink()
            if HUD_TEXT_INPUT_ACTIVE_PATH.exists():
                HUD_TEXT_INPUT_ACTIVE_PATH.unlink()
    except OSError:
        pass
