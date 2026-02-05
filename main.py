#!/usr/bin/env python3
import sys
import argparse
import faulthandler
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from window import PetraClipboard


def main():
    print("PETRA STARTUP - VERSION: ROBUST_FIX_V2_FUZZY_MIGRATION")
    # Enable faulthandler so Python prints stack traces on crashes (SIGSEGV)
    try:
        faulthandler.enable()
    except Exception:
        pass
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Petra Clipboard Manager')
    parser.add_argument('--hidden', action='store_true', 
                        help='Start with hidden window (for autostart)')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    # Important: Do not close application when window is closed (it is minimized)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle('Fusion')
    
    # Set application icon BEFORE configuring name
    # This is important for some desktop environments to detect it correctly
    icon = QIcon()
    icon_base = Path(__file__).parent / "icons"
    flatpak_base = Path("/app/share/icons/hicolor")
    
    # Add multiple icon sizes for better compatibility
    icon_sizes = [16, 32, 48, 64, 128, 256]
    icon_loaded = False
    
    # First try loading from local development folder
    for size in icon_sizes:
        png_path = icon_base / f"petra-{size}.png"
        if png_path.exists():
            icon.addFile(str(png_path), QSize(size, size))
            icon_loaded = True
    
    # If no specific sizes found, use general PNG or SVG
    if not icon_loaded:
        if (icon_base / "petra.png").exists():
            icon.addFile(str(icon_base / "petra.png"))
            icon_loaded = True
        elif (icon_base / "petra.svg").exists():
            icon.addFile(str(icon_base / "petra.svg"))
            icon_loaded = True
    
    # If not found locally, search in Flatpak paths
    if not icon_loaded:
        flatpak_paths = [
            flatpak_base / "scalable/apps/io.github.petra.svg",
            flatpak_base / "512x512/apps/io.github.petra.png",
        ]
        for fpath in flatpak_paths:
            if fpath.exists():
                icon.addFile(str(fpath))
                icon_loaded = True
                break
    
    # Set the icon in the application
    if icon_loaded:
        app.setWindowIcon(icon)
    
    # Set application name and desktop file for icon association
    # This is critical for the desktop system to show the correct icon
    app.setApplicationName("Petra")
    app.setDesktopFileName("io.github.petra")
    
    # Handle Ctrl+C correctly
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    window = PetraClipboard()
    
    # Only show window if not started with --hidden
    if not args.hidden:
        window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()