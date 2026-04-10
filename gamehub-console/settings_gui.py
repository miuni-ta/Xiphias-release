#!/usr/bin/env python3
import base64
from io import BytesIO
import os
from functools import lru_cache
import tkinter as tk
from tkinter import font as tkfont

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

from common import hud_bar_heights, load_config, read_workspace_version


CONFIG = load_config()
SCREEN_W = int(CONFIG["SCREEN_WIDTH"])
SCREEN_H = int(CONFIG["SCREEN_HEIGHT"])
STATUS_BAR_H, BOTTOM_BAR_H = hud_bar_heights(CONFIG)
APP_Y = STATUS_BAR_H
APP_H = max(1, SCREEN_H - STATUS_BAR_H - BOTTOM_BAR_H)

BASE_DIR = os.path.dirname(__file__)
ICON_DIR = os.path.join(BASE_DIR, "assets", "icons")

BG = "#040509"
PANEL_BG = "#1e1219"
HEADER_TEXT = "#ffffff"
ROW_BG = "#2a2435"
ROW_BORDER = "#3d3750"
ROW_FOCUS_START = "#f0184e"
ROW_FOCUS_END = "#f5793a"
ROW_FOCUS_TEXT = "#ffffff"
TEXT = "#ffffff"
TEXT_MUTED = "#b0aabd"
TEXT_DESTRUCTIVE = "#f5793a"
HOT_PINK = "#f0197a"
ROUNDED_SHAPE_AA_SCALE = 4

TITLE_FONT_FAMILY = "FF DIN"
TITLE_FONT_SIZE = 18
ITEM_FONT_SIZE = 13
VALUE_FONT_SIZE = 12
HEADER_TOP_PAD = 18
HEADER_LEFT_PAD = 18
HEADER_BOTTOM_PAD = 18
ROW_X = 4
ROW_WIDTH = SCREEN_W - 8
ROW_HEIGHT = 44
ROW_GAP = 8
ROW_RADIUS = 14
ROW_ICON_X = 30
ROW_TEXT_X = 62
ROW_VALUE_PAD = 30
ICON_SIZE = 18
GRADIENT_STEPS = 40


def software_version_value():
    version = str(read_workspace_version()).strip()
    if not version or version.lower() == "unknown":
        return "Unknown"
    if version.lower().startswith("v"):
        return version
    return f"v{version}"


ROWS = [
    {
        "label": "Volume",
        "value": "75%",
        "icon": "volume/volume_full.png",
        "focused": True,
    },
    {
        "label": "WiFi",
        "value": "Connected",
        "icon": "wifi/wifi_connected.png",
        "focused": False,
    },
    {
        "label": "Bluetooth",
        "value": "Off",
        "icon": "bluetooth/bluetooth_off.png",
        "focused": False,
    },
    {
        "label": "Brightness",
        "value": "80%",
        "icon": "hud/brightness.png",
        "focused": False,
    },
    {
        "label": "Check for Updates",
        "value": software_version_value(),
        "icon": "hud/cursor_settings.png",
        "focused": False,
    },
    {
        "label": "Restart Kiosk",
        "value": "",
        "icon": "hud/restart.png",
        "focused": False,
    },
    {
        "label": "Shutdown",
        "value": "",
        "icon": "hud/shutdown.png",
        "focused": False,
    },
]


def parse_hex_color(color):
    color = str(color).strip()
    if len(color) != 7 or not color.startswith("#"):
        raise ValueError(f"unsupported color: {color}")
    return tuple(int(color[index:index + 2], 16) for index in (1, 3, 5))


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


