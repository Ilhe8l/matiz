import json
import unittest

from matiz import animations, render, settings
from matiz.palettes import PALETTES, ROLES, with_alpha


def defaults(**overrides):
    return settings.merge(settings.DEFAULTS, overrides)


class PaletteTest(unittest.TestCase):
    def test_every_palette_fills_every_role(self):
        for palette in PALETTES.values():
            self.assertEqual(set(palette.colors), set(ROLES), palette.id)

    def test_alpha_is_two_hex_digits(self):
        self.assertEqual(with_alpha("#a7c080", 85 / 255), "#a7c08055")
        self.assertEqual(with_alpha("#a7c080", 1), "#a7c080ff")


class SettingsTest(unittest.TestCase):
    def test_put_keeps_the_stored_type(self):
        s = defaults()
        settings.put(s, "window.rounding", "14.0")
        settings.put(s, "blur.enabled", "false")
        settings.put(s, "opacity.apps", "0.7")
        self.assertEqual(s["window"]["rounding"], 14)
        self.assertIs(s["blur"]["enabled"], False)
        self.assertEqual(s["opacity"]["apps"], 0.7)

    def test_unknown_stored_keys_do_not_drop_defaults(self):
        s = settings.merge(settings.DEFAULTS, {"window": {"rounding": 4}})
        self.assertEqual(s["window"]["rounding"], 4)
        self.assertEqual(s["window"]["gaps_in"], settings.DEFAULTS["window"]["gaps_in"])


class RenderTest(unittest.TestCase):
    def test_hyprland_uses_settings_and_accent(self):
        s = defaults(accent="blue", window={"rounding": 17})
        lua = render.hyprland(s)
        self.assertIn("rounding = 17", lua)
        self.assertIn(PALETTES["everforest-hard"]["blue"].lstrip("#"), lua)

    def test_translucency_can_be_turned_off(self):
        on = render.hyprland(defaults())
        off = render.hyprland(defaults(opacity={"translucent_apps": False}))
        self.assertIn("matiz-translucent-1", on)
        self.assertNotIn("matiz-translucent", off)

    def test_animations_off_disables_them(self):
        self.assertIn("enabled = false", animations.to_lua("off"))

    def test_animation_speed_scales(self):
        lua = animations.to_lua("hyprdots", speed=2)
        self.assertIn('leaf = "windows", enabled = true, speed = 12,', lua)

    def test_waybar_config_keeps_comment_and_other_keys(self):
        current = '// header\n{"position": "top", "height": 31, "modules-left": ["clock"]}\n'
        out = render.waybar_config(defaults(bar={"position": "bottom", "height": 28}), current)
        self.assertTrue(out.startswith("// header\n"))
        data = json.loads(out.split("\n", 1)[1])
        self.assertEqual((data["position"], data["height"]), ("bottom", 28))
        self.assertEqual(data["modules-left"], ["clock"])

    def test_fuzzel_only_touches_known_color_keys(self):
        current = "[main]\nfont=Inter\n[colors]\nbackground=000000ff\nunknown=123\n[border]\nwidth=1\n"
        out = render.fuzzel(defaults(), current)
        self.assertIn("font=Inter", out)
        self.assertIn("unknown=123", out)
        self.assertNotIn("background=000000ff", out)

    def test_rofi_launcher_is_stable_across_runs(self):
        current = "window { border-color: #a7c08055; }\nelement selected { border-color: #a7c080aa; }\nlistview { columns: 5; lines: 3; }\n"
        s = defaults(accent="red", launcher={"columns": 6})
        once = render.rofi_launcher(s, current)
        self.assertEqual(once, render.rofi_launcher(s, once))
        self.assertIn("columns: 6;", once)

    def test_lock_screen_never_has_an_empty_cmd_label(self):
        lock = render.hyprlock(defaults(lock={"name": "Ana"}))
        self.assertIn('echo " "', lock)
        self.assertIn("$name = Ana", lock)
        self.assertIn("text = A\n", lock)


if __name__ == "__main__":
    unittest.main()
