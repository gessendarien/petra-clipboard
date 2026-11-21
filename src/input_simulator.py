import os
import subprocess
import json
from display_detector import DisplayDetector


# Linux input-event keycodes used by ydotool >= 1.0 ("<code>:<1|0>")
_YDOTOOL_KEYCODES = {
    'ctrl': 29, 'control': 29,
    'shift': 42,
    'alt': 56,
    'super': 125, 'logo': 125,
    'tab': 15,
    'v': 47,
    'insert': 110,
}

# wtype modifier names
_WTYPE_MODIFIERS = {
    'ctrl': 'ctrl', 'control': 'ctrl',
    'shift': 'shift',
    'alt': 'alt',
    'super': 'logo', 'logo': 'logo',
}


class InputSimulator:
    """Multi-backend key simulation with a safe cascade.

    For every action the tools returned by
    ``DisplayDetector.get_key_simulation_chain()`` are tried in order until
    one succeeds. If none is available or all fail, the action returns False
    silently: the content is already in the clipboard, Petra hides itself and
    the user pastes manually with Ctrl+V ("manual paste mode"). This is the
    expected behaviour on GNOME/KDE Wayland and inside the Flatpak sandbox.
    """

    def __init__(self):
        self.detector = DisplayDetector()
        self.display_server = self.detector.get_display_server()
        self.is_flatpak = self.detector.is_flatpak
        if os.environ.get('PETRA_MANUAL_PASTE') == '1':
            self.key_chain = []
        else:
            self.key_chain = self.detector.get_key_simulation_chain()
        self.key_tool = self.key_chain[0] if self.key_chain else None
        if not self.key_chain:
            print("Auto-paste unavailable in this session: manual paste mode (Ctrl+V).")

    @property
    def auto_paste_available(self):
        return bool(self.key_chain)

    def _run_command(self, cmd, timeout=5):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0 and result.stderr:
                print(f"{cmd[0]}: {result.stderr.strip()}")
            return result.returncode == 0
        except FileNotFoundError:
            return False
        except subprocess.TimeoutExpired:
            print(f"Timeout running {cmd[0]}")
            return False
        except Exception as e:
            print(f"Error running {cmd[0]}: {e}")
            return False

    # ── Key combinations ───────────────────────────────────────────

    def simulate_key(self, key_combination):
        """Simulate a key combination like 'ctrl+v' or 'alt+Tab'."""
        for tool in self.key_chain:
            handler = getattr(self, f'_key_{tool}', None)
            if handler and handler(key_combination):
                return True
        return False

    def _key_xdotool(self, combo):
        return self._run_command(['xdotool', 'key', '--clearmodifiers', combo])

    def _key_wtype(self, combo):
        keys = [k.strip() for k in combo.split('+') if k.strip()]
        if not keys:
            return False
        cmd = ['wtype']
        modifiers = [_WTYPE_MODIFIERS.get(k.lower(), k.lower()) for k in keys[:-1]]
        for mod in modifiers:
            cmd += ['-M', mod]
        cmd += ['-k', keys[-1]]
        for mod in reversed(modifiers):
            cmd += ['-m', mod]
        return self._run_command(cmd)

    def _key_ydotool(self, combo):
        keys = [k.strip().lower() for k in combo.split('+') if k.strip()]
        codes = [_YDOTOOL_KEYCODES.get(k) for k in keys]
        if not codes or None in codes:
            return False
        sequence = [f"{c}:1" for c in codes] + [f"{c}:0" for c in reversed(codes)]
        return self._run_command(['ydotool', 'key'] + sequence)

    # ── Typing text ────────────────────────────────────────────────

    def _type_text(self, text):
        for tool in self.key_chain:
            if tool == 'xdotool':
                cmd = ['xdotool', 'type', '--clearmodifiers', '--delay', '0', '--', text]
            elif tool == 'wtype':
                cmd = ['wtype', '--', text]
            elif tool == 'ydotool':
                cmd = ['ydotool', 'type', '--', text]
            else:
                continue
            if self._run_command(cmd, timeout=10):
                return True
        return False

    # ── Public actions ─────────────────────────────────────────────

    def simulate_paste(self):
        """Simulate Ctrl+V."""
        return self.simulate_key('ctrl+v')

    def simulate_terminal_paste(self):
        """Paste into a terminal by typing the clipboard text directly
        (avoids depending on Ctrl+Shift+V). Falls back to Ctrl+Shift+V."""
        if not self.key_chain:
            return False
        text = None
        try:
            from PyQt6.QtWidgets import QApplication
            text = QApplication.clipboard().text()
        except Exception:
            pass
        if text and self._type_text(text):
            return True
        return self.simulate_key('ctrl+shift+v')

    def simulate_alt_tab(self):
        return self.simulate_key('alt+Tab')

    # ── Window focus (best effort, X11 / Sway / Hyprland only) ─────

    def get_active_window(self):
        try:
            if self.display_server == 'x11' and self.detector.is_tool_available('xdotool'):
                result = subprocess.run(['xdotool', 'getactivewindow'],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    return result.stdout.strip() or None
            elif self.detector.is_tool_available('swaymsg'):
                result = subprocess.run(['swaymsg', '-t', 'get_tree'],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    def find_focused(node):
                        if node.get('focused'):
                            return node
                        for child in node.get('nodes', []) + node.get('floating_nodes', []):
                            found = find_focused(child)
                            if found:
                                return found
                        return None
                    focused = find_focused(json.loads(result.stdout))
                    return str(focused.get('id', '')) if focused else None
            elif self.detector.is_tool_available('hyprctl'):
                result = subprocess.run(['hyprctl', 'activewindow', '-j'],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    window = json.loads(result.stdout)
                    return str(window.get('address', '')) if window else None
        except Exception as e:
            print(f"Error getting active window: {e}")
        return None

    def activate_window(self, window_id):
        if not window_id:
            return False
        if self.display_server == 'x11' and self.detector.is_tool_available('xdotool'):
            return self._run_command(['xdotool', 'windowactivate', '--sync', window_id], timeout=2)
        if self.detector.is_tool_available('swaymsg'):
            return self._run_command(['swaymsg', f'[con_id={window_id}]', 'focus'], timeout=2)
        if self.detector.is_tool_available('hyprctl'):
            return self._run_command(['hyprctl', 'dispatch', 'focuswindow',
                                      f'address:{window_id}'], timeout=2)
        return False
