import json
from datetime import datetime
from pathlib import Path

from dialogs import SettingsDialog

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "petra"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.pinned_file = self.config_dir / "pinned.json"
        self.config_file = self.config_dir / "config.json"
        
        self.max_images = 10
        self.language = 'es'
        self.config = {}
        self.show_clear_btn = True
        self.show_pin_btn = False
        self.shortcut = 'Control + Shift + v'
        self.theme = 'dark'
        
        self.load_config()

    def load_config(self):
        default = {
            'language': 'es',
            'max_images': 10,
            'shortcut': 'Control + Shift + v',
            'show_clear_btn': True,
            'show_pin_btn': False,
            'theme': 'dark'
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default
                try:
                    with open(self.config_file, 'w') as f:
                        json.dump(self.config, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass

            self.language = self.config.get('language', default['language'])
            self.max_images = int(self.config.get('max_images', default['max_images']))
            self.shortcut = self.config.get('shortcut', default['shortcut'])
            self.show_clear_btn = bool(self.config.get('show_clear_btn', True))
            self.show_pin_btn = bool(self.config.get('show_pin_btn', False))
            self.theme = self.config.get('theme', default.get('theme', 'dark'))
        except Exception:
            self.config = default
            self.language = default['language']
            self.max_images = default['max_images']
            self.shortcut = default['shortcut']
            self.show_clear_btn = True
            self.theme = 'dark'

    def save_config(self):
        try:
            if not isinstance(self.config, dict):
                self.config = {}
                
            self.config['language'] = getattr(self, 'language', 'es')
            self.config['max_images'] = getattr(self, 'max_images', 10)
            self.config['shortcut'] = getattr(self, 'shortcut', 'Control + Shift + v')
            self.config['show_clear_btn'] = getattr(self, 'show_clear_btn', True)
            self.config['show_pin_btn'] = getattr(self, 'show_pin_btn', False)
            self.config['theme'] = getattr(self, 'theme', 'dark')
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_pinned(self):
        pinned = [
            {
                'content': c['content'],
                'type': c['type'],
                'timestamp': c['timestamp'].isoformat(),
                'pinned': True
            }
            for c in self.clips if c['pinned']
        ]
        with open(self.pinned_file, 'w') as f:
            json.dump(pinned, f, indent=2)

    def load_pinned(self):
        if self.pinned_file.exists():
            try:
                with open(self.pinned_file, 'r') as f:
                    pinned = json.load(f)
                    if not hasattr(self, 'clips'):
                        self.clips = []
                    for item in pinned:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        self.clips.append(item)
            except Exception as e:
                print(f"Error loading pinned: {e}")

    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            try:
                self.max_images = int(getattr(self, 'max_images', 10))
            except Exception:
                pass