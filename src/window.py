from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, 
                             QGridLayout, QSizePolicy, QApplication, QGraphicsOpacityEffect,
                             QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, QTimer, QThreadPool, QSize, QEvent, pyqtSignal, QRectF
from PyQt6.QtGui import QIcon, QPixmap, QFont, QFontDatabase, QPainter, QColor, QBrush, QPen, QRadialGradient, QLinearGradient, QAction
from pathlib import Path
import os
import subprocess

from widgets import ProgressButton, ClipItem
from clipboard import ClipboardManager
from filters import FilterManager
from config import ConfigManager
from global_shortcut_multi import GlobalShortcutManager
from themes_manager import ThemesManager
from emoji_keywords import search_emojis, ALL_EMOJIS, EMOJI_CATEGORIES


def get_emoji_font():
    """Obtiene la mejor fuente de emoji colorida disponible en el sistema."""
    emoji_fonts = [
        "Noto Color Emoji",
        "Twemoji",
        "Twitter Color Emoji", 
        "Apple Color Emoji",
        "Segoe UI Emoji",
        "EmojiOne Color",
        "JoyPixels",
        "OpenMoji Color",
    ]
    available = QFontDatabase.families()
    for font_name in emoji_fonts:
        if font_name in available:
            return font_name
    return None


def ensure_emoji_presentation(emoji):
    """
    Asegura que el emoji use presentación gráfica (colorida) en lugar de texto.
    Agrega el selector de variación U+FE0F si es necesario.
    """
    # If it already ends with emoji variation selector, return as is
    if emoji.endswith('\uFE0F'):
        return emoji
    
    # List of emojis that commonly render as text without the selector
    text_style_emojis = {
        '☺', '☹', '☠', '✋', '✌', '☝', '✍', '❤', '♈', '♉', '♊', '♋',
        '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓', '⛎', '☮', '✝', '☪',
        '☸', '✡', '☯', '☦', '⛈', '☀', '⛅', '☁', '⌛', '⏳', '⌚', '⏰',
        '⏱', '⏲', '☢', '☣', '↩', '↪', '⚡', '♻', '☑', '✔', '✖', '❌',
        '❎', '➕', '➖', '➗', '✳', '✴', '❇', '‼', '⁉', '❓', '❔', '❕',
        '❗', '▪', '▫', '◾', '◽', '◼', '◻', '⬛', '⬜', '⭐', '⭕',
    }
    
    # Get the first base character (without modifiers)
    base_char = emoji[0] if emoji else ''
    
    # If it is an emoji that tends to show as text, add selector
    if base_char in text_style_emojis:
        return emoji + '\uFE0F'
    

    return emoji


