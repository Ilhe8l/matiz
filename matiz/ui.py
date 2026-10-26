import os
import subprocess
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango

from . import apply, render, settings as store, wallpapers
from .animations import PRESETS
from .palettes import ACCENTS, PALETTES, hex_to_rgb

APP_ID = "io.github.ilhe8l.Matiz"
APPLY_DELAY_MS = 350

ACCENT_NAMES = {"green": "Verde", "aqua": "Água", "blue": "Azul", "purple": "Roxo",
                "yellow": "Amarelo", "orange": "Laranja", "red": "Vermelho"}


def swatch(colors, size=18, gap=4):
    """A strip of rounded color squares."""
    area = Gtk.DrawingArea()
    area.set_content_width(len(colors) * (size + gap))
    area.set_content_height(size)
    area.set_valign(Gtk.Align.CENTER)

    def draw(_area, cr, _w, _h):
        for i, color in enumerate(colors):
            r, g, b = (v / 255 for v in hex_to_rgb(color))
            x, radius = i * (size + gap), 5
            cr.new_sub_path()
            cr.arc(x + size - radius, radius, radius, -1.5708, 0)
            cr.arc(x + size - radius, size - radius, radius, 0, 1.5708)
            cr.arc(x + radius, size - radius, radius, 1.5708, 3.1416)
            cr.arc(x + radius, radius, radius, 3.1416, 4.7124)
            cr.close_path()
            cr.set_source_rgb(r, g, b)
            cr.fill()

    area.set_draw_func(draw)
    return area


def dot(color, size=30):
    """A filled circle, used inside the accent buttons."""
    area = Gtk.DrawingArea(content_width=size, content_height=size,
                           halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)

    def draw(_area, cr, w, h):
        r, g, b = (v / 255 for v in hex_to_rgb(color))
        cr.arc(w / 2, h / 2, min(w, h) / 2, 0, 6.2832)
        cr.set_source_rgb(r, g, b)
        cr.fill()

    area.set_draw_func(draw)
    return area


def list_themes(kind):
    """kind: 'gtk', 'icons' or 'cursors'."""
    home = Path.home()
    if kind == "gtk":
        roots = [home / ".themes", home / ".local/share/themes", Path("/usr/share/themes")]
        test = lambda d: (d / "gtk-3.0").is_dir()
    else:
        roots = [home / ".icons", home / ".local/share/icons", Path("/usr/share/icons")]
        if kind == "cursors":
            test = lambda d: (d / "cursors").is_dir()
        else:
            test = lambda d: (d / "index.theme").exists() and not (d / "cursors").is_dir() and d.name != "default"
    names = set()
    for root in roots:
        if root.is_dir():
            names.update(d.name for d in root.iterdir() if d.is_dir() and test(d))
    return sorted(names, key=str.lower)


class MatizWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Matiz")
        self.set_default_size(980, 700)
        self.settings = store.load()
        self._pending = None
        self._loading = True
        self.css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), self.css,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        self._refresh_css()

        self.toasts = Adw.ToastOverlay()
        self.set_content(self.toasts)

        split = Adw.NavigationSplitView()
        self.toasts.set_child(split)

        self.stack = Gtk.Stack(transition_type=Gtk.StackTransitionType.CROSSFADE)
        pages = [
            ("theme", "Tema", "applications-graphics-symbolic", self.page_theme()),
            ("wallpaper", "Papel de parede", "image-x-generic-symbolic", self.page_wallpaper()),
            ("windows", "Janelas", "window-new-symbolic", self.page_windows()),
            ("animations", "Animações", "media-playlist-shuffle-symbolic", self.page_animations()),
            ("bar", "Barra e menus", "view-app-grid-symbolic", self.page_bar()),
            ("appearance", "Ícones e fontes", "preferences-desktop-font-symbolic", self.page_appearance()),
            ("lock", "Tela de bloqueio", "system-lock-screen-symbolic", self.page_lock()),
            ("terminal", "Terminal", "utilities-terminal-symbolic", self.page_terminal()),
        ]

        sidebar_list = Gtk.ListBox(css_classes=["navigation-sidebar"])
        for key, title, icon, page in pages:
            self.stack.add_titled(page, key, title)
            row = Gtk.Box(spacing=12, margin_top=8, margin_bottom=8, margin_start=6)
            row.append(Gtk.Image.new_from_icon_name(icon))
            row.append(Gtk.Label(label=title, xalign=0))
            sidebar_list.append(Gtk.ListBoxRow(child=row, name=key))

        content_header = Adw.HeaderBar()
        reset = Gtk.Button(icon_name="edit-undo-symbolic", tooltip_text="Restaurar o padrão")
        reset.connect("clicked", self.on_reset)
        content_header.pack_end(reset)
        content_view = Adw.ToolbarView()
        content_view.add_top_bar(content_header)
        content_view.set_content(self.stack)
        self.content_page = Adw.NavigationPage(child=content_view, title="Tema")

        sidebar_header = Adw.HeaderBar()
        sidebar_view = Adw.ToolbarView()
        sidebar_view.add_top_bar(sidebar_header)
        sidebar_view.set_content(Gtk.ScrolledWindow(child=sidebar_list))
        split.set_sidebar(Adw.NavigationPage(child=sidebar_view, title="Matiz"))
        split.set_content(self.content_page)

        def on_row(_list, row):
            if row:
                self.stack.set_visible_child_name(row.get_name())
                self.content_page.set_title(self.stack.get_page(self.stack.get_visible_child()).get_title())
                split.set_show_content(True)

        sidebar_list.connect("row-selected", on_row)
        sidebar_list.select_row(sidebar_list.get_row_at_index(0))
        self._loading = False

    # Saving and applying

    def change(self, key, value):
        if self._loading:
            return
        store.put(self.settings, key, value)
        if self._pending:
            GLib.source_remove(self._pending)
        self._pending = GLib.timeout_add(APPLY_DELAY_MS, self._apply_now)

    def _apply_now(self):
        self._pending = None
        store.save(self.settings)
        snapshot = store.merge(self.settings, {})
        threading.Thread(target=apply.apply, args=(snapshot,), daemon=True).start()
        self._refresh_css()
        return False

    def _refresh_css(self):
        self.css.load_from_string(render.app_css(self.settings) + """
            .swatch-button { padding: 3px; min-width: 36px; min-height: 36px; border-radius: 999px; }
            .swatch-button.selected { box-shadow: 0 0 0 3px @window_fg_color; }
            .wall { border-radius: 14px; }
            flowboxchild:selected .wall { box-shadow: 0 0 0 3px @accent_color; }
        """)

    def on_reset(self, _button):
        dialog = Adw.MessageDialog(transient_for=self, heading="Restaurar o padrão?",
                                   body="Todas as personalizações do Matiz voltam aos valores iniciais.")
        dialog.add_response("cancel", "Cancelar")
        dialog.add_response("reset", "Restaurar")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)

        def on_response(_d, response):
            if response == "reset":
                self.settings = store.merge(store.DEFAULTS, {})
                self._apply_now()
                self.toasts.add_toast(Adw.Toast(title="Padrão restaurado; reabra o Matiz para ver os valores"))

        dialog.connect("response", on_response)
        dialog.present()

    # Row helpers bound to a settings key

    def spin(self, title, key, lo, hi, step=1, digits=0, subtitle=None):
        row = Adw.SpinRow.new_with_range(lo, hi, step)
        row.set_title(title)
        if subtitle:
            row.set_subtitle(subtitle)
        row.set_digits(digits)
        row.set_value(store.get(self.settings, key))
        row.connect("notify::value", lambda r, _p: self.change(key, r.get_value()))
        return row

    def switch(self, title, key, subtitle=None):
        row = Adw.SwitchRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        row.set_active(store.get(self.settings, key))
        row.connect("notify::active", lambda r, _p: self.change(key, r.get_active()))
        return row

    def slider(self, title, key, lo, hi, step=0.05, subtitle=None, percent=True):
        row = Adw.ActionRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, step)
        scale.set_value(store.get(self.settings, key))
        scale.set_hexpand(True)
        scale.set_size_request(260, -1)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        if percent:
            scale.set_format_value_func(lambda _s, v: f"{round(v * 100)}%")
        else:
            scale.set_format_value_func(lambda _s, v: f"{v:.2f}×")
        scale.connect("value-changed", lambda s: self.change(key, round(s.get_value(), 2)))
        row.add_suffix(scale)
        return row

    def combo(self, title, key, options, labels=None):
        labels = labels or options
        row = Adw.ComboRow(title=title, model=Gtk.StringList.new(labels))
        current = store.get(self.settings, key)
        if current in options:
            row.set_selected(options.index(current))
        row.connect("notify::selected", lambda r, _p: self.change(key, options[r.get_selected()]))
        return row

    # Pages

    def page_theme(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Paleta", description="Cores usadas em todo o desktop")
        page.add(group)
        first = None
        for pid, palette in PALETTES.items():
            row = Adw.ActionRow(title=palette.name)
            check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
            if first is None:
                first = check
            else:
                check.set_group(first)
            check.set_active(self.settings["palette"] == pid)
            check.connect("toggled", lambda c, pid=pid: c.get_active() and self.change("palette", pid))
            row.add_prefix(check)
            row.set_activatable_widget(check)
            row.add_suffix(swatch([palette[r] for r in ("bg", "surface", "fg") + ACCENTS]))
            group.add(row)

        accent_group = Adw.PreferencesGroup(title="Cor de destaque",
                                            description="Bordas, seleção, workspace ativa, botões")
        page.add(accent_group)
        box = Gtk.Box(spacing=14, margin_top=6, margin_bottom=6, halign=Gtk.Align.START)
        self.accent_buttons = {}
        palette = PALETTES[self.settings["palette"]]
        for accent in ACCENTS:
            button = Gtk.Button(css_classes=["swatch-button", "circular", "flat"],
                                tooltip_text=ACCENT_NAMES[accent], halign=Gtk.Align.CENTER)
            button.set_child(dot(palette[accent]))
            button.connect("clicked", self.on_accent, accent)
            self.accent_buttons[accent] = button
            box.append(button)
        self._mark_accent()
        accent_group.add(box)
        return page

    def on_accent(self, _button, accent):
        self.change("accent", accent)
        self._mark_accent()

    def _mark_accent(self):
        for name, button in self.accent_buttons.items():
            if name == self.settings["accent"]:
                button.add_css_class("selected")
            else:
                button.remove_css_class("selected")

    def page_wallpaper(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Papel de parede",
                                     description=f"Imagens em {wallpapers.wallpaper_dir()}")
        page.add(group)
        flow = Gtk.FlowBox(selection_mode=Gtk.SelectionMode.SINGLE, max_children_per_line=4,
                           min_children_per_line=2, column_spacing=14, row_spacing=14, homogeneous=True)
        current = wallpapers.current()
        self._wall_paths = wallpapers.list_wallpapers()
        for i, path in enumerate(self._wall_paths):
            picture = Gtk.Picture(css_classes=["wall"], content_fit=Gtk.ContentFit.COVER,
                                  can_shrink=True, width_request=190, height_request=120)
            picture.set_overflow(Gtk.Overflow.HIDDEN)
            picture.set_tooltip_text(path.stem)
            flow.append(picture)
            self._load_thumb(picture, path)
            if current and path == current:
                flow.select_child(flow.get_child_at_index(i))
        flow.connect("child-activated", lambda _f, child: self._on_wall(child.get_index()))
        group.add(flow)
        return page

    def _load_thumb(self, picture, path):
        def work():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(str(path), 380, -1, True)
            except GLib.Error:
                return
            GLib.idle_add(lambda: picture.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf)) and False)
        threading.Thread(target=work, daemon=True).start()

    def _on_wall(self, index):
        path = self._wall_paths[index]
        wallpapers.set_wallpaper(path)
        self.toasts.add_toast(Adw.Toast(title=f"Papel de parede: {path.stem}", timeout=2))

    def page_windows(self):
        page = Adw.PreferencesPage()
        layout = Adw.PreferencesGroup(title="Layout")
        layout.add(self.spin("Espaço entre janelas", "window.gaps_in", 0, 30))
        layout.add(self.spin("Margem da tela", "window.gaps_out", 0, 60))
        layout.add(self.spin("Arredondamento", "window.rounding", 0, 30))
        page.add(layout)

        border = Adw.PreferencesGroup(title="Borda")
        border.add(self.spin("Espessura", "window.border_size", 0, 8))
        border.add(self.switch("Gradiente", "window.gradient_border",
                               "Mistura a cor de destaque com uma segunda cor"))
        border.add(self.switch("Sombra", "window.shadow"))
        page.add(border)

        blur = Adw.PreferencesGroup(title="Desfoque (blur)")
        blur.add(self.switch("Ativado", "blur.enabled", "Atrás de janelas translúcidas, barra e menus"))
        blur.add(self.spin("Tamanho", "blur.size", 1, 20))
        blur.add(self.spin("Passadas", "blur.passes", 1, 6, subtitle="Mais passadas, mais suave e mais pesado"))
        page.add(blur)

        opacity = Adw.PreferencesGroup(title="Transparência")
        opacity.add(self.switch("Apps translúcidos", "opacity.translucent_apps",
                                "VS Code, Thunar, navegadores, Steam e ferramentas"))
        opacity.add(self.slider("Editores e arquivos", "opacity.apps", 0.5, 1.0))
        opacity.add(self.slider("Navegadores", "opacity.browsers", 0.5, 1.0))
        opacity.add(self.slider("Janelas sem foco", "opacity.inactive_dim", 0.5, 1.0,
                                subtitle="Vale para todas as janelas"))
        page.add(opacity)
        return page

    def page_animations(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Estilo")
        page.add(group)
        first = None
        for pid, preset in PRESETS.items():
            row = Adw.ActionRow(title=preset["name"], subtitle=preset["description"])
            check = Gtk.CheckButton(valign=Gtk.Align.CENTER)
            if first is None:
                first = check
            else:
                check.set_group(first)
            check.set_active(self.settings["animations"]["preset"] == pid)
            check.connect("toggled", lambda c, pid=pid: c.get_active() and self.change("animations.preset", pid))
            row.add_prefix(check)
            row.set_activatable_widget(check)
            group.add(row)
        speed = Adw.PreferencesGroup(title="Duração")
        speed.add(self.slider("Multiplicador", "animations.speed", 0.4, 2.5, step=0.1, percent=False,
                              subtitle="Menor é mais rápido"))
        page.add(speed)
        return page

    def page_bar(self):
        page = Adw.PreferencesPage()
        bar = Adw.PreferencesGroup(title="Barra (Waybar)")
        bar.add(self.combo("Posição", "bar.position", ["top", "bottom"], ["Em cima", "Embaixo"]))
        bar.add(self.spin("Altura", "bar.height", 24, 48))
        bar.add(self.spin("Tamanho da fonte", "bar.font_size", 9, 18))
        bar.add(self.slider("Opacidade das pílulas", "bar.opacity", 0.3, 1.0))
        page.add(bar)

        launcher = Adw.PreferencesGroup(title="Menu de apps (Super+A)")
        launcher.add(self.spin("Colunas", "launcher.columns", 3, 8))
        launcher.add(self.spin("Linhas", "launcher.rows", 2, 6))
        launcher.add(self.slider("Opacidade dos menus", "launcher.opacity", 0.4, 1.0,
                                 subtitle="Vale também para os menus do fuzzel (Super+V e outros)"))
        test = Adw.ActionRow(title="Abrir o menu para testar", activatable=True)
        test.add_suffix(Gtk.Image.new_from_icon_name("go-next-symbolic"))
        test.connect("activated", lambda _r: subprocess.Popen([str(Path.home() / ".local/bin/app-launcher")]))
        launcher.add(test)
        page.add(launcher)
        return page

    def page_appearance(self):
        page = Adw.PreferencesPage()
        themes = Adw.PreferencesGroup(title="Temas")
        themes.add(self.combo("Tema GTK", "appearance.gtk_theme", list_themes("gtk")))
        themes.add(self.combo("Ícones", "appearance.icon_theme", list_themes("icons")))
        themes.add(self.combo("Cursor", "appearance.cursor_theme", list_themes("cursors")))
        themes.add(self.spin("Tamanho do cursor", "appearance.cursor_size", 16, 64, step=4))
        page.add(themes)

        fonts = Adw.PreferencesGroup(title="Fontes")
        for title, key in (("Interface", "appearance.ui_font"), ("Monoespaçada", "appearance.mono_font")):
            row = Adw.ActionRow(title=title)
            button = Gtk.FontDialogButton(dialog=Gtk.FontDialog(), valign=Gtk.Align.CENTER)
            button.set_font_desc(Pango.FontDescription.from_string(store.get(self.settings, key)))
            button.connect("notify::font-desc",
                           lambda b, _p, key=key: self.change(key, b.get_font_desc().to_string()))
            row.add_suffix(button)
            fonts.add(row)
        page.add(fonts)
        return page

    def page_lock(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Tela de bloqueio")
        name = Adw.EntryRow(title="Nome na saudação")
        name.set_text(self.settings["lock"]["name"])
        name.connect("changed", lambda e: self.change("lock.name", e.get_text()))
        group.add(name)
        group.add(self.spin("Desfoque do fundo", "lock.blur_passes", 0, 6))
        group.add(self.slider("Brilho do fundo", "lock.brightness", 0.2, 1.0))
        test = Adw.ActionRow(title="Bloquear agora para ver", subtitle="Use sua senha para voltar",
                             activatable=True)
        test.add_suffix(Gtk.Image.new_from_icon_name("system-lock-screen-symbolic"))
        test.connect("activated", lambda _r: subprocess.Popen(["loginctl", "lock-session"]))
        group.add(test)
        page.add(group)
        return page

    def page_terminal(self):
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup(title="Kitty", description="Aplicado ao vivo nas janelas abertas")
        group.add(self.switch("Usar as cores da paleta", "terminal.colors"))
        group.add(self.slider("Opacidade do fundo", "terminal.opacity", 0.4, 1.0))
        page.add(group)
        return page


class MatizApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        Adw.StyleManager.get_default().set_color_scheme(Adw.ColorScheme.FORCE_DARK)

    def do_activate(self):
        window = self.get_active_window() or MatizWindow(self)
        window.present()


def run():
    return MatizApp().run([])
