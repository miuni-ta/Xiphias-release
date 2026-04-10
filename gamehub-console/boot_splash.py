#!/usr/bin/env python3
import base64
from io import BytesIO
import math
import os
import tkinter as tk
from pathlib import Path
import time

try:
    from PIL import Image
except Exception as exc:
    raise SystemExit(f"Pillow is required for boot_splash.py: {exc}")

from common import config_int, load_config
from splash_audio import SplashJinglePlayer


os.environ["DISPLAY"] = os.environ.get("DISPLAY", ":0")

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "images" / "gbl_logo.png"
BACKGROUND = "#000000"
FRAME_INTERVAL_MS = 33
FADE_DURATION_MS = 850
FULL_HOLD_DURATION_MS = 1800
HANDOFF_HOLD_DURATION_MS = 180
HANDOFF_MIN_HOLD_DURATION_MS = 120
HANDOFF_MAX_WAIT_MS = 12000
HANDOFF_POLL_INTERVAL_MS = 60
LOGO_MAX_WIDTH_RATIO = 0.86
LOGO_MAX_HEIGHT_RATIO = 0.74
SPLASH_MODE_FULL = "full"
SPLASH_MODE_HANDOFF = "handoff"
SPLASH_AUDIO_ENABLED = False


def ease_in_out(progress):
    progress = max(0.0, min(1.0, float(progress)))
    return 0.5 - (0.5 * math.cos(progress * math.pi))


def fit_size(width, height, max_width, max_height):
    width = max(1, int(width))
    height = max(1, int(height))
    max_width = max(1, int(max_width))
    max_height = max(1, int(max_height))
    scale = min(max_width / width, max_height / height)
    return (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale))),
    )


def opacity_steps(duration_ms, frame_interval_ms):
    frame_count = max(2, int(math.ceil(duration_ms / max(1, frame_interval_ms))) + 1)
    last_index = frame_count - 1
    return [ease_in_out(index / last_index) for index in range(frame_count)]


def image_to_photoimage(image):
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return tk.PhotoImage(data=base64.b64encode(buffer.getvalue()).decode("ascii"))


