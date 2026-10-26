"""Color palettes. Every palette fills the same roles so templates never branch on theme."""

from dataclasses import dataclass, field

ROLES = ("bg", "bg_alt", "surface", "border", "fg", "fg_dim",
         "green", "aqua", "blue", "purple", "yellow", "orange", "red")

ACCENTS = ("green", "aqua", "blue", "purple", "yellow", "orange", "red")


@dataclass(frozen=True)
class Palette:
    id: str
    name: str
    colors: dict = field(default_factory=dict)

    def __getitem__(self, role):
        return self.colors[role]


def _p(id, name, bg, bg_alt, surface, border, fg, fg_dim,
       green, aqua, blue, purple, yellow, orange, red):
    return Palette(id, name, dict(
        bg=bg, bg_alt=bg_alt, surface=surface, border=border, fg=fg, fg_dim=fg_dim,
        green=green, aqua=aqua, blue=blue, purple=purple, yellow=yellow, orange=orange, red=red))


PALETTES = {p.id: p for p in (
    _p("everforest-hard", "Everforest Dark Hard",
       "#1e2326", "#272e33", "#2e383c", "#4f5b58", "#d3c6aa", "#859289",
       "#a7c080", "#83c092", "#7fbbb3", "#d699b6", "#dbbc7f", "#e69875", "#e67e80"),
    _p("everforest-medium", "Everforest Dark Medium",
       "#232a2e", "#2d353b", "#343f44", "#56635f", "#d3c6aa", "#859289",
       "#a7c080", "#83c092", "#7fbbb3", "#d699b6", "#dbbc7f", "#e69875", "#e67e80"),
    _p("gruvbox", "Gruvbox Dark",
       "#1d2021", "#282828", "#3c3836", "#665c54", "#ebdbb2", "#a89984",
       "#b8bb26", "#8ec07c", "#83a598", "#d3869b", "#fabd2f", "#fe8019", "#fb4934"),
    _p("catppuccin-mocha", "Catppuccin Mocha",
       "#11111b", "#1e1e2e", "#313244", "#45475a", "#cdd6f4", "#9399b2",
       "#a6e3a1", "#94e2d5", "#89b4fa", "#cba6f7", "#f9e2af", "#fab387", "#f38ba8"),
    _p("nord", "Nord",
       "#242933", "#2e3440", "#3b4252", "#4c566a", "#eceff4", "#a3abb9",
       "#a3be8c", "#8fbcbb", "#81a1c1", "#b48ead", "#ebcb8b", "#d08770", "#bf616a"),
    _p("tokyo-night", "Tokyo Night",
       "#16161e", "#1a1b26", "#24283b", "#414868", "#c0caf5", "#9aa5ce",
       "#9ece6a", "#73daca", "#7aa2f7", "#bb9af7", "#e0af68", "#ff9e64", "#f7768e"),
    _p("rose-pine", "Rosé Pine",
       "#191724", "#1f1d2e", "#26233a", "#403d52", "#e0def4", "#908caa",
       "#9ccfd8", "#9ccfd8", "#31748f", "#c4a7e7", "#f6c177", "#ebbcba", "#eb6f92"),
    _p("kanagawa", "Kanagawa",
       "#16161d", "#1f1f28", "#2a2a37", "#54546d", "#dcd7ba", "#a6a69c",
       "#98bb6c", "#7aa89f", "#7e9cd8", "#957fb8", "#e6c384", "#ffa066", "#e46876"),
)}


def hex_to_rgb(color):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def with_alpha(color, alpha):
    """'#a7c080', 0.2 -> '#a7c08033' (rofi, fuzzel and dunst take #rrggbbaa)."""
    return f"{color}{round(alpha * 255):02x}"


def rgba(color, alpha):
    """'#a7c080', 0.2 -> 'rgba(167, 192, 128, 0.2)' for GTK CSS and hyprlock."""
    r, g, b = hex_to_rgb(color)
    return f"rgba({r}, {g}, {b}, {alpha:g})"
