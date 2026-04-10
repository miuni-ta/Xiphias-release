#!/usr/bin/env python3
from array import array
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET

import evdev
import websocket

from audio_output import detect_output_format, get_shared_audio_output
from common import (
    REPO_ROOT,
    TOUCH_TOKENS,
    ensure_onboard_xtest,
    hud_bar_heights,
    hud_text_input_active,
    load_config,
    quick_menu_active,
    touchscreen_present,
)


os.environ["DISPLAY"] = ":0"

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG = load_config()
CDP_URL = f"http://localhost:{CONFIG['REMOTE_DEBUG_PORT']}"
SCREEN_WIDTH = int(CONFIG["SCREEN_WIDTH"])
SCREEN_HEIGHT = int(CONFIG["SCREEN_HEIGHT"])
SCREEN_MIN_X = 0
SCREEN_MAX_X = max(0, SCREEN_WIDTH - 1)
SCREEN_MIN_Y = 0
SCREEN_MAX_Y = max(0, SCREEN_HEIGHT - 1)
STATUS_BAR_HEIGHT, BOTTOM_BAR_HEIGHT = hud_bar_heights(CONFIG)
CURSOR_MIN_X = SCREEN_MIN_X
CURSOR_MAX_X = SCREEN_MAX_X
CURSOR_MIN_Y = STATUS_BAR_HEIGHT
CURSOR_MAX_Y = max(CURSOR_MIN_Y, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT - 1)
STANDARD_TOUCH_CURSOR = touchscreen_present()
CURSOR_MIN_SPEED = 35.0
CURSOR_MAX_SPEED = 1400.0
CURSOR_RESPONSE_EXPONENT = 1.75
CURSOR_SMOOTHING = 14.0
CURSOR_RELEASE_SMOOTHING = 22.0
CURSOR_LOOP_DELAY = 0.01
CURSOR_POSITION_SYNC_INTERVAL = 0.35
DEADZONE = 0.16
HOLD_DURATION = 2.0
SCROLL_DELAY = 0.08
DEFAULT_AXIS_MAX = 32767.0
KB_POLL_INTERVAL = 0.03
VIEWPORT_FIX_POLL_INTERVAL = 1.0
KB_CHECK_DELAY = 0.02
TOUCH_CHECK_DELAY = 0.02
ONBOARD_THEME_DIR = os.path.expanduser("~/.local/share/onboard/themes")
ONBOARD_THEME_SOURCE = os.path.join(BASE_DIR, "gamepad_dark.theme")
ONBOARD_COLORS_SOURCE = os.path.join(BASE_DIR, "gamepad_dark.colors")
ONBOARD_THEME = os.path.join(ONBOARD_THEME_DIR, "gamepad_dark.theme")
ONBOARD_COLORS = os.path.join(ONBOARD_THEME_DIR, "gamepad_dark.colors")
ONBOARD_LAYOUT = os.path.join(BASE_DIR, "gamepad_keyboard.onboard")
ONBOARD_LAYOUT_SVG = os.path.join(BASE_DIR, "gamepad_keyboard.svg")
WRAPPER_URL_PREFIX = (REPO_ROOT / "kiosk-wrapper.html").resolve().as_uri()
KEYBOARD_WIDTH = SCREEN_WIDTH
KEYBOARD_HEIGHT = 180
KEYBOARD_X = 0
KEYBOARD_Y = max(0, SCREEN_HEIGHT - BOTTOM_BAR_HEIGHT - KEYBOARD_HEIGHT)
KEYBOARD_WINDOW_NAME = "^Onboard$"
ONBOARD_AUX_WINDOW_NAME = "onboard"
KEYBOARD_WINDOW_TITLE = "Onboard"
ONBOARD_AUX_WINDOW_TITLE = "onboard"
CHROMIUM_WINDOW_CLASS = "chromium"
KEYBOARD_WINDOW_RESTORE_DELAYS = (0.0, 0.03, 0.08, 0.16, 0.3, 0.6)
KEYBOARD_WINDOW_REFRESH_INTERVAL = 0.08
KEYBOARD_FOCUS_GRACE_PERIOD = 0.0
KEYBOARD_HIDDEN_Y = SCREEN_HEIGHT
KEYBOARD_ANIMATION_DURATION = 0.24
KEYBOARD_ANIMATION_STEP = 0.012
KEYBOARD_WINDOW_LOCK = threading.RLock()
KEYBOARD_TARGET_VISIBLE = False
KEYBOARD_VISIBILITY_GENERATION = 0
SOUND_SAMPLE_RATE = 22050
SOUND_MASTER_GAIN = 0.28
SOUND_ENVELOPE_FLOOR = 0.0008
KEYBOARD_TOUCH_SOUND_MIN_INTERVAL_SEC = 0.055
KEYBOARD_KEY_SOUND_MIN_INTERVAL_SEC = 0.05


class KeyboardSoundPlayer:
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

    def build_tone_run(self, frequencies, duration=0.04, gap=0.016, volume=0.22, waveform="triangle", sweep=18.0):
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

    def build_soft_click(self, frequency, end_frequency=None, duration=0.04, volume=0.18, waveform="sine"):
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

    def play_keyboard_open(self):
        return self.play_cached(
            "keyboard_open",
            lambda: self.build_tone_run(
                (520, 700),
                duration=0.04,
                gap=0.014,
                volume=0.24,
                waveform="triangle",
                sweep=28.0,
            ),
            "osk-open",
            family="keyboard-transition",
            replace_family=True,
        )

    def play_keyboard_close(self):
        return self.play_cached(
            "keyboard_close",
            lambda: self.build_tone_run(
                (700, 520),
                duration=0.04,
                gap=0.014,
                volume=0.24,
                waveform="triangle",
                sweep=-28.0,
            ),
            "osk-close",
            family="keyboard-transition",
            replace_family=True,
        )

    def play_keyboard_key_click(self):
        return self.play_cached(
            "keyboard_key_click",
            lambda: self.build_soft_click(
                610,
                end_frequency=560,
                duration=0.036,
                volume=0.17,
                waveform="sine",
            ),
            "osk-key-click",
            family="keyboard-keypress",
            min_interval=KEYBOARD_KEY_SOUND_MIN_INTERVAL_SEC,
            replace_family=True,
        )

    def play_keyboard_backspace(self):
        return self.play_cached(
            "keyboard_backspace",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 640,
                        "end_frequency": 410,
                        "duration": 0.07,
                        "waveform": "triangle",
                        "volume": 0.2,
                        "attack": 0.004,
                    }
                ]
            ),
            "osk-backspace",
            family="keyboard-keypress",
            min_interval=KEYBOARD_KEY_SOUND_MIN_INTERVAL_SEC,
            replace_family=True,
        )

    def play_keyboard_enter(self):
        return self.play_cached(
            "keyboard_enter",
            lambda: self.synthesize(
                [
                    {
                        "frequency": 520,
                        "end_frequency": 760,
                        "duration": 0.075,
                        "waveform": "triangle",
                        "volume": 0.21,
                        "attack": 0.005,
                    }
                ]
            ),
            "osk-enter",
            family="keyboard-keypress",
            min_interval=KEYBOARD_KEY_SOUND_MIN_INTERVAL_SEC,
            replace_family=True,
        )


