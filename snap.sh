#!/bin/bash
# Petra Clipboard - Snap Manager

set -e

APP_NAME="Petra"
SNAP_NAME="petra-clipboard"
APP_VERSION=$(cat global-version.txt)
OUTPUT_DIR="output"
SNAP_FILE="${OUTPUT_DIR}/${APP_NAME}-${APP_VERSION}-amd64.snap"

# ANSI Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}─────────────────────────────────────${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}─────────────────────────────────────${NC}"
}

ensure_output_dir() {
    mkdir -p "$OUTPUT_DIR"
}

check_snapcraft() {
    if ! command -v snapcraft &> /dev/null; then
        echo -e "${RED}snapcraft is not installed.${NC}"
        read -p "Install it now? (y/N): " response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            sudo snap install snapcraft --classic
        else
            echo -e "${RED}Cannot continue without snapcraft.${NC}"
            exit 1
        fi
    fi
}

check_snap_file() {
    if [ ! -f "$SNAP_FILE" ]; then
        echo -e "${RED}File not found: $SNAP_FILE${NC}"
        echo -e "${YELLOW}Build the package first using option 1.${NC}"
        exit 1
    fi
}

# ─────────────────────────────────────
#  1. Build
# ─────────────────────────────────────

build_snap() {
    print_header "Building Petra Snap v${APP_VERSION}"
    check_snapcraft
    ensure_output_dir

    # Create snap/local/ if it doesn't exist
    mkdir -p snap/local

    # Create the launcher
    cat > snap/local/petra << 'EOF'
#!/bin/bash
cd $SNAP/usr/share/petra/src
exec python3 main.py "$@"
EOF
    chmod +x snap/local/petra
    echo -e "${GREEN}Launcher created at snap/local/petra${NC}"

    # Build
    echo "Running snapcraft..."
    snapcraft pack

    # Move generated .snap to output/
    GENERATED=$(ls -t *.snap 2>/dev/null | head -1)
    if [ -n "$GENERATED" ]; then
        mv "$GENERATED" "$SNAP_FILE"
        echo ""
        echo -e "${GREEN}Snap created: $SNAP_FILE ($(du -h "$SNAP_FILE" | cut -f1))${NC}"
    else
        echo -e "${RED}No .snap file was generated.${NC}"
        exit 1
    fi
}

# ─────────────────────────────────────
#  2. Install locally
# ─────────────────────────────────────

install_snap() {
    print_header "Installing Petra Snap locally"
    check_snap_file

    echo "Installing $SNAP_FILE in devmode..."
    sudo snap install --devmode "$SNAP_FILE"

    echo ""
    echo -e "${GREEN}Petra installed successfully.${NC}"
    echo -e "${YELLOW}Run it with: ${SNAP_NAME}${NC}"
}

# ─────────────────────────────────────
#  3. Uninstall
# ─────────────────────────────────────

uninstall_snap() {
    print_header "Uninstalling Petra Snap"

    if snap list "$SNAP_NAME" &> /dev/null; then
        sudo snap remove "$SNAP_NAME"
        echo -e "${GREEN}Petra uninstalled successfully.${NC}"
    else
        echo -e "${YELLOW}Petra is not installed as a Snap.${NC}"
    fi
}

# ─────────────────────────────────────
#  4. Publish to Snap Store
# ─────────────────────────────────────

publish_snap() {
    print_header "Publish to Snap Store"
    check_snap_file
    check_snapcraft

    # Login if not authenticated
    if ! snapcraft whoami &> /dev/null; then
        echo "Logging in to Snapcraft..."
        snapcraft login
    fi

    echo "Select a release channel:"
    echo "  1) edge      (unstable, automatic builds)"
    echo "  2) beta      (testing with selected users)"
    echo "  3) candidate (release candidate)"
    echo "  4) stable    (production)"
    echo ""
    read -p "Channel [1-4]: " channel_opt

    case $channel_opt in
        1) CHANNEL="edge" ;;
        2) CHANNEL="beta" ;;
        3) CHANNEL="candidate" ;;
        4) CHANNEL="stable" ;;
        *)
            echo -e "${RED}Invalid option.${NC}"
            exit 1
            ;;
    esac

    echo ""
    # Register the snap name (safe to run even if already registered)
    echo "Registering snap name (safe if already registered)..."
    snapcraft register "$SNAP_NAME" || true

    echo ""
    echo -e "${YELLOW}Uploading $SNAP_FILE to channel '$CHANNEL'...${NC}"
    snapcraft upload "$SNAP_FILE" --release="$CHANNEL"

    echo ""
    echo -e "${GREEN}Published to channel '$CHANNEL' successfully.${NC}"
    echo -e "${GREEN}Visit: https://snapcraft.io/${SNAP_NAME}${NC}"
}

# ─────────────────────────────────────
#  5. Clean build artifacts
# ─────────────────────────────────────

clean_snap() {
    print_header "Cleaning build artifacts"

    # Clean snapcraft cache
    snapcraft clean 2>/dev/null && echo -e "${GREEN}Snapcraft cache cleaned.${NC}" || true

    # Clean build directories
    rm -rf parts/ prime/ stage/ *.snap
    echo -e "${GREEN}Build directories removed (parts/, prime/, stage/).${NC}"

    # Ask before deleting the output .snap
    if [ -f "$SNAP_FILE" ]; then
        echo ""
        read -p "Also delete $SNAP_FILE from output/? (y/N): " response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            rm -f "$SNAP_FILE"
            echo -e "${GREEN}Removed: $SNAP_FILE${NC}"
        else
            echo -e "${YELLOW}Kept: $SNAP_FILE${NC}"
        fi
    fi
}

# ─────────────────────────────────────
#  Main menu
# ─────────────────────────────────────

clear
print_header "Petra Clipboard - Snap Manager v${APP_VERSION}"
echo "Select an option:"
echo ""
echo "  1) Build Snap (.snap in output/)"
echo "  2) Install locally (devmode)"
echo "  3) Uninstall"
echo "  4) Publish to Snap Store"
echo "  5) Clean build artifacts"
echo "  6) Exit"
echo ""
read -p "Option [1-6]: " option

case $option in
    1) build_snap ;;
    2) install_snap ;;
    3) uninstall_snap ;;
    4) publish_snap ;;
    5) clean_snap ;;
    6) echo "Exiting."; exit 0 ;;
    *)
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac
