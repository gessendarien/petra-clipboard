import os
import shutil
from pathlib import Path


class DisplayDetector:
    """Detect the graphical session and the input tools reachable from Petra.

    Two different things are tracked:

    * ``session_type``: the desktop session ('x11' or 'wayland').
    * ``qt_platform``: the backend Qt is actually using ('xcb' when Petra runs
      through X11/XWayland, 'wayland' when it runs as a native Wayland client).

    All checks are local (``shutil.which`` / filesystem). Nothing is executed
    on the host, so it works the same inside a strict Flatpak sandbox.
    """

    def __init__(self):
        self.is_flatpak = self._detect_flatpak()
        self.session_type = self._detect_session_type()
        self.qt_platform = self._detect_qt_platform()
        # Kept for backwards compatibility with existing callers
        self.display_server = self.session_type
        self.available_tools = self.detect_available_tools()

    # ── Environment ────────────────────────────────────────────────

    @staticmethod
    def _detect_flatpak():
        return Path('/.flatpak-info').exists() or bool(os.environ.get('FLATPAK_ID'))

    @staticmethod
    def _detect_session_type():
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        if os.environ.get('WAYLAND_DISPLAY') or xdg_session_type == 'wayland':
            return 'wayland'
        return 'x11'

    @staticmethod
    def _detect_qt_platform():
        try:
            from PyQt6.QtGui import QGuiApplication
            name = QGuiApplication.platformName()
            if name:
                return name.lower()
        except Exception:
            pass
        return os.environ.get('QT_QPA_PLATFORM', '').lower() or None

    @property
    def x11_available(self):
        """True when an X server (native X11 or XWayland) is reachable."""
        return bool(os.environ.get('DISPLAY'))

    @property
    def ydotool_socket_available(self):
        """ydotool only works when its daemon socket is reachable."""
        candidates = []
        env_socket = os.environ.get('YDOTOOL_SOCKET')
        if env_socket:
            candidates.append(env_socket)
        runtime_dir = os.environ.get('XDG_RUNTIME_DIR')
        if runtime_dir:
            candidates.append(os.path.join(runtime_dir, '.ydotool_socket'))
        candidates.append('/tmp/.ydotool_socket')
        return any(os.path.exists(p) for p in candidates)

    # ── Tools ──────────────────────────────────────────────────────

    def detect_available_tools(self):
        tools = {
            'xdotool': self._check_tool('xdotool') and self.x11_available,
            'wtype': self._check_tool('wtype') and self.session_type == 'wayland',
            'ydotool': self._check_tool('ydotool') and self.ydotool_socket_available,
            'swaymsg': self._check_tool('swaymsg') and bool(os.environ.get('SWAYSOCK')),
            'hyprctl': self._check_tool('hyprctl') and bool(os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')),
        }
        print(f"Session: {self.session_type} | Qt platform: {self.qt_platform} | "
              f"Flatpak: {self.is_flatpak} | Tools: "
              f"{[name for name, ok in tools.items() if ok] or 'none'}")
        return tools

    @staticmethod
    def _check_tool(tool_name):
        return shutil.which(tool_name) is not None

    def get_display_server(self):
        return self.session_type

    def is_tool_available(self, tool_name, server=None):
        # 'server' kept for backwards compatibility; availability is now global
        return self.available_tools.get(tool_name, False)

    def get_key_simulation_chain(self):
        """Ordered list of tools to try when simulating keys.

        X11 session:      xdotool
        Wayland session:  wtype (wlroots/Hyprland) -> ydotool (daemon running)
                          -> xdotool (only reaches XWayland windows)
        An empty list means "manual paste mode": Petra only restores the
        content to the clipboard and hides, the user presses Ctrl+V.
        """
        if self.session_type == 'x11':
            order = ['xdotool']
        else:
            order = ['wtype', 'ydotool', 'xdotool']
        return [tool for tool in order if self.is_tool_available(tool)]

    def get_recommended_tool(self, action, server=None):
        if action == 'key_simulation':
            chain = self.get_key_simulation_chain()
            return chain[0] if chain else None
        return None