KEYBOARD_SOUND_PLAYER = KeyboardSoundPlayer()

INPUT_FOCUS_JS = (
    "(function(){"
    "var el=document.activeElement;"
    "if(!el)return false;"
    "var tag=el.tagName.toUpperCase();"
    "var type=(el.type||'').toLowerCase();"
    "var skip=['button','submit','reset','checkbox','radio','file','image','range','color'];"
    "if(tag==='TEXTAREA')return true;"
    "if(tag==='INPUT'&&skip.indexOf(type)===-1)return true;"
    "if(el.isContentEditable)return true;"
    "return false;"
    "})()"
)
KEEP_INPUT_VISIBLE_JS = (
    "(function(){"
    "var el=document.activeElement;"
    "if(!el)return false;"
    "var tag=el.tagName.toUpperCase();"
    "var type=(el.type||'').toLowerCase();"
    "var skip=['button','submit','reset','checkbox','radio','file','image','range','color'];"
    "if(!(tag==='TEXTAREA'||(tag==='INPUT'&&skip.indexOf(type)===-1)||el.isContentEditable))return false;"
    "var margin=16;"
    f"var keyboardOverlap={KEYBOARD_HEIGHT};"
    "var safeBottom=Math.max(margin, window.innerHeight-keyboardOverlap-margin);"
    "var rect=el.getBoundingClientRect();"
    "var delta=0;"
    "if(rect.bottom>safeBottom)delta=rect.bottom-safeBottom;"
    "else if(rect.top<margin)delta=rect.top-margin;"
    "if(!delta)return true;"
    "var node=el.parentElement;"
    "while(node){"
    "var style=window.getComputedStyle(node);"
    "var overflowY=style.overflowY||style.overflow||'';"
    "if(node.scrollHeight>node.clientHeight+4&&/(auto|scroll)/.test(overflowY)){"
    "node.scrollBy({top:delta,behavior:'smooth'});"
    "rect=el.getBoundingClientRect();"
    "if(rect.bottom<=safeBottom&&rect.top>=margin)return true;"
    "}"
    "node=node.parentElement;"
    "}"
    "window.scrollBy({top:delta,behavior:'smooth'});"
    "rect=el.getBoundingClientRect();"
    "if(rect.bottom>safeBottom||rect.top<margin){"
    "el.scrollIntoView({behavior:'smooth',block:'center',inline:'nearest'});"
    "}"
    "return true;"
    "})()"
)
INSTALL_INPUT_BLUR_HOOK_JS = (
    "(function(){"
    "if(window.__gamehubBlurHookInstalled)return true;"
    "window.__gamehubBlurHookInstalled=true;"
    "function isEditable(el){"
    "if(!el||el.nodeType!==1)return false;"
    "var tag=(el.tagName||'').toUpperCase();"
    "var type=(el.type||'').toLowerCase();"
    "var skip=['button','submit','reset','checkbox','radio','file','image','range','color'];"
    "return tag==='TEXTAREA'||(tag==='INPUT'&&skip.indexOf(type)===-1)||!!el.isContentEditable;"
    "}"
    "function pathHasEditable(target){"
    "var path=typeof target.composedPath==='function'?target.composedPath():null;"
    "if(path&&path.length){"
    "for(var i=0;i<path.length;i++){"
    "if(isEditable(path[i]))return true;"
    "}"
    "return false;"
    "}"
    "var node=target;"
    "while(node){"
    "if(isEditable(node))return true;"
    "node=node.parentElement;"
    "}"
    "return false;"
    "}"
    "function blurIfOutside(event){"
    "var active=document.activeElement;"
    "if(!isEditable(active))return;"
    "if(pathHasEditable(event.target))return;"
    "active.blur();"
    "}"
    "['pointerdown','mousedown','touchstart'].forEach(function(type){"
    "document.addEventListener(type, blurIfOutside, true);"
    "});"
    "return true;"
    "})()"
)
INSTALL_ZOOM_LOCK_JS = (
    "(function(){"
    "var head=document.head||document.documentElement;"
    "var viewport=document.querySelector('meta[name=\"viewport\"]');"
    "if(!viewport){"
    "viewport=document.createElement('meta');"
    "viewport.name='viewport';"
    "head.appendChild(viewport);"
    "}"
    "viewport.setAttribute('content','width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover');"
    "var styleId='__gamehub_zoom_lock_style';"
    "var style=document.getElementById(styleId);"
    "if(!style){"
    "style=document.createElement('style');"
    "style.id=styleId;"
    "head.appendChild(style);"
    "}"
    "style.textContent='html,body,#root,.gbl-viewport{touch-action:pan-x pan-y!important;overscroll-behavior:none!important;}';"
    "if(window.__gamehubZoomLockInstalled)return true;"
    "window.__gamehubZoomLockInstalled=true;"
    "function blockGesture(event){event.preventDefault();event.stopPropagation();}"
    "function blockMultiTouch(event){if(event.touches&&event.touches.length>1){event.preventDefault();event.stopPropagation();}}"
    "function blockZoomWheel(event){if(event.ctrlKey){event.preventDefault();event.stopPropagation();}}"
    "function blockZoomShortcut(event){"
    "var key=(event.key||'').toLowerCase();"
    "if((event.ctrlKey||event.metaKey)&&(key==='+'||key==='='||key==='-'||key==='_'||key==='0')){"
    "event.preventDefault();"
    "event.stopPropagation();"
    "}"
    "}"
    "document.addEventListener('keydown',blockZoomShortcut,true);"
    "document.addEventListener('wheel',blockZoomWheel,{capture:true,passive:false});"
    "['gesturestart','gesturechange','gestureend'].forEach(function(type){"
    "document.addEventListener(type,blockGesture,{capture:true,passive:false});"
    "});"
    "['touchstart','touchmove'].forEach(function(type){"
    "document.addEventListener(type,blockMultiTouch,{capture:true,passive:false});"
    "});"
    "return true;"
    "})()"
)
INSTALL_SELECTION_LOCK_JS = (
    "(function(){"
    "var head=document.head||document.documentElement;"
    "if(!head)return false;"
    "var styleId='__gamehub_selection_lock_style';"
    "var style=document.getElementById(styleId);"
    "if(!style){"
    "style=document.createElement('style');"
    "style.id=styleId;"
    "head.appendChild(style);"
    "}"
    "style.textContent='html,body,body *{-webkit-user-select:none!important;user-select:none!important;-webkit-touch-callout:none!important;-webkit-tap-highlight-color:transparent!important;}input,textarea,[contenteditable=\"\"],[contenteditable=\"true\"],[contenteditable=\"plaintext-only\"],[contenteditable=\"\"] *,[contenteditable=\"true\"] *,[contenteditable=\"plaintext-only\"] *{-webkit-user-select:text!important;user-select:text!important;-webkit-touch-callout:default!important;}';"
    "function isEditable(node){"
    "var el=node&&node.nodeType===1?node:(node&&node.parentElement?node.parentElement:null);"
    "while(el){"
    "var tag=(el.tagName||'').toUpperCase();"
    "var type=(el.type||'').toLowerCase();"
    "var editableAttr=el.getAttribute?el.getAttribute('contenteditable'):null;"
    "if(tag==='TEXTAREA')return true;"
    "if(tag==='INPUT'&&type!=='button'&&type!=='submit'&&type!=='reset'&&type!=='checkbox'&&type!=='radio'&&type!=='file'&&type!=='image'&&type!=='range'&&type!=='color')return true;"
    "if(editableAttr!==null&&editableAttr.toLowerCase()!=='false')return true;"
    "el=el.parentElement;"
    "}"
    "return false;"
    "}"
    "function clearSelection(){"
    "var sel=window.getSelection?window.getSelection():null;"
    "if(sel&&sel.rangeCount&&!sel.isCollapsed){"
    "sel.removeAllRanges();"
    "}"
    "}"
    "function blockSelection(event){"
    "if(isEditable(event.target))return;"
    "event.preventDefault();"
    "clearSelection();"
    "}"
    "if(window.__gamehubSelectionLockInstalled){"
    "clearSelection();"
    "return true;"
    "}"
    "window.__gamehubSelectionLockInstalled=true;"
    "document.addEventListener('selectstart',blockSelection,true);"
    "document.addEventListener('dragstart',blockSelection,true);"
    "document.addEventListener('dblclick',blockSelection,true);"
    "document.addEventListener('mousedown',function(event){"
    "if(event.detail>1){"
    "blockSelection(event);"
    "}"
    "},true);"
    "document.addEventListener('selectionchange',function(){"
    "var sel=window.getSelection?window.getSelection():null;"
    "if(!sel||sel.isCollapsed)return;"
    "if(isEditable(sel.anchorNode)||isEditable(sel.focusNode))return;"
    "clearSelection();"
    "},true);"
    "return true;"
    "})()"
)
INSTALL_VIEWPORT_FIT_FIX_JS = (
    "(function(){"
    "var styleId='__gamehub_kiosk_viewport_fix';"
    "function applyFix(){"
    "var viewport=document.querySelector('.gbl-viewport');"
    "if(!viewport)return false;"
    "var baseWidth=viewport.offsetWidth||parseFloat(getComputedStyle(viewport).width)||window.innerWidth||1;"
    "var baseHeight=viewport.offsetHeight||parseFloat(getComputedStyle(viewport).height)||window.innerHeight||1;"
    "if(!(baseWidth>0&&baseHeight>0))return false;"
    "var scaleX=window.innerWidth/baseWidth;"
    "var scaleY=window.innerHeight/baseHeight;"
    "var style=document.getElementById(styleId);"
    "if(!style){"
    "style=document.createElement('style');"
    "style.id=styleId;"
    "document.head.appendChild(style);"
    "}"
    "style.textContent='html,body,#root{width:100%!important;height:100%!important;overflow:hidden!important;display:flex!important;align-items:center!important;justify-content:center!important;background:#0b0c10!important;}.gbl-viewport{margin:0 auto!important;transform-origin:center center!important;transform:scale('+scaleX+','+scaleY+')!important;}';"
    "return true;"
    "}"
    "if(!window.__gamehubKioskViewportFixInstalled){"
    "window.__gamehubKioskViewportFixInstalled=true;"
    "window.addEventListener('resize', applyFix, {passive:true});"
    "}"
    "return applyFix();"
    "})()"
)