class BootSplash:
    def __init__(self):
        config = load_config()
        self.screen_width = max(1, config_int(config, "SCREEN_WIDTH", 800))
        self.screen_height = max(1, config_int(config, "SCREEN_HEIGHT", 480))
        self.mode = self.resolve_mode()
        self.ready_file = self.resolve_ready_file()
        self.handoff_min_hold_ms = self.resolve_int_env(
            "BOOT_SPLASH_MIN_HOLD_MS",
            HANDOFF_MIN_HOLD_DURATION_MS,
            minimum=0,
        )
        self.handoff_max_wait_ms = self.resolve_int_env(
            "BOOT_SPLASH_MAX_WAIT_MS",
            HANDOFF_MAX_WAIT_MS,
            minimum=self.handoff_min_hold_ms,
        )
        self.jingle_player = None
        if SPLASH_AUDIO_ENABLED:
            self.jingle_player = SplashJinglePlayer(
                client_name="gamehub-console",
                stream_name="gamehub-splash-jingle",
            )
        self.handoff_started_at = None
        self.fade_in_opacities = opacity_steps(FADE_DURATION_MS, FRAME_INTERVAL_MS)
        self.frame_index = 0

        self.root = tk.Tk()
        self.root.configure(bg=BACKGROUND, cursor="none")
        self.root.overrideredirect(True)
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+0+0")
        self.root.lift()
        try:
            self.root.attributes("-fullscreen", True)
        except tk.TclError:
            pass
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass

        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg=BACKGROUND,
            bd=0,
            highlightthickness=0,
            relief="flat",
            cursor="none",
        )
        self.canvas.pack(fill="both", expand=True)

        self.logo_frames = self.build_logo_frames()
        self.fade_out_frames = [
            self.logo_frames[index]
            for index in range(len(self.logo_frames) - 2, -1, -1)
        ]
        initial_frame = (
            self.logo_frames[-1]
            if self.mode == SPLASH_MODE_HANDOFF
            else self.logo_frames[0]
        )
        self.image_item = self.canvas.create_image(
            self.screen_width // 2,
            self.screen_height // 2,
            image=initial_frame,
        )

    def resolve_mode(self):
        mode = os.environ.get("BOOT_SPLASH_MODE", SPLASH_MODE_FULL).strip().lower()
        if mode == SPLASH_MODE_HANDOFF:
            return SPLASH_MODE_HANDOFF
        return SPLASH_MODE_FULL

    def resolve_ready_file(self):
        raw_value = os.environ.get("BOOT_SPLASH_READY_FILE", "").strip()
        if not raw_value:
            return None
        return Path(raw_value).expanduser()

    def resolve_int_env(self, name, default, minimum=0):
        raw_value = os.environ.get(name, "").strip()
        if not raw_value:
            return default
        try:
            return max(minimum, int(raw_value))
        except ValueError:
            return default

    def build_logo_frames(self):
        if not LOGO_PATH.exists():
            raise FileNotFoundError(f"Missing splash logo: {LOGO_PATH}")

        source = Image.open(LOGO_PATH).convert("RGBA")
        target_width, target_height = fit_size(
            source.width,
            source.height,
            int(round(self.screen_width * LOGO_MAX_WIDTH_RATIO)),
            int(round(self.screen_height * LOGO_MAX_HEIGHT_RATIO)),
        )
        if (target_width, target_height) != source.size:
            source = source.resize((target_width, target_height), Image.LANCZOS)

        source_alpha = source.getchannel("A")
        frames = []
        for opacity in self.fade_in_opacities:
            frame = source.copy()
            frame.putalpha(source_alpha.point(lambda value, scale=opacity: int(round(value * scale))))
            frames.append(image_to_photoimage(frame))
        return frames

    def run(self):
        self.play_splash_jingle()
        if self.mode == SPLASH_MODE_HANDOFF:
            self.root.after(0, self.begin_handoff)
        else:
            self.root.after(0, self.fade_in_step)
        self.root.mainloop()

    def play_splash_jingle(self):
        if self.jingle_player is None:
            return
        try:
            self.jingle_player.play()
        except Exception:
            pass

    def begin_handoff(self):
        self.canvas.itemconfigure(self.image_item, image=self.logo_frames[-1])
        self.handoff_started_at = time.monotonic()
        self.root.after(HANDOFF_HOLD_DURATION_MS, self.wait_for_handoff_ready)

    def handoff_ready(self):
        if self.ready_file is None:
            return True
        return self.ready_file.exists()

    def handoff_timed_out(self):
        if self.handoff_started_at is None:
            return False
        elapsed_ms = (time.monotonic() - self.handoff_started_at) * 1000.0
        return elapsed_ms >= self.handoff_max_wait_ms

    def handoff_min_hold_elapsed(self):
        if self.handoff_started_at is None:
            return True
        elapsed_ms = (time.monotonic() - self.handoff_started_at) * 1000.0
        return elapsed_ms >= self.handoff_min_hold_ms

    def wait_for_handoff_ready(self):
        if self.handoff_timed_out():
            self.begin_fade_out()
            return
        if self.handoff_min_hold_elapsed() and self.handoff_ready():
            self.begin_fade_out()
            return
        self.root.after(HANDOFF_POLL_INTERVAL_MS, self.wait_for_handoff_ready)

    def fade_in_step(self):
        self.canvas.itemconfigure(self.image_item, image=self.logo_frames[self.frame_index])
        if self.frame_index >= len(self.logo_frames) - 1:
            self.root.after(FULL_HOLD_DURATION_MS, self.begin_fade_out)
            return
        self.frame_index += 1
        self.root.after(FRAME_INTERVAL_MS, self.fade_in_step)

    def begin_fade_out(self):
        self.frame_index = 0
        self.fade_out_step()

    def fade_out_step(self):
        if self.frame_index >= len(self.fade_out_frames):
            self.root.destroy()
            return
        self.canvas.itemconfigure(self.image_item, image=self.fade_out_frames[self.frame_index])
        self.frame_index += 1
        self.root.after(FRAME_INTERVAL_MS, self.fade_out_step)


def main():
    splash = BootSplash()
    splash.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
