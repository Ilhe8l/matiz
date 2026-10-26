import argparse
import json
import sys

from . import apply, settings as store
from .animations import PRESETS
from .palettes import ACCENTS, PALETTES


def main(argv=None):
    parser = argparse.ArgumentParser(prog="matiz", description="Personalização do desktop Hyprland.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("gui", help="abre o app (padrão)")
    sub.add_parser("apply", help="gera e aplica tudo a partir das configurações salvas")
    sub.add_parser("show", help="mostra as configurações atuais")
    p_get = sub.add_parser("get", help="lê um valor, ex.: window.rounding")
    p_get.add_argument("key")
    p_set = sub.add_parser("set", help="altera um valor e aplica, ex.: window.rounding 14")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_palette = sub.add_parser("palette", help="troca a paleta: " + ", ".join(PALETTES))
    p_palette.add_argument("id", choices=list(PALETTES))
    p_accent = sub.add_parser("accent", help="troca a cor de destaque")
    p_accent.add_argument("color", choices=ACCENTS)
    p_anim = sub.add_parser("animations", help="troca o preset de animações")
    p_anim.add_argument("preset", choices=list(PRESETS))
    sub.add_parser("reset", help="volta tudo ao padrão")

    args = parser.parse_args(argv)
    command = args.command or "gui"

    if command == "gui":
        from .ui import run
        return run()

    current = store.load()
    if command == "show":
        print(json.dumps(current, indent=2, ensure_ascii=False))
        return 0
    if command == "get":
        print(json.dumps(store.get(current, args.key), ensure_ascii=False))
        return 0

    if command == "set":
        try:
            store.put(current, args.key, args.value)
        except KeyError:
            print(f"chave desconhecida: {args.key}", file=sys.stderr)
            return 1
    elif command == "palette":
        current["palette"] = args.id
    elif command == "accent":
        current["accent"] = args.color
    elif command == "animations":
        current["animations"]["preset"] = args.preset
    elif command == "reset":
        current = store.merge(store.DEFAULTS, {})

    store.save(current)
    changed = apply.apply(current)
    print("aplicado: " + (", ".join(changed) if changed else "nada mudou"))
    return 0
