import subprocess
import os
from pathlib import Path
from display_detector import DisplayDetector
from PyQt6.QtCore import QTimer

class GlobalShortcutManager:
    def __init__(self):
        self.detector = DisplayDetector()
        self.display_server = self.detector.get_display_server()
        self.config_dir = Path.home() / ".config" / "petra"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Timer para verificar comandos
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.check_toggle_command)
    
    def setup_global_shortcut(self, shortcut_str='Super + v'):
        """Configurar atajo global multi-backend"""
        if self.display_server == 'x11':
            return self._setup_x11_shortcut(shortcut_str)
        elif self.display_server == 'wayland':
            return self._setup_wayland_shortcut(shortcut_str)
        else:
            print(f"Servidor de display no soportado: {self.display_server}")
            return False
    
    def _setup_x11_shortcut(self, shortcut_str):
        """Configurar atajo global en X11 usando xbindkeys"""
        if not self.detector.is_tool_available('xbindkeys'):
            print("xbindkeys no disponible en X11")
            return False
        
        script_path = self.config_dir / "toggle_petra.sh"
        script_content = f"""#!/bin/bash
WINDOW_ID=$(xdotool search --classname petra 2>/dev/null | head -1)
if [ -z "$WINDOW_ID" ]; then
    echo "show" > /tmp/petra_command
else
    VISIBLE=$(xdotool search --onlyvisible --classname petra 2>/dev/null | head -1)
    if [ -z "$VISIBLE" ]; then
        echo "show" > /tmp/petra_command
    else
        echo "hide" > /tmp/petra_command
    fi
fi
"""
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            script_path.chmod(0o755)
            
            xbindkeys_config = Path.home() / ".xbindkeysrc"
            config_entry = f'\n# Petra Clipboard Manager\n"bash {script_path}"\n    {shortcut_str}\n'
            
            if xbindkeys_config.exists():
                with open(xbindkeys_config, 'r') as f:
                    lines = f.read().splitlines()
                new_lines = []
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if line.strip() == '# Petra Clipboard Manager':
                        i += 3
                        continue
                    new_lines.append(line)
                    i += 1
                new_lines.append('')
                new_lines.append('# Petra Clipboard Manager')
                new_lines.append(f'"bash {script_path}"')
                new_lines.append(f'    {shortcut_str}')
                with open(xbindkeys_config, 'w') as f:
                    f.write('\n'.join(new_lines) + '\n')
            else:
                with open(xbindkeys_config, 'w') as f:
                    f.write(config_entry)

            # Reiniciar xbindkeys
            subprocess.run(['killall', 'xbindkeys'], check=False, stderr=subprocess.DEVNULL)
            subprocess.run(['xbindkeys'], check=False, stderr=subprocess.DEVNULL)
            
            self.command_timer.start(100)
            return True
            
        except Exception as e:
            print(f"No se pudo configurar xbindkeys: {e}")
            return False
    
    def _setup_wayland_shortcut(self, shortcut_str):
        """Configurar atajo global en Wayland"""
        tool = self.detector.get_recommended_tool('global_shortcut')
        
        if tool == 'swaymsg':
            return self._setup_sway_shortcut(shortcut_str)
        elif tool == 'hyprctl':
            return self._setup_hyprland_shortcut(shortcut_str)
        else:
            print("No se pudo configurar atajo global en Wayland - compositor no soportado")
            # Fallback: usar demonio personalizado con ydotool
            return self._setup_wayland_fallback(shortcut_str)
    
    def _setup_sway_shortcut(self, shortcut_str):
        """Configurar atajo en Sway"""
        try:
            sway_config = Path.home() / ".config" / "sway" / "config"
            sway_config.parent.mkdir(parents=True, exist_ok=True)
            
            # Convertir formato de atajo (Super+v → $mod+v)
            sway_shortcut = shortcut_str.replace('Super', '$mod')
            
            config_entry = f'\n# Petra Clipboard Manager\nbindsym {sway_shortcut} exec bash {self.config_dir / "toggle_petra.sh"}\n'
            
            if sway_config.exists():
                with open(sway_config, 'r') as f:
                    content = f.read()
                
                # Remover configuración anterior
                lines = content.splitlines()
                new_lines = []
                i = 0
                while i < len(lines):
                    if '# Petra Clipboard Manager' in lines[i]:
                        i += 2  # Saltar línea de comentario y bindsym
                        continue
                    new_lines.append(lines[i])
                    i += 1
                
                new_lines.append(config_entry)
                with open(sway_config, 'w') as f:
                    f.write('\n'.join(new_lines))
            else:
                with open(sway_config, 'w') as f:
                    f.write(config_entry)
            
            # Recargar configuración de Sway
            subprocess.run(['swaymsg', 'reload'], capture_output=True)
            
            # Crear script de toggle actualizado para Wayland
            self._create_wayland_toggle_script()
            self.command_timer.start(100)
            return True
            
        except Exception as e:
            print(f"Error configurando atajo en Sway: {e}")
            return False
    
    def _setup_hyprland_shortcut(self, shortcut_str):
        """Configurar atajo en Hyprland"""
        try:
            hypr_config = Path.home() / ".config" / "hypr" / "hyprland.conf"
            hypr_config.parent.mkdir(parents=True, exist_ok=True)
            
            # Hyprland usa formato similar
            config_entry = f'\n# Petra Clipboard Manager\nbind = {shortcut_str}, exec, bash {self.config_dir / "toggle_petra.sh"}\n'
            
            if hypr_config.exists():
                with open(hypr_config, 'r') as f:
                    content = f.read()
                
                lines = content.splitlines()
                new_lines = []
                i = 0
                while i < len(lines):
                    if '# Petra Clipboard Manager' in lines[i]:
                        i += 1  # Saltar línea de bind
                        continue
                    new_lines.append(lines[i])
                    i += 1
                
                new_lines.append(config_entry)
                with open(hypr_config, 'w') as f:
                    f.write('\n'.join(new_lines))
            else:
                with open(hypr_config, 'w') as f:
                    f.write(config_entry)
            
            # Crear script de toggle actualizado para Wayland
            self._create_wayland_toggle_script()
            self.command_timer.start(100)
            return True
            
        except Exception as e:
            print(f"Error configurando atajo en Hyprland: {e}")
            return False
    
    def _setup_wayland_fallback(self, shortcut_str):
        """Fallback para Wayland usando demonio personalizado"""
        print("Configurando fallback para Wayland...")
        # Para Wayland sin soporte nativo, podríamos usar un demonio con ydotool
        # Esto es más complejo y requeriría permisos elevados
        self._create_wayland_toggle_script()
        self.command_timer.start(100)
        return True
    
    def _create_wayland_toggle_script(self):
        """Crear script de toggle actualizado para Wayland"""
        script_path = self.config_dir / "toggle_petra.sh"
        script_content = """#!/bin/bash
# Script multi-backend para toggle de Petra
if [ "$XDG_SESSION_TYPE" = "wayland" ] || [ -n "$WAYLAND_DISPLAY" ]; then
    # Wayland: buscar proceso de Petra
    if pgrep -f "python.*petra" > /dev/null; then
        # Petra está corriendo, verificar si la ventana está visible
        # En Wayland esto es más complejo, usamos un archivo de estado
        if [ -f /tmp/petra_visible ]; then
            echo "hide" > /tmp/petra_command
            rm -f /tmp/petra_visible
        else
            echo "show" > /tmp/petra_command
            touch /tmp/petra_visible
        fi
    else
        echo "show" > /tmp/petra_command
        touch /tmp/petra_visible
    fi
else
    # X11: método original
    WINDOW_ID=$(xdotool search --classname petra 2>/dev/null | head -1)
    if [ -z "$WINDOW_ID" ]; then
        echo "show" > /tmp/petra_command
    else
        VISIBLE=$(xdotool search --onlyvisible --classname petra 2>/dev/null | head -1)
        if [ -z "$VISIBLE" ]; then
            echo "show" > /tmp/petra_command
        else
            echo "hide" > /tmp/petra_command
        fi
    fi
fi
"""
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            script_path.chmod(0o755)
            return True
        except Exception as e:
            print(f"Error creando script de toggle: {e}")
            return False
    
    def check_toggle_command(self):
        """Verificar comandos de toggle (común para ambos backends)"""
        command_file = Path("/tmp/petra_command")
        if command_file.exists():
            try:
                with open(command_file, 'r') as f:
                    command = f.read().strip()
                command_file.unlink()
                
                if command == "show":
                    if hasattr(self, 'show_window'):
                        self.show_window()
                elif command == "hide":
                    if hasattr(self, 'hide'):
                        self.hide()
            except:
                pass
    
    def register_global_hotkey(self, shortcut_str='Super + v'):
        """Re-registrar el atajo global (para cambios en configuración)"""
        return self.setup_global_shortcut(shortcut_str)