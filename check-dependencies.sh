#!/bin/bash
# Check and install dependencies for building Petra Flatpak

set -e

# List of required dependencies
dependencies=(
    "flatpak-builder"
    "qt6-base-dev"
)

# KDE runtime and SDK
kde_dependencies=(
    "org.kde.Platform//6.7"
    "org.kde.Sdk//6.7"
)

# Function to check if a command exists
check_command() {
    command -v "$1" &> /dev/null
}

# Iterate over dependencies and check if they are installed
for dep in "${dependencies[@]}"; do
    echo "Checking for $dep..."
    if check_command "$dep"; then
        echo "$dep is already installed."
    else
        echo "$dep is not installed. Installing..."
        if [[ "$dep" == "flatpak-builder" ]]; then
            sudo apt install -y flatpak-builder
        elif [[ "$dep" == "qt6-base-dev" ]]; then
            sudo apt install -y qt6-base-dev
        else
            echo "Unknown dependency: $dep"
        fi
    fi
    echo ""
done

# Check KDE runtime and SDK
for kde_dep in "${kde_dependencies[@]}"; do
    echo "Checking for $kde_dep..."
    if flatpak info "$kde_dep" &> /dev/null; then
        echo "$kde_dep is already installed."
    else
        echo "$kde_dep is not installed. Installing..."
        flatpak install -y flathub "$kde_dep"
    fi
    echo ""
done

echo "All dependencies are installed. You are ready to build Petra!"