@lru_cache(maxsize=256)
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
def load_icon(relative_path, color, size):
    path = os.path.join(ICON_DIR, *relative_path.split("/"))
    if GdkPixbuf is not None:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
            if size > 0 and (pixbuf.get_width() != size or pixbuf.get_height() != size):
                pixbuf = pixbuf.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
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

    if size > 0 and source.width() != size and source.height() != size:
        step_x = max(1, source.width() // size)
        step_y = max(1, source.height() // size)
        source = source.subsample(step_x, step_y)
    return tint_photo_image(source, color)


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
    steps=GRADIENT_STEPS,
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


def rounded_rect(canvas, x1, y1, x2, y2, radius, fill, outline):
    if fill:
        draw_rounded_rect(canvas, x1, y1, x2, y2, radius, fill)
    if outline:
        draw_rounded_outline(canvas, x1, y1, x2, y2, radius, outline)


def interpolate_hex_color(start_color, end_color, progress):
    start_rgb = parse_hex_color(start_color)
    end_rgb = parse_hex_color(end_color)
    blended = tuple(
        int(round(start_value + (end_value - start_value) * progress))
        for start_value, end_value in zip(start_rgb, end_rgb)
    )
    return f"#{blended[0]:02x}{blended[1]:02x}{blended[2]:02x}"


def draw_gradient_rounded_rect(canvas, x1, y1, x2, y2, radius, start_color, end_color, steps=GRADIENT_STEPS):
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


class SettingsPreview:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GameHub Settings Preview")
        self.root.geometry(f"{SCREEN_W}x{APP_H}+0+{APP_Y}")
        self.root.configure(bg=BG)
        self.root.overrideredirect(True)
        try:
            self.root.wm_attributes("-topmost", True)
        except tk.TclError:
            pass
        try:
            self.root.wm_attributes("-type", "dock")
        except tk.TclError:
            pass

        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("q", lambda _event: self.root.destroy())
        self.root.bind("Q", lambda _event: self.root.destroy())

        self.images = []
        self.title_font = tkfont.Font(family=TITLE_FONT_FAMILY, size=TITLE_FONT_SIZE, weight="bold")
        self.item_font = tkfont.Font(family=TITLE_FONT_FAMILY, size=ITEM_FONT_SIZE, weight="bold")
        self.value_font = tkfont.Font(family=TITLE_FONT_FAMILY, size=max(10, VALUE_FONT_SIZE - 1), weight="bold")

        self.canvas = tk.Canvas(
            self.root,
            width=SCREEN_W,
            height=APP_H,
            bg=BG,
            bd=0,
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw()

    def draw_header(self):
        self.canvas.create_text(
            HEADER_LEFT_PAD,
            HEADER_TOP_PAD + 16,
            anchor="w",
            text="Settings",
            fill=HEADER_TEXT,
            font=self.title_font,
        )

    def draw_rows(self):
        list_top = HEADER_TOP_PAD + 32 + HEADER_BOTTOM_PAD
        list_bottom = list_top + (len(ROWS) * ROW_HEIGHT) + ((len(ROWS) - 1) * ROW_GAP)
        rounded_rect(
            self.canvas,
            0,
            list_top - 6,
            SCREEN_W,
            min(APP_H, list_bottom + 6),
            16,
            PANEL_BG,
            PANEL_BG,
        )
        for index, item in enumerate(ROWS):
            y_pos = list_top + index * (ROW_HEIGHT + ROW_GAP)
            focused = bool(item["focused"])
            destructive = item["label"] in {"Restart Kiosk", "Shutdown"}
            text_color = ROW_FOCUS_TEXT if focused else (TEXT_DESTRUCTIVE if destructive else TEXT)
            value_color = ROW_FOCUS_TEXT if focused else TEXT_MUTED
            icon_color = ROW_FOCUS_TEXT if focused else TEXT_MUTED

            if focused:
                draw_bordered_gradient_rounded_rect(
                    self.canvas,
                    ROW_X,
                    y_pos,
                    ROW_X + ROW_WIDTH,
                    y_pos + ROW_HEIGHT,
                    ROW_RADIUS,
                    ROW_FOCUS_START,
                    ROW_FOCUS_END,
                    ROW_FOCUS_END,
                )
            else:
                draw_bordered_rounded_rect(
                    self.canvas,
                    ROW_X,
                    y_pos,
                    ROW_X + ROW_WIDTH,
                    y_pos + ROW_HEIGHT,
                    ROW_RADIUS,
                    ROW_BG,
                    ROW_BORDER,
                )

            icon_image = load_icon(item["icon"], icon_color, ICON_SIZE)
            if icon_image is not None:
                self.images.append(icon_image)
                self.canvas.create_image(
                    ROW_ICON_X,
                    y_pos + ROW_HEIGHT / 2,
                    image=icon_image,
                )

            self.canvas.create_text(
                ROW_TEXT_X,
                y_pos + ROW_HEIGHT / 2,
                anchor="w",
                text=item["label"],
                fill=text_color,
                font=self.item_font,
            )

            if item["value"]:
                self.canvas.create_text(
                    SCREEN_W - ROW_VALUE_PAD,
                    y_pos + ROW_HEIGHT / 2,
                    anchor="e",
                    text=item["value"],
                    fill=value_color,
                    font=self.value_font,
                )

    def draw(self):
        self.canvas.delete("all")
        self.images = []
        self.canvas.images = self.images
        self.draw_header()
        self.draw_rows()

    def run(self):
        self.root.mainloop()


def main():
    preview = SettingsPreview()
    preview.run()


if __name__ == "__main__":
    main()
