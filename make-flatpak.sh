#!/bin/bash
# Create a distributable .flatpak file

set -e

APP_ID="io.github.petra"
OUTPUT="petra.flatpak"

# Spinner function
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while ps -p $pid > /dev/null 2>&1; do
        for i in $(seq 0 9); do
            printf "\r  ${spinstr:$i:1} Creating bundle..."
            sleep $delay
        done
    done
    printf "\r                              \r"
}

echo "─────────────────────────────────────"
echo "  Creating Petra Bundle"
echo "─────────────────────────────────────"

if [ ! -d "flatpak-repo" ]; then
    echo "Error: Repository does not exist. Run ./build-flatpak.sh first"
    exit 1
fi

# Run build-bundle in background with spinner
flatpak build-bundle flatpak-repo "$OUTPUT" "$APP_ID" > /dev/null 2>&1 &
spinner $!
wait $!

echo "─────────────────────────────────────"
echo "  Done!"
echo "─────────────────────────────────────"
echo ""
echo "File created: $OUTPUT"
echo "Size: $(du -h "$OUTPUT" | cut -f1)"
echo ""
echo "To install on another machine:"
echo "  flatpak install $OUTPUT"
