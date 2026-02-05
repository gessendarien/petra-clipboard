import os
import subprocess
from pathlib import Path

class DisplayDetector:
    def __init__(self):
        self.is_flatpak = self._detect_flatpak()
        self.display_server = self.detect_display_server()
        self.available_tools = self.detect_available_tools()
    
    def _detect_flatpak(self):
        """Detectar si estamos ejecutando dentro de Flatpak"""
        return Path('/.flatpak-info').exists()
        
    def detect_display_server(self):
        """Detectar si estamos en X11 o Wayland"""
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        x11_display = os.environ.get('DISPLAY')
        
        # Check Wayland specific environment variables
        if wayland_display or xdg_session_type == 'wayland':
            return 'wayland'
        elif x11_display:
            return 'x11'
        else:
            # Fallback: try detecting via other methods
            try:
                # Check if we are in a known Wayland compositor
                result = subprocess.run(['pgrep', '-x', 'sway'], capture_output=True, text=True)
                if result.returncode == 0:
                    return 'wayland'
                    
                result = subprocess.run(['pgrep', '-x', 'hyprland'], capture_output=True, text=True)
                if result.returncode == 0:
                    return 'wayland'
                    
                result = subprocess.run(['pgrep', '-x', 'gnome-shell'], capture_output=True, text=True)
                if result.returncode == 0:
                    # GNOME can use Wayland or X11
                    if 'wayland' in os.environ.get('XDG_CURRENT_DESKTOP', '').lower():
                        return 'wayland'
            except:
                pass
                
            return 'x11'  # Fallback to X11 for compatibility
    
    def detect_available_tools(self):
        """Detectar qué herramientas están disponibles en el sistema"""
        tools = {
            'x11': {
                'xdotool': self._check_tool('xdotool'),
                'xbindkeys': self._check_tool('xbindkeys')
            },
            'wayland': {
                'ydotool': self._check_tool('ydotool'),
                'wtype': self._check_tool('wtype'),
                'swaymsg': self._check_tool('swaymsg'),
                'hyprctl': self._check_tool('hyprctl')
            }
        }
        return tools
    
    def _check_tool(self, tool_name):
        """Verificar si una herramienta está disponible"""
        try:
            if self.is_flatpak:
                # In Flatpak, detection via 'which' or 'command -v' is failing due to PATH issues.
                # To avoid blocking functionality, we will try a simple direct execution
                # and if it fails, we will assume True anyway to let the user receive
                # the real execution error instead of silently disabling the feature.
                print(f"DEBUG: Checking for {tool_name} inside Flatpak via host...")
                
                # Attempt direct execution
                cmd = [tool_name, '--version']
                if tool_name == 'wtype':
                    cmd = [tool_name, '--help']
                    
                result = subprocess.run(
                    ['flatpak-spawn', '--host'] + cmd,
                    capture_output=True,
                    timeout=2,
                    cwd='/tmp' # CRITICAL: Force CWD to /tmp
                )
                
                if result.returncode == 0:
                    return True
                    
                print(f"DEBUG: Could not verify {tool_name}, assuming available to avoid blocking.")
                return True # Assume available to avoid blocking functionality
            else:
                # Outside Flatpak, check normally
                subprocess.run(['which', tool_name], capture_output=True, check=True, timeout=2)
                return True
        except Exception as e:
            print(f"DEBUG: Error checking {tool_name}: {e}")
            if self.is_flatpak: return True # Permissive fallback in Flatpak
            return False
    
    def get_display_server(self):
        return self.display_server
    
    def is_tool_available(self, tool_name, server=None):
        if server is None:
            server = self.display_server
        return self.available_tools.get(server, {}).get(tool_name, False)
    
    def get_recommended_tool(self, action, server=None):
        """Obtener la mejor herramienta disponible para una acción específica"""
        if server is None:
            server = self.display_server
            
        if server == 'x11':
            if action == 'key_simulation':
                return 'xdotool' if self.is_tool_available('xdotool') else None
            elif action == 'global_shortcut':
                return 'xbindkeys' if self.is_tool_available('xbindkeys') else None
                
        elif server == 'wayland':
            if action == 'key_simulation':
                # Prefer ydotool, then wtype
                if self.is_tool_available('ydotool'):
                    return 'ydotool'
                elif self.is_tool_available('wtype'):
                    return 'wtype'
                return None
            elif action == 'global_shortcut':
                # Depends on compositor
                if self.is_tool_available('swaymsg'):
                    return 'swaymsg'
                elif self.is_tool_available('hyprctl'):
                    return 'hyprctl'
                return None
                
        return None