def is_running(name):
    return subprocess.run(["pgrep", "-f", name], capture_output=True).returncode == 0


def kill_process(name):
    subprocess.run(["pkill", "-f", name], capture_output=True)


def run_command(args):
    return subprocess.run(args, capture_output=True, text=True)


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


def find_touchscreen():
    for path in evdev.list_devices():
        dev = evdev.InputDevice(path)
        name = dev.name.lower()
        if any(token in name for token in TOUCH_TOKENS):
            return dev
    return None


def clamp_screen_position(x_pos, y_pos):
    clamped_x = max(SCREEN_MIN_X, min(SCREEN_MAX_X, int(round(x_pos))))
    clamped_y = max(SCREEN_MIN_Y, min(SCREEN_MAX_Y, int(round(y_pos))))
    return clamped_x, clamped_y


def keyboard_cursor_bounds():
    min_x = max(SCREEN_MIN_X, KEYBOARD_X)
    max_x = max(min_x, min(SCREEN_MAX_X, KEYBOARD_X + KEYBOARD_WIDTH - 1))
    min_y = max(CURSOR_MIN_Y, KEYBOARD_Y)
    max_y = max(min_y, min(CURSOR_MAX_Y, KEYBOARD_Y + KEYBOARD_HEIGHT - 1))
    return min_x, max_x, min_y, max_y


