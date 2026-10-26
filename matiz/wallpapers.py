"""Wallpaper listing and switching, delegated to the `wallpaper` script when it is installed."""

import os
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
CACHE = Path(os.environ.get("XDG_CACHE_HOME", HOME / ".cache")) / "hypr-wall"
EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def wallpaper_dir():
    return Path(os.environ.get("MATIZ_WALLPAPERS", HOME / "Pictures/Wallpapers"))


def list_wallpapers():
    root = wallpaper_dir()
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.suffix.lower() in EXTENSIONS and p.is_file())


def current():
    link = CACHE / "current"
    return link.resolve() if link.exists() else None


def set_wallpaper(path):
    script = shutil.which("wallpaper") or str(HOME / ".local/bin/wallpaper")
    if Path(script).exists():
        subprocess.Popen([script, "set", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif shutil.which("hyprctl"):
        subprocess.Popen(["hyprctl", "hyprpaper", "wallpaper", f", {path}, cover"],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
