"""Writes the rendered files and reloads whatever reads them."""

import os
import shutil
import subprocess
from pathlib import Path

from . import render

HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config"))

# (name, path, render function, needs the current file text)
TARGETS = [
    ("hyprland", CONFIG / "hypr/matiz.lua", render.hyprland, False),
    ("waybar-theme", CONFIG / "waybar/theme.css", render.waybar_theme, False),
    ("waybar-config", CONFIG / "waybar/config.jsonc", render.waybar_config, True),
    ("rofi-theme", CONFIG / "rofi/theme.rasi", render.rofi_theme, False),
    ("rofi-launcher", CONFIG / "rofi/launcher.rasi", render.rofi_launcher, True),
    ("fuzzel", CONFIG / "fuzzel/fuzzel.ini", render.fuzzel, True),
    ("dunst", CONFIG / "dunst/dunstrc", render.dunst, True),
    ("hyprlock", CONFIG / "hypr/hyprlock.conf", render.hyprlock, False),
    ("lock-info", CONFIG / "hypr/lock-info", render.lock_info, False),
    ("kitty", CONFIG / "kitty/matiz-colors.conf", render.kitty, False),
    ("qt6", CONFIG / "qt6ct/colors/Matiz.conf", render.qt_palette, False),
    ("qt5", CONFIG / "qt5ct/colors/Matiz.conf", render.qt_palette, False),
]


def _write(path, text):
    """Atomic write (Hyprland and waybar watch some of these files); True if it changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == text:
        return False
    tmp = path.with_name(path.name + ".matiz-tmp")
    tmp.write_text(text)
    if text.startswith("#!"):
        tmp.chmod(0o755)
    tmp.replace(path)
    return True


def render_all(settings):
    changed = []
    for name, path, fn, needs_current in TARGETS:
        if name == "kitty" and not settings["terminal"]["colors"]:
            continue
        if needs_current:
            if not path.exists():
                continue
            text = fn(settings, path.read_text())
        else:
            text = fn(settings)
        if _write(path, text):
            changed.append(name)
    _ensure_includes()
    return changed


def _ensure_includes():
    """One-time hooks so the main configs pick up the generated files."""
    kitty = CONFIG / "kitty/kitty.conf"
    if kitty.exists() and "matiz-colors.conf" not in kitty.read_text():
        with kitty.open("a") as f:
            f.write("\n# Colors and opacity from Matiz\ninclude matiz-colors.conf\n")

    for version in ("qt5ct", "qt6ct"):
        conf = CONFIG / version / f"{version}.conf"
        if not conf.exists():
            continue
        text = conf.read_text()
        target = f"color_scheme_path={CONFIG / version / 'colors/Matiz.conf'}"
        lines = [target if l.startswith("color_scheme_path=") else l for l in text.splitlines()]
        if target not in lines:
            lines.insert(1, target)
        _write(conf, "\n".join(lines) + "\n")


def _run(*cmd):
    if shutil.which(cmd[0]):
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)


def apply_appearance(settings):
    a = settings["appearance"]
    iface = "org.gnome.desktop.interface"
    for key, value in (("gtk-theme", a["gtk_theme"]), ("icon-theme", a["icon_theme"]),
                       ("cursor-theme", a["cursor_theme"]), ("font-name", a["ui_font"]),
                       ("monospace-font-name", a["mono_font"]), ("color-scheme", "prefer-dark")):
        _run("gsettings", "set", iface, key, value)
    _run("gsettings", "set", iface, "cursor-size", str(a["cursor_size"]))

    for version in ("3.0", "4.0"):
        ini = CONFIG / f"gtk-{version}/settings.ini"
        _write(ini, "[Settings]\n"
                    "gtk-application-prefer-dark-theme=1\n"
                    f"gtk-theme-name={a['gtk_theme']}\n"
                    f"gtk-icon-theme-name={a['icon_theme']}\n"
                    f"gtk-cursor-theme-name={a['cursor_theme']}\n"
                    f"gtk-cursor-theme-size={a['cursor_size']}\n"
                    f"gtk-font-name={a['ui_font']}\n")
    if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
        _run("hyprctl", "setcursor", a["cursor_theme"], str(a["cursor_size"]))


def reload(changed):
    in_hyprland = bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"))
    if in_hyprland and "hyprland" in changed:
        _run("hyprctl", "reload")
    if "waybar-config" in changed or "waybar-theme" in changed:
        _run("pkill", "-SIGUSR2", "-x", "waybar")   # reloads both config and style
    if "dunst" in changed:
        _run("dunstctl", "reload")
    if "kitty" in changed:
        _run("pkill", "-SIGUSR1", "-x", "kitty")


def apply(settings):
    changed = render_all(settings)
    apply_appearance(settings)
    reload(changed)
    return changed
