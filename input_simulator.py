import subprocess
import time
import shlex
from display_detector import DisplayDetector

class InputSimulator:
    def __init__(self):
        self.detector = DisplayDetector()
        self.display_server = self.detector.get_display_server()
        self.key_tool = self.detector.get_recommended_tool('key_simulation')
        self.is_flatpak = self.detector.is_flatpak
    
    def _run_command(self, cmd, **kwargs):
        """Ejecutar comando, usando flatpak-spawn si estamos en Flatpak"""
        if self.is_flatpak:
            # Use absolute paths for known tools
            tool = cmd[0]
            if tool in ['xdotool', 'ydotool', 'wtype', 'xclip', 'xsel']:
                cmd[0] = f'/usr/bin/{tool}'
            cmd = ['flatpak-spawn', '--host'] + cmd
            # Force CWD to /tmp to avoid directory error
            if 'cwd' not in kwargs:
                kwargs['cwd'] = '/tmp'
        return subprocess.run(cmd, **kwargs)
        
    def simulate_key(self, key_combination):
        """Simular una combinación de teclas"""
        if self.display_server == 'x11':
            return self._simulate_key_x11(key_combination)
        elif self.display_server == 'wayland':
            return self._simulate_key_wayland(key_combination)
        else:
            print(f"Unsupported display server: {self.display_server}")
            return False
    
    def _simulate_key_x11(self, key_combination):
        """Simular teclas en X11 usando xdotool"""
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool not available in X11")
            return False
            
        try:
            # xdotool expects combinations like "ctrl+v" or "alt+Tab"
            command = ['xdotool', 'key', '--clearmodifiers', key_combination]
            result = self._run_command(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout simulating key with xdotool")
            return False
        except Exception as e:
            print(f"Error simulating key with xdotool: {e}")
            return False
    
    def _simulate_key_wayland(self, key_combination):
        """Simular teclas en Wayland"""
        if self.key_tool == 'ydotool':
            return self._simulate_key_ydotool(key_combination)
        elif self.key_tool == 'wtype':
            return self._simulate_key_wtype(key_combination)
        else:
            print("No tool available to simulate keys in Wayland")
            return False
    
    def _simulate_key_ydotool(self, key_combination):
        """Simular teclas usando ydotool"""
        try:
            # ydotool uses similar format: "ctrl+v" or "alt+tab"
            command = ['ydotool', 'key', key_combination]
            result = self._run_command(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout simulating key with ydotool")
            return False
        except Exception as e:
            print(f"Error simulating key with ydotool: {e}")
            return False
    
    def _simulate_key_wtype(self, key_combination):
        """Simular teclas usando wtype"""
        try:
            # wtype uses different format: "-M ctrl v" or "-M alt Tab"
            keys = key_combination.split('+')
            command = ['wtype']
            
            for key in keys[:-1]:
                command.extend(['-M', shlex.quote(key.lower())])
            command.extend(['-k', shlex.quote(keys[-1])])
            
            result = self._run_command(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout simulating key with wtype")
            return False
        except Exception as e:
            print(f"Error simulating key with wtype: {e}")
            return False
    
    def simulate_paste(self):
        """Simular Ctrl+V para pegar"""
        return self.simulate_key('ctrl+v')
    
    def simulate_terminal_paste(self):
        """Simular Ctrl+Shift+V para pegar en terminal.
        Nota: Como Petra usa Ctrl+Shift+V como atajo global, este método
        intenta usar xdotool type para escribir directamente el contenido
        del portapapeles en la terminal."""
        if self.display_server == 'x11':
            return self._paste_to_terminal_x11()
        elif self.display_server == 'wayland':
            if self.key_tool == 'ydotool':
                return self._paste_to_terminal_ydotool()
            elif self.key_tool == 'wtype':
                return self._paste_to_terminal_wtype()
        return False
    
    def _paste_to_terminal_x11(self):
        """Pegar en terminal en X11 usando xdotool type."""
        try:
            text = None
            
            # Try to get clipboard content with different methods
            # Method 1: xclip
            try:
                result = self._run_command(['xclip', '-selection', 'clipboard', '-o'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    text = result.stdout
            except FileNotFoundError:
                pass
            
            # Method 2: xsel
            if not text:
                try:
                    result = self._run_command(['xsel', '--clipboard', '--output'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        text = result.stdout
                except FileNotFoundError:
                    pass
            
            # Method 3: Get from PyQt directly (slower but always works)
            if not text:
                try:
                    from PyQt6.QtWidgets import QApplication
                    clipboard = QApplication.clipboard()
                    text = clipboard.text()
                except Exception:
                    pass
            
            if text:
                # Use xdotool type to write text
                # --clearmodifiers prevents modifiers from affecting typing
                cmd = ['xdotool', 'type', '--clearmodifiers', '--delay', '0', '--', text]
                type_result = self._run_command(cmd, capture_output=True, text=True, timeout=10)
                return type_result.returncode == 0
            return False
        except Exception as e:
            print(f"Error pasting to terminal X11: {e}")
            return False
    
    def _paste_to_terminal_ydotool(self):
        """Pegar en terminal usando ydotool."""
        try:
            import subprocess
            # Get clipboard content with wl-paste
            result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                text = result.stdout
                cmd = ['ydotool', 'type', '--', text]
                type_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return type_result.returncode == 0
            return False
        except Exception as e:
            print(f"Error with ydotool: {e}")
            return False
    
    def _paste_to_terminal_wtype(self):
        """Pegar en terminal usando wtype."""
        try:
            import subprocess
            # Get clipboard content
            result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                text = result.stdout
                cmd = ['wtype', '--', text]
                type_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return type_result.returncode == 0
            return False
        except Exception as e:
            print(f"Error with wtype: {e}")
            return False
    
    def simulate_alt_tab(self):
        """Simular Alt+Tab para cambiar de ventana"""
        return self.simulate_key('alt+Tab')
    
    def get_active_window(self):
        """Obtener la ventana activa actual"""
        if self.display_server == 'x11':
            return self._get_active_window_x11()
        elif self.display_server == 'wayland':
            return self._get_active_window_wayland()
        return None
    
    def _get_active_window_x11(self):
        """Obtener ventana activa en X11"""
        try:
            result = subprocess.run(['xdotool', 'getactivewindow'], 
                                  capture_output=True, text=True, timeout=2)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    def _get_active_window_wayland(self):
        """Obtener información de ventana activa en Wayland"""
        try:
            # Try with different compositors
            if self.detector.is_tool_available('swaymsg'):
                result = subprocess.run(['swaymsg', '-t', 'get_tree'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    import json
                    tree = json.loads(result.stdout)
                    # Find focused window (recursive function)
                    def find_focused(node):
                        if node.get('focused'):
                            return node
                        for child in node.get('nodes', []) + node.get('floating_nodes', []):
                            focused = find_focused(child)
                            if focused:
                                return focused
                        return None
                    
                    focused = find_focused(tree)
                    return str(focused.get('id', '')) if focused else None
            
            elif self.detector.is_tool_available('hyprctl'):
                result = subprocess.run(['hyprctl', 'activewindow', '-j'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    import json
                    window = json.loads(result.stdout)
                    return str(window.get('address', '')) if window else None
                    
        except Exception as e:
            print(f"Error getting active window in Wayland: {e}")
        
        return None
    
    def activate_window(self, window_id):
        """Activar una ventana específica"""
        if self.display_server == 'x11':
            return self._activate_window_x11(window_id)
        elif self.display_server == 'wayland':
            return self._activate_window_wayland(window_id)
        return False
    
    def _activate_window_x11(self, window_id):
        """Activar ventana en X11"""
        try:
            result = subprocess.run(['xdotool', 'windowactivate', '--sync', window_id], 
                                  capture_output=True, text=True, timeout=2)
            return result.returncode == 0
        except Exception:
            return False
    
    def _activate_window_wayland(self, window_id):
        """Activar ventana en Wayland"""
        try:
            if self.detector.is_tool_available('swaymsg') and window_id:
                result = subprocess.run(['swaymsg', f'[con_id={window_id}]', 'focus'], 
                                      capture_output=True, text=True, timeout=2)
                return result.returncode == 0
            elif self.detector.is_tool_available('hyprctl') and window_id:
                result = subprocess.run(['hyprctl', 'dispatch', 'focuswindow', f'address:{window_id}'], 
                                      capture_output=True, text=True, timeout=2)
                return result.returncode == 0
        except Exception:
            pass
        return False