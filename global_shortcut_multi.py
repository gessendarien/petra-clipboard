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
            # In some Flatpak environments, host PATH is not passed correctly.
            tool = cmd[0]
            if tool in ['xdotool', 'xbindkeys', 'pkill']: # pkill is usually also in /usr/bin
                 cmd[0] = f'/usr/bin/{tool}'
            
            cmd = ['flatpak-spawn', '--host'] + cmd
            # CRITICAL: Force CWD to /tmp because sandbox directory (/app/...)
            # does not exist on host, and flatpak-spawn will fail if it tries to use it.
            if 'cwd' not in kwargs:
                kwargs['cwd'] = '/tmp'
                
        return subprocess.run(cmd, **kwargs)
    
    def setup_global_shortcut(self, shortcut_str='Super + v'):
        print(f"Configuring global shortcut: {shortcut_str}")
        
        if self.display_server == 'x11':
            return self._setup_x11_direct_shortcut(shortcut_str)
        else:
            print("Wayland - alternative method")
            return False
    
    def _setup_x11_direct_shortcut(self, shortcut_str):
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool not found. Install it: sudo apt install xdotool")
            return False
            
    # --- Helper to write to HOST via PIPE ---
    def _write_host_file(self, host_path, content):
        """Escribe contenido en un archivo del HOST usando flatpak-spawn y tee."""
        if not self.is_flatpak:
            # Fallback for non-flatpak local development
            try:
                p = Path(host_path)
                p.parent.mkdir(parents=True, exist_ok=True)
                with open(p, 'w') as f:
                    f.write(content)
                p.chmod(0o755)
                return True
            except Exception as e:
                print(f"Error writing local: {e}")
                return False

        # In Flatpak: Use stdin pipe to 'tee' on host
        cmd = ['flatpak-spawn', '--host', 'tee', str(host_path)]
        try:
            # Use input=content.encode() to pass data via stdin
            res = subprocess.run(
                cmd, 
                input=content.encode('utf-8'), 
                stdout=subprocess.DEVNULL, # tee writes to stdout too, we silence it
                stderr=subprocess.PIPE,
                cwd='/tmp'
            )
            if res.returncode != 0:
                print(f"Error writing to host {host_path}: {res.stderr}")
                return False
                
            # Make executable
            subprocess.run(
                ['flatpak-spawn', '--host', 'chmod', '+x', str(host_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd='/tmp'
            )
            return True
        except Exception as e:
            print(f"Exception writing to host: {e}")
            return False

    def _setup_x11_direct_shortcut(self, shortcut_str):
        if not self.detector.is_tool_available('xdotool'):
            print("xdotool not found. Install it: sudo apt install xdotool")
            return False
            
        # "PIPE" STRATEGY: We do not depend on shared paths.
        # Everything happens in HOST /tmp.
        
        host_script_path = "/tmp/petra_toggle.sh"
        host_command_file = "/tmp/petra_command_pipe"
        host_config_path = "/tmp/petra_xbindkeysrc"
        
        # SIMPLIFIED Script: Only writes "toggle", Python decides whether to show/hide
        script_content = f"""#!/bin/bash
echo "toggle" > "{host_command_file}"
"""
        # 1. Inject script into HOST
        if not self._write_host_file(host_script_path, script_content):
            print("Failed to inject script into host")
            return False

        # 2. Generate xbindkeys config
        # Convert shortcut format to xbindkeys format
        # "Super + v" -> "Mod4 + v", "Control" -> "Control", etc.
        xbindkeys_shortcut = shortcut_str
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Super', 'Mod4')
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Alt', 'Alt')  # Already correct
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Ctrl', 'Control')
        xbindkeys_shortcut = xbindkeys_shortcut.replace('Shift', 'Shift')  # Already correct
        
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
        
        # First we kill the specific previous instance of this config
        kill_cmd = ['pkill', '-f', f'xbindkeys -f {host_config_path}']
        self._run_command(kill_cmd, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        
        # Start new instance
        command = ['xbindkeys', '-f', host_config_path]
        res = self._run_command(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        print(f"DEBUG: xbindkeys restart result: {res.returncode}")
        
        print("Shortcut configured via PIPE Strategy.")
        return True

    def check_toggle_command(self):
        # Read command file FROM HOST via flatpak-spawn cat
        # We do not try to open it locally.
        
        host_command_file = "/tmp/petra_command_pipe"
        
        cmd = ['flatpak-spawn', '--host', 'cat', host_command_file]
        try:
            res = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                cwd='/tmp',
                timeout=0.5  # Fast timeout to avoid blocking
            )
            
            if res.returncode == 0:
                command = res.stdout.strip()
                # Clean up file on host immediately
                subprocess.run(
                     ['flatpak-spawn', '--host', 'rm', '-f', host_command_file],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd='/tmp',
                     timeout=0.5
                )
                
                if command == "toggle":
                    # Python decides based on its own state
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
            pass  # Timeout - no pending command
        except Exception:
            pass
    
    def register_global_hotkey(self, shortcut_str='Super + v'):
        return self.setup_global_shortcut(shortcut_str)