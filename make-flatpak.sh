#!/bin/bash
# Create a distributable .flatpak file

set -e

APP_ID="io.github.petra"
OUTPUT="petra.flatpak"

echo "─────────────────────────────────────"
echo "  Creating Petra Bundle"
echo "─────────────────────────────────────"

if [ ! -d "flatpak-repo" ]; then
    echo "Error: Repository does not exist. Run ./build-flatpak.sh first"
    exit 1
fi

flatpak build-bundle flatpak-repo "$OUTPUT" "$APP_ID"

echo ""
echo "─────────────────────────────────────"
echo "  Done!"
echo "─────────────────────────────────────"
echo ""
echo "File created: $OUTPUT"
echo "Size: $(du -h "$OUTPUT" | cut -f1)"
echo ""
echo "To install on another machine:"
echo "  flatpak install $OUTPUT"
