# Matiz

A small GTK 4 / libadwaita app (and CLI) to theme a Hyprland desktop from one place:
palette and accent color, window gaps, borders, blur and translucency, animation
presets, the Waybar bar, the rofi and fuzzel menus, dunst notifications, the hyprlock
lock screen, kitty, Qt (qt5ct/qt6ct) and GTK.

Settings live in `~/.config/matiz/settings.json`. Every change is rendered into the
config files of each program and applied live (`hyprctl reload`, `SIGUSR2` to Waybar,
`dunstctl reload`, `SIGUSR1` to kitty, gsettings for GTK).

Matiz is built on top of
[avell-linux-control-center](https://github.com/Ilhe8l/avell-linux-control-center),
my fork of [LuizRojas/avell-linux-control-center](https://github.com/LuizRojas/avell-linux-control-center).

## Requirements

- Hyprland 0.56 or newer (Lua config)
- System `python3` with PyGObject, GTK 4.12+ and libadwaita 1.4+
- Optional: waybar, rofi 2.x, fuzzel, dunst, hyprlock, hyprpaper, kitty, qt5ct/qt6ct

## Install

```sh
./install.sh            # puts `matiz` in ~/.local/bin and adds the app to the menu
matiz apply             # first run: writes every generated file
```

Then make Hyprland load the generated theme by ending `~/.config/hypr/hyprland.lua` with:

```lua
if not pcall(require, "matiz") then
    hl.exec_cmd("notify-send 'Matiz' 'Theme not loaded: run matiz apply'")
end
```

Keep colors, borders, blur, animations and app opacity out of `hyprland.lua`;
Matiz owns them in `~/.config/hypr/matiz.lua`.

## Files Matiz writes

| Program | File | How |
|---|---|---|
| Hyprland | `hypr/matiz.lua` | generated |
| Waybar | `waybar/theme.css`, `position`/`height` in `waybar/config.jsonc` | generated / edited |
| rofi | `rofi/theme.rasi`, grid size and accents in `rofi/launcher.rasi` | generated / edited |
| fuzzel | `[colors]` in `fuzzel/fuzzel.ini` | edited |
| dunst | urgency sections of `dunst/dunstrc` | edited |
| hyprlock | `hypr/hyprlock.conf` | generated |
| kitty | `kitty/matiz-colors.conf`, included from `kitty.conf` | generated |
| Qt | `qt5ct/colors/Matiz.conf`, `qt6ct/colors/Matiz.conf` | generated |
| GTK | gsettings, `gtk-3.0/settings.ini`, `gtk-4.0/settings.ini` | applied |

"Edited" means only the listed keys change; the rest of the file is left alone.

## CLI

```sh
matiz                       # open the app
matiz palette gruvbox       # everforest-hard, everforest-medium, gruvbox, catppuccin-mocha,
                            # nord, tokyo-night, rose-pine, kanagawa
matiz accent aqua           # green, aqua, blue, purple, yellow, orange, red
matiz animations smooth     # hyprdots, smooth, bouncy, fast, off
matiz set window.rounding 14
matiz get bar
matiz show
matiz reset
```

## Tests

```sh
python3 -m unittest discover -s tests
```
