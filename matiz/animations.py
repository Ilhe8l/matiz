"""Animation presets rendered as Hyprland Lua. Speeds are Hyprland's (deciseconds, lower is faster)."""

PRESETS = {
    "hyprdots": {
        "name": "HyprDots",
        "description": "Janelas deslizam com um leve quique; borda gira ao focar",
        "curves": {
            "wind": (0.05, 0.9, 0.1, 1.05),
            "winIn": (0.1, 1.1, 0.1, 1.1),
            "winOut": (0.3, -0.3, 0, 1),
            "liner": (1, 1, 1, 1),
            "popOut": (0.4, 0, 1, 0.6),
        },
        "animations": [
            ("windows", 6, "wind", "slide"),
            ("windowsIn", 6, "winIn", "slide"),
            ("windowsOut", 5, "winOut", "slide"),
            ("windowsMove", 5, "wind", "slide"),
            ("border", 1, "liner", None),
            ("borderangle", 30, "liner", "once"),
            ("fade", 10, "default", None),
            ("workspaces", 5, "wind", None),
            ("specialWorkspace", 5, "wind", "slidevert"),
            ("layersIn", 3, "wind", "popin 88%"),
            ("layersOut", 2, "popOut", "popin 92%"),
            ("fadeLayersIn", 2, "default", None),
            ("fadeLayersOut", 2, "default", None),
        ],
    },
    "smooth": {
        "name": "Suave",
        "description": "Janelas crescem a partir do centro, sem quique",
        "curves": {
            "easeOutQuint": (0.23, 1, 0.32, 1),
            "easeInOut": (0.65, 0.05, 0.36, 1),
            "linear": (0, 0, 1, 1),
        },
        "animations": [
            ("windows", 5, "easeOutQuint", "popin 85%"),
            ("windowsOut", 3, "easeInOut", "popin 85%"),
            ("windowsMove", 4, "easeOutQuint", None),
            ("border", 5, "easeOutQuint", None),
            ("fade", 4, "easeOutQuint", None),
            ("workspaces", 5, "easeOutQuint", "slide"),
            ("specialWorkspace", 5, "easeOutQuint", "slidevert"),
            ("layersIn", 4, "easeOutQuint", "popin 90%"),
            ("layersOut", 2, "linear", "fade"),
        ],
    },
    "bouncy": {
        "name": "Elástico",
        "description": "Bastante quique, para quem gosta de movimento",
        "curves": {
            "overshot": (0.13, 0.99, 0.29, 1.1),
            "snap": (0.2, 1.4, 0.4, 1),
        },
        "animations": [
            ("windows", 6, "overshot", "popin 70%"),
            ("windowsOut", 4, "overshot", "popin 70%"),
            ("windowsMove", 6, "snap", None),
            ("border", 8, "default", None),
            ("fade", 6, "default", None),
            ("workspaces", 6, "overshot", "slide"),
            ("specialWorkspace", 6, "overshot", "slidevert"),
            ("layersIn", 5, "snap", "popin 80%"),
            ("layersOut", 3, "default", "fade"),
        ],
    },
    "fast": {
        "name": "Rápido",
        "description": "Transições curtas, quase instantâneas",
        "curves": {
            "quick": (0.15, 0, 0.1, 1),
        },
        "animations": [
            ("windows", 2, "quick", "popin 90%"),
            ("windowsOut", 2, "quick", "popin 90%"),
            ("border", 2, "quick", None),
            ("fade", 2, "quick", None),
            ("workspaces", 2, "quick", "slide"),
            ("layers", 2, "quick", "fade"),
        ],
    },
    "off": {
        "name": "Desligado",
        "description": "Sem animações",
        "curves": {},
        "animations": [],
    },
}


def to_lua(preset_id, speed=1.0):
    preset = PRESETS.get(preset_id, PRESETS["hyprdots"])
    if not preset["animations"]:
        return "hl.config({ animations = { enabled = false } })\n"

    lines = ["hl.config({ animations = { enabled = true } })"]
    for name, (x1, y1, x2, y2) in preset["curves"].items():
        lines.append(f'hl.curve("{name}", {{ type = "bezier", points = {{ {{{x1}, {y1}}}, {{{x2}, {y2}}} }} }})')
    for leaf, base_speed, curve, style in preset["animations"]:
        value = max(0.5, round(base_speed * speed, 2))
        style_part = f', style = "{style}"' if style else ""
        lines.append(f'hl.animation({{ leaf = "{leaf}", enabled = true, speed = {value:g}, bezier = "{curve}"{style_part} }})')
    return "\n".join(lines) + "\n"
