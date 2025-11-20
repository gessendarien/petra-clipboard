from PyQt6.QtCore import QTimer, QThreadPool, QRunnable, QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QPainterPath
from datetime import datetime
from pathlib import Path
import subprocess
import re

from input_simulator import InputSimulator

class ImageTaskSignals(QObject):
    processed = pyqtSignal(str, object, str, str, object, object)

class ImageTask(QRunnable):
    def __init__(self, image, key, image_name="Imagen"):
        super().__init__()
        self.image = image
        self.key = key
        self.image_name = image_name
        self.signals = ImageTaskSignals()

    def run(self):
        try:
            img = self.image
            if img.width() > 1200 or img.height() > 1200:
                img = img.scaled(1200, 1200, Qt.AspectRatioMode.KeepAspectRatio,
                                 Qt.TransformationMode.FastTransformation)

            from PyQt6.QtCore import QBuffer, QIODevice
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            img.save(buffer, "PNG", 50)
            image_data = buffer.data()
            image_hash = str(hash(bytes(image_data)))

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            unique_id = f"{self.image_name}_{timestamp}"

            try:
                from PyQt6.QtCore import QRectF
                scaled = img.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.FastTransformation)

                thumb = QImage(40, 40, QImage.Format.Format_ARGB32)
                thumb.fill(Qt.GlobalColor.transparent)

                painter = QPainter(thumb)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)

                path = QPainterPath()
                path.addRoundedRect(QRectF(0, 0, 40, 40), 6, 6)
                painter.setClipPath(path)

                x = (scaled.width() - 40) // 2
                y = (scaled.height() - 40) // 2
                painter.drawImage(-x, -y, scaled)
                painter.end()
            except Exception:
                thumb = None

            self.signals.processed.emit(unique_id, img, image_hash, self.image_name, self.key, thumb)
        except Exception as e:
            print(f"ImageTask error: {e}")

