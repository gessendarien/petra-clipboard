#!/bin/bash

APP_ID="io.github.gessendarien.petra"
DEB_NAME="petra"
SNAP_NAME="petra"

echo "Desinstalando Petra Clipboard..."

# 1. Desinstalar el flatpak del usuario
if command -v flatpak &> /dev/null; then
    if flatpak list --user | grep -q "$APP_ID"; then
        echo "Eliminando Flatpak de usuario..."
        flatpak uninstall --user -y "$APP_ID"
    fi

    # 2. Desinstalar el flatpak del sistema (por si acaso)
    if flatpak list --system | grep -q "$APP_ID"; then
        echo "Eliminando Flatpak de sistema (puede pedir contraseña sudo)..."
        sudo flatpak uninstall --system -y "$APP_ID"
    fi

    # Eliminar el repositorio local temporal si existe
    if flatpak remotes --user | grep -q "petra-local"; then
        echo "Eliminando repositorio petra-local..."
        flatpak remote-delete --user petra-local
    fi
fi

# 3. Desinstalar versión .deb (Debian/Ubuntu/Mint)
if command -v dpkg &> /dev/null; then
    if dpkg -s "$DEB_NAME" &> /dev/null; then
        echo "Eliminando paquete Debian (.deb) (puede pedir contraseña sudo)..."
        sudo apt-get remove --purge -y "$DEB_NAME"
    fi
fi

# 4. Desinstalar versión Snap (futuro)
if command -v snap &> /dev/null; then
    if snap list "$SNAP_NAME" &> /dev/null; then
        echo "Eliminando paquete Snap (puede pedir contraseña sudo)..."
        sudo snap remove "$SNAP_NAME"
    fi
fi

# 5. Eliminar el atajo de teclado del escritorio (Cinnamon/GNOME)
echo "Limpiando atajos de teclado del sistema..."
# Cinnamon
if command -v gsettings &> /dev/null && gsettings get org.cinnamon.desktop.keybindings custom-list &>/dev/null; then
    # Find and remove the Petra Clipboard keybinding
    CUSTOM_LIST=$(gsettings get org.cinnamon.desktop.keybindings custom-list 2>/dev/null)
    # Remove all entries whose name is "Petra Clipboard"
    for key in $(gsettings get org.cinnamon.desktop.keybindings custom-list 2>/dev/null | tr -d "[]'" | tr ',' ' '); do
        PATH_KEY="/org/cinnamon/desktop/keybindings/custom-keybindings/${key}/"
        NAME=$(dconf read "${PATH_KEY}name" 2>/dev/null | tr -d "'")
        if [ "$NAME" = "Petra Clipboard" ]; then
            dconf reset -f "$PATH_KEY"
            NEW_LIST=$(gsettings get org.cinnamon.desktop.keybindings custom-list 2>/dev/null | sed "s/, '$key'//g; s/'$key', //g; s/'$key'//g")
            gsettings set org.cinnamon.desktop.keybindings custom-list "$NEW_LIST" 2>/dev/null || true
        fi
    done
fi
# GNOME
if command -v gsettings &> /dev/null && gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings &>/dev/null; then
    for path in $(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null | tr -d "[]\", " | tr "'" '\n'); do
        [ -z "$path" ] && continue
        NAME=$(dconf read "${path}name" 2>/dev/null | tr -d "'")
        if [ "$NAME" = "Petra Clipboard" ]; then
            dconf reset -f "$path"
        fi
    done
fi

# 6. Eliminar accesos directos y configuraciones locales residuales
echo "Limpiando archivos residuales locales..."
DESKTOP_FILE_LOCAL="$HOME/.local/share/applications/$APP_ID.desktop"
if [ -f "$DESKTOP_FILE_LOCAL" ]; then
    rm -f "$DESKTOP_FILE_LOCAL"
fi

# Eliminar carpeta de caché y configuración para limpiar todo completamente
rm -rf "$HOME/.cache/petra"
rm -rf "$HOME/.config/petra"

echo "¡Desinstalación completada!"
