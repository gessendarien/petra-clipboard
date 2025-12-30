import subprocess
import time
from display_detector import DisplayDetector

class InputSimulator:
    def __init__(self):
        self.detector = DisplayDetector()
        self.display_server = self.detector.get_display_server()
        self.key_tool = self.detector.get_recommended_tool('key_simulation')
        
    def simulate_key(self, key_combination):
        """Simular una combinación de teclas"""
        if self.display_server == 'x11':
            return self._simulate_key_x11(key_combination)
        elif self.display_server == 'wayland':
            return self._simulate_key_wayland(key_combination)
        else:
            print(f"Servidor de display no soportado: {self.display_server}")
            return False
    
    def _simulate_key_x11(self, key_combination):
        """Simular teclas en X11 usando xdotool"""
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool no disponible en X11")
            return False
            
        try:
            # xdotool espera combinaciones como "ctrl+v" o "alt+Tab"
            command = ['xdotool', 'key', '--clearmodifiers', key_combination]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout al simular tecla con xdotool")
            return False
        except Exception as e:
            print(f"Error al simular tecla con xdotool: {e}")
            return False
    
    def _simulate_key_wayland(self, key_combination):
        """Simular teclas en Wayland"""
        if self.key_tool == 'ydotool':
            return self._simulate_key_ydotool(key_combination)
        elif self.key_tool == 'wtype':
            return self._simulate_key_wtype(key_combination)
        else:
            print("No hay herramienta disponible para simular teclas en Wayland")
            return False
    
    def _simulate_key_ydotool(self, key_combination):
        """Simular teclas usando ydotool"""
        try:
            # ydotool usa formato similar: "ctrl+v" o "alt+tab"
            command = ['ydotool', 'key', key_combination]
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout al simular tecla con ydotool")
            return False
        except Exception as e:
            print(f"Error al simular tecla con ydotool: {e}")
            return False
    
    def _simulate_key_wtype(self, key_combination):
        """Simular teclas usando wtype"""
        try:
            # wtype usa formato diferente: "-M ctrl v" o "-M alt Tab"
            keys = key_combination.split('+')
            command = ['wtype']
            
            for key in keys[:-1]:
                command.extend(['-M', key.lower()])
            command.extend(['-k', keys[-1]])
            
            result = subprocess.run(command, capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print("Timeout al simular tecla con wtype")
            return False
        except Exception as e:
            print(f"Error al simular tecla con wtype: {e}")
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
            import subprocess
            text = None
            
            # Intentar obtener el contenido del portapapeles con diferentes métodos
            # Método 1: xclip
            try:
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    text = result.stdout
            except FileNotFoundError:
                pass
            
            # Método 2: xsel
            if not text:
                try:
                    result = subprocess.run(['xsel', '--clipboard', '--output'], 
                                          capture_output=True, text=True, timeout=2)
                    if result.returncode == 0:
                        text = result.stdout
                except FileNotFoundError:
                    pass
            
            # Método 3: Obtener de PyQt directamente (más lento pero siempre funciona)
            if not text:
                try:
                    from PyQt6.QtWidgets import QApplication
                    clipboard = QApplication.clipboard()
                    text = clipboard.text()
                except Exception:
                    pass
            
            if text:
                # Usar xdotool type para escribir el texto
                # --clearmodifiers evita que modificadores afecten la escritura
                cmd = ['xdotool', 'type', '--clearmodifiers', '--delay', '0', '--', text]
                type_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return type_result.returncode == 0
            return False
        except Exception as e:
            print(f"Error al pegar en terminal X11: {e}")
            return False
    
    def _paste_to_terminal_ydotool(self):
        """Pegar en terminal usando ydotool."""
        try:
            import subprocess
            # Obtener contenido del portapapeles con wl-paste
            result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                text = result.stdout
                cmd = ['ydotool', 'type', '--', text]
                type_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return type_result.returncode == 0
            return False
        except Exception as e:
            print(f"Error con ydotool: {e}")
            return False
    
    def _paste_to_terminal_wtype(self):
        """Pegar en terminal usando wtype."""
        try:
            import subprocess
            # Obtener contenido del portapapeles
            result = subprocess.run(['wl-paste'], capture_output=True, text=True, timeout=2)
            if result.returncode == 0 and result.stdout:
                text = result.stdout
                cmd = ['wtype', '--', text]
                type_result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return type_result.returncode == 0
            return False
        except Exception as e:
            print(f"Error con wtype: {e}")
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
        except:
            pass
        return None
    
    def _get_active_window_wayland(self):
        """Obtener información de ventana activa en Wayland"""
        try:
            # Intentar con diferentes compositors
            if self.detector.is_tool_available('swaymsg'):
                result = subprocess.run(['swaymsg', '-t', 'get_tree'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0:
                    import json
                    tree = json.loads(result.stdout)
                    # Buscar ventana enfocada (función recursiva)
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
            print(f"Error obteniendo ventana activa en Wayland: {e}")
        
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
        except:
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
        except:
            pass
        return False