class ClipboardManager:
    def __init__(self):
        self.clips = []
        self.last_clipboard = ""
        self.clipboard_images = {}
        self.inserting_emoji = False
        self.last_emoji_inserted = None
        self.processing_keys = set()
        self.thread_pool = QThreadPool.globalInstance()
        self.last_active_window = None
        self.window_pinned = False
        
        # Input simulator multi-backend
        self.input_simulator = InputSimulator()
        
        # Timer for clipboard monitoring
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_clipboard)
        
        # Timer for clear animation
        self.clear_timer = QTimer()
        self.clear_timer.timeout.connect(self.update_clear_progress)
        self.clear_progress = 0

    def setup_clipboard_monitor(self):
        self.timer.start(300)

    def initialize_clipboard_state(self):
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            if mime_data.hasImage():
                img = clipboard.image()
                if not img.isNull():
                    from PyQt6.QtCore import QBuffer, QIODevice
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    img.save(buffer, "PNG")
                    image_data = buffer.data()
                    image_hash = hash(bytes(image_data))
                    self.last_clipboard = str(image_hash)
            elif mime_data.hasText():
                self.last_clipboard = mime_data.text()
            elif mime_data.hasUrls():
                urls = mime_data.urls()
                if urls:
                    self.last_clipboard = urls[0].toString()
        except Exception as e:
            print(f"Error al inicializar portapapeles: {e}")

    def check_clipboard(self):
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            current = None
            clip_type = "text"  # Por defecto
            
            if mime_data.hasImage():
                img = clipboard.image()
                if not img.isNull():
                    try:
                        key = img.cacheKey()
                    except Exception:
                        key = (img.width(), img.height(), img.format())

                    if key in self.processing_keys:
                        return

                    self.processing_keys.add(key)
                    task = ImageTask(img.copy(), key)
                    task.signals.processed.connect(self.on_image_processed)
                    self.thread_pool.start(task)
                else:
                    print(f"✗ No se pudo capturar la imagen")
                    return
            elif mime_data.hasUrls():
                urls = mime_data.urls()
                if urls:
                    qurl = urls[0]
                    local_path = qurl.toLocalFile()
                    if local_path and local_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
                        try:
                            img = QImage(local_path)
                            if img.isNull():
                                return

                            try:
                                key = (img.width(), img.height(), Path(local_path).stat().st_mtime)
                            except Exception:
                                key = (img.width(), img.height(), img.format())

                            if key in self.processing_keys:
                                return

                            self.processing_keys.add(key)
                            image_name = Path(local_path).stem or "Imagen"
                            task = ImageTask(img, key, image_name=image_name)
                            task.signals.processed.connect(self.on_image_processed)
                            self.thread_pool.start(task)
                        except Exception as e:
                            print(f"Error al cargar imagen desde archivo: {e}")
                    else:
                        current = qurl.toString()
                        clip_type = "url"  # Específicamente URL
            elif mime_data.hasText():
                current = mime_data.text()
                # Detectar el tipo correcto
                clip_type = self.detect_type(current)
            
            if self.inserting_emoji or (self.last_emoji_inserted and current == self.last_emoji_inserted):
                self.inserting_emoji = False
                self.last_emoji_inserted = None
                return
            
            if current and current.strip():
                if clip_type != "image" and current == self.last_clipboard:
                    return
                if clip_type != "image":
                    self.last_clipboard = current
                # Pasar el tipo específico detectado
                self.add_clip(current, clip_type)
        except Exception as e:
            print(f"Error al detectar portapapeles: {e}")

    def on_image_processed(self, unique_id, img, image_hash, image_name, key, thumb_qimage):
        try:
            if key in self.processing_keys:
                self.processing_keys.discard(key)

            if str(image_hash) == self.last_clipboard:
                return

            current = unique_id
            clip_type = "image"  # Específicamente imagen
            self.clipboard_images[unique_id] = img
            self.last_clipboard = str(image_hash)
            
            try:
                if not hasattr(self, '_thumbnail_cache'):
                    self._thumbnail_cache = {}
                cache_key = f"thumb_{unique_id}"
                if thumb_qimage is not None:
                    from PyQt6.QtGui import QPixmap
                    pix = QPixmap.fromImage(thumb_qimage)
                    self._thumbnail_cache[cache_key] = pix
            except Exception as e:
                print(f"Error al convertir thumb en main thread: {e}")

            # Pasar el tipo específico
            self.add_clip(current, clip_type)
        except Exception as e:
            print(f"Error en on_image_processed: {e}")

    def add_clip(self, content, clip_type=None):
        content = str(content).strip()
        if not content or len(content) > 5000:
            return
            
        # Para imágenes, el content es un ID único, no el contenido real
        if clip_type == "image":
            # Verificar si ya existe esta imagen en los clips
            for clip in self.clips[:5]:
                if clip['content'] == content and clip['type'] == 'image' and not clip['pinned']:
                    return
        else:
            # Para texto/URLs, verificar duplicados normales
            for clip in self.clips[:5]:
                if clip['content'] == content and not clip['pinned']:
                    return
            
        if clip_type is None:
            clip_type = self.detect_type(content)
            
        clip = {
            'content': content,
            'type': clip_type,
            'timestamp': datetime.now(),
            'pinned': False
        }
        
        old_clips = list(self.clips)
        self.clips.insert(0, clip)
        
        non_pinned = [c for c in self.clips if not c['pinned']]
        if len(non_pinned) > 20:
            pinned = [c for c in self.clips if c['pinned']]
            self.clips = pinned + non_pinned[:20]
            
        image_keys = [c['content'] for c in self.clips if c['type'] == 'image' and not c['pinned']]
        try:
            limit = int(getattr(self, 'max_images', 10))
        except Exception:
            limit = 10
            
        if len(image_keys) > limit:
            for k in image_keys[limit:]:
                if k in self.clipboard_images:
                    del self.clipboard_images[k]
                    
        visible_keys = set(c['content'] for c in self.clips if c['type'] == 'image')
        self.clipboard_images = {k: v for k, v in self.clipboard_images.items() if k in visible_keys}
        
        if old_clips != self.clips:
            self.refresh_ui()

    def detect_type(self, content):
        url_regex = re.compile(r'(https?://|ftp://|www\.|\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?)', re.IGNORECASE)
        if url_regex.search(content):
            return "url"
        elif re.match(r'^#[0-9A-Fa-f]{6}$', content):
            return "color"
        elif self.is_emoji(content):
            return "emoji"
        else:
            return "text"

    def is_emoji(self, text):
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticones
            u"\U0001F300-\U0001F5FF"  # símbolos & pictogramas
            u"\U0001F680-\U0001F6FF"  # transporte & símbolos de mapa
            u"\U0001F1E0-\U0001F1FF"  # banderas
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        text_stripped = text.strip()
        emojis = emoji_pattern.findall(text_stripped)
        return len(emojis) > 0 and len(''.join(emojis)) >= len(text_stripped) * 0.5

    def copy_and_close(self, content):
        try:
            clipboard = QApplication.clipboard()
            
            if content in self.clipboard_images:
                image = self.clipboard_images[content]
                clipboard.setImage(image)
                print(f"✓ Imagen restaurada al portapapeles")
            else:
                clipboard.setText(content)
                print(f"✓ Texto restaurado al portapapeles")
            
            try:
                if not getattr(self, 'window_pinned', False):
                    self.hide()
            except Exception:
                self.hide()

            try:
                if getattr(self, 'window_pinned', False):
                    # Guardar ventana activa usando el nuevo método multi-backend
                    self.last_active_window = self.input_simulator.get_active_window()
                    
                    # Intentar cambiar de ventana usando el nuevo simulador
                    self.input_simulator.simulate_alt_tab()
                        
                    QTimer.singleShot(250, self.simulate_paste)
                    QTimer.singleShot(800, self.reactivate_petra)
                else:
                    QTimer.singleShot(150, self.simulate_paste)
            except Exception:
                self.simulate_paste()
        except Exception as e:
            print(f"✗ Error: {e}")

    def paste_and_close(self, content):
        self.copy_and_close(content)

    def simulate_paste(self):
        """Simular pegado usando el simulador multi-backend"""
        return self.input_simulator.simulate_paste()

    def reactivate_petra(self):
        """Reactivar la ventana de Petra después de pegar (multi-backend)"""
        # En Wayland, la reactivación puede no ser necesaria o funcionar diferente
        if self.input_simulator.display_server == 'x11':
            try:
                proc = subprocess.run(['xdotool', 'search', '--classname', 'petra'], 
                                    capture_output=True, text=True, timeout=0.5)
                if proc and proc.stdout:
                    wid = proc.stdout.strip().splitlines()[0]
                    if wid:
                        self.input_simulator.activate_window(wid)
            except:
                pass

    def start_clear_animation(self):
        self.clear_progress = 0
        self.clear_timer.start(15)

    def cancel_clear_animation(self):
        self.clear_timer.stop()
        self.clear_progress = 0
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setProgress(0)

    def update_clear_progress(self):
        self.clear_progress += 1
        
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setProgress(self.clear_progress)
        
        if self.clear_progress >= 100:
            self.clear_timer.stop()
            self.clear_all_unpinned()
            self.cancel_clear_animation()

    def clear_all_unpinned(self):
        """Borrar todos los elementos que no estén pinned"""
        self.clips = [c for c in self.clips if c['pinned']]
        pinned_images = [c['content'] for c in self.clips if c['type'] == 'image']
        self.clipboard_images = {k: v for k, v in self.clipboard_images.items() if k in pinned_images}
        self.refresh_ui()