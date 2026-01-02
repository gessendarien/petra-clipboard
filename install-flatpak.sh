#!/bin/bash
# Install Petra Flatpak

set -e

FLATPAK_FILE="petra.flatpak"
APP_ID="io.github.petra"

echo "─────────────────────────────────────"
echo "  Installing Petra Flatpak"
echo "─────────────────────────────────────"

if [ ! -f "$FLATPAK_FILE" ]; then
    echo "Error: $FLATPAK_FILE not found"
    echo "Run ./make-flatpak.sh first to create it"
    exit 1
fi

# Uninstall if already installed
if flatpak list --user | grep -q "$APP_ID"; then
    echo "Removing previous installation..."
    flatpak uninstall --user -y "$APP_ID" 2>/dev/null || true
fi

echo "Installing $FLATPAK_FILE..."
flatpak install --user -y "$FLATPAK_FILE"

# Update desktop database for menu integration
mkdir -p ~/.local/share/applications
ln -sf ~/.local/share/flatpak/exports/share/applications/io.github.petra.desktop ~/.local/share/applications/ 2>/dev/null || true
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo ""
echo "─────────────────────────────────────"
echo "  Done!"
echo "─────────────────────────────────────"
echo ""
echo "Run with: flatpak run $APP_ID"
