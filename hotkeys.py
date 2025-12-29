from PyQt6.QtCore import QTimer, QSize
from PyQt6.QtGui import QIcon
from pathlib import Path
import subprocess

class HotkeyManager:
    def __init__(self):
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.check_toggle_command)

    def setup_global_shortcut(self):
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
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        script_path.chmod(0o755)
        
        self.command_timer.start(100)
        self.register_global_hotkey()

    def register_global_hotkey(self):
        xbindkeys_config = Path.home() / ".xbindkeysrc"
        script_path = self.config_dir / "toggle_petra.sh"
        shortcut_str = getattr(self, 'shortcut', 'Super + v')
        config_entry = f'\n# Petra Clipboard Manager\n"bash {script_path}"\n    {shortcut_str}\n'
        
        try:
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

            subprocess.run(['killall', 'xbindkeys'], check=False, stderr=subprocess.DEVNULL)
            subprocess.run(['xbindkeys'], check=False, stderr=subprocess.DEVNULL)
        except Exception as e:
            print(f"No se pudo configurar xbindkeys: {e}")

    def check_toggle_command(self):
        command_file = Path("/tmp/petra_command")
        if command_file.exists():
            try:
                with open(command_file, 'r') as f:
                    command = f.read().strip()
                command_file.unlink()
                
                if command == "show":
                    self.show_window()
                elif command == "hide":
                    self.hide()
            except:
                pass

    def show_window(self):
        try:
            proc = subprocess.run(['xdotool', 'getactivewindow'], capture_output=True, text=True, timeout=0.2)
            wid = proc.stdout.strip() if proc and proc.stdout else None
            if wid:
                self.last_active_window = wid
        except Exception:
            self.last_active_window = None

        self.center_window()
        self.show()
        self.activateWindow()
        self.raise_()
        self.search_bar.setFocus()

    def toggle_window_pin(self):
        try:
            self.window_pinned = not getattr(self, 'window_pinned', False)
            self.pin_window_btn.setChecked(self.window_pinned)
            self.update_pin_button_icon()
        except Exception:
            pass

    def update_pin_button_icon(self):
        try:
            icons_folder = self.themes_manager.get_icons_folder() if hasattr(self, 'themes_manager') else 'dark'
            icons_dir = Path(__file__).parent / 'icons' / icons_folder
            pin_path = icons_dir / 'pin.png'
            unpin_path = icons_dir / 'unpinned.png'
            pinned_path = icons_dir / 'pinned.png'
            
            if getattr(self, 'window_pinned', False):
                if unpin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(unpin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                    self.pin_window_btn.setText("")
                elif pin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                    self.pin_window_btn.setText("")
                else:
                    self.pin_window_btn.setIcon(QIcon())
                    self.pin_window_btn.setText("📌")
            else:
                if pinned_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pinned_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                    self.pin_window_btn.setText("")
                elif pin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                    self.pin_window_btn.setText("")
                else:
                    self.pin_window_btn.setIcon(QIcon())
                    self.pin_window_btn.setText("📌")
        except Exception:
            pass

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_window()