#!/bin/bash
# Build and test Petra Flatpak

set -e

APP_ID="io.github.petra"
BUILD_DIR="flatpak-build"
REPO_DIR="flatpak-repo"

echo "─────────────────────────────────────"
echo "  Building Petra Flatpak"
echo "─────────────────────────────────────"

# Check if flatpak-builder is installed
if ! command -v flatpak-builder &> /dev/null; then
    echo "Error: flatpak-builder is not installed"
    echo "Install with: sudo apt install flatpak-builder"
    exit 1
fi

# Install KDE runtime and SDK if not installed
echo "Checking KDE runtime..."
flatpak install --user -y flathub org.kde.Platform//6.7 org.kde.Sdk//6.7 2>/dev/null || true

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf "$BUILD_DIR" "$REPO_DIR" .flatpak-builder

# Build the flatpak
echo "Building (this may take several minutes the first time)..."
flatpak-builder --user --force-clean "$BUILD_DIR" "$APP_ID.yml"

# Create local repository
echo "Creating local repository..."
flatpak-builder --user --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$APP_ID.yml"

# Install locally for testing
echo "Installing locally..."
flatpak --user remote-add --no-gpg-verify --if-not-exists petra-local "$REPO_DIR"
flatpak --user install -y --reinstall petra-local "$APP_ID"

echo ""
echo "─────────────────────────────────────"
echo "  Done!"
echo "─────────────────────────────────────"
echo ""
echo "Useful commands:"
echo "  Run:        flatpak run $APP_ID"
echo "  Uninstall:  flatpak --user uninstall $APP_ID"
echo "  View logs:  flatpak run $APP_ID 2>&1"
echo ""
echo "Generated files:"
echo "  - $BUILD_DIR/     (temporary build)"
echo "  - $REPO_DIR/      (local repository)"
echo "  - .flatpak-builder/ (cache de build)"
