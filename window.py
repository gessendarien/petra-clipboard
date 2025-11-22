from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, 
                             QGridLayout, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QTimer, QThreadPool, QSize
from PyQt6.QtGui import QIcon, QPixmap
from pathlib import Path
import subprocess

from widgets import ProgressButton, ClipItem
from clipboard import ClipboardManager
from filters import FilterManager
from config import ConfigManager
from global_shortcut_multi import GlobalShortcutManager
from themes_manager import ThemesManager

class PetraClipboard(QMainWindow, ClipboardManager, FilterManager, ConfigManager, GlobalShortcutManager):
    def __init__(self):
        QMainWindow.__init__(self)
        ClipboardManager.__init__(self)
        FilterManager.__init__(self)
        ConfigManager.__init__(self)
        GlobalShortcutManager.__init__(self)
        
        # Inicializar atributos necesarios
        self.clips = []  # Añadir esta línea
        self.window_pinned = False  # Añadir esta línea
        
        # Manager de temas
        self.themes_manager = ThemesManager()
        
        self.setup_ui()
        self.load_pinned()
        # self.clear_all_unpinned()  # Comentar esta línea temporalmente
        self.initialize_clipboard_state()
        self.setup_clipboard_monitor()
        self.setup_global_shortcut()
        
        # Aplicar tema después de cargar configuración
        self.apply_theme()
        
    def setup_ui(self):
        self.setWindowTitle("Petra")
        self.setFixedSize(515, 680)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Widget central
        central = QWidget()
        central.setObjectName("main_window")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Barra superior
        self.setup_header(main_layout)
        
        # Barra de búsqueda
        self.setup_search_bar(main_layout)
        
        # Filtros
        self.setup_filters(main_layout)
        
        # Área de scroll
        self.setup_scroll_area(main_layout)
        
        self.center_window()
    
    def setup_header(self, main_layout):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        header_layout.setSpacing(8)
        
        # Botón configuración
        settings_btn = QPushButton("")
        settings_btn.setObjectName("settings_button")
        settings_btn.setFixedSize(38, 38)
        self.setup_icon_button(settings_btn, 'config.png', "⚙️")
        settings_btn.clicked.connect(self.open_settings)
        
        # Botón borrar todo - ProgressButton
        self.clear_btn = ProgressButton("")
        self.clear_btn.setObjectName("clear_button")
        self.clear_btn.setFixedSize(38, 38)
        self.setup_icon_button(self.clear_btn, 'delete.png', "🗑️")
        
        # Conectar señales - IMPORTANTE: usar pressed/released, no clicked
        self.clear_btn.pressed.connect(self.start_clear_animation)
        self.clear_btn.released.connect(self.cancel_clear_animation)
        
        # Botón cerrar
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_button")
        close_btn.setFixedSize(38, 38)
        close_btn.clicked.connect(self.hide)
        
        # Botón fijar ventana
        self.pin_window_btn = QPushButton("")
        self.pin_window_btn.setObjectName("pin_button")
        self.pin_window_btn.setFixedSize(38, 38)
        self.pin_window_btn.setCheckable(True)
        self.setup_pin_button_icon()
        self.pin_window_btn.clicked.connect(self.toggle_window_pin)
        
        header_layout.addWidget(settings_btn)
        header_layout.addWidget(self.clear_btn)
        header_layout.addWidget(self.pin_window_btn)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        main_layout.addWidget(header)
    
    def setup_search_bar(self, main_layout):
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setMinimumHeight(40)
        self.search_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_bar.textChanged.connect(self.filter_items)
        search_layout.addWidget(self.search_bar)
        
        main_layout.addWidget(search_container)
    
    def setup_filters(self, main_layout):
        filters_container = QWidget()
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setContentsMargins(15, 5, 15, 12)
        filters_layout.setSpacing(12)
        
        self.filter_buttons = {}
        filters = [
            ("all", "☰"),
            ("text", "📄"),
            ("image", "🖼"),
            ("url", "🔗"),
            ("emoji", "😀"),
        ]
        
        icon_files = {
            'all': 'all.png',
            'text': 'texts.png',
            'image': 'images.png',
            'url': 'links.png',
            'emoji': 'emojis.png',
        }

        for filter_id, fallback in filters:
            btn = QPushButton("")
            btn.setFixedSize(44, 44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, f=filter_id: self.set_filter(f))
            self.setup_icon_button(btn, icon_files.get(filter_id), fallback)
            self.filter_buttons[filter_id] = btn
            filters_layout.addWidget(btn)

        filters_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.update_filter_styles()
        main_layout.addWidget(filters_container)
    
    def setup_scroll_area(self, main_layout):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        main_layout.addWidget(scroll)
    
    def setup_icon_button(self, button, icon_name, fallback):
        try:
            icons_dir = Path(__file__).parent / 'icons'
            if icon_name:
                icon_path = icons_dir / icon_name
                if icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
                    button.setIconSize(QSize(20, 20))
                    return
            button.setText(fallback)
        except Exception:
            button.setText(fallback)
    
    def setup_pin_button_icon(self):
        try:
            icons_dir = Path(__file__).parent / 'icons'
            pin_path = icons_dir / 'pin.png'
            unpin_path = icons_dir / 'unpinned.png'
            pinned_path = icons_dir / 'pinned.png'
            
            if getattr(self, 'window_pinned', False):
                if unpin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(unpin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                elif pin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                else:
                    self.pin_window_btn.setText("📌")
            else:
                if pinned_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pinned_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                elif pin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                else:
                    self.pin_window_btn.setText("📌")
        except Exception:
            self.pin_window_btn.setText("📌")
            
        # Visibility from config
        try:
            if getattr(self, 'show_pin_btn', False):
                self.pin_window_btn.show()
            else:
                self.pin_window_btn.hide()
        except Exception:
            self.pin_window_btn.hide()
            
        self.pin_window_btn.setChecked(bool(getattr(self, 'window_pinned', False)))
    
    def apply_theme(self):
        """Aplicar el tema actual a toda la interfaz"""
        try:
            # Aplicar tema a la ventana principal
            self.themes_manager.set_theme(self.theme)
            self.themes_manager.apply_theme_to_widget(self)
            
            # Actualizar el color del borde animado del botón eliminar
            theme_colors = self.themes_manager.get_theme_colors()
            if hasattr(self, 'clear_btn') and self.clear_btn:
                # Usar el color específico para el borde o el color accent como fallback
                border_color = theme_colors.get('clear_button_border', theme_colors.get('accent', '#ff6b35'))
                self.clear_btn.setBorderColor(border_color)
            
            # Actualizar estilos de filtros
            self.update_filter_styles()
            
            # Forzar actualización de todos los widgets hijos
            self.update_styles_recursive(self)
            
            # Refrescar UI para aplicar cambios
            self.refresh_ui()
            
        except Exception as e:
            print(f"Error aplicando tema: {e}")
    
    def update_styles_recursive(self, widget):
        """Actualizar estilos recursivamente para todos los widgets hijos"""
        try:
            # Aplicar tema al widget actual
            self.themes_manager.apply_theme_to_widget(widget)
            
            # Recorrer todos los hijos
            for child in widget.findChildren(QWidget):
                self.update_styles_recursive(child)
                
        except Exception as e:
            print(f"Error actualizando estilos: {e}")
    
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def closeEvent(self, event):
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'command_timer'):
            self.command_timer.stop()
        event.accept()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None
        
    def refresh_ui(self):
        #print("=== DEBUG CLIPS ===")
        #for clip in self.clips:
        #    print(f"Content: {clip['content'][:50]}... | Type: {clip['type']}")
        #print("===================")

        # Limpiar layout
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        search_text = self.search_bar.text().lower()
        
        # Separar pinned y no pinned
        pinned = [c for c in self.clips if c['pinned']]
        unpinned = [c for c in self.clips if not c['pinned']]
        
        # Filtrar por tipo y búsqueda - CORREGIDO
        def matches(clip):
            # Si hay texto de búsqueda, filtrar por contenido primero
            if search_text and search_text not in clip['content'].lower():
                return False
            
            # Luego filtrar por tipo
            if self.current_filter == "all":
                return True
            elif self.current_filter == "text":
                return clip['type'] == "text"
            elif self.current_filter == "image":
                return clip['type'] == "image"
            elif self.current_filter == "url":
                return clip['type'] == "url"
            elif self.current_filter == "emoji":
                return clip['type'] == "emoji"
            else:
                return True
        
        pinned = [c for c in pinned if matches(c)]
        unpinned = [c for c in unpinned if matches(c)]
        
        # Mostrar pinned sin etiqueta
        if pinned:
            for clip in pinned:
                self.add_clip_widget(clip)
        
        # Mostrar recientes
        if unpinned:
            for clip in unpinned:
                self.add_clip_widget(clip)   
    
    def add_clip_widget(self, clip):
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 4, 15, 4)
        container_layout.setSpacing(0)
        
        widget = ClipItem(clip['content'], clip['type'], clip['timestamp'], clip['pinned'], self)
        widget.clicked.connect(self.copy_and_close)
        widget.double_clicked.connect(self.paste_and_close)
        widget.delete_requested.connect(lambda: self.delete_clip(clip))
        widget.pin_toggled.connect(lambda: self.toggle_pin(clip))
        
        container_layout.addWidget(widget)
        self.content_layout.insertWidget(self.content_layout.count() - 1, container)
    
    def delete_clip(self, clip):
        self.clips.remove(clip)
        if clip['pinned']:
            self.save_pinned()
        self.refresh_ui()
    
    def toggle_pin(self, clip):
        clip['pinned'] = not clip['pinned']
        self.save_pinned()
        self.refresh_ui()

    # Métodos de filtros
    def set_filter(self, filter_id):
        self.current_filter = filter_id
        self.update_filter_styles()
        if filter_id == "emoji":
            self.show_emoji_picker()
            return
        self.refresh_ui()

    def update_filter_styles(self):
        for filter_id, btn in self.filter_buttons.items():
            if filter_id == self.current_filter:
                btn.setObjectName("filter_button_active")
            else:
                btn.setObjectName("filter_button_inactive")
        
        # Re-aplicar el tema para actualizar los estilos
        self.themes_manager.apply_theme_to_widget(self)

    def filter_items(self):
        self.refresh_ui()

    def show_emoji_picker(self):
        """Mostrar selector de emojis en el área de contenido"""
        # Limpiar el contenido actual
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Crear widget de emojis
        emoji_container = QWidget()
        emoji_layout = QVBoxLayout(emoji_container)
        emoji_layout.setContentsMargins(15, 15, 15, 15)
        emoji_layout.setSpacing(10)
        
        # Grid de emojis
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)
        
        # Lista de emojis modernos uniformes
        emojis = [
            # Caras y emociones
            "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
            "😉", "😊", "😇", "😍", "🤩", "😘", "😗", "😚", "😙", "😋",
            "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐",
            "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😌",
            "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮", "🤧",
            "😵", "🤯", "🤠", "😎", "🤓", "🧐", "😕", "😟", "🙁", "☹️",
            "😮", "😯", "😲", "😳", "😦", "😧", "😨", "😰", "😥", "😢",
            "😭", "😱", "😖", "😣", "😞", "😓", "😩", "😫", "😤", "😡",
            # Gestos y manos
            "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤏", "✌️", "🤞", "🤟",
            "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍", "👎",
            "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏",
            "✍️", "💅", "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻",
            # Corazones y símbolos
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
            "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮️",
            "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️", "🛐",
            "⛎", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐",
            # Objetos tecnológicos
            "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "🕹️", "💽",
            "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽️", "🎞️",
            # Símbolos útiles
            "✅", "✔️", "☑️", "❌", "❎", "✖️", "➕", "➖", "➗", "✳️",
            "✴️", "❇️", "‼️", "⁉️", "❓", "❔", "❕", "❗", "⭐", "🌟",
            "💫", "💥", "💢", "💯", "🔥", "⚡", "🌈", "☀️", "⭕", "🚫",
        ]
        
        row, col = 0, 0
        for emoji in emojis:
            btn = QPushButton(emoji)
            btn.setObjectName("emoji_button")
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, e=emoji: self.insert_emoji(e))
            grid.addWidget(btn, row, col)
            col += 1
            if col > 7:
                col = 0
                row += 1
        
        emoji_layout.addWidget(grid_widget)
        self.content_layout.insertWidget(0, emoji_container)

    def insert_emoji(self, emoji):
        """Insertar emoji en el portapapeles y pegarlo sin agregarlo al historial"""
        self.inserting_emoji = True
        self.last_emoji_inserted = emoji
        self.last_clipboard = emoji
        clipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        
        try:
            # Usar el simulador multi-backend para cambiar de ventana
            self.input_simulator.simulate_alt_tab()
            
            QTimer.singleShot(150, self.simulate_paste)
            QTimer.singleShot(500, self.clear_emoji_flags)
        except Exception as e:
            print(f"Error al cambiar foco: {e}")

    def clear_emoji_flags(self):
        """Limpiar flags de inserción de emoji"""
        self.inserting_emoji = False
        self.last_emoji_inserted = None

    # Métodos de HotkeyManager que necesitan implementación
    def show_window(self):
        """Mostrar ventana (para GlobalShortcutManager)"""
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
        """Alternar el estado de fijar ventana"""
        try:
            self.window_pinned = not getattr(self, 'window_pinned', False)
            self.pin_window_btn.setChecked(self.window_pinned)
            self.update_pin_button_icon()
        except Exception:
            pass

    def update_pin_button_icon(self):
        """Actualizar icono del botón de fijar ventana"""
        try:
            icons_dir = Path(__file__).parent / 'icons'
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
        """Alternar visibilidad de la ventana"""
        if self.isVisible():
            self.hide()
        else:
            self.show_window()