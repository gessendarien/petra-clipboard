#!/bin/bash
# Script to easily update the central version of Petra Clipboard

if [ -z "$1" ]; then
    echo "Usage: ./bump_version.sh <new_version>"
    echo "Example: ./bump_version.sh 0.0.2"
    exit 1
fi

NEW_VERSION=$1

# Update the global-version.txt
echo "$NEW_VERSION" > global-version.txt
echo "Updated global-version.txt to $NEW_VERSION"

# Update main.py
sed -i -E "s/print\(\"Petra Clipboard v.*\"\)/print(\"Petra Clipboard v$NEW_VERSION\")/" src/main.py
echo "Updated src/main.py"

# Update README.md
sed -i -E "s/Version-Beta%20.*-orange/Version-Beta%20$NEW_VERSION-orange/" README.md
echo "Updated README.md"

# Update index.html
sed -i -E "s/<span id=\"app-version\">.*<\/span>/<span id=\"app-version\">$NEW_VERSION<\/span>/" index.html
echo "Updated index.html"

# Update download links in index.html
sed -i -E "s|releases/download/[0-9]+\.[0-9]+\.[0-9]+/Petra-[0-9]+\.[0-9]+\.[0-9]+-all\.deb|releases/download/$NEW_VERSION/Petra-$NEW_VERSION-all.deb|g" index.html
sed -i -E "s|releases/download/[0-9]+\.[0-9]+\.[0-9]+/Petra-[0-9]+\.[0-9]+\.[0-9]+-x86_64\.AppImage|releases/download/$NEW_VERSION/Petra-$NEW_VERSION-x86_64.AppImage|g" index.html
echo "Updated download links in index.html"

# Update Flatpak MetaInfo (for Flathub/Software Centers)
sed -i -E "s/<release version=\".*\" date=\".*\">/<release version=\"$NEW_VERSION\" date=\"$(date +%Y-%m-%d)\">/" io.github.gessendarien.petra.metainfo.xml
echo "Updated io.github.gessendarien.petra.metainfo.xml"

echo "Version bump complete."
