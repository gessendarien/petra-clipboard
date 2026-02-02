import subprocess
import os
from pathlib import Path
from display_detector import DisplayDetector
from PyQt6.QtCore import QTimer
import shlex


class GlobalShortcutManager:
    def __init__(self):
        self.detector = DisplayDetector()
        self.display_server = self.detector.get_display_server()
        self.config_dir = Path.home() / ".config" / "petra"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.is_flatpak = self.detector.is_flatpak
        
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.check_toggle_command)
        self.command_timer.start(100)
    
    def _run_command(self, cmd, **kwargs):
        """Ejecutar comando, usando flatpak-spawn si estamos en Flatpak"""
        if self.is_flatpak:
            # En algunos entornos Flatpak, el PATH del host no se pasa correctamente.
            tool = cmd[0]
            if tool in ['xdotool', 'xbindkeys', 'pkill']: # pkill también suele estar en /usr/bin
                 cmd[0] = f'/usr/bin/{tool}'
            
            cmd = ['flatpak-spawn', '--host'] + cmd
            # CRÍTICO: Forzar CWD a /tmp porque el directorio del sandbox (/app/...)
            # no existe en el host, y flatpak-spawn fallará si intenta usarlo.
            if 'cwd' not in kwargs:
                kwargs['cwd'] = '/tmp'
                
        return subprocess.run(cmd, **kwargs)
    
    def setup_global_shortcut(self, shortcut_str='Super + v'):
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
            
    # --- Helper para escribir en el HOST via PIPE ---
    def _write_host_file(self, host_path, content):
        """Escribe contenido en un archivo del HOST usando flatpak-spawn y tee."""
        if not self.is_flatpak:
            # Fallback para desarrollo local no-flatpak
            try:
                p = Path(host_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, 'w') as f:
                    f.write(content)
                p.chmod(0o755)
                return True
            except Exception as e:
                print(f"Error escribiendo local: {e}")
                return False

        # En Flatpak: Usar stdin pipe hacia 'tee' en el host
        cmd = ['flatpak-spawn', '--host', 'tee', str(host_path)]
        try:
            # Usar input=content.encode() para pasar datos por stdin
            res = subprocess.run(
                cmd, 
                input=content.encode('utf-8'), 
                stdout=subprocess.DEVNULL, # tee escribe a stdout también, lo silenciamos
                stderr=subprocess.PIPE,
                cwd='/tmp'
            )
            if res.returncode != 0:
                print(f"Error escribiendo en host {host_path}: {res.stderr}")
                return False
                
            # Hacer ejecutable
            subprocess.run(
                ['flatpak-spawn', '--host', 'chmod', '+x', str(host_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd='/tmp'
            )
            return True
        except Exception as e:
            print(f"Excepción al escribir en host: {e}")
            return False

    def _setup_x11_direct_shortcut(self, shortcut_str):
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool no encontrado. Instálalo: sudo apt install xdotool")
            return False
            
        # ESTRATEGIA "PIPE": No dependemos de rutas compartidas.
        # Todo ocurre en /tmp del HOST.
        
        host_script_path = "/tmp/petra_toggle.sh"
        host_command_file = "/tmp/petra_command_pipe"
        host_config_path = "/tmp/petra_xbindkeysrc"
        
        # Script SIMPLIFICADO: Solo escribe "toggle", Python decide si mostrar/ocultar
        script_content = f"""#!/bin/bash
echo "toggle" > "{host_command_file}"
"""
        # 1. Inyectar script en el HOST
        if not self._write_host_file(host_script_path, script_content):
            print("Fallo al inyectar script en host")
            return False

        # 2. Generar config xbindkeys
        # Convertir el formato del atajo al formato de xbindkeys
        # "Super + v" -> "Mod4 + v", "Control" -> "Control", etc.
        xbindkeys_shortcut = shortcut_str
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Super', 'Mod4')
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Alt', 'Alt')  # Ya es correcto
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Ctrl', 'Control')
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Shift', 'Shift')  # Ya es correcto
        
        config_lines = []
        config_lines.append('# Petra Clipboard Manager')
        config_lines.append(f'"{host_script_path}"')
        config_lines.append(f'  {xbindkeys_shortcut}')
        xbindkeys_content = '\n'.join(config_lines) + '\n'

        # 3. Inyectar config en el HOST
        if not self._write_host_file(host_config_path, xbindkeys_content):
             print("Fallo al inyectar config en host")
             return False

        # 4. Reiniciar xbindkeys en el HOST
        print(f"DEBUG: Reiniciando xbindkeys con config {host_config_path}")
        
        # Primero matamos la instancia anterior específica de esta config
        kill_cmd = ['pkill', '-f', f'xbindkeys -f {host_config_path}']
        self._run_command(kill_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        
        # Iniciar nueva instancia
        command = ['xbindkeys', '-f', host_config_path]
        res = self._run_command(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print(f"DEBUG: xbindkeys restart result: {res.returncode}")
        
        print("Atajo configurado via PIPE Strategy.")
        return True

    def check_toggle_command(self):
        # Leer el archivo de comando DEL HOST via flatpak-spawn cat
        # No intentamos abrirlo localmente.
        
        host_command_file = "/tmp/petra_command_pipe"
        
        cmd = ['flatpak-spawn', '--host', 'cat', host_command_file]
        try:
            res = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd='/tmp',
                timeout=0.5  # Timeout rápido para no bloquear
            )
            
            if res.returncode == 0:
                command = res.stdout.strip()
                # Limpiar el archivo en el host inmediatamente
                subprocess.run(
                     ['flatpak-spawn', '--host', 'rm', '-f', host_command_file],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='/tmp',
                     timeout=0.5
                )
                
                if command == "toggle":
                    # Python decide basado en su propio estado
                    if self.isVisible():
                        self.hide()
                    else:
                        self.show_window() if hasattr(self, 'show_window') else self.show()
                elif command == "show":
                    if hasattr(self, 'show_window'):
                        self.show_window()
                elif command == "hide":
                    self.hide()
        except subprocess.TimeoutExpired:
            pass  # Timeout - no hay comando pendiente
        except Exception:
            pass
    
    def register_global_hotkey(self, shortcut_str='Super + v'):
        return self.setup_global_shortcut(shortcut_str)