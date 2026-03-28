import json
import base64
import hashlib
from datetime import datetime
from pathlib import Path
import os

from dialogs import SettingsDialog

class ConfigManager:
    def __init__(self):
        config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config"))
        self.config_dir = config_base / "petra"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.pinned_file = self.config_dir / "pinned.json"
        self.config_file = self.config_dir / "config.json"
        self.pinned_images_dir = self.config_dir / "pinned_images"
        self.pinned_images_dir.mkdir(parents=True, exist_ok=True)
        self.max_images = 15
        self.max_clips = 25
        self.language = 'en'
        self.config = {}
        self.show_clear_btn = True
        self.show_pin_btn = True
        self.shortcut = 'Super + v'
        self.theme = 'zorin'
        self.recent_emojis = []
        self.open_position = 'center'  # 'mouse', 'center', 'left', 'right'
        
        self.load_config()

    def validate_config(self, config, default):
        """Validate the structure and values of the configuration."""
        for key, value in default.items():
            if key not in config or not isinstance(config[key], type(value)):
                config[key] = value
        return config

    def load_config(self):
        default = {
            'language': 'en',
            'max_images': 15,
            'max_clips': 25,
            'shortcut': 'Super + v',
            'show_clear_btn': True,  # Ensure this is enabled by default
            'show_pin_btn': True,    # Ensure this is enabled by default
            'theme': 'zorin',
            'recent_emojis': [],
            'open_position': 'center'
        }

        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                
                # Validate the loaded configuration
                self.config = self.validate_config(self.config, default)
            else:
                self.config = default
                with open(self.config_file, 'w') as f:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, IOError):
            print("Configuration file corrupt. Restoring default values.")
            self.config = default
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)

        self.language = self.config.get('language', default['language'])
        self.max_images = int(self.config.get('max_images', default['max_images']))
        self.max_clips = int(self.config.get('max_clips', default.get('max_clips', 20)))
        self.shortcut = self.config.get('shortcut', default['shortcut'])
        self.show_clear_btn = bool(self.config.get('show_clear_btn', True))  # Default to True
        self.show_pin_btn = bool(self.config.get('show_pin_btn', True))      # Default to True
        self.theme = self.config.get('theme', default.get('theme', 'dark'))
        self.recent_emojis = list(self.config.get('recent_emojis', []))[:16]
        self.open_position = self.config.get('open_position', 'mouse')

    def save_config(self):
        try:
            if not isinstance(self.config, dict):
                self.config = {}
                
            self.config['language'] = getattr(self, 'language', 'es')
            self.config['max_images'] = getattr(self, 'max_images', 10)
            self.config['max_clips'] = getattr(self, 'max_clips', 20)
            self.config['shortcut'] = getattr(self, 'shortcut', 'Super + v')
            self.config['show_clear_btn'] = getattr(self, 'show_clear_btn', True)
            self.config['show_pin_btn'] = getattr(self, 'show_pin_btn', True)
            self.config['theme'] = getattr(self, 'theme', 'dark')
            self.config['recent_emojis'] = getattr(self, 'recent_emojis', [])[:16]
            self.config['open_position'] = getattr(self, 'open_position', 'mouse')
            
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
                
                # For images, save file to disk and hash
                if c['type'] == 'image' and hasattr(self, 'clipboard_images'):
                    image_id = c['content']
                    if image_id in self.clipboard_images:
                        try:
                            img = self.clipboard_images[image_id]
                            image_path = self.pinned_images_dir / f"{image_id}.png"
                            img.save(str(image_path), "PNG")
                            item['image_file'] = f"{image_id}.png"
                            
                            # Save image hash to avoid duplicates on restart
                            if hasattr(self, '_image_hashes') and image_id in self._image_hashes:
                                item['image_hash'] = self._image_hashes[image_id]
                        except Exception as e:
                            print(f"Error saving pinned image: {e}")
                
                pinned.append(item)
        
        with open(self.pinned_file, 'w') as f:
            json.dump(pinned, f, indent=2)
        
        # Clean up orphan images (no longer pinned)
        self._cleanup_orphan_images(pinned)
    
    def _cleanup_orphan_images(self, pinned_items):
        """Remove images that are no longer pinned"""
        try:
            pinned_files = {item.get('image_file') for item in pinned_items if item.get('image_file')}
            for img_file in self.pinned_images_dir.iterdir():
                if img_file.name not in pinned_files:
                    img_file.unlink()
        except Exception as e:
            print(f"Error cleaning orphan images: {e}")

    def load_pinned(self):
        if self.pinned_file.exists():
            try:
                with open(self.pinned_file, 'r') as f:
                    pinned = json.load(f)
                    if not hasattr(self, 'clips'):
                        self.clips = []
                    if not hasattr(self, 'clipboard_images'):
                        self.clipboard_images = {}
                    if not hasattr(self, '_image_hashes'):
                        self._image_hashes = {}
                    if not hasattr(self, '_pinned_image_hashes'):
                        self._pinned_image_hashes = set()
                    
                    for item in pinned:
                        item['timestamp'] = datetime.fromisoformat(item['timestamp'])
                        
                        # For images, load from disk
                        if item['type'] == 'image' and item.get('image_file'):
                            try:
                                from PyQt6.QtGui import QImage
                                from PyQt6.QtCore import QBuffer, QIODevice, Qt
                                image_path = self.pinned_images_dir / item['image_file']
                                if image_path.exists():
                                    img = QImage(str(image_path))
                                    if not img.isNull():
                                        self.clipboard_images[item['content']] = img
                                        
                                        # Recalculate hash using same method as ImageTask
                                        # to guarantee consistency (MD5 of PNG scaled to 1200px, quality 50)
                                        img_for_hash = img
                                        if img_for_hash.width() > 1200 or img_for_hash.height() > 1200:
                                            img_for_hash = img_for_hash.scaled(
                                                1200, 1200, 
                                                Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.FastTransformation
                                            )
                                        buffer = QBuffer()
                                        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                                        img_for_hash.save(buffer, "PNG", 50)
                                        image_data = buffer.data()
                                        calculated_hash = hashlib.md5(bytes(image_data)).hexdigest()
                                        
                                        self._image_hashes[item['content']] = calculated_hash
                                        self._pinned_image_hashes.add(calculated_hash)
                                    else:
                                        # Corrupt image, skip
                                        continue
                                else:
                                    # File does not exist, skip
                                    continue
                            except Exception as e:
                                print(f"Error loading pinned image: {e}")
                                continue
                        
                        self.clips.append(item)
            except Exception as e:
                print(f"Error loading pinned: {e}")

    def open_settings(self):
        dlg = SettingsDialog(self)
        # If an update is pending, start the tilt animation on the github button
        if getattr(self, '_pending_update_anim', False):
            dlg.start_update_animation()
        if dlg.exec():
            try:
                self.max_images = int(getattr(self, 'max_images', 10))
            except Exception:
                pass