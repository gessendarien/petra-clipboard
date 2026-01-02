from PyQt6.QtCore import QTimer, QThreadPool, QRunnable, QObject, pyqtSignal, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QPainter, QPainterPath
from datetime import datetime
from pathlib import Path
import subprocess
import re
import hashlib

from input_simulator import InputSimulator

class ImageTaskSignals(QObject):
    processed = pyqtSignal(str, object, str, str, object, object)

class ImageTask(QRunnable):
    def __init__(self, image, key, image_name="Imagen.png"):
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
            image_hash = hashlib.md5(bytes(image_data)).hexdigest()

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
        self._image_hashes = {}  # Almacena hashes de imágenes para persistencia
        self._pinned_image_hashes = set()  # Hashes de imágenes fijadas para evitar duplicados
        
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
                    # Usar el mismo proceso de escalado y compresión que ImageTask
                    # para que el hash sea consistente y se detecten duplicados
                    if img.width() > 1200 or img.height() > 1200:
                        img = img.scaled(1200, 1200, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.FastTransformation)
                    
                    from PyQt6.QtCore import QBuffer, QIODevice
                    buffer = QBuffer()
                    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                    img.save(buffer, "PNG", 50)  # Misma calidad que ImageTask
                    image_data = buffer.data()
                    image_hash = hashlib.md5(bytes(image_data)).hexdigest()
                    self.last_clipboard = image_hash
                    
                    # Si la imagen actual del portapapeles ya está en los pins,
                    # añadir su hash a _pinned_image_hashes para evitar duplicados
                    if hasattr(self, '_pinned_image_hashes') and image_hash in self._pinned_image_hashes:
                        # Ya está marcado, no hacer nada extra
                        pass
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
                        # Es una imagen local - procesarla
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
                            image_name = Path(local_path).name or "Imagen"
                            task = ImageTask(img, key, image_name=image_name)
                            task.signals.processed.connect(self.on_image_processed)
                            self.thread_pool.start(task)
                        except Exception as e:
                            print(f"Error al cargar imagen desde archivo: {e}")
                    elif qurl.toString().startswith('file:///'):
                        # Es un archivo local (no imagen) - ignorar
                        # Los archivos copiados desde el explorador generan file:///
                        # y no queremos guardarlos como URLs
                        return
                    else:
                        # Es una URL real (http://, https://, etc.)
                        current = qurl.toString()
                        clip_type = "url"
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
            
            # Verificar si este hash ya existe en imágenes fijadas (evita duplicados al reiniciar)
            if hasattr(self, '_pinned_image_hashes') and str(image_hash) in self._pinned_image_hashes:
                self.last_clipboard = str(image_hash)
                return

            current = unique_id
            clip_type = "image"  # Específicamente imagen
            self.clipboard_images[unique_id] = img
            self.last_clipboard = str(image_hash)
            
            # Guardar el hash de la imagen para poder persistirlo si se fija
            if not hasattr(self, '_image_hashes'):
                self._image_hashes = {}
            self._image_hashes[unique_id] = str(image_hash)
            
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
        
        # Detectar tipo si no se proporciona
        if clip_type is None:
            clip_type = self.detect_type(content)
        
        # NO agregar emojis a la lista de clips - solo se insertan y van a recientes
        if clip_type == "emoji":
            return
        
        # Verificar si ya existe este contenido en CUALQUIER clip (fijado o no)
        for clip in self.clips:
            if clip['content'] == content:
                # Ya existe, no duplicar
                return
            
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
        # Primero verificar si es un comando de terminal (tiene prioridad sobre URLs ambiguas)
        if self.is_terminal_command(content):
            return "command"
        
        # Si tiene espacios y NO empieza con un protocolo explícito, no es URL
        # Esto evita que "cat archivo.txt" sea detectado como URL
        has_spaces = ' ' in content.strip()
        has_explicit_protocol = bool(re.match(r'^(https?://|ftp://)', content.strip(), re.IGNORECASE))
        
        if not has_spaces or has_explicit_protocol:
            # Solo buscar URLs si no hay espacios O si tiene protocolo explícito
            url_regex = re.compile(r'(https?://|ftp://|www\.|\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?)', re.IGNORECASE)
            if url_regex.search(content):
                return "url"
        
        if re.match(r'^#[0-9A-Fa-f]{6}$', content):
            return "color"
        elif self.is_emoji(content):
            return "emoji"
        else:
            return "text"

    def is_terminal_command(self, text):
        """Detectar si el texto parece ser un comando de terminal Linux."""
        text = text.strip()
        
        # No detectar comandos muy largos o multi-línea compleja
        if len(text) > 500 or text.count('\n') > 5:
            return False
        
        # Lista de comandos comunes de Linux/Unix
        common_commands = [
            # Navegación y archivos
            'ls', 'cd', 'pwd', 'mkdir', 'rmdir', 'rm', 'cp', 'mv', 'touch', 'cat',
            'head', 'tail', 'less', 'more', 'find', 'locate', 'which', 'whereis',
            'file', 'stat', 'du', 'df', 'ln', 'readlink', 'tree', 'basename', 'dirname',
            # Permisos y usuarios
            'chmod', 'chown', 'chgrp', 'sudo', 'su', 'whoami', 'id', 'groups',
            'useradd', 'userdel', 'usermod', 'passwd', 'adduser',
            # Procesos
            'ps', 'top', 'htop', 'kill', 'killall', 'pkill', 'pgrep', 'bg', 'fg',
            'jobs', 'nohup', 'nice', 'renice', 'watch', 'timeout',
            # Red
            'ping', 'curl', 'wget', 'ssh', 'scp', 'rsync', 'netstat', 'ss', 'ip',
            'ifconfig', 'dig', 'nslookup', 'host', 'traceroute', 'nc', 'telnet',
            # Paquetes
            'apt', 'apt-get', 'aptitude', 'dpkg', 'yum', 'dnf', 'pacman', 'snap',
            'flatpak', 'pip', 'pip3', 'npm', 'yarn', 'cargo', 'gem', 'brew',
            # Texto
            'grep', 'awk', 'sed', 'cut', 'sort', 'uniq', 'wc', 'tr', 'diff',
            'comm', 'tee', 'xargs', 'printf', 'echo', 'read',
            # Compresión
            'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'bzip2', 'xz', '7z',
            # Sistema
            'systemctl', 'service', 'journalctl', 'dmesg', 'uname', 'hostname',
            'uptime', 'free', 'lscpu', 'lsblk', 'lsusb', 'lspci', 'mount', 'umount',
            'fdisk', 'parted', 'mkfs', 'fsck',
            # Git
            'git', 'gh',
            # Docker/Contenedores
            'docker', 'docker-compose', 'podman', 'kubectl', 'minikube',
            # Desarrollo
            'python', 'python3', 'node', 'java', 'javac', 'gcc', 'g++', 'make',
            'cmake', 'go', 'rustc', 'ruby', 'perl', 'php',
            # Editores/herramientas
            'vim', 'nvim', 'nano', 'emacs', 'code', 'subl',
            # Otros comunes
            'man', 'info', 'help', 'alias', 'export', 'source', 'env', 'printenv',
            'history', 'clear', 'reset', 'exit', 'logout', 'shutdown', 'reboot',
            'date', 'cal', 'bc', 'expr', 'seq', 'yes', 'true', 'false', 'test',
            'xdg-open', 'open', 'xclip', 'xsel', 'notify-send',
        ]
        
        # Obtener primera palabra (comando principal)
        first_line = text.split('\n')[0].strip()
        words = first_line.split()
        if not words:
            return False
        
        first_word = words[0]
        
        # Quitar sudo/env si está al inicio
        if first_word in ['sudo', 'env', 'nohup', 'time']:
            if len(words) > 1:
                first_word = words[1]
            else:
                return False
        
        # Verificar si es un comando conocido
        if first_word in common_commands:
            return True
        
        # Detectar patrones comunes de comandos
        command_patterns = [
            r'^\./[\w.-]+',  # ./script.sh
            r'^\|',  # Pipe al inicio (continuación)
            r'\|\s*\w+',  # Comandos con pipe
            r'^[\w.-]+\s+--?[\w-]',  # comando --opcion o comando -o
            r'^\$\s*\w+',  # $VAR o $ comando (prompt)
        ]
        
        for pattern in command_patterns:
            if re.search(pattern, text):
                return True
        
        return False

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

    def copy_and_close(self, content, use_terminal_paste=False):
        try:
            clipboard = QApplication.clipboard()
            
            # Detectar si es un comando para usar pegado de terminal
            clip_type = None
            for c in self.clips:
                if c.get('content') == content:
                    clip_type = c.get('type')
                    break
            
            is_command = clip_type == 'command' or use_terminal_paste
            
            if content in self.clipboard_images:
                image = self.clipboard_images[content]
                clipboard.setImage(image)
                
                # Actualizar last_clipboard con el hash de la imagen para evitar duplicados
                # cuando el monitor detecte esta misma imagen en el portapapeles
                if hasattr(self, '_image_hashes') and content in self._image_hashes:
                    self.last_clipboard = self._image_hashes[content]
                
                print(f"✓ Imagen restaurada al portapapeles")
            else:
                clipboard.setText(content)
                # Actualizar last_clipboard para texto también
                self.last_clipboard = content
                if is_command:
                    print(f"✓ Comando restaurado al portapapeles (Ctrl+Shift+V)")
                else:
                    print(f"✓ Texto restaurado al portapapeles")
            
            # Decide whether to hide after marking so the copied state can be applied first
            should_hide = False
            try:
                should_hide = not getattr(self, 'window_pinned', False)
            except Exception:
                should_hide = True

            # Marcar el widget como copiado para cambiar su apariencia.
            # Clear existing copied flags and set the clicked one to the string "true"
            try:
                # Clear previous 'copied' state from all ClipItem widgets first
                for i in range(self.content_layout.count()):
                    item = self.content_layout.itemAt(i)
                    if item and item.widget():
                        w = item.widget()
                        # only clear widgets that are currently marked 'true'
                        if w.property('copied') == 'true':
                            w.setProperty('copied', 'false')
                            w.style().unpolish(w)
                            w.style().polish(w)
                            try:
                                if hasattr(w, '_update_background'):
                                    w._update_background()
                            except Exception:
                                pass

                # Set the clicked widget's copied property to the string 'true'
                for i in range(self.content_layout.count()):
                    item = self.content_layout.itemAt(i)
                    if item and item.widget():
                        widget = item.widget()
                        if hasattr(widget, 'content') and widget.content == content:
                            widget.setProperty('copied', 'true')
                            # ensure pressed transient flag isn't left set
                            try:
                                widget.setProperty('pressed', 'false')
                            except Exception:
                                pass
                            widget.style().unpolish(widget)
                            widget.style().polish(widget)
                            try:
                                if hasattr(widget, '_update_background'):
                                    widget._update_background()
                            except Exception:
                                pass
                            break
            except Exception as e:
                print(f"Error marcando widget como copiado: {e}")

            # Persist copied state in the underlying clip data model so it survives UI refreshes
            try:
                for c in self.clips:
                    c['copied'] = (c.get('content') == content)
            except Exception:
                pass

            # Guardar si es comando para usar el método de pegado correcto
            self._pending_paste_is_command = is_command

            # hide after marking if appropriate (keeps marking visible for pinned windows)
            try:
                if should_hide:
                    self.hide()

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
        """Simular pegado usando el simulador multi-backend.
        Usa Ctrl+Shift+V para comandos de terminal, Ctrl+V para el resto."""
        is_command = getattr(self, '_pending_paste_is_command', False)
        self._pending_paste_is_command = False  # Resetear
        
        if is_command:
            return self.input_simulator.simulate_terminal_paste()
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
        """Solo iniciar el timer, el botón ya se marcó como presionado"""
        self.clear_progress = 0
        self.clear_timer.start(15)

    def cancel_clear_animation(self):
        """Solo detener el timer, el botón ya se reseteó"""
        self.clear_timer.stop()
        self.clear_progress = 0

    def update_clear_progress(self):
        self.clear_progress += 1
        
        if hasattr(self, 'clear_btn'):
            self.clear_btn.setProgress(self.clear_progress)
        
        if self.clear_progress >= 100:
            self.clear_timer.stop()
            self.clear_all_unpinned()
            # Resetear el botón después de completar
            if hasattr(self, 'clear_btn'):
                self.clear_btn.setProgress(0)
    def clear_all_unpinned(self):
        """Borrar todos los elementos que no estén pinned"""
        self.clips = [c for c in self.clips if c['pinned']]
        pinned_images = [c['content'] for c in self.clips if c['type'] == 'image']
        self.clipboard_images = {k: v for k, v in self.clipboard_images.items() if k in pinned_images}
        if hasattr(self, 'refresh_ui'):
            self.refresh_ui()