def point_in_bounds(x_pos, y_pos, bounds):
    min_x, max_x, min_y, max_y = bounds
    return min_x <= x_pos <= max_x and min_y <= y_pos <= max_y


def keyboard_interaction_target(x_pos=None, y_pos=None):
    if not keyboard_is_open() or keyboard_suppressed():
        return False
    if x_pos is None or y_pos is None:
        position = get_cursor_position()
        if position is None:
            return False
        x_pos, y_pos = position
    return point_in_bounds(int(round(x_pos)), int(round(y_pos)), keyboard_cursor_bounds())


def load_keyboard_special_key_regions():
    cached = getattr(load_keyboard_special_key_regions, "_cache", None)
    if cached is not None:
        return cached
    resolved = ((0.0, 0.0, float(KEYBOARD_WIDTH), float(KEYBOARD_HEIGHT)), {})
    try:
        root = ET.parse(ONBOARD_LAYOUT_SVG).getroot()
        view_box = root.get("viewBox", "").strip().replace(",", " ").split()
        if len(view_box) == 4:
            view_x, view_y, view_width, view_height = (float(value) for value in view_box)
        else:
            view_x = 0.0
            view_y = 0.0
            view_width = float(root.get("width", KEYBOARD_WIDTH))
            view_height = float(root.get("height", KEYBOARD_HEIGHT))
        regions = {}
        for element in root.iter():
            key_id = (element.get("id") or "").strip()
            if key_id not in {"BKSP", "RTRN"}:
                continue
            regions[key_id] = (
                float(element.get("x", "0")),
                float(element.get("y", "0")),
                float(element.get("width", "0")),
                float(element.get("height", "0")),
            )
        if regions:
            resolved = ((view_x, view_y, view_width, view_height), regions)
    except Exception:
        pass
    load_keyboard_special_key_regions._cache = resolved
    return resolved


def keyboard_sound_kind(x_pos=None, y_pos=None):
    if not keyboard_interaction_target(x_pos, y_pos):
        return None
    if x_pos is None or y_pos is None:
        position = get_cursor_position()
        if position is None:
            return None
        x_pos, y_pos = position
    view_box, regions = load_keyboard_special_key_regions()
    view_x, view_y, view_width, view_height = view_box
    local_x = float(x_pos) - float(KEYBOARD_X)
    local_y = float(y_pos) - float(KEYBOARD_Y)
    if KEYBOARD_WIDTH <= 0 or KEYBOARD_HEIGHT <= 0:
        return "default"
    svg_x = view_x + (local_x * view_width / float(KEYBOARD_WIDTH))
    svg_y = view_y + (local_y * view_height / float(KEYBOARD_HEIGHT))
    for key_id, (rect_x, rect_y, rect_width, rect_height) in regions.items():
        if rect_x <= svg_x <= rect_x + rect_width and rect_y <= svg_y <= rect_y + rect_height:
            if key_id == "BKSP":
                return "backspace"
            if key_id == "RTRN":
                return "enter"
    return "default"


def play_keyboard_interaction_sound(x_pos=None, y_pos=None):
    sound_kind = keyboard_sound_kind(x_pos, y_pos)
    if sound_kind == "backspace":
        return KEYBOARD_SOUND_PLAYER.play_keyboard_backspace()
    if sound_kind == "enter":
        return KEYBOARD_SOUND_PLAYER.play_keyboard_enter()
    if sound_kind == "default":
        return KEYBOARD_SOUND_PLAYER.play_keyboard_key_click()
    return False


def controller_cursor_bounds():
    if keyboard_is_open() and not keyboard_suppressed():
        return keyboard_cursor_bounds()
    return CURSOR_MIN_X, CURSOR_MAX_X, CURSOR_MIN_Y, CURSOR_MAX_Y


def clamp_controller_cursor_position(x_pos, y_pos):
    min_x, max_x, min_y, max_y = controller_cursor_bounds()
    clamped_x = max(min_x, min(max_x, int(round(x_pos))))
    clamped_y = max(min_y, min(max_y, int(round(y_pos))))
    return clamped_x, clamped_y


def get_cursor_position():
    try:
        result = subprocess.run(
            ["xdotool", "getmouselocation", "--shell"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            values = {}
            for line in result.stdout.splitlines():
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                values[key.strip()] = value.strip()
            return int(values.get("X", "0")), int(values.get("Y", "0"))
    except Exception:
        return None


def move_to(x_pos, y_pos):
    subprocess.run(["xdotool", "mousemove", str(x_pos), str(y_pos)], capture_output=True)


def move_relative(dx, dy):
    subprocess.run(["xdotool", "mousemove_relative", "--", str(dx), str(dy)], capture_output=True)


def click(button):
    mapping = {"left": "1", "middle": "2", "right": "3"}
    if button == "left" and keyboard_interaction_target():
        play_keyboard_interaction_sound()
    subprocess.run(["xdotool", "click", mapping[button]], capture_output=True)


def scroll(direction):
    button = "4" if direction == "up" else "5"
    subprocess.run(["xdotool", "click", button], capture_output=True)


def go_home():
    subprocess.run(["xdotool", "key", "ctrl+w"], capture_output=True)


def get_debug_targets():
    with urllib.request.urlopen(f"{CDP_URL}/json", timeout=2) as response:
        tabs = json.loads(response.read().decode("utf-8"))

    targets = [
        tab
        for tab in tabs
        if tab.get("type") in {"page", "iframe"} and tab.get("webSocketDebuggerUrl")
    ]
    targets.sort(
        key=lambda tab: (
            tab.get("url", "").startswith(WRAPPER_URL_PREFIX),
            0 if tab.get("url", "").startswith(("http://", "https://")) else 1,
            0 if tab.get("type") == "iframe" else 1,
            tab.get("url", ""),
        )
    )
    return targets


def evaluate_target_js(target, expression):
    ws = None
    try:
        ws = websocket.create_connection(
            target["webSocketDebuggerUrl"],
            timeout=2,
            origin=f"http://localhost:{CONFIG['REMOTE_DEBUG_PORT']}",
        )
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {"expression": expression}}))
        result = json.loads(ws.recv())
        return result.get("result", {}).get("result", {}).get("value")
    except Exception:
        return None
    finally:
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass


def evaluate_js_on_targets(expression):
    results = []
    try:
        targets = get_debug_targets()
    except Exception:
        return results

    for target in targets:
        results.append((target, evaluate_target_js(target, expression)))
    return results


def keyboard_process_running():
    return is_running("onboard")


def keyboard_is_open():
    return bool(keyboard_window_ids(only_visible=True))


def window_name(window_id):
    try:
        result = run_command(["xdotool", "getwindowname", str(window_id)])
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def keyboard_window_ids(only_visible=False):
    try:
        search_cmd = ["xdotool", "search"]
        if only_visible:
            search_cmd.append("--onlyvisible")
        search_cmd.extend(["--name", "onboard"])
        result = run_command(search_cmd)
    except Exception:
        return []

    if result.returncode != 0:
        return []

    window_ids = []
    for raw_line in result.stdout.splitlines():
        candidate = raw_line.strip()
        if not candidate:
            continue
        try:
            window_id = int(candidate)
        except ValueError:
            continue
        if window_name(window_id) != KEYBOARD_WINDOW_TITLE:
            continue
        if window_id not in window_ids:
            window_ids.append(window_id)
    return window_ids


def window_geometry(window_id):
    try:
        result = run_command(["xdotool", "getwindowgeometry", "--shell", str(window_id)])
    except Exception:
        return {}

    if result.returncode != 0:
        return {}

    geometry = {}
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key not in {"X", "Y", "WIDTH", "HEIGHT"}:
            continue
        try:
            geometry[key] = int(value)
        except ValueError:
            continue
    return geometry


def browser_window_ids():
    try:
        result = run_command(["xdotool", "search", "--onlyvisible", "--class", CHROMIUM_WINDOW_CLASS])
    except Exception:
        return []

    if result.returncode != 0:
        return []

    window_ids = []
    for raw_line in result.stdout.splitlines():
        candidate = raw_line.strip()
        if not candidate:
            continue
        try:
            window_id = int(candidate)
        except ValueError:
            continue
        if window_id not in window_ids:
            window_ids.append(window_id)
    return window_ids


def onboard_aux_window_ids():
    try:
        result = run_command(["xdotool", "search", "--name", ONBOARD_AUX_WINDOW_NAME])
    except Exception:
        return []

    if result.returncode != 0:
        return []

    window_ids = []
    for raw_line in result.stdout.splitlines():
        candidate = raw_line.strip()
        if not candidate:
            continue
        try:
            window_id = int(candidate)
        except ValueError:
            continue
        if window_name(window_id) != ONBOARD_AUX_WINDOW_TITLE:
            continue
        if window_id in window_ids:
            continue
        window_ids.append(window_id)
    return window_ids


def extend_keyboard_grace():
    keyboard_grace_until = time.monotonic() + KEYBOARD_FOCUS_GRACE_PERIOD
    setattr(extend_keyboard_grace, "_until", keyboard_grace_until)
    return keyboard_grace_until


def keyboard_grace_active():
    return time.monotonic() < getattr(extend_keyboard_grace, "_until", 0.0)


def clear_keyboard_grace():
    setattr(extend_keyboard_grace, "_until", 0.0)


def browser_focus_allowed():
    return not hud_text_input_active()


def restore_keyboard_window(force=False):
    now = time.monotonic()
    last_refresh = getattr(restore_keyboard_window, "_last_refresh", 0.0)
    if not force and now - last_refresh < KEYBOARD_WINDOW_REFRESH_INTERVAL:
        return False

    restored = False
    for window_id in keyboard_window_ids():
        window_str = str(window_id)
        run_command(["xdotool", "windowmap", window_str])
        run_command(["xdotool", "windowraise", window_str])
        restored = True

    if restored:
        restore_keyboard_window._last_refresh = now
    return restored


def restore_browser_window(force=False):
    if not browser_focus_allowed():
        return False
    now = time.monotonic()
    last_refresh = getattr(restore_browser_window, "_last_refresh", 0.0)
    if not force and now - last_refresh < KEYBOARD_WINDOW_REFRESH_INTERVAL:
        return False

    for window_id in browser_window_ids():
        run_command(["xdotool", "windowactivate", "--sync", str(window_id)])
        restore_browser_window._last_refresh = now
        return True
    return False


def keyboard_visibility_state():
    with KEYBOARD_WINDOW_LOCK:
        return KEYBOARD_TARGET_VISIBLE, KEYBOARD_VISIBILITY_GENERATION


def set_keyboard_target_visible(visible):
    global KEYBOARD_TARGET_VISIBLE, KEYBOARD_VISIBILITY_GENERATION
    resolved_visible = bool(visible)
    with KEYBOARD_WINDOW_LOCK:
        changed = KEYBOARD_TARGET_VISIBLE != resolved_visible
        if changed:
            KEYBOARD_TARGET_VISIBLE = resolved_visible
            KEYBOARD_VISIBILITY_GENERATION += 1
        return KEYBOARD_TARGET_VISIBLE, KEYBOARD_VISIBILITY_GENERATION, changed


def hide_keyboard_aux_windows():
    hidden = False
    for window_id in onboard_aux_window_ids():
        run_command(["xdotool", "windowunmap", str(window_id)])
        hidden = True
    return hidden


def launch_keyboard_process():
    pythonpath = BASE_DIR
    if os.environ.get("PYTHONPATH"):
        pythonpath = BASE_DIR + os.pathsep + os.environ["PYTHONPATH"]
    subprocess.Popen(
        [
            "onboard",
            f"--layout={ONBOARD_LAYOUT}",
            f"--theme={ONBOARD_THEME}",
            f"--size={KEYBOARD_WIDTH}x{KEYBOARD_HEIGHT}",
            "-x",
            str(KEYBOARD_X),
            "-y",
            str(KEYBOARD_HIDDEN_Y),
        ],
        env=dict(os.environ, DISPLAY=":0", PYTHONPATH=pythonpath),
    )


def keyboard_tween(progress, opening):
    clamped = max(0.0, min(1.0, float(progress)))
    return clamped * clamped * clamped * (clamped * ((clamped * 6.0) - 15.0) + 10.0)


def position_keyboard_window(window_id, y_pos, map_window=True, resize_window=True, raise_window=True):
    window_str = str(window_id)
    if map_window:
        run_command(["xdotool", "windowmap", window_str])
    if resize_window:
        run_command(["xdotool", "windowsize", window_str, str(KEYBOARD_WIDTH), str(KEYBOARD_HEIGHT)])
    run_command(["xdotool", "windowmove", window_str, str(KEYBOARD_X), str(int(round(y_pos)))])
    if raise_window:
        run_command(["xdotool", "windowraise", window_str])


