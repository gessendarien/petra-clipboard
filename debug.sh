#!/bin/bash

echo "Petra Debug Tools"
echo "1) Launch in debug mode"
echo "2) Kill all instances"
read -p "Option: " opt

case $opt in
  1)
    cd "$(dirname "$0")"
    PETRA_DEBUG_KEYS=1 python3 src/main.py
    ;;
  2)
    echo "Closing any active instances of Petra Clipboard..."
    
    # Clean up single-instance socket
    SOCKET_PATH="${XDG_RUNTIME_DIR:-/tmp}/petra-clipboard.sock"
    if [ -S "$SOCKET_PATH" ] || [ -e "$SOCKET_PATH" ]; then
        rm -v "$SOCKET_PATH" 2>/dev/null
    fi

    # Kill processes more aggressively (-9 SIGKILL)
    # Search for various process names used in dev, snap, flatpak and appimage
    if command -v flatpak &> /dev/null; then
        flatpak kill io.github.gessendarien.petra 2>/dev/null
    fi
    pkill -9 -f -i "/snap/petra" 2>/dev/null
    pkill -9 -f -i "Petra.*AppImage" 2>/dev/null
    pkill -9 -f -i "petra-clipboard.*AppImage" 2>/dev/null
    pkill -9 -x -i "petra" 2>/dev/null
    pkill -9 -f -i "petra.*main.py" 2>/dev/null
    pkill -9 -f -i "python3.*src/main.py" 2>/dev/null
    pkill -9 -f -i "io.github.gessendarien.petra" 2>/dev/null
    
    # Extra check for any python process with main.py in the current directory subtree
    pkill -9 -f "python3.*main.py" 2>/dev/null
    
    echo "Petra Clipboard has been closed (Forcefully if necessary)."
    ;;
  *)
    echo "Invalid option"
    ;;
esac