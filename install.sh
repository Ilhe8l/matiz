#!/bin/sh
# Installs the `matiz` command and the app launcher entry for the current user.
# Uses the system python3, which carries PyGObject, GTK 4 and libadwaita.
set -e
here=$(cd "$(dirname "$0")" && pwd)
bin=${XDG_BIN_HOME:-$HOME/.local/bin}
apps=${XDG_DATA_HOME:-$HOME/.local/share}/applications
mkdir -p "$bin" "$apps"

cat > "$bin/matiz" <<SCRIPT
#!/bin/sh
PYTHONPATH="$here\${PYTHONPATH:+:\$PYTHONPATH}" exec /usr/bin/python3 -m matiz "\$@"
SCRIPT
chmod +x "$bin/matiz"

sed "s|@BIN@|$bin|" "$here/data/io.github.ilhe8l.Matiz.desktop" > "$apps/io.github.ilhe8l.Matiz.desktop"
echo "Instalado: $bin/matiz"
