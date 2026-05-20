#!/usr/bin/env python3
import os
import signal
import sys
import threading
import time
from dataclasses import dataclass

from evdev import AbsInfo, UInput, ecodes

from common import load_config


DEVICE_NAME = "Xiphias GPIO Gamepad"
AXIS_MAX = 32767
DEFAULT_BOUNCE_MS = 20
DEFAULT_ACTIVE_LOW = True
GPIOZERO_PIN_FACTORY = "lgpio"


@dataclass(frozen=True)
class GpioControl:
    name: str
    config_key: str
    default_gpio: int
    kind: str
    code: int = 0
    axis: str = ""
    direction: int = 0


CONTROLS = (
    GpioControl("dpad_up", "GPIO_GAMEPAD_DPAD_UP", 19, "axis", axis="y", direction=-1),
    GpioControl("dpad_down", "GPIO_GAMEPAD_DPAD_DOWN", 5, "axis", axis="y", direction=1),
    GpioControl("dpad_left", "GPIO_GAMEPAD_DPAD_LEFT", 13, "axis", axis="x", direction=-1),
    GpioControl("dpad_right", "GPIO_GAMEPAD_DPAD_RIGHT", 6, "axis", axis="x", direction=1),
    GpioControl("start", "GPIO_GAMEPAD_START", 26, "button", code=ecodes.BTN_START),
    GpioControl("select", "GPIO_GAMEPAD_SELECT", 10, "button", code=ecodes.BTN_SELECT),
    GpioControl("a", "GPIO_GAMEPAD_A", 20, "button", code=ecodes.BTN_SOUTH),
    GpioControl("b", "GPIO_GAMEPAD_B", 21, "button", code=ecodes.BTN_EAST),
    GpioControl("x", "GPIO_GAMEPAD_X", 12, "button", code=ecodes.BTN_WEST),
    GpioControl("y", "GPIO_GAMEPAD_Y", 16, "button", code=ecodes.BTN_NORTH),
    GpioControl("left_shoulder", "GPIO_GAMEPAD_L1", 9, "button", code=ecodes.BTN_TL),
    GpioControl("right_shoulder", "GPIO_GAMEPAD_R1", 8, "button", code=ecodes.BTN_TR),
    GpioControl("left_trigger", "GPIO_GAMEPAD_L2", 11, "button", code=ecodes.BTN_TL2),
    GpioControl("right_trigger", "GPIO_GAMEPAD_R2", 7, "button", code=ecodes.BTN_TR2),
)


def log(message):
    print(f"[gpio-gamepad] {message}", flush=True)


def config_bool(config, key, default):
    raw_value = str(config.get(key, "")).strip().lower()
    if raw_value in {"1", "true", "yes", "on", "enabled"}:
        return True
    if raw_value in {"0", "false", "no", "off", "disabled"}:
        return False
    return bool(default)


def config_float(config, key, default, minimum=0.0):
    raw_value = str(config.get(key, "")).strip()
    if not raw_value:
        return default
    try:
        return max(minimum, float(raw_value))
    except ValueError:
        return default


def config_pin(config, key, default):
    raw_value = str(config.get(key, default)).strip()
    if raw_value.lower() in {"", "none", "off", "disabled", "-1"}:
        return None
    try:
        pin = int(raw_value, 0)
    except ValueError:
        raise ValueError(f"{key} must be a BCM GPIO number, not {raw_value!r}") from None
    if pin < 0:
        return None
    return pin


def configured_controls(config):
    controls = []
    used_pins = {}
    for control in CONTROLS:
        pin = config_pin(config, control.config_key, control.default_gpio)
        if pin is None:
            continue
        previous = used_pins.get(pin)
        if previous is not None:
            raise ValueError(
                f"GPIO {pin} is assigned to both {previous.config_key} and {control.config_key}"
            )
        used_pins[pin] = control
        controls.append((control, pin))
    return controls


def build_uinput():
    abs_axis = AbsInfo(value=0, min=-AXIS_MAX, max=AXIS_MAX, fuzz=0, flat=0, resolution=0)
    hat_axis = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)
    capabilities = {
        ecodes.EV_KEY: [
            ecodes.BTN_SOUTH,
            ecodes.BTN_EAST,
            ecodes.BTN_NORTH,
            ecodes.BTN_WEST,
            ecodes.BTN_START,
            ecodes.BTN_SELECT,
            ecodes.BTN_TL,
            ecodes.BTN_TR,
            ecodes.BTN_TL2,
            ecodes.BTN_TR2,
        ],
        ecodes.EV_ABS: [
            (ecodes.ABS_X, abs_axis),
            (ecodes.ABS_Y, abs_axis),
            (ecodes.ABS_HAT0X, hat_axis),
            (ecodes.ABS_HAT0Y, hat_axis),
        ],
    }
    return UInput(capabilities, name=DEVICE_NAME, bustype=getattr(ecodes, "BUS_VIRTUAL", 0x06))


