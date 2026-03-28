#!/bin/bash

APP_ID="io.github.gessendarien.petra"
DEB_NAME="petra"
SNAP_NAME="petra"

echo "Uninstalling Petra Clipboard..."

# 1. Uninstall user-level flatpak
if command -v flatpak &> /dev/null; then
    if flatpak list --user | grep -q "$APP_ID"; then
        echo "Removing user-level Flatpak..."
        flatpak uninstall --user -y "$APP_ID"
    fi

    # 2. Uninstall system-level flatpak (just in case)
    if flatpak list --system | grep -q "$APP_ID"; then
        echo "Removing system-level Flatpak (may ask for sudo password)..."
        sudo flatpak uninstall --system -y "$APP_ID"
    fi

    # Delete local temporary repository if it exists
    if flatpak remotes --user | grep -q "petra-local"; then
        echo "Deleting petra-local remote repository..."
        flatpak remote-delete --user petra-local
    fi
fi

# 3. Uninstall .deb version (Debian/Ubuntu/Mint)
if command -v dpkg &> /dev/null; then
    if dpkg -s "$DEB_NAME" &> /dev/null; then
        echo "Removing Debian package (.deb) (may ask for sudo password)..."
        sudo apt-get remove --purge -y "$DEB_NAME"
    fi
fi

# 4. Uninstall Snap version
if command -v snap &> /dev/null; then
    if snap list "$SNAP_NAME" &> /dev/null; then
        echo "Removing Snap package (may ask for sudo password)..."
        sudo snap remove "$SNAP_NAME"
    fi
fi

# 5. Remove desktop keyboard shortcuts (Cinnamon/GNOME)
echo "Cleaning system keyboard shortcuts..."
# For Cinnamon
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
# For GNOME
if command -v gsettings &> /dev/null && gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings &>/dev/null; then
    for path in $(gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings 2>/dev/null | tr -d "[]\", " | tr "'" '\n'); do
        [ -z "$path" ] && continue
        NAME=$(dconf read "${path}name" 2>/dev/null | tr -d "'")
        if [ "$NAME" = "Petra Clipboard" ]; then
            dconf reset -f "$path"
        fi
    done
fi

# 6. Remove residual local shortcuts and configurations
echo "Cleaning local residual files..."
DESKTOP_FILE_LOCAL="$HOME/.local/share/applications/$APP_ID.desktop"
if [ -f "$DESKTOP_FILE_LOCAL" ]; then
    rm -f "$DESKTOP_FILE_LOCAL"
fi

# Delete cache and configuration folders for a complete cleanup
rm -rf "$HOME/.cache/petra"
rm -rf "$HOME/.config/petra"

echo "Uninstall completed!"
