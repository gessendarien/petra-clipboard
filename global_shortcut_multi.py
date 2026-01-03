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
        
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.check_toggle_command)
        self.command_timer.start(100)
    
    def setup_global_shortcut(self, shortcut_str='Control + Shift + v'):
        print(f"Configurando atajo global: {shortcut_str}")
        
        if self.display_server == 'x11':
            return self._setup_x11_direct_shortcut(shortcut_str)
        else:
            print("Wayland - método alternativo")
            return False
    
    def _setup_x11_direct_shortcut(self, shortcut_str):
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool no encontrado. Instálalo: sudo apt install xdotool")
            return False
        
        script_path = self.config_dir / "toggle_petra.sh"
        script_content = f"""#!/bin/bash
# Buscar ventana de Petra
WINDOW_ID=$(xdotool search --class "petra" 2>/dev/null | head -1)

if [ -z "$WINDOW_ID" ]; then
    # Petra no está corriendo o no tiene ventana
    echo "show" > /tmp/petra_command
else
    # Verificar si está visible
    VISIBLE=$(xdotool search --onlyvisible --class "petra" 2>/dev/null | head -1)
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
            
            config_lines = []
            if xbindkeys_config.exists():
                with open(xbindkeys_config, 'r') as f:
                    for line in f:
                        if 'petra' not in line.lower():
                            config_lines.append(line.strip())
            
            config_lines.append('# Petra Clipboard Manager')
            config_lines.append(f'"{script_path}"')
            config_lines.append(f'  {shortcut_str}')
            
            with open(xbindkeys_config, 'w') as f:
                f.write('\n'.join(config_lines) + '\n')
            
            subprocess.run(['pkill', 'xbindkeys'], stderr=subprocess.DEVNULL)
            subprocess.run(['xbindkeys'], stderr=subprocess.DEVNULL)
            
            print("Atajo configurado. Reinicia xbindkeys si no funciona:")
            print("pkill xbindkeys && xbindkeys")
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def check_toggle_command(self):
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
            except Exception:
                pass
    
    def register_global_hotkey(self, shortcut_str='Control + Shift + v'):
        return self.setup_global_shortcut(shortcut_str)