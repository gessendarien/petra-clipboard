#!/bin/bash
# Petra Clipboard - Flatpak Manager
# Unified script to build, bundle, and install Petra

set -e

# Configuration
APP_ID="io.github.petra"
BUILD_DIR="flatpak-build"
REPO_DIR="flatpak-repo"
BUNDLE_FILE="petra.flatpak"

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

check_dependencies() {
    print_header "Checking Dependencies"

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

    # Check KDE Runtimes
    if ! flatpak info org.kde.Platform//6.7 &> /dev/null; then
        MISSING_KDE+=("org.kde.Platform//6.7")
    fi
    if ! flatpak info org.kde.Sdk//6.7 &> /dev/null; then
        MISSING_KDE+=("org.kde.Sdk//6.7")
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
             echo "Installing Flatpak runtimes..."
             flatpak install --user -y flathub "${MISSING_KDE[@]}"
        fi
        echo -e "${GREEN}Dependencies installed successfully.${NC}"
    else
        echo -e "${RED}Cannot proceed without dependencies. Exiting.${NC}"
        exit 1
    fi
}

build_app() {
    print_header "Building Petra Flatpak"
    
    # Clean build outputs only (keep .flatpak-builder cache)
    echo "Cleaning build output directory..."
    rm -rf "$BUILD_DIR" "$REPO_DIR"
    
    # Build
    # Note: --force-clean cleans the build directory ($BUILD_DIR) but keeps the cache (.flatpak-builder)
    echo "Building application..."
    flatpak-builder --user --repo="$REPO_DIR" --force-clean "$BUILD_DIR" "$APP_ID.yml"
    echo -e "${GREEN}Build complete and repository created at $REPO_DIR${NC}"
}

install_local_repo() {
    print_header "Installing from Local Repository"
    flatpak --user remote-add --no-gpg-verify --if-not-exists petra-local "$REPO_DIR"
    flatpak --user install -y --reinstall petra-local "$APP_ID"
    echo -e "${GREEN}Installed successfully! Run with: flatpak run $APP_ID${NC}"
}

create_bundle() {
    print_header "Creating Flatpak Bundle"
    flatpak build-bundle "$REPO_DIR" "$BUNDLE_FILE" "$APP_ID"
    echo -e "${GREEN}Bundle created: $BUNDLE_FILE ($(du -h "$BUNDLE_FILE" | cut -f1))${NC}"
}

install_bundle() {
    print_header "Installing Bundle"
    
    # Uninstall if exists to ensure clean install
    if flatpak list --user | grep -q "$APP_ID"; then
        echo "Removing previous installation..."
        flatpak uninstall --user -y "$APP_ID" 2>/dev/null || true
    fi

    flatpak install --user -y "$BUNDLE_FILE"
    
    # Desktop integration
    echo "Updating desktop database..."
    mkdir -p ~/.local/share/applications
    ln -sf ~/.local/share/flatpak/exports/share/applications/"$APP_ID".desktop ~/.local/share/applications/ 2>/dev/null || true
    update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
    
    echo -e "${GREEN}Installed successfully!${NC}"
}

# Main Menu
clear
print_header "Petra Clipboard Manager - Build System"
echo "Select an option:"
echo "1) Build & Install Locally (Fastest for Dev)"
echo "2) Create Bundle (.flatpak) & Install (Verify Release)"
echo "3) Create Bundle (.flatpak) Only (For Sharing)"
echo "4) Exit"
echo ""
read -p "Option [1-4]: " option

case $option in
    1)
        check_dependencies
        build_app
        install_local_repo
        ;;
    2)
        check_dependencies
        build_app
        create_bundle
        install_bundle
        ;;
    3)
        check_dependencies
        build_app
        create_bundle
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
