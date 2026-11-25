#!/bin/bash
# Petra Clipboard - Universal Uninstaller
# Interactive menu to uninstall .deb, Flatpak, Snap, or clean AppImage data

APP_ID="io.github.gessendarien.petra-clipboard"
DEB_NAME="petra"
SNAP_NAMES=("petra-clipboard" "petra")

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}─────────────────────────────────────${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}─────────────────────────────────────${NC}"
}

clean_keyboard_shortcuts() {
    echo "Cleaning desktop keyboard shortcuts..."

    # Cinnamon
    if command -v gsettings &> /dev/null && gsettings get org.cinnamon.desktop.keybindings custom-list &>/dev/null; then
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
}

clean_user_data() {
    echo "Cleaning local configuration, cache, and autostart files..."

    local CONFIG_BASE="${XDG_CONFIG_HOME:-$HOME/.config}"
    local CACHE_BASE="${XDG_CACHE_HOME:-$HOME/.cache}"

    rm -rf "${CACHE_BASE}/petra"
    rm -rf "${CONFIG_BASE}/petra"
    rm -f "${CONFIG_BASE}/autostart/petra.desktop"
    rm -f "$HOME/.local/share/applications/${APP_ID}.desktop"

    # Remove single-instance socket if leftover
    rm -f "${XDG_RUNTIME_DIR:-/tmp}/petra-clipboard.sock"

    echo -e "${GREEN}Local cache, config, and autostart cleaned.${NC}"
}

prompt_clean_shared_data() {
    echo ""
    read -p "Also remove local config, cache, autostart, and keyboard shortcuts? (y/N): " resp
    if [[ "$resp" =~ ^[Yy]$ ]]; then
        clean_keyboard_shortcuts
        clean_user_data
    fi
}

# ─────────────────────────────────────
#  1. Debian Package (.deb)
# ─────────────────────────────────────

uninstall_deb() {
    print_header "Uninstalling Debian Package (.deb)"
    local found=false

    if command -v dpkg &> /dev/null && dpkg -s "$DEB_NAME" &> /dev/null; then
        found=true
        echo "Removing Debian package '${DEB_NAME}' (may ask for sudo password)..."
        sudo apt-get remove --purge -y "$DEB_NAME"
        echo -e "${GREEN}Debian package removed.${NC}"
    else
        echo -e "${YELLOW}Petra (.deb) is not installed.${NC}"
    fi

    if [ "$1" != "--all" ]; then
        prompt_clean_shared_data
    fi
}

# ─────────────────────────────────────
#  2. AppImage (Clean Cache & Config)
# ─────────────────────────────────────

clean_appimage() {
    print_header "Cleaning AppImage Data"
    echo -e "${YELLOW}Note: AppImage files are standalone executables — simply delete the .AppImage file manually.${NC}"
    echo "Removing AppImage cache, config, autostart, and shortcuts..."
    clean_keyboard_shortcuts
    clean_user_data
    echo -e "${GREEN}AppImage residual data cleaned.${NC}"
}

# ─────────────────────────────────────
#  3. Flatpak
# ─────────────────────────────────────