def wait_for_keyboard_windows(timeout=1.0):
    deadline = time.monotonic() + max(0.0, timeout)
    window_ids = keyboard_window_ids()
    while not window_ids and time.monotonic() < deadline:
        time.sleep(0.01)
        window_ids = keyboard_window_ids()
    return window_ids


def ensure_keyboard_process(wait_timeout=1.0, hide_ready_window=False):
    ensure_onboard_xtest()
    sync_onboard_assets()
    if not keyboard_process_running():
        launch_keyboard_process()
    window_ids = wait_for_keyboard_windows(wait_timeout)
    if hide_ready_window and window_ids:
        for window_id in window_ids:
            position_keyboard_window(
                window_id,
                KEYBOARD_HIDDEN_Y,
                map_window=True,
                resize_window=True,
                raise_window=False,
            )
            run_command(["xdotool", "windowunmap", str(window_id)])
        hide_keyboard_aux_windows()
    return window_ids


def prewarm_keyboard_process():
    with KEYBOARD_WINDOW_LOCK:
        ensure_keyboard_process(wait_timeout=1.0, hide_ready_window=True)


def animate_keyboard_windows(window_ids=None, opening=True):
    if window_ids is None:
        window_ids = wait_for_keyboard_windows()
    if not window_ids:
        return False

    if opening:
        start_positions = {window_id: KEYBOARD_HIDDEN_Y for window_id in window_ids}
        target_y = KEYBOARD_Y
    else:
        start_positions = {}
        for window_id in window_ids:
            geometry = window_geometry(window_id)
            start_positions[window_id] = geometry.get("Y", KEYBOARD_Y)
        target_y = KEYBOARD_HIDDEN_Y

    for window_id in window_ids:
        position_keyboard_window(
            window_id,
            start_positions.get(window_id, KEYBOARD_Y),
            map_window=opening,
            resize_window=opening,
            raise_window=True,
        )
    hide_keyboard_aux_windows()

    start_time = time.monotonic()
    duration = max(0.0, KEYBOARD_ANIMATION_DURATION)
    while True:
        elapsed = time.monotonic() - start_time
        progress = 1.0 if duration <= 0.0 else min(1.0, elapsed / duration)
        eased = keyboard_tween(progress, opening)
        for window_id in window_ids:
            start_y = start_positions.get(window_id, KEYBOARD_HIDDEN_Y if opening else KEYBOARD_Y)
            current_y = start_y + ((target_y - start_y) * eased)
            position_keyboard_window(
                window_id,
                current_y,
                map_window=False,
                resize_window=False,
                raise_window=False,
            )
        if progress >= 1.0:
            break
        time.sleep(KEYBOARD_ANIMATION_STEP)
    for window_id in window_ids:
        position_keyboard_window(
            window_id,
            target_y,
            map_window=False,
            resize_window=False,
            raise_window=True,
        )
    hide_keyboard_aux_windows()
    return True


def schedule_keyboard_window_restore(visibility_generation):
    def worker():
        for delay in KEYBOARD_WINDOW_RESTORE_DELAYS:
            time.sleep(delay)
            target_visible, current_generation = keyboard_visibility_state()
            if not target_visible or current_generation != visibility_generation:
                return
            restore_keyboard_window(force=True)
            if browser_focus_allowed():
                restore_browser_window(force=True)
            hide_keyboard_aux_windows()

    threading.Thread(target=worker, daemon=True).start()


def controller_input_blocked():
    return quick_menu_active()


def keyboard_suppressed():
    return quick_menu_active() and not hud_text_input_active()


def sync_onboard_assets():
    os.makedirs(ONBOARD_THEME_DIR, exist_ok=True)
    for source, target in (
        (ONBOARD_THEME_SOURCE, ONBOARD_THEME),
        (ONBOARD_COLORS_SOURCE, ONBOARD_COLORS),
    ):
        try:
            if not os.path.exists(target) or os.path.getmtime(source) > os.path.getmtime(target):
                shutil.copyfile(source, target)
        except OSError:
            pass


def show_keyboard():
    with KEYBOARD_WINDOW_LOCK:
        if keyboard_suppressed():
            set_keyboard_target_visible(False)
            clear_keyboard_grace()
            return
        _, visibility_generation, _ = set_keyboard_target_visible(True)
        extend_keyboard_grace()
        install_input_blur_hook()
        window_ids = keyboard_window_ids()
        if keyboard_is_open():
            restore_keyboard_window(force=True)
            for window_id in window_ids:
                position_keyboard_window(window_id, KEYBOARD_Y)
            if browser_focus_allowed():
                restore_browser_window(force=True)
            hide_keyboard_aux_windows()
            return
        if not window_ids:
            window_ids = ensure_keyboard_process(wait_timeout=0.6, hide_ready_window=False)
        if not window_ids:
            return
        KEYBOARD_SOUND_PLAYER.play_keyboard_open()
        animate_keyboard_windows(window_ids=window_ids, opening=True)
        schedule_keyboard_window_restore(visibility_generation)
        if browser_focus_allowed():
            restore_browser_window(force=True)
        current_position = get_cursor_position()
        if current_position is not None:
            min_x, max_x, min_y, max_y = keyboard_cursor_bounds()
            target_x = max(min_x, min(max_x, current_position[0]))
            target_y = max(min_y, min(max_y, current_position[1]))
            if current_position != (target_x, target_y):
                move_to(target_x, target_y)


def hide_keyboard():
    with KEYBOARD_WINDOW_LOCK:
        _, _, visibility_changed = set_keyboard_target_visible(False)
        clear_keyboard_grace()
        window_ids = keyboard_window_ids()
        if window_ids:
            if visibility_changed:
                KEYBOARD_SOUND_PLAYER.play_keyboard_close()
            animate_keyboard_windows(window_ids=window_ids, opening=False)
        for window_id in [*keyboard_window_ids(), *onboard_aux_window_ids()]:
            run_command(["xdotool", "windowunmap", str(window_id)])


def toggle_keyboard():
    if keyboard_is_open():
        hide_keyboard()
    else:
        if keyboard_suppressed():
            clear_keyboard_grace()
            return
        show_keyboard()
        keep_input_visible()


def install_input_blur_hook():
    installed = False
    for _, result in evaluate_js_on_targets(INSTALL_INPUT_BLUR_HOOK_JS):
        if isinstance(result, bool):
            installed = installed or result
    return installed


def install_zoom_lock():
    installed = False
    for _, result in evaluate_js_on_targets(INSTALL_ZOOM_LOCK_JS):
        if isinstance(result, bool):
            installed = installed or result
    return installed


def install_selection_lock():
    installed = False
    for _, result in evaluate_js_on_targets(INSTALL_SELECTION_LOCK_JS):
        if isinstance(result, bool):
            installed = installed or result
    return installed


def install_viewport_fit_fix():
    installed = False
    for _, result in evaluate_js_on_targets(INSTALL_VIEWPORT_FIT_FIX_JS):
        if isinstance(result, bool):
            installed = installed or result
    return installed


def get_input_focus_state():
    saw_bool = False
    for _, result in evaluate_js_on_targets(INPUT_FOCUS_JS):
        if isinstance(result, bool):
            saw_bool = True
            if result:
                return True
    if saw_bool:
        return False
    return None


def keep_input_visible():
    kept_visible = False
    for _, result in evaluate_js_on_targets(KEEP_INPUT_VISIBLE_JS):
        if isinstance(result, bool):
            kept_visible = kept_visible or result
    return kept_visible


def sync_keyboard_to_focus():
    if keyboard_suppressed():
        if keyboard_is_open():
            hide_keyboard()
        return
    if hud_text_input_active():
        extend_keyboard_grace()
        if not keyboard_is_open():
            show_keyboard()
        else:
            restore_keyboard_window()
            if browser_focus_allowed():
                restore_browser_window()
            hide_keyboard_aux_windows()
        return
    focus_state = get_input_focus_state()
    if focus_state is True:
        extend_keyboard_grace()
    if focus_state is True or keyboard_grace_active():
        if not keyboard_is_open():
            show_keyboard()
        else:
            restore_keyboard_window()
            restore_browser_window()
            hide_keyboard_aux_windows()
        if focus_state is True:
            keep_input_visible()
        return
    if focus_state is False and keyboard_is_open():
        hide_keyboard()


def settle_keyboard_after_input(delay):
    time.sleep(delay)
    sync_keyboard_to_focus()


def check_keyboard_after_click():
    settle_keyboard_after_input(KB_CHECK_DELAY)


def check_keyboard_after_touch():
    settle_keyboard_after_input(TOUCH_CHECK_DELAY)


def keyboard_focus_loop():
    while True:
        time.sleep(KB_POLL_INTERVAL)
        sync_keyboard_to_focus()


def viewport_fix_loop():
    while True:
        install_zoom_lock()
        install_selection_lock()
        install_viewport_fit_fix()
        time.sleep(VIEWPORT_FIX_POLL_INTERVAL)


