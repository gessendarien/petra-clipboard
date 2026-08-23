"""
Emoji picker module — extracted from window.py.

Contains:
- get_emoji_font()        — detects the best color emoji font on the system
- ensure_emoji_presentation() — adds VS16 to text-style emojis
- EmojiCarousel           — scrollable category selector widget
- EmojiPickerMixin        — methods mixed into PetraClipboard for the emoji panel

MRO NOTE:
  show_emoji_picker() intentionally overrides the no-op stub in FilterManager.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QPushButton,
                              QLabel, QScrollArea)
from PyQt6.QtCore import Qt, QTimer, QRectF, pyqtSignal
from PyQt6.QtGui import (QFont, QFontDatabase, QPainter, QColor, QBrush,
                          QRadialGradient)

from emoji_keywords import search_emojis, ALL_EMOJIS, EMOJI_CATEGORIES


# ─── Helper functions ────────────────────────────────────────────────

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


# ─── EmojiCarousel widget ────────────────────────────────────────────

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
        
        num_items = len(self.categories)
        if num_items == 0:
            return

        visible_range = 2  # 2 on each side
        
        for i in range(-visible_range, visible_range + 1):
            idx = (self.current_index + i) % num_items
            category_name, category_emojis = self.categories[idx]
            
            visual_i = i + self.anim_offset
            
            offset_x = visual_i * (self.item_width + self.spacing)
            x = center_x + offset_x
            y = center_y
            
            # Scale and opacity based on distance from center
            dist = abs(visual_i)
            
            scale = max(0.8, 1.0 - 0.2 * dist)
            opacity = max(0.6, 1.0 - 0.4 * dist)
            
            if dist < 0.5:
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
            if dist < 0.9:
                path = QRectF(-18, -18, 36, 36)
                painter.setBrush(QBrush(bg_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(path, 12, 12)
                
                if dist < 0.2:
                    gradient = QRadialGradient(0, 0, 24)
                    gradient.setColorAt(0, QColor(168, 85, 247, int(100 * (1.0 - dist*5))))
                    gradient.setColorAt(1, Qt.GlobalColor.transparent)

            # Draw Icons/Emoji
            representative_emoji = category_name.split()[0]
            display_emoji = ensure_emoji_presentation(representative_emoji)
            
            painter.setOpacity(opacity)
            font = QFont(self.emoji_font_name) if self.emoji_font_name else self.font()
            font.setPixelSize(22)
            painter.setFont(font)
            painter.setPen(QColor("#FFFFFF") if dist < 0.5 else QColor("#888888"))

            # Ajuste más sutil (-18 en lugar de -20 o -16)
            text_rect = QRectF(-17, -18, 36, 36)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, display_emoji)

            painter.restore()

    def mousePressEvent(self, event):
        center_x = self.width() / 2
        click_x = event.position().x()
        
        deadzone = 20
        
        if click_x > center_x + deadzone:
            self.scroll_next()
        elif click_x < center_x - deadzone:
            self.scroll_prev()

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        self._scroll_accumulator += angle
        
        threshold = 120
        
        if self._scroll_accumulator >= threshold:
            self.scroll_prev()
            self._scroll_accumulator = 0
        elif self._scroll_accumulator <= -threshold:
            self.scroll_next()
            self._scroll_accumulator = 0

    def start_animation(self, direction):
        if direction > 0:  # Next
             self.anim_offset = 1.0
             self.current_index = (self.current_index + 1) % len(self.categories)
        else:  # Prev
             self.anim_offset = -1.0
             self.current_index = (self.current_index - 1) % len(self.categories)
             
        self.anim_timer.start()
        self._emit_selection()
        self.update()

    def _update_animation(self):
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


# ─── EmojiPickerMixin ────────────────────────────────────────────────

class EmojiPickerMixin:
    """Mixin that adds emoji-picker functionality to PetraClipboard.

    MRO collision (intentional):
      show_emoji_picker() overrides the no-op stub in FilterManager.
    """

    def show_emoji_picker(self, search_query=""):
        """Override FilterManager.show_emoji_picker (intentional MRO override)."""
        from PyQt6.QtWidgets import QApplication
        
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
        
        recent_emojis = getattr(self, 'recent_emojis', [])[:16]
        self.recent_emoji_buttons = []
        self.selected_recent_emoji_index = -1
        self._emoji_keyboard_nav_active = False
        
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
                btn.installEventFilter(self)
                if emoji_font_name:
                    btn.setFont(QFont(emoji_font_name, 24))
            else:
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
            emojis = search_emojis(search_query, ALL_EMOJIS)
            if emojis:
                grid_widget = QWidget()
                grid = QGridLayout(grid_widget)
                grid.setSpacing(8)
                self._populate_emoji_grid(emojis, grid, emoji_font_name)
                emoji_layout.addWidget(grid_widget)
            else:
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
            categories = list(EMOJI_CATEGORIES.items())
            self.carousel = EmojiCarousel(categories, emoji_font_name, self)
            
            self._emoji_category_content = QWidget()
            self._emoji_category_content_layout = QGridLayout(self._emoji_category_content)
            self._emoji_category_content_layout.setSpacing(8)
            self._emoji_category_content_layout.setContentsMargins(5, 10, 5, 10)
            
            self.emoji_scroll = QScrollArea()
            self.emoji_scroll.setWidgetResizable(True)
            self.emoji_scroll.setWidget(self._emoji_category_content)
            self.emoji_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.emoji_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
            
            self.carousel.categorySelected.connect(
                lambda name, emojis: self._on_emoji_category_selected(name, emojis, emoji_font_name)
            )
            
            emoji_layout.addWidget(self.emoji_scroll)
            emoji_layout.addWidget(self.carousel)
            
            if categories:
                 name, emojis = categories[0]
                 self._on_emoji_category_selected(name, emojis, emoji_font_name)
        
        self.content_layout.insertWidget(0, emoji_container)
    
    def _on_emoji_category_selected(self, category_name, emojis, emoji_font_name):
        """Maneja la selección de categoría en el carrusel."""
        while self._emoji_category_content_layout.count():
            item = self._emoji_category_content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self._populate_emoji_grid(emojis, self._emoji_category_content_layout, emoji_font_name)
        
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
        from PyQt6.QtWidgets import QApplication
        
        self.inserting_emoji = True
        self.last_emoji_inserted = emoji
        self.last_clipboard = emoji
        clipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        
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

    def _navigate_recent_emojis(self, direction):
        """Navegar por los botones de emojis recientes con flechas arriba/abajo."""
        if not hasattr(self, 'recent_emoji_buttons') or not self.recent_emoji_buttons:
            return
        
        recent_emojis = getattr(self, 'recent_emojis', [])[:16]
        if not recent_emojis:
            return
        
        self._emoji_keyboard_nav_active = True
        
        num_available = len(recent_emojis)
        
        current_idx = getattr(self, 'selected_recent_emoji_index', -1)
        
        if current_idx == -1:
            new_idx = 0
        else:
            new_idx = current_idx + direction
            if new_idx < 0:
                new_idx = num_available - 1
            elif new_idx >= num_available:
                new_idx = 0
        
        self._select_recent_emoji(new_idx)
    
    def _on_emoji_mouse_enter(self, event, index):
        """Detectar cuando el mouse entra en un botón de emoji reciente."""
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
        
        if not getattr(self, '_emoji_keyboard_nav_active', False):
            self.selected_recent_emoji_index = index
            return
        
        colors = self.themes_manager.get_theme_colors()
        border_color = colors.get('emoji_selection_border', '#4CAF50')
        bg_color = colors.get('emoji_selection_bg', '#3a3a3a')
        
        old_idx = getattr(self, 'selected_recent_emoji_index', -1)
        if old_idx >= 0 and old_idx < len(self.recent_emoji_buttons):
            old_btn = self.recent_emoji_buttons[old_idx]
            old_btn.setStyleSheet("")
        
        if index >= 0 and index < len(self.recent_emoji_buttons):
            btn = self.recent_emoji_buttons[index]
            if btn.isEnabled():
                btn.setStyleSheet(f"QPushButton {{ border: 2px solid {border_color}; background-color: {bg_color}; }}")
                self.selected_recent_emoji_index = index
            else:
                self.selected_recent_emoji_index = -1
        else:
            self.selected_recent_emoji_index = -1
