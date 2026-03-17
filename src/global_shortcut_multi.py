import subprocess
import os
import sys
import threading
import stat
from pathlib import Path
from display_detector import DisplayDetector
from PyQt6.QtCore import QTimer, QSocketNotifier, pyqtSignal, QObject
import shlex


class _FifoReaderSignal(QObject):
    """Helper to emit Qt signals from the FIFO reader thread."""
    commandReceived = pyqtSignal(str)


class GlobalShortcutManager:
    HOST_COMMAND_PIPE = "/tmp/petra_command_pipe"

    def __init__(self, on_toggle=None, on_show=None, on_hide=None):
        self.detector = DisplayDetector()
        self.display_server = self.detector.get_display_server()
        config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config"))
        self.config_dir = config_base / "petra"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.is_flatpak = self.detector.is_flatpak

        # Signal bridge for thread -> Qt main loop
        self._fifo_signal = _FifoReaderSignal()
        self._fifo_signal.commandReceived.connect(self._process_command)

        # File descriptor / notifier for non-Flatpak FIFO reading
        self._fifo_fd = None
        self._fifo_notifier = None

        # Thread for Flatpak FIFO reading
        self._fifo_thread = None
        self._fifo_thread_stop = threading.Event()

        # Callbacks for command processing (decoupled from window)
        self._on_toggle = on_toggle
        self._on_show = on_show
        self._on_hide = on_hide

        # Fallback timer (slow, only as safety net)
        self._fallback_timer = QTimer()
        self._fallback_timer.timeout.connect(self._fallback_check)
        self._fallback_timer.start(2000)

    def _run_command(self, cmd, **kwargs):
        """Run command directly (in flatpak we bundled xbindkeys/xdotool)."""
        return subprocess.run(cmd, **kwargs)
    
    def setup_global_shortcut(self, shortcut_str='Super + v'):
        print(f"Configuring global shortcut: {shortcut_str}")
        
        if self.display_server == 'x11':
            return self._setup_x11_direct_shortcut(shortcut_str)
        else:
            print("Wayland - alternative method")
            return False

    def _write_host_file(self, host_path, content):
        """Write content to a file (always local inside the sandbox if in Flatpak)"""
        try:
            p = Path(host_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, 'w') as f:
                f.write(content)
            p.chmod(0o755)
            return True
        except Exception as e:
            print(f"Error writing file {host_path}: {e}")
            return False

    def _ensure_fifo(self):
        """Create the FIFO (named pipe) locally."""
        pipe_path = self.HOST_COMMAND_PIPE
        p = Path(pipe_path)
        if p.exists():
            # If it's already a FIFO, reuse it
            if stat.S_ISFIFO(p.stat().st_mode):
                return True
            # Otherwise remove the stale regular file and recreate
            p.unlink(missing_ok=True)
        try:
            os.mkfifo(pipe_path)
            return True
        except OSError as e:
            print(f"Error creating FIFO: {e}")
            return False

    def _start_fifo_listener(self):
        """Start listening on the FIFO for commands."""
        self._start_fifo_listener_direct()

    def _start_fifo_listener_direct(self):
        """Non-Flatpak: open FIFO with QSocketNotifier for zero-polling."""
        pipe_path = self.HOST_COMMAND_PIPE
        try:
            # Open in non-blocking read mode.
            # O_RDONLY|O_NONBLOCK ensures open() returns immediately even if
            # no writer has opened the FIFO yet.
            self._fifo_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)

            self._fifo_notifier = QSocketNotifier(
                self._fifo_fd, QSocketNotifier.Type.Read
            )
            self._fifo_notifier.activated.connect(self._on_fifo_ready)
            self._fifo_notifier.setEnabled(True)
            print("FIFO listener started (direct, QSocketNotifier)")
        except OSError as e:
            print(f"Error opening FIFO for listening: {e}")

    def _on_fifo_ready(self):
        """Called by QSocketNotifier when data is available on the FIFO."""
        if self._fifo_fd is None:
            return
        try:
            data = os.read(self._fifo_fd, 1024)
            if data:
                command = data.decode('utf-8', errors='replace').strip()
                if command:
                    self._process_command(command)
            else:
                # EOF — the writer closed. Re-open the FIFO to wait for
                # the next writer (re-arm the notifier).
                self._reopen_fifo_direct()
        except BlockingIOError:
            pass
        except OSError as e:
            print(f"Error reading FIFO: {e}")
            self._reopen_fifo_direct()

    def _reopen_fifo_direct(self):
        """Re-open the FIFO after EOF so we can receive the next command."""
        try:
            if self._fifo_notifier:
                self._fifo_notifier.setEnabled(False)
                self._fifo_notifier.deleteLater()
                self._fifo_notifier = None
            if self._fifo_fd is not None:
                os.close(self._fifo_fd)
                self._fifo_fd = None
        except OSError:
            pass

        pipe_path = self.HOST_COMMAND_PIPE
        try:
            self._fifo_fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
            self._fifo_notifier = QSocketNotifier(
                self._fifo_fd, QSocketNotifier.Type.Read
            )
            self._fifo_notifier.activated.connect(self._on_fifo_ready)
            self._fifo_notifier.setEnabled(True)
        except OSError as e:
            print(f"Error re-opening FIFO: {e}")


    def _process_command(self, command):
        """Process a command received from the FIFO (runs on Qt main thread)."""
        if command == "toggle":
            if self._on_toggle:
                self._on_toggle()
        elif command == "show":
            if self._on_show:
                self._on_show()
        elif command == "hide":
            if self._on_hide:
                self._on_hide()

    def _fallback_check(self):
        """
        Slow fallback timer (2s). Only processes commands if the FIFO
        listener missed something (e.g. FIFO was replaced by a regular file).
        """
        pipe_path = self.HOST_COMMAND_PIPE
        p = Path(pipe_path)
        if not p.exists():
            return
        # Only process if it's a regular file (not a FIFO — FIFO is handled
        # by the notifier). This catches edge cases where something wrote
        # a regular file instead.
        try:
            if stat.S_ISFIFO(p.stat().st_mode):
                return  # FIFO is handled by QSocketNotifier
            command = p.read_text().strip()
            p.unlink(missing_ok=True)
            if command:
                self._process_command(command)
        except Exception:
            return

    def _setup_x11_direct_shortcut(self, shortcut_str):
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool not found. Install it: sudo apt install xdotool")
            return False
            
        # "PIPE" STRATEGY: We use a real FIFO (named pipe).
        # Everything happens in HOST /tmp.
        
        host_script_path = "/tmp/petra_toggle.sh"
        host_command_file = self.HOST_COMMAND_PIPE
        host_config_path = "/tmp/petra_xbindkeysrc"
        
        # 0. Ensure FIFO exists on host
        self._ensure_fifo()
        
        # SIMPLIFIED Script: Only writes "toggle" to the FIFO
        script_content = f"""#!/bin/bash
echo "toggle" > "{host_command_file}"
"""
        # 1. Inject script into HOST
        if not self._write_host_file(host_script_path, script_content):
            print("Failed to inject script into host")
            return False

        # 2. Generate xbindkeys config
        xbindkeys_shortcut = shortcut_str
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Super', 'Mod4')
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Ctrl', 'Control')
        
        config_lines = []
        config_lines.append('# Petra Clipboard Manager')
        config_lines.append(f'"{host_script_path}"')
        config_lines.append(f'  {xbindkeys_shortcut}')
        xbindkeys_content = '\n'.join(config_lines) + '\n'

        # 3. Inject config into HOST
        if not self._write_host_file(host_config_path, xbindkeys_content):
             print("Failed to inject config into host")
             return False

        # 4. Restart xbindkeys on HOST
        print(f"DEBUG: Restarting xbindkeys with config {host_config_path}")
        
        # First kill the specific previous instance of this config
        kill_cmd = ['pkill', '-f', f'xbindkeys -f {host_config_path}']
        self._run_command(kill_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        
        # Start new instance
        command = ['xbindkeys', '-f', host_config_path]
        res = self._run_command(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print(f"DEBUG: xbindkeys restart result: {res.returncode}")

        # 5. Start FIFO listener
        self._start_fifo_listener()
        
        print("Shortcut configured via FIFO Strategy.")
        return True

    def cleanup_fifo(self):
        """Clean up FIFO resources. Call on application exit."""
        # Stop thread
        self._fifo_thread_stop.set()

        # Close notifier and fd
        if self._fifo_notifier:
            self._fifo_notifier.setEnabled(False)
            self._fifo_notifier.deleteLater()
            self._fifo_notifier = None
        if self._fifo_fd is not None:
            try:
                os.close(self._fifo_fd)
            except OSError:
                pass
            self._fifo_fd = None

        # Stop fallback timer
        if hasattr(self, '_fallback_timer'):
            self._fallback_timer.stop()

    def register_global_hotkey(self, shortcut_str='Super + v'):
        return self.setup_global_shortcut(shortcut_str)