class Controller:
    def __init__(self):
        self.ax = 0.0
        self.ay = 0.0
        self.filtered_ax = 0.0
        self.filtered_ay = 0.0
        self.b_time = None
        self.lb_held = False
        self.rb_held = False
        self.dup_held = False
        self.ddown_held = False
        self.last_touch_check = 0.0
        self.axis_info = {}
        self.cursor_x = None
        self.cursor_y = None
        self.cursor_remainder_x = 0.0
        self.cursor_remainder_y = 0.0
        self.last_cursor_sync = 0.0
        self.last_keyboard_touch_sound_at = 0.0

    def configure_device(self, dev):
        self.axis_info = {}
        for axis_code in (evdev.ecodes.ABS_X, evdev.ecodes.ABS_Y):
            try:
                info = dev.absinfo(axis_code)
            except Exception:
                info = None
            if info is None or info.max <= info.min:
                continue
            center = (info.min + info.max) / 2.0
            hardware_deadzone = max(float(info.flat or 0), float(info.fuzz or 0))
            self.axis_info[axis_code] = {
                "center": center,
                "negative_span": max(1.0, center - info.min),
                "positive_span": max(1.0, info.max - center),
                "hardware_deadzone": hardware_deadzone,
            }
        self.reset_state()
        self.sync_cursor_position(force=True)

    def norm_axis(self, code, value):
        info = self.axis_info.get(code)
        if info is None:
            return max(-1.0, min(1.0, float(value) / DEFAULT_AXIS_MAX))
        offset = float(value) - info["center"]
        if abs(offset) <= info["hardware_deadzone"]:
            return 0.0
        span = info["positive_span"] if offset >= 0 else info["negative_span"]
        return max(-1.0, min(1.0, offset / span))

    def axis_blend(self, current, target, dt):
        rate = CURSOR_RELEASE_SMOOTHING if abs(target) < abs(current) else CURSOR_SMOOTHING
        return 1.0 - math.exp(-rate * dt)

    def adjusted_analog_vector(self):
        magnitude = math.hypot(self.filtered_ax, self.filtered_ay)
        if magnitude <= DEADZONE:
            return 0.0, 0.0, 0.0
        scaled_magnitude = min(1.0, (magnitude - DEADZONE) / (1.0 - DEADZONE))
        return self.filtered_ax / magnitude, self.filtered_ay / magnitude, scaled_magnitude

    def sync_cursor_position(self, force=False):
        now = time.monotonic()
        if not force and self.cursor_x is not None and self.cursor_y is not None:
            if now - self.last_cursor_sync < CURSOR_POSITION_SYNC_INTERVAL:
                return True
        position = get_cursor_position()
        if position is None:
            return False
        if STANDARD_TOUCH_CURSOR:
            target_x, target_y = clamp_screen_position(*position)
        else:
            target_x, target_y = clamp_controller_cursor_position(*position)
        self.cursor_x = target_x
        self.cursor_y = target_y
        self.last_cursor_sync = now
        if position != (target_x, target_y):
            move_to(target_x, target_y)
        return True

    def move_cursor_by(self, dx, dy):
        if not dx and not dy:
            return
        if self.cursor_x is None or self.cursor_y is None:
            if not self.sync_cursor_position(force=True):
                move_relative(dx, dy)
                return
        target_x, target_y = clamp_controller_cursor_position(self.cursor_x + dx, self.cursor_y + dy)
        if target_x == self.cursor_x and target_y == self.cursor_y:
            return
        move_to(target_x, target_y)
        self.cursor_x = target_x
        self.cursor_y = target_y

    def cursor_step(self, dt):
        self.filtered_ax += (self.ax - self.filtered_ax) * self.axis_blend(self.filtered_ax, self.ax, dt)
        self.filtered_ay += (self.ay - self.filtered_ay) * self.axis_blend(self.filtered_ay, self.ay, dt)

        adjusted_x, adjusted_y, magnitude = self.adjusted_analog_vector()
        if magnitude <= 0.0:
            return 0, 0

        speed = CURSOR_MIN_SPEED * magnitude
        speed += (CURSOR_MAX_SPEED - CURSOR_MIN_SPEED) * (magnitude ** CURSOR_RESPONSE_EXPONENT)

        self.cursor_remainder_x += adjusted_x * speed * dt
        self.cursor_remainder_y += adjusted_y * speed * dt

        if self.cursor_remainder_x > 0:
            dx = math.floor(self.cursor_remainder_x)
        elif self.cursor_remainder_x < 0:
            dx = math.ceil(self.cursor_remainder_x)
        else:
            dx = 0

        if self.cursor_remainder_y > 0:
            dy = math.floor(self.cursor_remainder_y)
        elif self.cursor_remainder_y < 0:
            dy = math.ceil(self.cursor_remainder_y)
        else:
            dy = 0

        self.cursor_remainder_x -= dx
        self.cursor_remainder_y -= dy
        return dx, dy

    def reset_state(self):
        self.ax = 0.0
        self.ay = 0.0
        self.filtered_ax = 0.0
        self.filtered_ay = 0.0
        self.b_time = None
        self.lb_held = False
        self.rb_held = False
        self.dup_held = False
        self.ddown_held = False
        self.cursor_remainder_x = 0.0
        self.cursor_remainder_y = 0.0

    def cursor_loop(self):
        last_tick = time.monotonic()
        while True:
            now = time.monotonic()
            dt = min(0.05, max(0.001, now - last_tick))
            last_tick = now

            if controller_input_blocked():
                self.reset_state()
                time.sleep(0.05)
                continue

            self.sync_cursor_position()
            dx, dy = self.cursor_step(dt)
            if dx or dy:
                self.move_cursor_by(dx, dy)

            if self.lb_held or self.dup_held:
                scroll("up")
                time.sleep(SCROLL_DELAY)
            elif self.rb_held or self.ddown_held:
                scroll("down")
                time.sleep(SCROLL_DELAY)
            else:
                time.sleep(CURSOR_LOOP_DELAY)

    def schedule_touch_focus_check(self):
        now = time.time()
        if now - self.last_touch_check < TOUCH_CHECK_DELAY:
            return
        self.last_touch_check = now
        threading.Thread(target=check_keyboard_after_touch, daemon=True).start()

    def play_touch_keyboard_key_click(self):
        if not keyboard_interaction_target():
            return False
        now = time.monotonic()
        if now - self.last_keyboard_touch_sound_at < KEYBOARD_TOUCH_SOUND_MIN_INTERVAL_SEC:
            return False
        self.last_keyboard_touch_sound_at = now
        return play_keyboard_interaction_sound()

    def touch_loop(self):
        while True:
            dev = find_touchscreen()
            if not dev:
                time.sleep(5)
                continue

            touch_active = False
            try:
                for event in dev.read_loop():
                    if controller_input_blocked():
                        touch_active = False
                        continue
                    if event.type == evdev.ecodes.EV_KEY and event.code == evdev.ecodes.BTN_TOUCH:
                        if event.value == 1:
                            touch_active = True
                        elif event.value == 0 and touch_active:
                            touch_active = False
                            self.play_touch_keyboard_key_click()
                            self.schedule_touch_focus_check()
                    elif event.type == evdev.ecodes.EV_ABS and event.code == evdev.ecodes.ABS_MT_TRACKING_ID:
                        if event.value == -1:
                            touch_active = False
                            self.play_touch_keyboard_key_click()
                            self.schedule_touch_focus_check()
            except OSError:
                touch_active = False
                time.sleep(2)

    def handle(self, dev):
        for event in dev.read_loop():
            if controller_input_blocked():
                self.reset_state()
                continue

            if event.type == evdev.ecodes.EV_ABS:
                if event.code == evdev.ecodes.ABS_X:
                    self.ax = self.norm_axis(evdev.ecodes.ABS_X, event.value)
                elif event.code == evdev.ecodes.ABS_Y:
                    self.ay = self.norm_axis(evdev.ecodes.ABS_Y, event.value)
                elif event.code == evdev.ecodes.ABS_HAT0Y:
                    self.dup_held = event.value == -1
                    self.ddown_held = event.value == 1

            elif event.type == evdev.ecodes.EV_KEY:
                code = event.code
                value = event.value

                if code == evdev.ecodes.BTN_SOUTH and value == 1:
                    click("left")
                    threading.Thread(target=check_keyboard_after_click, daemon=True).start()
                elif code == evdev.ecodes.BTN_EAST:
                    if value == 1:
                        self.b_time = time.time()
                    elif value == 0 and self.b_time:
                        if time.time() - self.b_time >= HOLD_DURATION:
                            hide_keyboard()
                            go_home()
                        self.b_time = None
                elif code == evdev.ecodes.BTN_WEST and value == 1:
                    click("middle")
                elif code == evdev.ecodes.BTN_NORTH and value == 1:
                    toggle_keyboard()
                elif code == evdev.ecodes.BTN_TL:
                    self.lb_held = value == 1
                elif code == evdev.ecodes.BTN_TR:
                    self.rb_held = value == 1

    def run(self):
        install_zoom_lock()
        install_selection_lock()
        install_viewport_fit_fix()
        threading.Thread(target=prewarm_keyboard_process, daemon=True).start()
        threading.Thread(target=keyboard_focus_loop, daemon=True).start()
        threading.Thread(target=viewport_fix_loop, daemon=True).start()
        threading.Thread(target=self.cursor_loop, daemon=True).start()
        threading.Thread(target=self.touch_loop, daemon=True).start()

        while True:
            dev = find_gamepad()
            if not dev:
                time.sleep(5)
                continue
            try:
                self.configure_device(dev)
                self.handle(dev)
            except OSError:
                self.reset_state()
                time.sleep(2)


if __name__ == "__main__":
    Controller().run()