class EmojiCarousel(QWidget):
    categorySelected = pyqtSignal(str, list)

    def __init__(self, categories, emoji_font_name=None, parent=None):
        super().__init__(parent)
        self.categories = categories  # List of (name, emojis)
        self.current_index = 0
        self.emoji_font_name = emoji_font_name
        self.setFixedHeight(50)
        self.setMouseTracking(True)
        # Calculate item positions
        self.item_width = 44
        self.spacing = 6
        self.spacing = 6
        # Animation
        self.anim_offset = 0.0
        self.anim_timer = QTimer(self)
        self.anim_timer.setInterval(16)  # ~60 FPS
        self.anim_timer.timeout.connect(self._update_animation)
        
        # Scroll Sensitivity
        self._scroll_accumulator = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw container background (pill shape)
        width = self.width()
        height = self.height()
        
        # Draw items
        center_x = width / 2
        center_y = height / 2
        
        # We show 5 items: current, 2 left, 2 right
        # But we need to handle cyclic scrolling logic visually if possible, 
        # or just clamp. The requirement says "scrollable", so let's assume cyclic or bounded.
        # Given 16 categories, cyclic is nice.
        
        num_items = len(self.categories)
        if num_items == 0:
            return

        visible_range = 2  # 2 on each side
        
        for i in range(-visible_range, visible_range + 1):
            idx = (self.current_index + i) % num_items
            category_name, category_emojis = self.categories[idx]
            
            # Position relative to center
            # Apply animation offset
            # When moving next (anim_offset goes 1 -> 0), items shift left.
            # When moving prev (anim_offset goes -1 -> 0), items shift right.
            visual_i = i + self.anim_offset
            
            offset_x = visual_i * (self.item_width + self.spacing)
            x = center_x + offset_x
            y = center_y
            
            # Scale and opacity based on distance from center
            dist = abs(visual_i)
            
            scale = max(0.8, 1.0 - 0.2 * dist)
            opacity = max(0.6, 1.0 - 0.4 * dist)
            
            if dist < 0.5:
                # Center item (or transitioning to/from it)
                bg_color = QColor("#A855F7")
                bg_color.setAlpha(int(255 * (1.0 - dist)))
                icon_color = QColor("#FFFFFF")
            else:
                bg_color = Qt.GlobalColor.transparent
                icon_color = QColor("#CCCCCC")
                
            # Draw Item
            painter.save()
            painter.translate(x, y)
            painter.scale(scale, scale)
            
            # Draw background for center item
            if dist < 0.9: # Show background only when near center
                path = QRectF(-18, -18, 36, 36)
                painter.setBrush(QBrush(bg_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(path, 12, 12)
                
                # Add a subtle glow
                if dist < 0.2:
                    gradient = QRadialGradient(0, 0, 24)
                    gradient.setColorAt(0, QColor(168, 85, 247, int(100 * (1.0 - dist*5))))
                    gradient.setColorAt(1, Qt.GlobalColor.transparent)
                    # painter.setBrush(QBrush(gradient))
                    # painter.drawEllipse(-40, -40, 80, 80)

            # Draw Icons/Emoji
            # Since we don't have separate icons for categories in the description,
            # we use the first emoji of the category as the icon.
            representative_emoji = category_name.split()[0] # Name is like "🍔 Comida"
            display_emoji = ensure_emoji_presentation(representative_emoji)
            
            painter.setOpacity(opacity)
            font = QFont(self.emoji_font_name) if self.emoji_font_name else self.font()
            font.setPixelSize(22)
            painter.setFont(font)
            painter.setPen(QColor("#FFFFFF") if dist < 0.5 else QColor("#888888"))

            # Text rect
            # Adjusted to center aesthetically (moved Left 1px, Down 2px from original)
            text_rect = QRectF(-17, -16, 36, 36)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_emoji)

            painter.restore()

    def mousePressEvent(self, event):
        # Allow clicking on side items to select them
        center_x = self.width() / 2
        click_x = event.position().x()
        
        # Simplified navigation: Click Right -> Next, Click Left -> Prev
        # Center deadzone to avoid accidental clicks on the selected item
        deadzone = 20
        
        if click_x > center_x + deadzone:
            self.scroll_next()
        elif click_x < center_x - deadzone:
            self.scroll_prev()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        self._scroll_accumulator += angle
        
        # Threshold for scrolling (standard wheel notch is 120)
        # We require at least one notch or significant touchpad movement
        threshold = 120
        
        if self._scroll_accumulator >= threshold:
            self.scroll_prev()
            self._scroll_accumulator = 0
            # Optional: Keep remainder if you want "momentum" logic, 
            # but resetting is safer for reducing sensitivity.
        elif self._scroll_accumulator <= -threshold:
            self.scroll_next()
            self._scroll_accumulator = 0

    def start_animation(self, direction):
        # direction: 1 (next, come from right), -1 (prev, come from left)
        # We update index immediately, but set offset to visually 'undo' the change
        # If we go next (idx + 1), we want to appear as if we are at idx, so offset = 1 
        # (center is at visual 1, which puts it to the right, wait...)
        
        # If we move index +1 (Next), the old center is now at -1.
        # We want to animate from Old Center (now -1) to New Center (0).
        # So we start offset at 1.0? 
        # visual_pos = index + offset. 
        # At start: new_index + offset = old_index
        # offset = old_index - new_index
        
        if direction > 0: # Next
             self.anim_offset = 1.0
             self.current_index = (self.current_index + 1) % len(self.categories)
        else: # Prev
             self.anim_offset = -1.0
             self.current_index = (self.current_index - 1) % len(self.categories)
             
        self.anim_timer.start()
        self._emit_selection()
        self.update()

    def _update_animation(self):
        # Interpolate anim_offset towards 0
        if abs(self.anim_offset) < 0.05:
            self.anim_offset = 0.0
            self.anim_timer.stop()
        else:
            self.anim_offset *= 0.6
        self.update()

    def scroll_next(self):
        self.start_animation(1)

    def scroll_prev(self):
        self.start_animation(-1)
        
    def _emit_selection(self):
        name, emojis = self.categories[self.current_index]
        self.categorySelected.emit(name, emojis)


class PetraClipboard(QMainWindow, ClipboardManager, FilterManager, ConfigManager):
    def __init__(self):
        QMainWindow.__init__(self)
        ClipboardManager.__init__(self)
        FilterManager.__init__(self)
        ConfigManager.__init__(self)

        # Shortcut manager as composed object (not inherited)
        self.shortcut_manager = GlobalShortcutManager(
            on_toggle=self._handle_shortcut_toggle,
            on_show=self.show_window,
            on_hide=self.hide
        )
        
        self.clips = []
        self.window_pinned = False
        
        self.themes_manager = ThemesManager()
        # guard to avoid re-entrant key handling
        self._handling_key = False
        # persist currently selected clip content between UI refreshes
        self._selected_content = None
        # whether keyboard-based selection mode is active (disabled by default)
        # selection visuals only appear after the user presses a key.
        self._keyboard_selection_active = False
        # track long-press emulation for keys that simulate header buttons
        self._key_q_down = False
        self._key_w_down = False
        
        self.setup_ui()
        self.load_pinned()
        self.initialize_clipboard_state()
        self.setup_clipboard_monitor()
        self.shortcut_manager.setup_global_shortcut(self.shortcut)
        
        self.apply_theme()
        
        # Initialize system tray icon
        self.setup_tray_icon()

        # ── Auto-update checker ──────────────────────────────────────
        self._update_available_version = None
        self._pending_update_anim = False
        self._update_checker = None
        self._setup_update_checker()

    def _setup_update_checker(self):
        """Launch a background update check 3 seconds after startup."""
        from updater import UpdateChecker
        self._update_checker = UpdateChecker(self)
        self._update_checker.update_available.connect(self._on_update_available)
        QTimer.singleShot(3000, self._update_checker.start)

    def _on_update_available(self, version):
        """Handle the update_available signal from UpdateChecker."""
        # Always store the available version and mark animation as pending
        self._update_available_version = version
        self._pending_update_anim = True
        # Only suppress the tray notification if user chose "don't remind" or is snap
        from updater import detect_install_type
        if self.config.get('ignored_update') == version or detect_install_type() == 'snap':
            return
        # System tray notification (language-aware)
        if hasattr(self, 'tray_icon'):
            lang = getattr(self, 'language', 'es')
            msg = "Nueva versión disponible" if lang == 'es' else "New version available"
            self.tray_icon.showMessage(
                "Petra",
                msg,
                QSystemTrayIcon.MessageIcon.Information,
                4000,
            )

    def _handle_shortcut_toggle(self):
        """Toggle window visibility — called by the shortcut manager."""
        if self.isVisible():
            self.hide()
        else:
            self.show_window()

    def setup_tray_icon(self):
        """Configura el icono de la bandeja del sistema"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Resolvemos las rutas de los iconos
        icons_root = Path(__file__).parent.parent / 'icons'
        icon_path = icons_root / 'petra_systray.png'
        
        # Cadena de fallback local
        if not icon_path.exists():
            icon_path = icons_root / 'petra.png'
        if not icon_path.exists():
            icons_folder = getattr(self.themes_manager, 'get_icons_folder', lambda: 'dark')()
            icon_path = icons_root / icons_folder / 'all.png'
            
        icon = QIcon()
        if icon_path.exists():
            # MUY IMPORTANTE PARA FLATPAK/WAYLAND: 
            # Creando el QIcon a partir de un QPixmap fuerza a Qt a enviar
            # los píxeles de la imagen (RGBA) por D-Bus (SNI) al host.
            # Si usamos QIcon(str(path)), Qt envía el string de la ruta absoluta.
            # Como la ruta es interna del sandbox de Flatpak ("/app/..."), el 
            # host de GNOME/PopOS no encuentra la imagen y muestra un icono invisible.
            pixmap = QPixmap(str(icon_path))
            icon = QIcon(pixmap)
        else:
            icon = self.style().standardIcon(Qt.Style.SP_ComputerIcon)
                
        self.tray_icon.setIcon(icon)
        
        # Context Menu
        tray_menu = QMenu()
        
        show_action = QAction("Mostrar", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect activation (click)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """Maneja la activación del icono de la bandeja"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_window()


    def setup_ui(self):
        self.setWindowTitle("Petra")
        self.setFixedSize(515, 680)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Performance: debounce refresh_ui to batch updates
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setSingleShot(True)
        self._refresh_timer.timeout.connect(self._do_refresh_ui)
        
        central = QWidget()
        central.setObjectName("main_window")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        # Bottom margin so main_window rounded corners are visible
        main_layout.setContentsMargins(0, 0, 0, 12)
        main_layout.setSpacing(0)
        
        self.setup_header(main_layout)
        self.setup_search_bar(main_layout)
        self.setup_filters(main_layout)
        self.setup_scroll_area(main_layout)
        
        self.center_window()

        # Install a minimal global key listener so arrow keys (and later other
        # shortcuts) are handled at the application level regardless of focus.
        try:
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
        except Exception:
            pass
    
    def setup_header(self, main_layout):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 0, 15, 0)
        header_layout.setSpacing(8)
        
        self.settings_btn = QPushButton("")
        self.settings_btn.setObjectName("settings_button")
        self.settings_btn.setFixedSize(38, 38)
        self.setup_icon_button(self.settings_btn, 'config.png')
        self.settings_btn.clicked.connect(self.open_settings)
        
        self.clear_btn = ProgressButton("")
        self.clear_btn.setObjectName("clear_button")
        self.clear_btn.setFixedSize(38, 38)
        self.setup_icon_button(self.clear_btn, 'delete.png')
        
        self.clear_btn.pressed.connect(self.start_clear_animation)
        self.clear_btn.released.connect(self.cancel_clear_animation)
        
        # Close button WITH "X"
        close_btn = QPushButton("✕")
        close_btn.setObjectName("close_button")
        close_btn.setFixedSize(38, 38)
        close_btn.clicked.connect(self.hide)
        
        self.pin_window_btn = QPushButton("")
        self.pin_window_btn.setObjectName("pin_button")
        self.pin_window_btn.setFixedSize(38, 38)
        self.pin_window_btn.setCheckable(True)
        self.setup_pin_button_icon()
        self.pin_window_btn.clicked.connect(self.toggle_window_pin)
        
        header_layout.addWidget(self.settings_btn)
        header_layout.addWidget(self.clear_btn)
        header_layout.addWidget(self.pin_window_btn)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)
        
        main_layout.addWidget(header)
    
    def setup_search_bar(self, main_layout):
        from PyQt6.QtGui import QAction, QPixmap, QPainter, QColor
        from PyQt6.QtCore import QSize
        
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 8, 12, 8)
        search_layout.setSpacing(0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setMinimumHeight(40)
        self.search_bar.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_bar.textChanged.connect(self.filter_items)
        self.search_bar.textChanged.connect(self._update_clear_action_visibility)
        
        # X action to clear text (positioned INSIDE search_bar on the right)
        self.search_clear_action = QAction(self.search_bar)
        self.search_clear_action.triggered.connect(self._clear_search_text)
        self.search_bar.addAction(self.search_clear_action, QLineEdit.ActionPosition.TrailingPosition)
        # Hide action by default (will show when there is text)
        self.search_clear_action.setVisible(False)
        # Update icon with theme color
        self._update_search_clear_icon()
        
        search_layout.addWidget(self.search_bar)
        main_layout.addWidget(search_container)
    
    def _update_search_clear_icon(self):
        """Actualiza el ícono X de limpiar búsqueda con el color del tema"""
        from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont
        from PyQt6.QtCore import Qt
        
        if not hasattr(self, 'search_clear_action'):
            return
        
        # Get confirm_text color from current theme
        try:
            theme_colors = self.themes_manager.get_theme_colors()
            text_color = theme_colors.get('confirm_text', '#FFFFFF')
        except Exception:
            text_color = '#FFFFFF'
        
        # Create a pixmap with X drawn in theme color
        size = 16
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QColor(text_color))
        font = QFont()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "✕")
        painter.end()
        
        self.search_clear_action.setIcon(QIcon(pixmap))
    
    def _update_clear_action_visibility(self, text):
        """Mostrar u ocultar la acción X según si hay texto"""
        if hasattr(self, 'search_clear_action'):
            self.search_clear_action.setVisible(bool(text))
    
    def _clear_search_text(self):
        """Limpiar el texto del buscador"""
        if hasattr(self, 'search_bar'):
            self.search_bar.clear()
            self.search_bar.setFocus()
    
    def setup_filters(self, main_layout):
        filters_container = QWidget()
        filters_layout = QHBoxLayout(filters_container)
        filters_layout.setContentsMargins(15, 5, 15, 12)
        filters_layout.setSpacing(12)
        
        self.filter_buttons = {}
        filters = [
            ("all", "all.png"),
            ("text", "texts.png"),
            ("image", "images.png"),
            ("url", "links.png"),
            ("emoji", "emojis.png"),
        ]

        for filter_id, icon_file in filters:
            btn = QPushButton("")
            btn.setFixedSize(44, 44)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, f=filter_id: self.set_filter(f))
            self.setup_icon_button(btn, icon_file)
            self.filter_buttons[filter_id] = btn
            filters_layout.addWidget(btn)

        filters_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.update_filter_styles()
        main_layout.addWidget(filters_container)
    
    def setup_scroll_area(self, main_layout):
        scroll = QScrollArea()
        scroll.setObjectName("main_scroll_area")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        self.scroll_area = scroll
        main_layout.addWidget(scroll)
    
    def setup_icon_button(self, button, icon_name):
        try:
            icons_folder = self.themes_manager.get_icons_folder() if hasattr(self, 'themes_manager') else 'dark'
            icons_dir = Path(__file__).parent.parent / 'icons' / icons_folder
            if icon_name:
                icon_path = icons_dir / icon_name
                if icon_path.exists():
                    button.setIcon(QIcon(str(icon_path)))
                    button.setIconSize(QSize(20, 20))
        except Exception:
            pass
    
    def setup_pin_button_icon(self):
        try:
            icons_folder = self.themes_manager.get_icons_folder() if hasattr(self, 'themes_manager') else 'dark'
            icons_dir = Path(__file__).parent.parent / 'icons' / icons_folder
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
                if pinned_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pinned_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                elif pin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
            
        try:
            if getattr(self, 'show_pin_btn', False):
                self.pin_window_btn.show()
            else:
                self.pin_window_btn.hide()
        except Exception:
            self.pin_window_btn.hide()
            
        self.pin_window_btn.setChecked(bool(getattr(self, 'window_pinned', False)))
    
    def apply_theme(self):
        try:
            self.themes_manager.set_theme(self.theme)
            self.themes_manager.apply_theme_to_widget(self)
            
            theme_colors = self.themes_manager.get_theme_colors()
            if hasattr(self, 'clear_btn') and self.clear_btn:
                border_color = theme_colors.get('clear_button_border', theme_colors.get('accent', '#ff6b35'))
                self.clear_btn.setBorderColor(border_color)
            
            # Update header icons according to theme
            self.update_header_icons()
            
            # Update search clear icon with theme color
            if hasattr(self, '_update_search_clear_icon'):
                self._update_search_clear_icon()
            
            self.update_filter_styles()
            self.update_styles_recursive(self)
            self.refresh_ui()
            
        except Exception as e:
            print(f"Error aplicando tema: {e}")
    
    def update_header_icons(self):
        """Update header button icons according to current theme"""
        try:
            icons_folder = self.themes_manager.get_icons_folder()
            icons_dir = Path(__file__).parent.parent / 'icons' / icons_folder
            
            # Update settings button icon
            if hasattr(self, 'settings_btn') and self.settings_btn:
                config_path = icons_dir / 'config.png'
                if config_path.exists():
                    self.settings_btn.setIcon(QIcon(str(config_path)))
                    self.settings_btn.setIconSize(QSize(20, 20))
            
            # Update clear button icon
            if hasattr(self, 'clear_btn') and self.clear_btn:
                delete_path = icons_dir / 'delete.png'
                if delete_path.exists():
                    self.clear_btn.setIcon(QIcon(str(delete_path)))
                    self.clear_btn.setIconSize(QSize(20, 20))
            
            # Update pin button icon
            self.setup_pin_button_icon()
            
            # Update filter button icons
            filter_icons = {
                "all": "all.png",
                "text": "texts.png",
                "image": "images.png",
                "url": "links.png",
                "emoji": "emojis.png",
            }
            if hasattr(self, 'filter_buttons'):
                for filter_id, btn in self.filter_buttons.items():
                    icon_file = filter_icons.get(filter_id)
                    if icon_file:
                        icon_path = icons_dir / icon_file
                        if icon_path.exists():
                            btn.setIcon(QIcon(str(icon_path)))
                            btn.setIconSize(QSize(20, 20))
        except Exception:
            pass
    
    def update_styles_recursive(self, widget):
        try:
            self.themes_manager.apply_theme_to_widget(widget)
            # findChildren finds all descendants recursively, so we just need to iterate once
            for child in widget.findChildren(QWidget):
                self.themes_manager.apply_theme_to_widget(child)
        except Exception:
            pass
    
    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
    
    def position_at_left(self):
        """Posicionar la ventana a la izquierda de la pantalla con margen"""
        try:
            screen = QApplication.primaryScreen().geometry()
            margin = 200  # Margin from left edge
            x = margin
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception:
            self.center_window()
    
    def position_at_right(self):
        """Posicionar la ventana a la derecha de la pantalla con margen"""
        try:
            screen = QApplication.primaryScreen().geometry()
            margin = 200  # Margin from right edge
            x = screen.width() - self.width() - margin
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        except Exception:
            self.center_window()
    
    def position_at_mouse(self):
        """Posicionar la ventana en la ubicación actual del mouse"""
        try:
            from PyQt6.QtGui import QCursor
            cursor_pos = QCursor.pos()
            screen = QApplication.primaryScreen().geometry()
            
            # Calculate position so window does not go off screen
            x = cursor_pos.x() - self.width() // 2
            y = cursor_pos.y() - 20  # A little above the cursor
            
            # Ensure it does not go off edges
            if x < 0:
                x = 0
            elif x + self.width() > screen.width():
                x = screen.width() - self.width()
                
            if y < 0:
                y = 0
            elif y + self.height() > screen.height():
                y = screen.height() - self.height()
            
            self.move(x, y)
        except Exception:
            # Fallback to center if error
            self.center_window()
    
    def closeEvent(self, event):
        # Don't close, just hide the window so it can be reopened with the shortcut
        event.ignore()
        self.hide()
    
    def quit_application(self):
        """Actually quit the application"""
        if hasattr(self, 'timer'):
            self.timer.stop()
        if hasattr(self, 'shortcut_manager'):
            self.shortcut_manager.cleanup_fifo()
        QApplication.quit()
    
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
        """Debounced refresh - batches rapid updates together"""
        if hasattr(self, '_refresh_timer'):
            self._refresh_timer.start(50)  # 50ms debounce
        else:
            # Fallback if called before init completes
            self._do_refresh_ui()
    
    def _do_refresh_ui(self):
        """Actual UI refresh logic"""
        # If we are in emoji filter, show picker instead of clips
        if getattr(self, 'current_filter', None) == 'emoji':
            search_query = self.search_bar.text() if hasattr(self, 'search_bar') else ""
            self.show_emoji_picker(search_query)
            return
        
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        search_text = self.search_bar.text().lower()
        
        pinned = [c for c in self.clips if c['pinned']]
        unpinned = [c for c in self.clips if not c['pinned']]
        
        def matches(clip):
            if search_text and search_text not in clip['content'].lower():
                return False
            
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
        
        # Performance: limit visible items to 50
        MAX_VISIBLE_ITEMS = 50
        visible_unpinned = unpinned[:max(0, MAX_VISIBLE_ITEMS - len(pinned))]
        
        if pinned:
            for clip in pinned:
                self.add_clip_widget(clip)
        
        if visible_unpinned:
            for clip in visible_unpinned:
                self.add_clip_widget(clip)   
        # Ensure there is a selection among visible clips. If we had a
        # previously selected clip (self._selected_content) try to restore it.
        try:
            visible = self.get_visible_clip_widgets()
            # if none currently marked as selected, pick the first one
            found = False
            for w in visible:
                try:
                    if w.property('selected') == 'true':
                        found = True
                        break
                except Exception:
                    pass

            if not found and visible:
                # if we were tracking a previously selected content, restore it
                if self._selected_content:
                    for w in visible:
                        try:
                            if getattr(w, 'content', None) == self._selected_content:
                                self._set_selected_clip_widget(w)
                                found = True
                                break
                        except Exception:
                            pass

            # If there is still no selection, only auto-select the first
            # visible item when keyboard-selection mode is active. When the
            # window first appears keyboard-selection should be inactive so
            # nothing is highlighted until the user presses a key.
            if not found and visible and getattr(self, '_keyboard_selection_active', False):
                self._set_selected_clip_widget(visible[0])
        except Exception:
            pass
    
    def add_clip_widget(self, clip):
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(15, 4, 15, 4)
        container_layout.setSpacing(0)
        
        widget = ClipItem(clip['content'], clip['type'], clip['timestamp'], clip['pinned'], self)
        # Apply persisted copied state (if any) so the widget reflects copied appearance after refresh
        try:
            # Ensure transient states are cleared when creating the widget
            widget.setProperty('pressed', 'false')
            widget.setProperty('hover', 'false')

            if clip.get('copied'):
                widget.setProperty('copied', 'true')
            else:
                widget.setProperty('copied', 'false')
            # restore selected state if this content was the previously selected one
            try:
                if getattr(self, '_selected_content', None) and widget.content == self._selected_content:
                    widget.setProperty('selected', 'true')
                    try:
                        widget.setProperty('hover', 'true')
                    except Exception:
                        pass
                else:
                    widget.setProperty('selected', 'false')
                    try:
                        widget.setProperty('hover', 'false')
                    except Exception:
                        pass
            except Exception:
                widget.setProperty('selected', 'false')
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            try:
                # ensure overlay background matches persisted state
                if hasattr(widget, '_update_background'):
                    widget._update_background()
            except Exception:
                pass
        except Exception:
            pass
        widget.clicked.connect(self.copy_and_close)
        widget.double_clicked.connect(self.paste_and_close)
        widget.delete_requested.connect(lambda: self.delete_clip(clip))
        widget.pin_toggled.connect(lambda: self.toggle_pin(clip))
        # Connect signal for image preview
        if clip['type'] == 'image':
            widget.image_preview_requested.connect(self.show_image_preview)
        
        container_layout.addWidget(widget)
        self.content_layout.insertWidget(self.content_layout.count() - 1, container)
    
    def delete_clip(self, clip):
        # If it is a pinned image, remove its hash from set
        if clip['type'] == 'image' and clip['pinned']:
            if hasattr(self, '_image_hashes') and clip['content'] in self._image_hashes:
                image_hash = self._image_hashes[clip['content']]
                if hasattr(self, '_pinned_image_hashes'):
                    self._pinned_image_hashes.discard(image_hash)
        
        self.clips.remove(clip)
        
        # Clean orphaned image caches
        if clip['type'] == 'image':
            if clip['content'] in self.clipboard_images:
                del self.clipboard_images[clip['content']]
            self._cleanup_image_caches()
        
        if clip['pinned']:
            self.save_pinned()
        self.refresh_ui()
    
    def toggle_pin(self, clip):
        clip['pinned'] = not clip['pinned']
        
        # If it is an image, update pinned hashes set
        if clip['type'] == 'image' and hasattr(self, '_image_hashes'):
            image_hash = self._image_hashes.get(clip['content'])
            if image_hash:
                if not hasattr(self, '_pinned_image_hashes'):
                    self._pinned_image_hashes = set()
                if clip['pinned']:
                    self._pinned_image_hashes.add(image_hash)
                else:
                    self._pinned_image_hashes.discard(image_hash)
        
        self.save_pinned()
        # Clear selected content to avoid hover state being restored after refresh
        self._selected_content = None
        self._keyboard_selection_active = False
        self.refresh_ui()

    def show_image_preview(self, content):
        """Muestra el diálogo de vista previa de imagen.
        
        Args:
            content: La clave del contenido de la imagen en clipboard_images
        """
        try:
            # Verify image exists in cache
            if content not in self.clipboard_images:
                return
            
            # Import preview dialog
            from dialogs import ImagePreviewDialog
            
            # Get original image
            image = self.clipboard_images[content]
            
            # Create and show dialog
            preview_dialog = ImagePreviewDialog(image, self)
            preview_dialog.exec()
            
        except Exception as e:
            print(f"Error al mostrar vista previa de imagen: {e}")

    def set_filter(self, filter_id):
        self.current_filter = filter_id
        # Reset recent emoji selection when changing filter
        self.selected_recent_emoji_index = -1
        # Reset keyboard selection state to avoid incorrect highlighting
        self._selected_content = None
        self._keyboard_selection_active = False
        # Clear 'copied' state from all clips to avoid them appearing highlighted
        for c in self.clips:
            c['copied'] = False
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
        
        self.themes_manager.apply_theme_to_widget(self)

    def filter_items(self):
        # If we are in emoji filter, update picker with search
        if getattr(self, 'current_filter', None) == 'emoji':
            search_query = self.search_bar.text() if hasattr(self, 'search_bar') else ""
            self.show_emoji_picker(search_query)
            return
        self.refresh_ui()

    def show_emoji_picker(self, search_query=""):
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        emoji_container = QWidget()
        emoji_layout = QVBoxLayout(emoji_container)
        emoji_layout.setContentsMargins(15, 15, 15, 15)
        emoji_layout.setSpacing(8)
        
        emoji_font_name = get_emoji_font()
        
        # === SMALL RECENT TABLE (2 rows x 8 columns) ===
        recent_widget = QWidget()
        recent_grid = QGridLayout(recent_widget)
        recent_grid.setSpacing(8)
        recent_grid.setContentsMargins(0, 0, 0, 0)
        
        # Create 16 empty slots (2 rows x 8 columns)
        recent_emojis = getattr(self, 'recent_emojis', [])[:16]
        self.recent_emoji_buttons = []  # Save reference to buttons
        self.selected_recent_emoji_index = -1  # Selected emoji index (-1 = none)
        self._emoji_keyboard_nav_active = False  # Flag to detect keyboard navigation
        
        for i in range(16):
            row = i // 8
            col = i % 8
            
            btn = QPushButton()
            btn.setObjectName("emoji_button")
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            if i < len(recent_emojis):
                emoji = recent_emojis[i]
                display_emoji = ensure_emoji_presentation(emoji)
                btn.setText(display_emoji)
                btn.clicked.connect(lambda checked, e=emoji: self.insert_emoji(e))
                # Detect mouse enter via eventFilter to avoid Qt segfault
                btn.installEventFilter(self)
                if emoji_font_name:
                    btn.setFont(QFont(emoji_font_name, 24))
            else:
                # Empty slot with dimmer style
                btn.setEnabled(False)
                btn.setStyleSheet("QPushButton { background-color: #2a2a2a; border: 1px dashed #444; }")
            
            self.recent_emoji_buttons.append(btn)
            recent_grid.addWidget(btn, row, col)
        
        emoji_layout.addWidget(recent_widget)
        
        # Visual separator
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #444;")
        emoji_layout.addWidget(separator)
        emoji_layout.addSpacing(8)
        
        # === MAIN EMOJIS SECTION ===
        if search_query:
            # If there is search, show results in simple grid (no accordions)
            emojis = search_emojis(search_query, ALL_EMOJIS)
            if emojis:
                grid_widget = QWidget()
                grid = QGridLayout(grid_widget)
                grid.setSpacing(8)
                self._populate_emoji_grid(emojis, grid, emoji_font_name)
                emoji_layout.addWidget(grid_widget)
            else:
                # If no results, show message according to language
                lang = getattr(self, 'language', 'es')
                if lang == 'es':
                    msg = f"No se encontraron emojis para '{search_query}'"
                else:
                    msg = f"No emojis found for '{search_query}'"
                no_results = QLabel(msg)
                no_results.setStyleSheet("color: #888; font-size: 14px; padding: 20px;")
                no_results.setAlignment(Qt.AlignmentFlag.AlignCenter)
                emoji_layout.addWidget(no_results)
        else:
            # No search: show category grid (2 rows x 8 columns)
            # Custom Carousel
            categories = list(EMOJI_CATEGORIES.items())
            self.carousel = EmojiCarousel(categories, emoji_font_name, self)
            
            # Container for content
            self._emoji_category_content = QWidget()
            self._emoji_category_content_layout = QGridLayout(self._emoji_category_content)
            self._emoji_category_content_layout.setSpacing(8)
            self._emoji_category_content_layout.setContentsMargins(5, 10, 5, 10)
            
            # Nested Scroll Area
            self.emoji_scroll = QScrollArea()
            self.emoji_scroll.setWidgetResizable(True)
            self.emoji_scroll.setWidget(self._emoji_category_content)
            self.emoji_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            # Remove border/background from scroll area to blend in
            self.emoji_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            
            # Connect
            self.carousel.categorySelected.connect(
                lambda name, emojis: self._on_emoji_category_selected(name, emojis, emoji_font_name)
            )
            
            emoji_layout.addWidget(self.emoji_scroll)
            emoji_layout.addWidget(self.carousel)
            
            # Trigger first selection
            if categories:
                 # Populate first category initially
                 name, emojis = categories[0]
                 self._on_emoji_category_selected(name, emojis, emoji_font_name)
        
        self.content_layout.insertWidget(0, emoji_container)
    
    def _on_emoji_category_selected(self, category_name, emojis, emoji_font_name):
        """Maneja la selección de categoría en el carrusel."""
        # Clear previous content
        while self._emoji_category_content_layout.count():
            item = self._emoji_category_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Populate with category emojis
        self._populate_emoji_grid(emojis, self._emoji_category_content_layout, emoji_font_name)
        
        # Ensure scroll to top of content
        if hasattr(self, 'emoji_scroll'):
            self.emoji_scroll.verticalScrollBar().setValue(0)

    
    def _populate_emoji_grid(self, emojis, grid_layout, emoji_font_name):
        """Puebla un grid con botones de emoji."""
        row, col = 0, 0
        for emoji in emojis:
            display_emoji = ensure_emoji_presentation(emoji)
            btn = QPushButton(display_emoji)
            btn.setObjectName("emoji_button")
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if emoji_font_name:
                btn.setFont(QFont(emoji_font_name, 24))
            btn.clicked.connect(lambda checked, e=emoji: self.insert_emoji(e))
            grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 7:
                col = 0
                row += 1

    def insert_emoji(self, emoji):
        self.inserting_emoji = True
        self.last_emoji_inserted = emoji
        self.last_clipboard = emoji
        clipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        
        # Add to recent
        if not hasattr(self, 'recent_emojis'):
            self.recent_emojis = []
        if emoji in self.recent_emojis:
            self.recent_emojis.remove(emoji)
        self.recent_emojis.insert(0, emoji)
        self.recent_emojis = self.recent_emojis[:16]
        self.save_config()
        
        try:
            self.input_simulator.simulate_alt_tab()
            QTimer.singleShot(150, self.simulate_paste)
            QTimer.singleShot(500, self.clear_emoji_flags)
        except Exception as e:
            print(f"Error al cambiar foco: {e}")

    def clear_emoji_flags(self):
        self.inserting_emoji = False
        self.last_emoji_inserted = None

    def _ensure_window_icon(self):
        """Re-establece el ícono de la ventana para que aparezca en la barra de tareas."""
        try:
            from PyQt6.QtCore import QSize
            icon = QIcon()
            icon_base = Path(__file__).parent.parent / "icons"
            
            # Add multiple sizes
            for size in [16, 32, 48, 64, 128, 256]:
                png_path = icon_base / f"petra-{size}.png"
                if png_path.exists():
                    icon.addFile(str(png_path), QSize(size, size))
            
            # If no specific sizes, use general
            if icon.isNull():
                if (icon_base / "petra.png").exists():
                    icon.addFile(str(icon_base / "petra.png"))
                elif (icon_base / "petra.svg").exists():
                    icon.addFile(str(icon_base / "petra.svg"))
            
            if not icon.isNull():
                self.setWindowIcon(icon)
                app = QApplication.instance()
                if app:
                    app.setWindowIcon(icon)
        except Exception:
            pass

    def show_window(self):
        """Mostrar ventana centrada o en posición del mouse según configuración"""
        # Restore icon before showing window
        self._ensure_window_icon()
        
        try:
            # Save current active window
            if self.display_server == 'x11' and self.detector.is_tool_available('xdotool'):
                proc = subprocess.run(['xdotool', 'getactivewindow'], 
                                    capture_output=True, text=True, timeout=0.2)
                if proc.returncode == 0 and proc.stdout.strip():
                    self.last_active_window = proc.stdout.strip()
        except Exception:
            self.last_active_window = None

        # Position window according to configuration
        open_pos = getattr(self, 'open_position', 'mouse')
        if open_pos == 'mouse':
            self.position_at_mouse()
        elif open_pos == 'left':
            self.position_at_left()
        elif open_pos == 'right':
            self.position_at_right()
        else:  # 'center' or default
            self.center_window()
        # Ensure window is un-minimized and active
        self.setWindowState(self.windowState() & ~Qt.WindowState.WindowMinimized | Qt.WindowState.WindowActive)
        self.show()
        self.activateWindow()
        self.raise_()
        
        # Restore icon after showing (some compositors require it)
        QTimer.singleShot(50, self._ensure_window_icon)
        # Keyboard selection mode should be inactive when window first appears
        # (no item highlighted). We'll clear visual selection hints here and
        # only enable keyboard selection when a keypress is detected.
        try:
            self._keyboard_selection_active = False
            # Clear 'copied' state from data model
            for c in getattr(self, 'clips', []):
                c['copied'] = False
            # Reset all widget visual states
            for w in self.findChildren(ClipItem):
                try:
                    w.setProperty('selected', 'false')
                    w.setProperty('hover', 'false')
                    w.setProperty('pressed', 'false')
                    w.setProperty('copied', 'false')
                    w.style().unpolish(w)
                    w.style().polish(w)
                    if hasattr(w, '_update_background'):
                        w._update_background()
                except Exception:
                    pass
        except Exception:
            pass
        # ensure the search input isn't focused when the window first opens
        try:
            if hasattr(self, 'search_bar'):
                try:
                    self.search_bar.clearFocus()
                except Exception:
                    pass
        except Exception:
            pass
        # self.search_bar.setFocus()  # Removed autofocus from search bar
        
        # Create visibility state file
        try:
            visibility_file = Path("/tmp/petra_visible")
            visibility_file.touch()
        except Exception:
            pass

    def hide(self):
        """Ocultar ventana y limpiar estado"""
        # Before hiding, ensure all item states are reset so we don't leave
        # 'pressed' or 'hover' properties set on lingering widgets.
        try:
            for w in self.findChildren(ClipItem):
                try:
                    w.reset_states()
                except Exception:
                    # fallback: explicitly unset properties
                    try:
                        w.setProperty('hover', 'false')
                        w.setProperty('pressed', 'false')
                        w._update_background()
                    except Exception:
                        pass
        except Exception:
            pass

        # make sure the search box doesn't retain focus when the window is hidden
        try:
            if hasattr(self, 'search_bar'):
                try:
                    self.search_bar.clearFocus()
                except Exception:
                    pass
        except Exception:
            pass

        super().hide()
        try:
            visibility_file = Path("/tmp/petra_visible")
            if visibility_file.exists():
                visibility_file.unlink()
        except Exception:
            pass

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
            icons_dir = Path(__file__).parent.parent / 'icons' / icons_folder
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
                if pinned_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pinned_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
                elif pin_path.exists():
                    self.pin_window_btn.setIcon(QIcon(str(pin_path)))
                    self.pin_window_btn.setIconSize(QSize(20, 20))
        except Exception:
            pass

    def toggle_window(self):
        if self.isVisible():
            self.hide()
        else:
            self.show_window()

    # --- Keyboard navigation helpers ---
    def eventFilter(self, obj, event):
        # Minimal global keyboard reader: handle arrow keys to navigate
        try:
            # safely avoid re-entrant handling
            if getattr(self, '_handling_key', False):
                return super().eventFilter(obj, event)

            # Handle mouse hover on recent emoji buttons safely
            if event.type() == QEvent.Type.Enter and obj in getattr(self, 'recent_emoji_buttons', []):
                try:
                    idx = self.recent_emoji_buttons.index(obj)
                    self._on_emoji_mouse_enter(event, idx)
                except ValueError:
                    pass
                return super().eventFilter(obj, event)

            # Only process when visible AND when we are the active window. This
            # avoids trying to act on widgets when Petra is hidden or another
            # app/window is active (which previously caused segfaults).
            try:
                active = QApplication.activeWindow()
            except Exception:
                active = None

            if not getattr(self, 'isVisible', None) or not self.isVisible() or active is not self:
                return super().eventFilter(obj, event)
            if event.type() == QEvent.Type.KeyPress:
                # mark we're handling a key so we don't re-enter
                try:
                    self._handling_key = True
                except Exception:
                    pass
                
                # Ignore modifier key events alone (Alt, Ctrl, etc.)
                # to avoid activating keyboard navigation during Alt+Tab
                from PyQt6.QtCore import Qt
                key = event.key()
                modifiers_only = key in (Qt.Key.Key_Alt, Qt.Key.Key_Control, Qt.Key.Key_Shift, 
                                         Qt.Key.Key_Meta, Qt.Key.Key_Tab)
                # Also ignore if Alt is pressed (Alt+Tab to switch window)
                alt_pressed = event.modifiers() & Qt.KeyboardModifier.AltModifier
                
                if modifiers_only or alt_pressed:
                    try:
                        self._handling_key = False
                    except Exception:
                        pass
                    return super().eventFilter(obj, event)
                
                # Activate keyboard-selection mode on the first keypress (unless
                # the user is typing into the search bar).
                # Note: We don't pre-select any item here. navigate_down/up will
                # handle the initial selection when called.
                try:
                    focus = QApplication.focusWidget()
                    if not (hasattr(self, 'search_bar') and focus is self.search_bar):
                        if not getattr(self, '_keyboard_selection_active', False):
                            self._keyboard_selection_active = True
                except Exception:
                    pass
                k = event.key()
                # Ignore auto-repeat events so a held key triggers press once
                # and release once when released.
                try:
                    if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                        is_repeat = True
                    else:
                        is_repeat = False
                except Exception:
                    is_repeat = False
                if os.environ.get('PETRA_DEBUG_KEYS'):
                    try:
                        print(f"[petra-debug] eventFilter key={k} mods={event.modifiers()} visible={self.isVisible()} active={QApplication.activeWindow() is self}")
                    except Exception:
                        pass
                
                # Escape -> 3-step behavior for keyboard navigation:
                # 1) If there is text in the search -> clear it
                # 2) If search has focus (but is empty) -> clear focus
                # 3) If search does not have focus -> close/hide window
                if k == Qt.Key.Key_Escape:
                    try:
                        focus = QApplication.focusWidget()
                        search_has_focus = hasattr(self, 'search_bar') and focus is self.search_bar
                        search_has_text = hasattr(self, 'search_bar') and self.search_bar.text()
                        
                        # Step 1: If there is text in search, clear it
                        if search_has_text:
                            self.search_bar.clear()
                            try:
                                self._handling_key = False
                            except Exception:
                                pass
                            return True
                        
                        # Step 2: If search has focus (but is empty), clear focus
                        if search_has_focus:
                            self.search_bar.clearFocus()
                            try:
                                self._handling_key = False
                            except Exception:
                                pass
                            return True
                        
                        # Step 3: Search does not have focus -> close window
                        self.hide()
                        try:
                            self._handling_key = False
                        except Exception:
                            pass
                        return True
                    except Exception:
                        pass
                mods = event.modifiers()
                # emulate press-and-hold for Q -> pin button and W -> clear button
                try:
                    focus = QApplication.focusWidget()
                    # only simulate header buttons when user is not typing into search
                    if not (hasattr(self, 'search_bar') and focus is self.search_bar):
                        # Q down -> press clear button (visual down) until key release
                        # NOTE: 'Q' now performs the delete-all long-press behavior.
                        # IMPORTANT: Do NOT return True here! We need the KeyRelease to arrive.
                        if k == Qt.Key.Key_Q and not is_repeat:
                            if not getattr(self, '_key_q_down', False):
                                self._key_q_down = True
                                if hasattr(self, 'clear_btn') and self.clear_btn:
                                    self.clear_btn.setDown(True)
                                    self.clear_btn.is_actively_pressed = True
                                    self.clear_btn.setProgress(0)
                                    self.start_clear_animation()
                        # W down -> press pin button (visual down) until key release
                        # NOTE: 'W' now toggles pin on release (same as clicking pin)
                        # IMPORTANT: Do NOT return True here! We need the KeyRelease to arrive.
                        if k == Qt.Key.Key_W and not is_repeat:
                            if not getattr(self, '_key_w_down', False):
                                self._key_w_down = True
                                if hasattr(self, 'pin_window_btn') and self.pin_window_btn:
                                    self.pin_window_btn.setDown(True)
                except Exception:
                    pass

                # Ctrl+F -> focus search
                if (mods & Qt.KeyboardModifier.ControlModifier) and k == Qt.Key.Key_F:
                    try:
                        if hasattr(self, 'search_bar'):
                            self.search_bar.setFocus()
                            return True
                    except Exception:
                        pass

                # Enter/Return -> copy selected clip if any
                if k == Qt.Key.Key_Return or k == Qt.Key.Key_Enter:
                    try:
                        # If we are in emoji filter with a recent emoji selected
                        if getattr(self, 'current_filter', None) == 'emoji':
                            selected_idx = getattr(self, 'selected_recent_emoji_index', -1)
                            recent_emojis = getattr(self, 'recent_emojis', [])[:16]
                            if selected_idx >= 0 and selected_idx < len(recent_emojis):
                                emoji = recent_emojis[selected_idx]
                                from PyQt6.QtCore import QTimer as _QTimer
                                _QTimer.singleShot(0, lambda e=emoji: self.insert_emoji(e))
                                return True
                        
                        # Prefer using tracked selected content (survives refreshes)
                        sel = getattr(self, '_selected_content', None)
                        from PyQt6.QtCore import QTimer as _QTimer

                        def _safe_copy(c):
                            try:
                                self.copy_and_close(c)
                            except Exception as e:
                                print(f"ERROR: copy_and_close failed: {e}")

                        if sel is not None:
                            # locate visible widget with this content and schedule copy
                            try:
                                for w in self.get_visible_clip_widgets():
                                    try:
                                        if getattr(w, 'content', None) == sel:
                                            if os.environ.get('PETRA_DEBUG_KEYS'):
                                                print(f"[petra-debug] Enter triggered copy of selected content: {sel}")
                                            _QTimer.singleShot(0, lambda c=sel: _safe_copy(c))
                                            return True
                                    except Exception:
                                        pass
                            except Exception:
                                pass

                        # fallback: scan widgets for selected property
                        for w in self.get_visible_clip_widgets():
                            try:
                                if w.property('selected') == 'true':
                                    content = getattr(w, 'content', None)
                                    if content is not None:
                                        if os.environ.get('PETRA_DEBUG_KEYS'):
                                            print(f"[petra-debug] scheduling copy of content (len={len(str(content))})")
                                        _QTimer.singleShot(0, lambda c=content: _safe_copy(c))
                                        return True
                            except Exception:
                                pass
                    except Exception:
                        pass

                if k == Qt.Key.Key_Left:
                    # schedule the filter switch to avoid modifying UI mid-iteration
                    from PyQt6.QtCore import QTimer as _QTimer
                    _QTimer.singleShot(0, self.switch_filter_left)
                    return True
                if k == Qt.Key.Key_Right:
                    from PyQt6.QtCore import QTimer as _QTimer
                    _QTimer.singleShot(0, self.switch_filter_right)
                    return True
                if k == Qt.Key.Key_Up:
                    from PyQt6.QtCore import QTimer as _QTimer
                    _QTimer.singleShot(0, self.navigate_up)
                    return True
                if k == Qt.Key.Key_Down:
                    from PyQt6.QtCore import QTimer as _QTimer
                    _QTimer.singleShot(0, self.navigate_down)
                    return True
            # handle key releases (needed for Q/W hold semantics)
            if event.type() == QEvent.Type.KeyRelease:
                try:
                    k = event.key()
                    # ignore auto-repeat
                    try:
                        if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                            is_repeat = True
                        else:
                            is_repeat = False
                    except Exception:
                        is_repeat = False

                    focus = QApplication.focusWidget()
                    # don't steal keys when typing in the search bar
                    if hasattr(self, 'search_bar') and focus is self.search_bar:
                        return super().eventFilter(obj, event)

                    # Q release -> finalize clear button press (cancel animation on release)
                    from PyQt6.QtCore import Qt
                    if k == Qt.Key.Key_Q:
                        if not is_repeat and getattr(self, '_key_q_down', False):
                            # Q acts as clear release -> stop animation / reset
                            self._key_q_down = False
                            if hasattr(self, 'clear_btn') and self.clear_btn:
                                self.clear_btn.setDown(False)
                                self.cancel_clear_animation()
                                self.clear_btn.is_actively_pressed = False
                                self.clear_btn.setProgress(0)
                            return True

                    # W release -> cancel visual and toggle pin on release
                    if k == Qt.Key.Key_W and not is_repeat:
                        if getattr(self, '_key_w_down', False):
                            # W acts as pin release -> toggle on release
                            self._key_w_down = False
                            if hasattr(self, 'pin_window_btn') and self.pin_window_btn:
                                self.pin_window_btn.setDown(False)
                                # toggling the pin on release
                                self.toggle_window_pin()
                            # Only consume event when we actually processed W release
                            return True
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            try:
                # brief handling flag for this event processing
                self._handling_key = False
            except Exception:
                pass

        return super().eventFilter(obj, event)

    def get_visible_clip_widgets(self):
        """Return a list of ClipItem widgets currently shown (pinned + unpinned)
        according to current filter/search ordering (top to bottom)."""
        widgets = []
        try:
            count = self.content_layout.count()
            # content_layout ends with a stretch, so skip last item
            last = max(0, count - 1)
            for i in range(last):
                item = self.content_layout.itemAt(i)
                if not item:
                    continue
                container = item.widget()
                if container is None:
                    continue
                # ClipItem was added inside the container
                clip = container.findChild(ClipItem)
                if clip:
                    widgets.append(clip)
        except Exception:
            pass
        return widgets

    def _set_selected_clip_widget(self, clip_widget):
        # clear previous
        try:
            for w in list(self.get_visible_clip_widgets()):
                try:
                    if w is clip_widget:
                        w.setProperty('selected', 'true')
                        # visually mark selected widget using the same hover overlay
                        # so keyboard selection looks like a mouse hover
                        try:
                            w.setProperty('hover', 'true')
                        except Exception:
                            pass
                        try:
                            # persist selected content so selection survives UI refresh
                            self._selected_content = getattr(w, 'content', None)
                        except Exception:
                            pass
                    else:
                        w.setProperty('selected', 'false')
                        try:
                            w.setProperty('hover', 'false')
                        except Exception:
                            pass
                    w.style().unpolish(w)
                    w.style().polish(w)
                    try:
                        if hasattr(w, '_update_background'):
                            w._update_background()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def navigate_up(self):
        # avoid operating on widgets when window isn't visible
        if not getattr(self, 'isVisible', None) or not self.isVisible():
            return

        # If we are in emoji filter, navigate recent emojis
        if getattr(self, 'current_filter', None) == 'emoji':
            self._navigate_recent_emojis(-1)
            return

        try:
            visible = list(self.get_visible_clip_widgets())
        except Exception:
            visible = []
        if not visible:
            return

        # find current selected
        current = None
        for i, w in enumerate(visible):
            if w.property('selected') == 'true':
                current = i
                break

        if current is None:
            # no selection -> choose last
            new = len(visible) - 1
        else:
            new = (current - 1) if current > 0 else len(visible) - 1

        target = visible[new]
        # ensure visible and highlight
        try:
            container = target.parentWidget()
            if hasattr(self, 'scroll_area') and self.scroll_area:
                self.scroll_area.ensureWidgetVisible(container)
        except Exception:
            pass

        self._set_selected_clip_widget(target)

    def navigate_down(self):
        # avoid operating on widgets when window isn't visible
        if not getattr(self, 'isVisible', None) or not self.isVisible():
            return

        # If we are in emoji filter, navigate recent emojis
        if getattr(self, 'current_filter', None) == 'emoji':
            self._navigate_recent_emojis(1)
            return

        try:
            visible = list(self.get_visible_clip_widgets())
        except Exception:
            visible = []
        if not visible:
            return

        # If no item is selected, select the first one
        current = None
        for i, w in enumerate(visible):
            if w.property('selected') == 'true':
                current = i
                break

        if current is None:
            # No selection yet - select first item
            new = 0
        else:
            # Advance to next, wrap around to first
            new = (current + 1) if current < len(visible) - 1 else 0

        target = visible[new]
        try:
            container = target.parentWidget()
            if hasattr(self, 'scroll_area') and self.scroll_area:
                self.scroll_area.ensureWidgetVisible(container)
        except Exception:
            pass

        self._set_selected_clip_widget(target)

    def _navigate_recent_emojis(self, direction):
        """Navegar por los botones de emojis recientes con flechas arriba/abajo."""
        if not hasattr(self, 'recent_emoji_buttons') or not self.recent_emoji_buttons:
            return
        
        recent_emojis = getattr(self, 'recent_emojis', [])[:16]
        if not recent_emojis:
            return
        
        # Activate keyboard navigation
        self._emoji_keyboard_nav_active = True
        
        # Number of available emojis (not empty)
        num_available = len(recent_emojis)
        
        current_idx = getattr(self, 'selected_recent_emoji_index', -1)
        
        if current_idx == -1:
            # No selection, select first
            new_idx = 0
        else:
            # Move in indicated direction
            new_idx = current_idx + direction
            # Wrap around
            if new_idx < 0:
                new_idx = num_available - 1
            elif new_idx >= num_available:
                new_idx = 0
        
        self._select_recent_emoji(new_idx)
    
    def _on_emoji_mouse_enter(self, event, index):
        """Detectar cuando el mouse entra en un botón de emoji reciente."""
        # Disable keyboard navigation and remove highlight
        if getattr(self, '_emoji_keyboard_nav_active', False):
            self._emoji_keyboard_nav_active = False
            self._clear_emoji_selection()
    
    def _clear_emoji_selection(self):
        """Quitar el resaltado de selección de emoji."""
        old_idx = getattr(self, 'selected_recent_emoji_index', -1)
        if old_idx >= 0 and hasattr(self, 'recent_emoji_buttons') and old_idx < len(self.recent_emoji_buttons):
            old_btn = self.recent_emoji_buttons[old_idx]
            old_btn.setStyleSheet("")
        self.selected_recent_emoji_index = -1
    
    def _select_recent_emoji(self, index):
        """Seleccionar un emoji reciente por índice."""
        if not hasattr(self, 'recent_emoji_buttons'):
            return
        
        # If keyboard navigation is not active, do not show selection
        if not getattr(self, '_emoji_keyboard_nav_active', False):
            self.selected_recent_emoji_index = index
            return
        
        # Get theme colors
        colors = self.themes_manager.get_theme_colors()
        border_color = colors.get('emoji_selection_border', '#4CAF50')
        bg_color = colors.get('emoji_selection_bg', '#3a3a3a')
        
        # Remove previous selection
        old_idx = getattr(self, 'selected_recent_emoji_index', -1)
        if old_idx >= 0 and old_idx < len(self.recent_emoji_buttons):
            old_btn = self.recent_emoji_buttons[old_idx]
            old_btn.setStyleSheet("")  # Restore normal style
        
        # Apply new selection
        if index >= 0 and index < len(self.recent_emoji_buttons):
            btn = self.recent_emoji_buttons[index]
            if btn.isEnabled():
                btn.setStyleSheet(f"QPushButton {{ border: 2px solid {border_color}; background-color: {bg_color}; }}")
                self.selected_recent_emoji_index = index
            else:
                self.selected_recent_emoji_index = -1
        else:
            self.selected_recent_emoji_index = -1

    def switch_filter_left(self):
        try:
            if not getattr(self, 'isVisible', None) or not self.isVisible():
                return
            filters = list(self.filter_buttons.keys())
            current_index = filters.index(self.current_filter) if self.current_filter in filters else 0
            new_index = (current_index - 1) % len(filters)
            self.set_filter(filters[new_index])
            # Clear any current selection - user can use ↓ to select when ready
            self._clear_clip_selection()
        except Exception:
            pass

    def switch_filter_right(self):
        try:
            if not getattr(self, 'isVisible', None) or not self.isVisible():
                return
            filters = list(self.filter_buttons.keys())
            current_index = filters.index(self.current_filter) if self.current_filter in filters else 0
            new_index = (current_index + 1) % len(filters)
            self.set_filter(filters[new_index])
            # Clear any current selection - user can use ↓ to select when ready
            self._clear_clip_selection()
        except Exception:
            pass

    def _clear_clip_selection(self):
        """Clear any currently selected clip widget."""
        try:
            self._selected_content = None
            for w in self.get_visible_clip_widgets():
                try:
                    w.setProperty('selected', 'false')
                    w.setProperty('hover', 'false')
                    w.style().unpolish(w)
                    w.style().polish(w)
                    if hasattr(w, '_update_background'):
                        w._update_background()
                except Exception:
                    pass
        except Exception:
            pass