uninstall_flatpak() {
    print_header "Uninstalling Flatpak"

    if ! command -v flatpak &> /dev/null; then
        echo -e "${YELLOW}Flatpak is not installed on this system.${NC}"
        return 0
    fi

    local removed=false

    if flatpak list --user 2>/dev/null | grep -q "$APP_ID"; then
        echo "Removing user-level Flatpak (${APP_ID})..."
        flatpak uninstall --user -y "$APP_ID"
        removed=true
    fi

    if flatpak list --system 2>/dev/null | grep -q "$APP_ID"; then
        echo "Removing system-level Flatpak (${APP_ID}) (may ask for sudo password)..."
        sudo flatpak uninstall --system -y "$APP_ID"
        removed=true
    fi

    if flatpak remotes --user 2>/dev/null | grep -q "petra-local"; then
        echo "Deleting temporary 'petra-local' remote..."
        flatpak remote-delete --user petra-local
    fi

    if [ "$removed" = true ]; then
        echo -e "${GREEN}Flatpak uninstalled.${NC}"
    else
        echo -e "${YELLOW}Petra Flatpak is not installed.${NC}"
    fi

    local SANDBOX_DIR="$HOME/.var/app/${APP_ID}"
    if [ -d "$SANDBOX_DIR" ]; then
        if [ "$1" = "--all" ]; then
            rm -rf "$SANDBOX_DIR"
            echo -e "${GREEN}Removed Flatpak sandbox data (${SANDBOX_DIR}).${NC}"
        else
            echo ""
            read -p "Also delete Flatpak sandbox data (${SANDBOX_DIR})? (y/N): " resp
            if [[ "$resp" =~ ^[Yy]$ ]]; then
                rm -rf "$SANDBOX_DIR"
                echo -e "${GREEN}Flatpak sandbox data removed.${NC}"
            fi
        fi
    fi
}

# ─────────────────────────────────────
#  4. Snap
# ─────────────────────────────────────

uninstall_snap() {
    print_header "Uninstalling Snap"

    if ! command -v snap &> /dev/null; then
        echo -e "${YELLOW}Snap is not installed on this system.${NC}"
        return 0
    fi

    local removed=false
    for sname in "${SNAP_NAMES[@]}"; do
        if snap list "$sname" &> /dev/null; then
            echo "Removing Snap package '${sname}' (may ask for sudo password)..."
            sudo snap remove "$sname"
            removed=true
        fi
    done

    if [ "$removed" = true ]; then
        echo -e "${GREEN}Snap package removed.${NC}"
    else
        echo -e "${YELLOW}Petra Snap is not installed.${NC}"
    fi
}

# ─────────────────────────────────────
#  5. Reset App Data Only (Fresh Install State)
# ─────────────────────────────────────

reset_app_data() {
    print_header "Resetting App Data (Cache & Config Only)"
    echo "Resetting Petra to a fresh-install state without uninstalling packages..."
    clean_keyboard_shortcuts
    clean_user_data

    local SANDBOX_DIR="$HOME/.var/app/${APP_ID}"
    if [ -d "$SANDBOX_DIR" ]; then
        rm -rf "$SANDBOX_DIR"
        echo -e "${GREEN}Flatpak sandbox data reset (${SANDBOX_DIR}).${NC}"
    fi

    echo ""
    echo -e "${GREEN}App data reset complete! Petra will start like a fresh install.${NC}"
}

# ─────────────────────────────────────
#  6. Uninstall ALL
# ─────────────────────────────────────

uninstall_all() {
    print_header "Universal Uninstall (All Formats)"
    uninstall_deb --all
    echo ""
    uninstall_flatpak --all
    echo ""
    uninstall_snap --all
    echo ""
    clean_keyboard_shortcuts
    clean_user_data
    echo ""
    echo -e "${GREEN}Complete uninstall finished!${NC}"
    echo -e "${YELLOW}If you used an AppImage, remember to delete the .AppImage file manually.${NC}"
}

# ─────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────

clear
print_header "Petra Clipboard - Universal Uninstaller"
echo "Select what you want to remove:"
echo ""
echo "  1) Uninstall Debian Package (.deb)"
echo "  2) Clean AppImage data (cache, config & shortcuts)"
echo "  3) Uninstall Flatpak"
echo "  4) Uninstall Snap"
echo "  5) Reset app data only (cache & config — keep installed)"
echo "  6) Uninstall ALL (all formats + cache & config)"
echo "  7) Exit"
echo ""
read -p "Option [1-7]: " option

case $option in
    1) uninstall_deb ;;
    2) clean_appimage ;;
    3) uninstall_flatpak ;;
    4) uninstall_snap ;;
    5) reset_app_data ;;
    6) uninstall_all ;;
    7) echo "Exiting."; exit 0 ;;
    *)
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac
