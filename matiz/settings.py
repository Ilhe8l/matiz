"""User settings: a nested dict stored as JSON, merged over the defaults on load."""

import copy
import json
import os
import pwd
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
SETTINGS_FILE = CONFIG_DIR / "matiz" / "settings.json"


def _display_name():
    """First field of the account's GECOS ("Full Name,,,"), falling back to the login."""
    entry = pwd.getpwuid(os.getuid())
    return entry.pw_gecos.split(",")[0].strip() or entry.pw_name


DEFAULTS = {
    "palette": "everforest-hard",
    "accent": "green",
    "window": {
        "gaps_in": 3,
        "gaps_out": 8,
        "border_size": 2,
        "rounding": 10,
        "gradient_border": True,
        "shadow": False,
    },
    "blur": {
        "enabled": True,
        "size": 6,
        "passes": 3,
    },
    "opacity": {
        "translucent_apps": True,
        "apps": 0.80,
        "browsers": 0.90,
        "inactive_dim": 1.0,
    },
    "animations": {
        "preset": "hyprdots",
        "speed": 1.0,
    },
    "bar": {
        "position": "top",
        "height": 31,
        "font_size": 12,
        "opacity": 0.92,
    },
    "launcher": {
        "columns": 5,
        "rows": 3,
        "opacity": 0.85,
    },
    "appearance": {
        "gtk_theme": "Everforest-Dark",
        "icon_theme": "Tela-circle-green",
        "cursor_theme": "catppuccin-mocha-green-cursors",
        "cursor_size": 24,
        "ui_font": "Inter 11",
        "mono_font": "JetBrainsMono Nerd Font 11",
    },
    "lock": {
        "name": _display_name(),
        "blur_passes": 3,
        "brightness": 0.55,
    },
    "terminal": {
        "colors": True,
        "opacity": 0.78,
    },
}


def merge(base, override):
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge(out[key], value)
        else:
            out[key] = value
    return out


def load(path=SETTINGS_FILE):
    try:
        stored = json.loads(Path(path).read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        stored = {}
    return merge(DEFAULTS, stored)


def save(settings, path=SETTINGS_FILE):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def get(settings, dotted):
    node = settings
    for part in dotted.split("."):
        node = node[part]
    return node


def put(settings, dotted, value):
    *parents, last = dotted.split(".")
    node = settings
    for part in parents:
        node = node[part]
    current = node.get(last)
    if isinstance(current, bool):
        value = value if isinstance(value, bool) else str(value).lower() in ("1", "true", "yes", "on", "sim")
    elif isinstance(current, int) and not isinstance(value, bool):
        value = int(float(value))
    elif isinstance(current, float):
        value = float(value)
    node[last] = value
    return settings
