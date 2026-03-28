#!/bin/bash
# Petra Clipboard - Build Manager
# Unified script to build Flatpak, AppImage, and install Petra

set -e

# Configuration
APP_ID="io.github.gessendarien.petra"
APP_NAME="Petra"
APP_VERSION=$(cat global-version.txt)
BUILD_DIR="flatpak-build"
REPO_DIR="flatpak-repo"
OUTPUT_DIR="output"
BUNDLE_FILE="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}.flatpak"
DEB_FILE="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-all.deb"
APPIMAGE_FILE="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
APPIMAGETOOL_URL="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
PYTHON_STANDALONE_URL="https://github.com/indygreg/python-build-standalone/releases/download/20240224/cpython-3.11.8+20240224-x86_64-unknown-linux-gnu-install_only.tar.gz"
APPIMAGETOOL_CACHE=".cache/appimagetool"
PYTHON_CACHE=".cache/cpython-standalone.tar.gz"

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

ensure_output_dir() {
    mkdir -p "$OUTPUT_DIR"
}

# ─────────────────────────────────────
#  Flatpak Functions
# ─────────────────────────────────────

check_flatpak_dependencies() {
    print_header "Checking Flatpak Dependencies"

    MISSING_DEPS=()
    MISSING_KDE=()

    # Check system tools
    if ! command -v flatpak-builder &> /dev/null; then
        MISSING_DEPS+=("flatpak-builder")
    fi

    if command -v dpkg &> /dev/null; then
        if ! dpkg -s qt6-base-dev &> /dev/null; then
             MISSING_DEPS+=("qt6-base-dev")
        fi
    fi

    # Check KDE Runtimes and BaseApp
    if ! flatpak info org.kde.Platform//6.9 &> /dev/null; then
        MISSING_KDE+=("org.kde.Platform//6.9")
    fi
    if ! flatpak info org.kde.Sdk//6.9 &> /dev/null; then
        MISSING_KDE+=("org.kde.Sdk//6.9")
    fi
    if ! flatpak info com.riverbankcomputing.PyQt.BaseApp//6.9 &> /dev/null; then
        MISSING_KDE+=("com.riverbankcomputing.PyQt.BaseApp//6.9")
    fi

    if [ ${#MISSING_DEPS[@]} -eq 0 ] && [ ${#MISSING_KDE[@]} -eq 0 ]; then
        echo -e "${GREEN}All dependencies are installed.${NC}"
        return 0
    fi

    echo -e "${YELLOW}The following dependencies are missing:${NC}"
    for dep in "${MISSING_DEPS[@]}"; do echo " - System: $dep"; done
    for dep in "${MISSING_KDE[@]}"; do echo " - Flatpak: $dep"; done
    echo ""
    
    echo -e "${YELLOW}They are required to proceed.${NC}"
    read -p "Do you want to install them now? (y/N): " response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
            echo "Installing system dependencies (requires sudo)..."
            sudo apt update && sudo apt install -y "${MISSING_DEPS[@]}"
        fi
        
        if [ ${#MISSING_KDE[@]} -gt 0 ]; then
             echo "Ensuring Flathub remote is configured..."
             flatpak remote-add --user --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
             echo "Installing Flatpak runtimes..."
             flatpak install --user -y flathub "${MISSING_KDE[@]}"
        fi
        echo -e "${GREEN}Dependencies installed successfully.${NC}"
    else
        echo -e "${RED}Cannot proceed without dependencies. Exiting.${NC}"
        exit 1
    fi
}

build_flatpak() {
    print_header "Building Petra Flatpak"
    
    # Clean build outputs only (keep .flatpak-builder cache)
    echo "Cleaning build output directory..."
    rm -rf "$BUILD_DIR" "$REPO_DIR"
    
    # Build
    echo "Building application..."
    flatpak-builder --user --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$APP_ID.yml"
    echo -e "${GREEN}Build complete and repository created at $REPO_DIR${NC}"
}
create_flatpak_bundle() {
    print_header "Creating Flatpak Bundle"
    ensure_output_dir
    flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID"
    echo -e "${GREEN}Bundle created: $BUNDLE_FILE ($(du -h "$BUNDLE_FILE" | cut -f1))${NC}"
}
# ─────────────────────────────────────
#  AppImage Functions
# ─────────────────────────────────────

get_appimagetool() {
    # Return path to appimagetool, downloading if needed
    if [ -x "$APPIMAGETOOL_CACHE" ]; then
        echo "$APPIMAGETOOL_CACHE"
        return 0
    fi

    echo "Downloading appimagetool..." >&2
    mkdir -p "$(dirname "$APPIMAGETOOL_CACHE")"
    if ! curl -L -o "$APPIMAGETOOL_CACHE" "$APPIMAGETOOL_URL" 2>/dev/null; then
        if ! wget -O "$APPIMAGETOOL_CACHE" "$APPIMAGETOOL_URL" 2>/dev/null; then
            echo -e "${RED}Failed to download appimagetool. Install curl or wget.${NC}" >&2
            return 1
        fi
    fi
    chmod +x "$APPIMAGETOOL_CACHE"
    echo "$APPIMAGETOOL_CACHE"
}

create_appimage() {
    print_header "Creating Standalone AppImage"
    ensure_output_dir

    # Check host dependencies required for building (not running)
    for cmd in curl tar gzip; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}Command '$cmd' is required to build the AppImage but not found.${NC}"
            exit 1
        fi
    done

    # Get appimagetool
    TOOL=$(get_appimagetool) || exit 1
    echo -e "${GREEN}Using appimagetool: $TOOL${NC}"

    # Download Portable Python if not cached
    if [ ! -f "$PYTHON_CACHE" ]; then
        echo "Downloading portable Python (this may take a minute)..."
        mkdir -p "$(dirname "$PYTHON_CACHE")"
        if ! curl -L -o "$PYTHON_CACHE" "$PYTHON_STANDALONE_URL"; then
            echo -e "${RED}Failed to download portable Python.${NC}"
            exit 1
        fi
    fi

    # Create temporary AppDir
    APPDIR=$(mktemp -d)/AppDir
    mkdir -p "$APPDIR"

    echo "Building AppDir structure..."

    # ── opt/python (Standalone Python environment) ──
    echo "Extracting portable Python into AppDir..."
    mkdir -p "$APPDIR/opt/python"
    tar -xf "$PYTHON_CACHE" -C "$APPDIR/opt/python" --strip-components=1

    # ── Install PyQt6 into the portable Python ──
    echo "Installing PyQt6 into portable environment..."
    PYTHON_EXEC="$APPDIR/opt/python/bin/python3"
    
    # Ensure pip is up to date and install PyQt6
    "$PYTHON_EXEC" -m pip install --upgrade pip --no-warn-script-location >/dev/null
    if ! "$PYTHON_EXEC" -m pip install PyQt6 --no-warn-script-location >/dev/null; then
         echo -e "${RED}Failed to install PyQt6 within the portable environment.${NC}"
         exit 1
    fi
    
    # Clean up pip cache to save space
    rm -rf "$APPDIR/opt/python/lib/python3.11/site-packages/pip"
    rm -rf "$APPDIR/opt/python/lib/python3.11/site-packages/setuptools"
    find "$APPDIR/opt/python" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # ── usr/share/petra (application files) ──
    APP_DEST="$APPDIR/usr/share/petra"
    mkdir -p "$APP_DEST"
    cp -r src icons "$APP_DEST/"
    cp global-version.txt "$APP_DEST/"

    # ── usr/share/applications ──
    mkdir -p "$APPDIR/usr/share/applications"
    cp "$APP_ID.desktop" "$APPDIR/usr/share/applications/"

    # ── usr/share/metainfo ──
    mkdir -p "$APPDIR/usr/share/metainfo"
    cp "$APP_ID.metainfo.xml" "$APPDIR/usr/share/metainfo/"

    # ── usr/share/icons (hicolor) ──
    for size in 16 32 48 64 128 256 512; do
        ICON_DIR="$APPDIR/usr/share/icons/hicolor/${size}x${size}/apps"
        mkdir -p "$ICON_DIR"
        if [ -f "icons/petra-${size}.png" ]; then
            cp "icons/petra-${size}.png" "$ICON_DIR/$APP_ID.png"
        fi
    done

    # ── Root .desktop and icon (required by AppImage spec) ──
    cp "$APP_ID.desktop" "$APPDIR/"
    if [ -f "icons/petra-256.png" ]; then
        cp "icons/petra-256.png" "$APPDIR/$APP_ID.png"
        # Symlink .DirIcon
        ln -sf "$APP_ID.png" "$APPDIR/.DirIcon"
    fi

    # ── Bundle host tools (libxcb-cursor0 for Qt, xdotool & libxdo3 for pasting) ──
    echo "Bundling required system libraries and tools..."
    mkdir -p "$APPDIR/usr/lib" "$APPDIR/usr/bin"
    XCB_TEMP=$(mktemp -d)
    pushd "$XCB_TEMP" >/dev/null
    if apt-get download libxcb-cursor0 xdotool libxdo3 2>/dev/null; then
        for deb in *.deb; do dpkg -x "$deb" .; done
        cp usr/lib/*/lib*.so* "$APPDIR/usr/lib/" 2>/dev/null || true
        cp usr/bin/* "$APPDIR/usr/bin/" 2>/dev/null || true
    else
        echo -e "${YELLOW}Warning: Could not download required system dependencies to bundle.${NC}"
    fi
    popd >/dev/null
    rm -rf "$XCB_TEMP"

    # ── AppRun ──
    cat > "$APPDIR/AppRun" << 'APPRUN_EOF'
#!/bin/bash
# Petra Clipboard - Standalone AppImage Entry Point

HERE="$(dirname "$(readlink -f "$0")")"
APP_DIR="$HERE/usr/share/petra"
PYTHON="$HERE/opt/python/bin/python3"

# Set library path so PyQt6 finds Qt libraries properly within the AppImage
export LD_LIBRARY_PATH="$HERE/usr/lib:$HERE/opt/python/lib:$LD_LIBRARY_PATH"
export PATH="$HERE/usr/bin:$PATH"
export QT_QPA_PLATFORM_PLUGIN_PATH="$HERE/opt/python/lib/python3.11/site-packages/PyQt6/Qt6/plugins/platforms"

cd "$APP_DIR/src"
exec "$PYTHON" main.py "$@"
APPRUN_EOF
    chmod +x "$APPDIR/AppRun"

    # ── Build AppImage ──
    echo "Packaging AppImage..."
    ARCH=x86_64 "$TOOL" "$APPDIR" "$APPIMAGE_FILE" 2>&1 | tail -5

    # Cleanup
    rm -rf "$(dirname "$APPDIR")"

    if [ -f "$APPIMAGE_FILE" ]; then
        chmod +x "$APPIMAGE_FILE"
        echo ""
        echo -e "${GREEN}AppImage created: $APPIMAGE_FILE ($(du -h "$APPIMAGE_FILE" | cut -f1))${NC}"
        echo -e "${GREEN}This is a fully self-contained AppImage. It requires no Python installation on the host.${NC}"
    else
        echo -e "${RED}Failed to create AppImage.${NC}"
        exit 1
    fi
}

# ─────────────────────────────────────
#  Debian Package Functions
# ─────────────────────────────────────

create_debian_package() {
    print_header "Creating Debian Package (.deb)"
    ensure_output_dir

    if ! command -v dpkg-deb &> /dev/null; then
        echo -e "${RED}dpkg-deb is required but not found. Install dpkg.${NC}"
        exit 1
    fi

    local DEB_BUILD_DIR="$(mktemp -d)/${APP_NAME,,}_${APP_VERSION}_all"
    echo "Building Debian package structure in $DEB_BUILD_DIR..."

    # ── Create layout ──
    mkdir -p "$DEB_BUILD_DIR/DEBIAN"
    mkdir -p "$DEB_BUILD_DIR/opt/petra"
    mkdir -p "$DEB_BUILD_DIR/usr/bin"
    mkdir -p "$DEB_BUILD_DIR/usr/share/applications"
    mkdir -p "$DEB_BUILD_DIR/usr/share/metainfo"

    # ── DEBIAN/control ──
    cat > "$DEB_BUILD_DIR/DEBIAN/control" << EOF
Package: ${APP_NAME,,}
Version: ${APP_VERSION}
Architecture: all
Maintainer: Gessén Darién <casscastudios@gmail.com>
Depends: python3, python3-pyqt6, libxcb-cursor0, xdotool, wl-clipboard
Section: utils
Priority: optional
Description: Modern clipboard manager with emoji support
 Petra is a clipboard manager indicating your history and emojis.
 Support for pinning and quick shortcuts.
EOF

    # ── Copy Application Files ──
    cp -r src icons "$DEB_BUILD_DIR/opt/petra/"
    cp global-version.txt "$DEB_BUILD_DIR/opt/petra/"
    
    # Clean pycache if exists
    find "$DEB_BUILD_DIR/opt/petra" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

    # ── Executable Wrapper ──
    cat > "$DEB_BUILD_DIR/usr/bin/petra" << 'EOF'
#!/bin/bash
cd /opt/petra/src
exec python3 main.py "$@"
EOF
    chmod +x "$DEB_BUILD_DIR/usr/bin/petra"

    # ── Desktop Integration ──
    cp "$APP_ID.desktop" "$DEB_BUILD_DIR/usr/share/applications/"
    cp "$APP_ID.metainfo.xml" "$DEB_BUILD_DIR/usr/share/metainfo/"

    # Icons
    for size in 16 32 48 64 128 256 512; do
        ICON_DIR="$DEB_BUILD_DIR/usr/share/icons/hicolor/${size}x${size}/apps"
        mkdir -p "$ICON_DIR"
        if [ -f "icons/petra-${size}.png" ]; then
            cp "icons/petra-${size}.png" "$ICON_DIR/$APP_ID.png"
            cp "icons/petra-${size}.png" "$ICON_DIR/${APP_NAME,,}.png" # Also add simple name just in case
        fi
    done

    # ── Build Package ──
    echo "Packaging Debian bundle..."
    dpkg-deb --build "$DEB_BUILD_DIR" "$DEB_FILE"

    rm -rf "$(dirname "$DEB_BUILD_DIR")"

    if [ -f "$DEB_FILE" ]; then
        echo ""
        echo -e "${GREEN}Debian package created: $DEB_FILE ($(du -h "$DEB_FILE" | cut -f1))${NC}"
        echo -e "${YELLOW}To install, users can run: sudo dpkg -i $DEB_FILE${NC}"
    else
        echo -e "${RED}Failed to create Debian package.${NC}"
        exit 1
    fi
}

# ─────────────────────────────────────
#  Main Menu
# ─────────────────────────────────────

clear
print_header "Petra Clipboard Manager - Build System"
echo "Select an option:"
echo "1) Create Debian Package (.deb)"
echo "2) Create AppImage"
echo "3) Create Flatpak Bundle (.flatpak)"
echo "4) Exit"
echo ""
read -p "Option [1-4]: " option

case $option in
    1)
        create_debian_package
        ;;
    2)
        create_appimage
        ;;
    3)
        check_flatpak_dependencies
        build_flatpak
        create_flatpak_bundle
        ;;
    4)
        echo "Exiting."
        exit 0
        ;;
    *)
        echo "Invalid option."
        exit 1
        ;;
esac