class GpioGamepad:
    def __init__(self, controls, active_low, bounce_time):
        self.controls = controls
        self.active_low = active_low
        self.bounce_time = bounce_time
        self.ui = build_uinput()
        self.buttons = []
        self.lock = threading.Lock()
        self.held_controls = set()
        self.axis_state = {"x": 0, "y": 0}

    def start(self):
        os.environ.setdefault("GPIOZERO_PIN_FACTORY", GPIOZERO_PIN_FACTORY)
        from gpiozero import Button

        for control, pin in self.controls:
            button = Button(pin, pull_up=self.active_low, bounce_time=self.bounce_time)
            button.when_pressed = lambda item=control: self.handle_control(item, True)
            button.when_released = lambda item=control: self.handle_control(item, False)
            self.buttons.append(button)

        time.sleep(0.1)
        for (control, _pin), button in zip(self.controls, self.buttons):
            self.handle_control(control, button.is_pressed)

        log(f"started {DEVICE_NAME} with {len(self.controls)} GPIO controls")

    def stop(self):
        with self.lock:
            for control, _pin in self.controls:
                if control.kind == "button":
                    self.ui.write(ecodes.EV_KEY, control.code, 0)
            self.axis_state = {"x": 0, "y": 0}
            self.write_axis_unlocked("x", 0)
            self.write_axis_unlocked("y", 0)
            self.ui.syn()

        for button in self.buttons:
            try:
                button.close()
            except Exception:
                pass
        self.ui.close()

    def handle_control(self, control, pressed):
        with self.lock:
            if pressed:
                self.held_controls.add(control.name)
            else:
                self.held_controls.discard(control.name)

            if control.kind == "button":
                self.ui.write(ecodes.EV_KEY, control.code, 1 if pressed else 0)
            elif control.kind == "axis":
                self.update_axis_unlocked(control.axis)
            self.ui.syn()

    def update_axis_unlocked(self, axis):
        if axis == "x":
            negative_name = "dpad_left"
            positive_name = "dpad_right"
        else:
            negative_name = "dpad_up"
            positive_name = "dpad_down"

        negative = negative_name in self.held_controls
        positive = positive_name in self.held_controls
        value = 0
        if negative and not positive:
            value = -1
        elif positive and not negative:
            value = 1

        if self.axis_state.get(axis) == value:
            return
        self.axis_state[axis] = value
        self.write_axis_unlocked(axis, value)

    def write_axis_unlocked(self, axis, value):
        if axis == "x":
            self.ui.write(ecodes.EV_ABS, ecodes.ABS_X, value * AXIS_MAX)
            self.ui.write(ecodes.EV_ABS, ecodes.ABS_HAT0X, value)
        else:
            self.ui.write(ecodes.EV_ABS, ecodes.ABS_Y, value * AXIS_MAX)
            self.ui.write(ecodes.EV_ABS, ecodes.ABS_HAT0Y, value)


def sleep_when_disabled():
    log("GPIO gamepad is disabled by GPIO_GAMEPAD_ENABLED")
    while True:
        time.sleep(3600)


def main():
    config = load_config()
    if not config_bool(config, "GPIO_GAMEPAD_ENABLED", True):
        sleep_when_disabled()

    controls = configured_controls(config)
    if not controls:
        log("no GPIO controls are configured")
        return 1

    active_low = config_bool(config, "GPIO_GAMEPAD_ACTIVE_LOW", DEFAULT_ACTIVE_LOW)
    bounce_ms = config_float(config, "GPIO_GAMEPAD_BOUNCE_MS", DEFAULT_BOUNCE_MS, minimum=0.0)
    stop_event = threading.Event()

    def handle_signal(_signum, _frame):
        stop_event.set()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    gamepad = GpioGamepad(
        controls=controls,
        active_low=active_low,
        bounce_time=bounce_ms / 1000.0,
    )
    gamepad.start()

    try:
        while not stop_event.wait(1.0):
            pass
    finally:
        gamepad.stop()
        log("stopped")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        log(f"error: {exc}")
        sys.exit(1)
