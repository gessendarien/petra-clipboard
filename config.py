import json
import base64
from datetime import datetime
from pathlib import Path

from dialogs import SettingsDialog

class ConfigManager:
    def __init__(self):
        self.config_dir = Path.home() / ".config" / "petra"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.pinned_file = self.config_dir / "pinned.json"
        self.config_file = self.config_dir / "config.json"
        self.pinned_images_dir = self.config_dir / "pinned_images"
        self.pinned_images_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_images = 10
        self.language = 'es'
        self.config = {}
        self.show_clear_btn = True
        self.show_pin_btn = False
        self.shortcut = 'Control + Shift + v'
        self.theme = 'dark'
        self.recent_emojis = []
        self.open_at_mouse = False
        
        self.load_config()

    def load_config(self):
        default = {
            'language': 'es',
            'max_images': 10,
            'shortcut': 'Control + Shift + v',
            'show_clear_btn': True,
            'show_pin_btn': False,
            'theme': 'dark',
            'recent_emojis': [],
            'open_at_mouse': False
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
            self.recent_emojis = list(self.config.get('recent_emojis', []))[:16]
            self.open_at_mouse = bool(self.config.get('open_at_mouse', False))
        except Exception:
            self.config = default
            self.language = default['language']
            self.max_images = default['max_images']
            self.shortcut = default['shortcut']
            self.show_clear_btn = True
            self.theme = 'dark'
            self.recent_emojis = []

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
            self.config['recent_emojis'] = getattr(self, 'recent_emojis', [])[:16]
            self.config['open_at_mouse'] = getattr(self, 'open_at_mouse', False)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def save_pinned(self):
        pinned = []
        for c in self.clips:
            if c['pinned']:
                item = {
                    'content': c['content'],
                    'type': c['type'],
                    'timestamp': c['timestamp'].isoformat(),
                    'pinned': True
                }
                
                # Para imágenes, guardar el archivo en disco
                if c['type'] == 'image' and hasattr(self, 'clipboard_images'):
                    image_id = c['content']
                    if image_id in self.clipboard_images:
                        try:
                            img = self.clipboard_images[image_id]
                            image_path = self.pinned_images_dir / f"{image_id}.png"
                            img.save(str(image_path), "PNG")
                            item['image_file'] = f"{image_id}.png"
                        except Exception as e:
                            print(f"Error guardando imagen fijada: {e}")
                
                pinned.append(item)
        
        with open(self.pinned_file, 'w') as f:
            json.dump(pinned, f, indent=2)
        
        # Limpiar imágenes huérfanas (que ya no están fijadas)
        self._cleanup_orphan_images(pinned)
    
    def _cleanup_orphan_images(self, pinned_items):
        """Eliminar imágenes que ya no están fijadas"""
        try:
            pinned_files = {item.get('image_file') for item in pinned_items if item.get('image_file')}
            for img_file in self.pinned_images_dir.iterdir():
                if img_file.name not in pinned_files:
                    img_file.unlink()
        except Exception as e:
            print(f"Error limpiando imágenes huérfanas: {e}")

    def load_pinned(self):
        if self.pinned_file.exists():
            try:
                with open(self.pinned_file, 'r') as f:
                    pinned = json.load(f)
                    if not hasattr(self, 'clips'):
                        self.clips = []
                    if not hasattr(self, 'clipboard_images'):
                        self.clipboard_images = {}
                    
                    for item in pinned:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        
                        # Para imágenes, cargar desde disco
                        if item['type'] == 'image' and item.get('image_file'):
                            try:
                                from PyQt6.QtGui import QImage
                                image_path = self.pinned_images_dir / item['image_file']
                                if image_path.exists():
                                    img = QImage(str(image_path))
                                    if not img.isNull():
                                        self.clipboard_images[item['content']] = img
                                    else:
                                        # Imagen corrupta, saltar
                                        continue
                                else:
                                    # Archivo no existe, saltar
                                    continue
                            except Exception as e:
                                print(f"Error cargando imagen fijada: {e}")
                                continue
                        
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