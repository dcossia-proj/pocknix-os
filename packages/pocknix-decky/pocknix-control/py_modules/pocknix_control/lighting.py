import re

from .system import run_cmd

# stick-led-color (devices/sm8550/packages/pocknix-bsp-sm8550) - hardware-gated
# by /sys/class/leds/l:r1, not by board. Ported from armada's lighting.py (this
# fork's sibling project): pocknix-decky-loader.service runs as root, so this
# calls the script directly rather than through armada's `.privileged` helper
# indirection (which existed for a different, unprivileged decky setup there).
STICK_LED_SCRIPT = "/usr/bin/stick-led-color"
STICK_LED_MODES = {"static", "breathing", "battery", "battery-breathing", "rainbow", "chase", "alternating", "reactive", "multidot", "ambilight"}
STICK_LED_PARAMS = ("speed", "intensity", "size")
FLASH_BUTTONS = (
    "south", "east", "north", "west",
    "l1", "r1", "l3", "r3", "l4", "r4",
    "start", "select",
    "dpad_up", "dpad_down", "dpad_left", "dpad_right",
    "other",
)
DEFAULT_COLOR = "0050FF"
DEFAULT_MODE = "static"
DEFAULT_SCREEN_LINK = False


def stick_led_supported():
    from pathlib import Path

    return Path("/sys/class/leds/l:r1").exists()


def _default_state(supported):
    return {
        "supported": supported,
        "mode": DEFAULT_MODE,
        "color": DEFAULT_COLOR,
        "screenLink": DEFAULT_SCREEN_LINK,
        "params": {},
        "flashColors": {},
    }


def _parse_state(out):
    mode, color, screen_link, params, flash_colors = DEFAULT_MODE, DEFAULT_COLOR, DEFAULT_SCREEN_LINK, {}, {}
    for line in out.splitlines():
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if key == "mode" and value in STICK_LED_MODES:
            mode = value
        elif key == "color" and re.fullmatch(r"[0-9A-Fa-f]{6}", value or ""):
            color = value
        elif key == "screen_link":
            screen_link = value == "1"
        elif key.startswith("flash_") and key[len("flash_"):] in FLASH_BUTTONS:
            if re.fullmatch(r"[0-9A-Fa-f]{6}", value or ""):
                flash_colors[key[len("flash_"):]] = value.upper()
        elif "_" in key and key.split("_", 1)[0] in STICK_LED_PARAMS:
            try:
                params[key] = float(value)
            except ValueError:
                pass
    return {
        "supported": True,
        "mode": mode,
        "color": color,
        "screenLink": screen_link,
        "params": params,
        "flashColors": flash_colors,
    }


def stick_led_state():
    if not stick_led_supported():
        return _default_state(False)
    proc = run_cmd([STICK_LED_SCRIPT, "get"], timeout=5)
    if proc is None or proc.returncode != 0:
        return _default_state(True)
    return _parse_state(proc.stdout or "")


def _run_or_raise(args, timeout=5):
    proc = run_cmd([STICK_LED_SCRIPT, *args], timeout=timeout)
    if proc is None:
        raise RuntimeError("stick-led-color failed to spawn")
    if proc.returncode != 0:
        raise RuntimeError(f"stick-led-color failed (rc={proc.returncode}): {(proc.stderr or '').strip()[:300]}")


def set_stick_led_color(value):
    value = str(value).lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise ValueError("invalid color")
    _run_or_raise(["set", value.upper()])
    return stick_led_state()


def set_stick_led_mode(mode):
    if mode not in STICK_LED_MODES:
        raise ValueError("invalid stick led mode")
    _run_or_raise(["set-mode", mode])
    return stick_led_state()


def set_stick_led_screen_link(enabled):
    _run_or_raise(["set-screen-link", "on" if enabled else "off"])
    return stick_led_state()


def set_stick_led_param(param, mode, value):
    if param not in STICK_LED_PARAMS:
        raise ValueError("invalid stick led param")
    _run_or_raise(["set-param", param, mode, str(float(value))])
    return stick_led_state()


def set_stick_led_flash_color(button, value):
    if button not in FLASH_BUTTONS:
        raise ValueError("invalid flash button")
    value = str(value).lstrip("#")
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", value):
        raise ValueError("invalid color")
    _run_or_raise(["set-flash-color", button, value.upper()])
    return stick_led_state()
