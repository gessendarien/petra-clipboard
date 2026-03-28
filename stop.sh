#!/bin/bash

echo "Closing any active instances of Petra Clipboard..."

# 1. Close via Flatpak
if command -v flatpak &> /dev/null; then
    flatpak kill io.github.gessendarien.petra 2>/dev/null
fi

# 2. Close Snap processes
# Snaps run binaries within their virtual namespace (/snap/petra/...)
pkill -f -i "/snap/petra" 2>/dev/null

# 3. Close AppImages
# Searches specifically for AppImages executed with "Petra" in the name
pkill -f -i "Petra.*AppImage" 2>/dev/null
pkill -f -i "petra-clipboard.*AppImage" 2>/dev/null

# 4. Close .deb packages and native Python runs
# Exact match for the installed executable (e.g. in /usr/bin)
pkill -x -i "petra" 2>/dev/null

# Match for scripts executed using Python (e.g. python3 src/main.py)
pkill -f -i "petra.*main.py" 2>/dev/null

# Match the application's desktop ID
pkill -f -i "io.github.gessendarien.petra" 2>/dev/null

echo "Petra Clipboard has been closed."
