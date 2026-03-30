#!/usr/bin/env python3
import sys
import os
import argparse
import faulthandler
import socket
import threading
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, QTimer
from window import PetraClipboard


# Socket path for single-instance communication
SOCKET_PATH = os.path.join(
    os.environ.get('XDG_RUNTIME_DIR', '/tmp'),
    'petra-clipboard.sock'
)


def send_command(cmd='SHOW'):
    """Try to send a command to an already-running instance.
    Returns True if the command was sent successfully."""
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2)
        client.connect(SOCKET_PATH)
        client.sendall(cmd.encode('utf-8'))
        client.close()
        return True
    except (ConnectionRefusedError, FileNotFoundError, OSError):
        return False


def start_socket_server(window):
    """Start a Unix socket server that listens for commands from new instances."""
    # Clean up stale socket
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    server.settimeout(1)  # Allow periodic checks for app exit

    def listen():
        while True:
            try:
                conn, _ = server.accept()
                data = conn.recv(1024).decode('utf-8', errors='ignore')
                conn.close()
                if data == 'SHOW':
                    # Use QTimer to safely interact with GUI from this thread
                    QTimer.singleShot(0, window.show_window)
                elif data == 'TOGGLE':
                    QTimer.singleShot(0, window._handle_shortcut_toggle)
            except socket.timeout:
                continue
            except OSError:
                break

    thread = threading.Thread(target=listen, daemon=True)
    thread.start()
    return server


def main():
    print("Petra Clipboard v0.1.0")
    # Enable faulthandler so Python prints stack traces on crashes (SIGSEGV)
    try:
        faulthandler.enable()
    except Exception:
        pass
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Petra Clipboard Manager')
    parser.add_argument('--hidden', action='store_true', 
                        help='Start with hidden window (for autostart)')
    parser.add_argument('--toggle', action='store_true', 
                        help='Toggle window visibility (for shortcut)')
    args = parser.parse_args()
    
    # Single-instance check: try to connect to an existing instance
    cmd_to_send = 'TOGGLE' if args.toggle else 'SHOW'
    if send_command(cmd_to_send):
        print(f"Petra is already running. Sending {cmd_to_send} command.")
        sys.exit(0)
    
    app = QApplication(sys.argv)
    # Important: Do not close application when window is closed (it is minimized)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle('Fusion')
    
    # Set application icon BEFORE configuring name
    # This is important for some desktop environments to detect it correctly
    icon = QIcon()
    icon_base = Path(__file__).parent.parent / "icons"
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
            flatpak_base / "scalable/apps/io.github.gessendarien.petra.svg",
            flatpak_base / "512x512/apps/io.github.gessendarien.petra.png",
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
    app.setApplicationDisplayName("Petra")
    app.setDesktopFileName("io.github.gessendarien.petra")
    
    # Handle Ctrl+C correctly
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    window = PetraClipboard()
    
    # Start socket server for single-instance communication
    sock_server = start_socket_server(window)
    
    # Clean up socket on exit
    def cleanup():
        try:
            sock_server.close()
        except Exception:
            pass
        try:
            if os.path.exists(SOCKET_PATH):
                os.unlink(SOCKET_PATH)
        except Exception:
            pass
    
    app.aboutToQuit.connect(cleanup)
    
    # Only show window if not started with --hidden
    if not args.hidden:
        window.show_window()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()