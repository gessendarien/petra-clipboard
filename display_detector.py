import os
import subprocess
from pathlib import Path

class DisplayDetector:
    def __init__(self):
        self.display_server = self.detect_display_server()
        self.available_tools = self.detect_available_tools()
        
    def detect_display_server(self):
        """Detectar si estamos en X11 o Wayland"""
        wayland_display = os.environ.get('WAYLAND_DISPLAY')
        xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '').lower()
        x11_display = os.environ.get('DISPLAY')
        
        # Verificar variables de entorno específicas de Wayland
        if wayland_display or xdg_session_type == 'wayland':
            return 'wayland'
        elif x11_display:
            return 'x11'
        else:
            # Fallback: intentar detectar mediante otros métodos
            try:
                # Verificar si estamos en un compositor de Wayland conocido
                result = subprocess.run(['pgrep', '-x', 'sway'], capture_output=True, text=True)
                if result.returncode == 0:
                    return 'wayland'
                    
                result = subprocess.run(['pgrep', '-x', 'hyprland'], capture_output=True, text=True)
                if result.returncode == 0:
                    return 'wayland'
                    
                result = subprocess.run(['pgrep', '-x', 'gnome-shell'], capture_output=True, text=True)
                if result.returncode == 0:
                    # GNOME puede usar Wayland o X11
                    if 'wayland' in os.environ.get('XDG_CURRENT_DESKTOP', '').lower():
                        return 'wayland'
            except:
                pass
                
            return 'x11'  # Fallback a X11 por compatibilidad
    
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
            subprocess.run(['which', tool_name], capture_output=True, check=True)
            return True
        except:
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
                # Preferir ydotool, luego wtype
                if self.is_tool_available('ydotool'):
                    return 'ydotool'
                elif self.is_tool_available('wtype'):
                    return 'wtype'
                return None
            elif action == 'global_shortcut':
                # Depende del compositor
                if self.is_tool_available('swaymsg'):
                    return 'swaymsg'
                elif self.is_tool_available('hyprctl'):
                    return 'hyprctl'
                return None
                
        return None