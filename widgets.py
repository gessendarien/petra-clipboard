from PyQt6.QtWidgets import (QLineEdit, QPushButton, QFrame, QVBoxLayout, 
                             QHBoxLayout, QLabel, QWidget)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer, QRect, QEvent, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QPen, QColor, QIcon, QPixmap, QPainterPath
from datetime import datetime
import re
import html
from pathlib import Path

class ShortcutEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(False)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Backspace, Qt.Key.Key_Delete):
            self.clear()
            return

        mods = []
        m = event.modifiers()
        if m & Qt.KeyboardModifier.MetaModifier:
            mods.append('Super')
        if m & Qt.KeyboardModifier.ControlModifier:
            mods.append('Control')
        if m & Qt.KeyboardModifier.AltModifier:
            mods.append('Alt')
        if m & Qt.KeyboardModifier.ShiftModifier:
            mods.append('Shift')

        key = event.key()
        if key in (
            Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta,
            Qt.Key.Key_Super_L, Qt.Key.Key_Super_R
        ):
            if mods:
                self.setText(' + '.join(mods))
            return

        key_name = self._key_name_from_event(event)
        parts = mods + ([key_name] if key_name else [])
        if parts:
            self.setText(' + '.join(parts))
        else:
            super().keyPressEvent(event)

    def _key_name_from_event(self, event):
        key = event.key()
        if Qt.Key.Key_A <= key <= Qt.Key.Key_Z:
            return chr(key).lower()
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            return chr(key)
        mapping = {
            Qt.Key.Key_Space: 'space',
            Qt.Key.Key_Return: 'Return',
            Qt.Key.Key_Enter: 'Return',
            Qt.Key.Key_Escape: 'Escape',
            Qt.Key.Key_Tab: 'Tab',
            Qt.Key.Key_Backtab: 'Tab',
            Qt.Key.Key_Left: 'Left',
            Qt.Key.Key_Right: 'Right',
            Qt.Key.Key_Up: 'Up',
            Qt.Key.Key_Down: 'Down',
        }
        return mapping.get(key, event.text() or '')

class ProgressButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.progress = 0
        self.border_color = "#ff6b35"
        self.is_actively_pressed = False
    
    def setBorderColor(self, color):
        self.border_color = color
        self.update()
    
    def setProgress(self, value):
        self.progress = value
        self.update()
    
    def mousePressEvent(self, event):
        self.is_actively_pressed = True
        self.setProgress(0)
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        self.is_actively_pressed = False
        self.setProgress(0)
        super().mouseReleaseEvent(event)
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.is_actively_pressed and self.progress > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            pen = QPen(QColor(self.border_color))
            pen.setWidth(3)
            painter.setPen(pen)
            
            rect = self.rect().adjusted(2, 2, -2, -2)
            span_angle = int((self.progress / 100) * 360 * 16)
            painter.drawArc(rect, -90 * 16, -span_angle)
            
            painter.end()

class ClipItem(QFrame):
    clicked = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    delete_requested = pyqtSignal()
    pin_toggled = pyqtSignal()
    
    def __init__(self, content, item_type, timestamp, pinned=False, main_window=None):
        super().__init__()
        self.content = content
        self.item_type = item_type
        self.timestamp = timestamp
        self.pinned = pinned
        self.main_window = main_window
        self.setup_ui()
        
    def setup_ui(self):
        self.setObjectName("clip_item")
        # Allow hover pseudo-state to work reliably and ensure stylesheet backgrounds are painted
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        # Ensure default dynamic states exist (strings so stylesheet matches)
        self.setProperty('copied', 'false')
        self.setProperty('hover', 'false')
        self.setProperty('pressed', 'false')
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(70)
        self.setMaximumHeight(70)
        self.setMaximumWidth(485)
        # enable hover events to work reliably even when mouse is over child widgets
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        
        # Icono
        icon_label = QLabel()
        icon_label.setFixedSize(40, 40)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # PARA IMÁGENES: mostrar preview en miniatura
        if self.item_type == "image" and self.main_window and self.content in self.main_window.clipboard_images:
            self.setup_image_thumbnail(icon_label)
        else:
            # Para otros tipos, usar ícono normal
            icon_loaded = False
            try:
                icons_dir = Path(__file__).parent / 'icons'
                icon_files = {
                    "text": "texts.png",
                    "url": "links.png", 
                    "image": "images.png",
                    "emoji": "emojis.png",
                    "color": "colors.png"
                }
                icon_file = icon_files.get(self.item_type)
                if icon_file:
                    icon_path = icons_dir / icon_file
                    if icon_path.exists():
                        pixmap = QPixmap(str(icon_path))
                        if not pixmap.isNull():
                            icon_label.setPixmap(pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                            icon_label.setStyleSheet("background-color: transparent;")
                            icon_loaded = True
            except Exception:
                pass

            if not icon_loaded:
                if self.item_type == "color":
                    bg_color = self.content if self.content.startswith("#") else "#3d2a4d"
                    icon_label.setStyleSheet(f"""
                        background-color: {bg_color};
                        border-radius: 6px;
                        border: 1px solid rgba(255, 255, 255, 0.2);
                    """)
                else:
                    icon_label.setStyleSheet("""
                        background-color: transparent;
                        border-radius: 6px;
                        border: none;
                    """)
        
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        text_label = self.create_text_label()
        time_label = self.create_time_label()
        
        content_layout.addWidget(text_label)
        content_layout.addWidget(time_label)
        
        layout.addWidget(icon_label)
        layout.addLayout(content_layout)
        layout.addStretch()

        # background overlay for hover/copy visuals (starts hidden)
        self._bg = QWidget(self)
        self._bg.setObjectName('clip_item_bg')
        self._bg.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._bg.setGeometry(self.rect())
        self._bg.lower()
        self._bg.hide()

        self.setup_action_buttons(layout)

        self.setLayout(layout)

        # Install eventFilter on all child widgets so hover over children still updates parent
        for child in self.findChildren(QWidget):
            try:
                if child is not self._bg and child is not self.actions_widget:
                    child.installEventFilter(self)
            except Exception:
                pass

    # hover/press state is handled by final event handlers and overlay background

    def paintEvent(self, event):
        # Draw background according to state so hover/fill is always visible
        try:
            colors = None
            if self.main_window and hasattr(self.main_window, 'themes_manager'):
                try:
                    colors = self.main_window.themes_manager.get_theme_colors()
                except Exception:
                    colors = None

            # fallback colors
            def c(key, fallback):
                if colors and key in colors:
                    return colors[key]
                return fallback

            is_copied = (self.property('copied') == 'true')
            is_hover = (self.property('hover') == 'true')
            is_pressed = (self.property('pressed') == 'true')

            def _make_translucent_color_string(s, alpha=0.18):
                """Return an rgba(...) string for color s with given alpha (0..1).
                If s is already rgba(...) it will adjust the alpha."""
                try:
                    if isinstance(s, QColor):
                        r = s.red(); g = s.green(); b = s.blue()
                    else:
                        if isinstance(s, str) and s.startswith('rgba'):
                            # attempt parse and override alpha
                            parts = s[s.find('(')+1:s.find(')')].split(',')
                            r = int(parts[0].strip()); g = int(parts[1].strip()); b = int(parts[2].strip())
                        else:
                            qc = QColor(s)
                            if not qc.isValid():
                                qc = QColor('#000000')
                            r = qc.red(); g = qc.green(); b = qc.blue()
                    a = max(0, min(1, alpha))
                    return f'rgba({r}, {g}, {b}, {a})'
                except Exception:
                    return f'rgba(0, 0, 0, {max(0, min(1, alpha))})'

            if is_copied:
                if is_pressed:
                    # copied pressed -> reuse element_click so there are no dependencies
                    bg = c('element_click', '#8A5CEA')
                elif is_hover:
                    # use the single hover source for consistency
                    bg = c('clip_hover_bg', '#00D6D6')
                else:
                    # default copied state: use a subtle translucent tint so it does not
                    # look identical to hover (prevents the "persistent hover" feeling)
                    base = c('clip_hover_bg', '#00D6D6')
                    # produce a translucent rgba color for paint
                    bg = _make_translucent_color_string(base, alpha=0.18)
            else:
                if is_pressed:
                    bg = c('element_click', '#8A5CEA')
                elif is_hover:
                    bg = c('clip_hover_bg', '#00D6D6')
                else:
                    bg = None

            # paint rounded rect background (fill full area — no border used)
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if bg:
                # overlay should cover the full widget (no border inset)
                inset = 0
                inner = self.rect().adjusted(inset, inset, -inset, -inset)

                # parse color or rgba
                def parse_color_string(s):
                    try:
                        if s.startswith('rgba'):
                            # rgba(r,g,b,a)
                            parts = s[s.find('(')+1:s.find(')')].split(',')
                            r = int(parts[0].strip())
                            g = int(parts[1].strip())
                            b = int(parts[2].strip())
                            a = float(parts[3].strip())
                            qc = QColor(r, g, b, int(a * 255))
                            return qc
                        else:
                            qc = QColor(s)
                            if not qc.isValid():
                                return QColor('#000000')
                            return qc
                    except Exception:
                        return QColor('#000000')

                brush = parse_color_string(bg) if isinstance(bg, str) else QColor('#000000')
                painter.setBrush(brush)
                painter.setPen(Qt.PenStyle.NoPen)
                radius = 10
                path = QPainterPath()
                path.addRoundedRect(inner, radius, radius)
                painter.fillPath(path, brush)
            painter.end()
        except Exception:
            pass

        super().paintEvent(event)
    
    def setup_image_thumbnail(self, icon_label):
        try:
            cache_key = f"thumb_{self.content}"
            if not hasattr(self.main_window, '_thumbnail_cache'):
                self.main_window._thumbnail_cache = {}
            
            if cache_key in self.main_window._thumbnail_cache:
                rounded = self.main_window._thumbnail_cache[cache_key]
            else:
                from PyQt6.QtCore import QRectF
                original = QPixmap.fromImage(self.main_window.clipboard_images[self.content])
                if not original.isNull():
                    rounded = QPixmap(40, 40)
                    rounded.fill(Qt.GlobalColor.transparent)
                    
                    painter = QPainter(rounded)
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(0, 0, 40, 40), 6, 6)
                    painter.setClipPath(path)
                    
                    scaled = original.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                                            Qt.TransformationMode.FastTransformation)
                    
                    x = (scaled.width() - 40) // 2
                    y = (scaled.height() - 40) // 2
                    painter.drawPixmap(-x, -y, scaled)
                    painter.end()
                    
                    self.main_window._thumbnail_cache[cache_key] = rounded
                else:
                    self.set_default_icon_style(icon_label)
                    rounded = None
            
            if rounded:
                icon_label.setPixmap(rounded)
                icon_label.setStyleSheet("background-color: transparent;")
            else:
                self.set_default_icon_style(icon_label)
        except Exception as e:
            self.set_default_icon_style(icon_label)
    
    def create_text_label(self):
        url_re = re.compile(r'((?:https?://|ftp://|www\.|\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s]*)?))', re.IGNORECASE)
        render_as_link = False
        try:
            if hasattr(self, 'main_window') and getattr(self.main_window, 'current_filter', None) == 'url':
                render_as_link = True
        except Exception:
            pass
            
        # Obtener el color del enlace del tema actual
        link_color = '#BB86FC'  # default morado
        if self.main_window and hasattr(self.main_window, 'themes_manager'):
            try:
                link_color = self.main_window.themes_manager.get_current_theme()['colors']['link_color']
            except Exception:
                pass
            
        if render_as_link or url_re.search(self.content):
            def _linkify(match):
                u = match.group(1)
                href = u
                if not re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', u):
                    href = 'http://' + u
                return f'<a href="{html.escape(href)}" style="color: {link_color}; text-decoration: none;">{html.escape(u)}</a>'

            escaped = html.escape(self.content)
            html_text = url_re.sub(lambda m: _linkify(m), escaped)
            text_label = QLabel(html_text)
            text_label.setObjectName("clip_text_link")
            text_label.setTextFormat(Qt.TextFormat.RichText)
            text_label.setOpenExternalLinks(True)
            text_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
            text_label.setWordWrap(False)
        else:
            text_label = QLabel(self.truncate_text(self.content, 43))
            text_label.setObjectName("clip_text_normal")
            text_label.setWordWrap(False)
            text_label.setTextFormat(Qt.TextFormat.PlainText)
            text_label.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            
        # Aplicar el tema al QLabel si el administrador de temas está disponible
        if self.main_window and hasattr(self.main_window, 'themes_manager'):
            self.main_window.themes_manager.apply_theme_to_widget(text_label)
        
        return text_label
    
    def create_time_label(self):
        time_text = self.format_timestamp()
        time_label = QLabel(time_text)
        time_label.setObjectName("clip_time")
        return time_label
    
    def setup_action_buttons(self, layout):
        self.actions_widget = QWidget()
        actions_layout = QHBoxLayout(self.actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(4)
        
        self.pin_action_btn = QPushButton("")
        self.pin_action_btn.setObjectName("pin_action_button")
        self.pin_action_btn.setFixedSize(32, 32)
        self.pin_action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        icons_dir = Path(__file__).parent / 'icons'
        pin_path = icons_dir / 'pin.png'
        unpin_path = icons_dir / 'unpin.png'
        self._pin_icon = QIcon(str(pin_path)) if pin_path.exists() else None
        self._unpin_icon = QIcon(str(unpin_path)) if unpin_path.exists() else None
        
        if self.pinned:
            if self._pin_icon:
                self.pin_action_btn.setIcon(self._pin_icon)
                self.pin_action_btn.setIconSize(QSize(18, 18))
        else:
            if self._pin_icon:
                self.pin_action_btn.setIcon(self._pin_icon)
                self.pin_action_btn.setIconSize(QSize(18, 18))
                
        self.pin_action_btn.installEventFilter(self)
        self.pin_action_btn.clicked.connect(self.pin_toggled.emit)
        
        self.delete_action_btn = QPushButton("✕")
        self.delete_action_btn.setObjectName("delete_action_button")
        self.delete_action_btn.setFixedSize(32, 32)
        self.delete_action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_action_btn.clicked.connect(self.delete_requested.emit)
        
        actions_layout.addWidget(self.delete_action_btn)
        actions_layout.addWidget(self.pin_action_btn)

        if self.pinned:
            self.actions_widget.show()
            self.delete_action_btn.hide()
        else:
            self.actions_widget.hide()
            self.delete_action_btn.show()
        
        layout.addWidget(self.actions_widget)
    
    def get_icon_style(self):
        if self.item_type == "color":
            return ("", self.content if self.content.startswith("#") else "#3d2a4d")
        elif self.item_type == "url":
            return ("", "transparent")
        elif self.item_type == "image":
            return ("", "transparent")
        elif self.item_type == "emoji":
            return ("", "transparent")
        else:
            return ("", "transparent")
    
    def set_default_icon_style(self, icon_label):
        if self.item_type == "color":
            bg_color = self.content if self.content.startswith("#") else "#3d2a4d"
            icon_label.setStyleSheet(f"""
                background-color: {bg_color};
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            """)
        else:
            icon_label.setStyleSheet("""
                background-color: transparent;
                border-radius: 6px;
                border: none;
            """)
    
    def truncate_text(self, text, max_len):
        text = text.replace('\n', ' ').strip()
        return text[:max_len] + "..." if len(text) > max_len else text
    
    def format_timestamp(self):
        now = datetime.now()
        diff = now - self.timestamp
        
        if diff.days == 0 and self.timestamp.date() == now.date():
            return self.timestamp.strftime("%-I:%M %p")
        else:
            return self.timestamp.strftime("%d/%m/%Y")
    
    def _update_background(self):
        """Update background overlay widget based on hover/pressed/copied state and theme colors."""
        try:
            colors = None
            if self.main_window and hasattr(self.main_window, 'themes_manager'):
                try:
                    colors = self.main_window.themes_manager.get_theme_colors()
                except Exception:
                    colors = None

            def getc(k, fallback=None):
                return colors.get(k, fallback) if colors else fallback

            is_copied = (self.property('copied') == 'true')
            is_hover = (self.property('hover') == 'true')
            is_pressed = (self.property('pressed') == 'true')

            bg = None
            def _make_translucent_qss(s, alpha=0.18):
                # produce a CSS rgba string for stylesheet usage
                try:
                    if isinstance(s, str) and s.startswith('rgba'):
                        # override alpha value
                        parts = s[s.find('(')+1:s.find(')')].split(',')
                        r = int(parts[0].strip()); g = int(parts[1].strip()); b = int(parts[2].strip())
                    else:
                        qc = QColor(s)
                        if not qc.isValid():
                            qc = QColor('#000000')
                        r = qc.red(); g = qc.green(); b = qc.blue()
                    return f'rgba({r}, {g}, {b}, {max(0, min(1, alpha))})'
                except Exception:
                    return f'rgba(0, 0, 0, {max(0, min(1, alpha))})'

            if is_copied:
                if is_pressed:
                    # use element_click for the pressed variation
                    bg = getc('element_click', '#8A5CEA')
                elif is_hover:
                    bg = getc('clip_hover_bg', '#00D6D6')
                else:
                    # show a subtle translucent tint when item is copied but not hovered
                    base = getc('clip_hover_bg', '#00D6D6')
                    bg = _make_translucent_qss(base, alpha=0.18)
            else:
                if is_pressed:
                    bg = getc('element_click', '#8A5CEA')
                elif is_hover:
                    bg = getc('clip_hover_bg', '#00D6D6')
                else:
                    bg = None

            if bg:
                # overlay fills the whole widget
                self._bg.setGeometry(self.rect())
                self._bg.setStyleSheet(f"background-color: {bg}; border-radius: 8px;")
                self._bg.show()
            else:
                # fall back to transparent so parent's background shows
                self._bg.setStyleSheet("background-color: transparent; border-radius: 8px;")
                self._bg.hide()
        except Exception:
            try:
                self._bg.setStyleSheet("background-color: transparent; border-radius: 8px;")
                self._bg.hide()
            except Exception:
                pass

    def resizeEvent(self, event):
        try:
            if hasattr(self, '_bg') and self._bg:
                self._bg.setGeometry(self.rect())
        except Exception:
            pass
        super().resizeEvent(event)

    def event(self, event):
        # handle hover enter/leave consistently even if children get mouse events
        try:
            if event.type() == QEvent.Type.HoverEnter:
                self.setProperty('hover', 'true')
                self._update_background()
            elif event.type() == QEvent.Type.HoverLeave:
                self.setProperty('hover', 'false')
                self._update_background()
        except Exception:
            pass
        return super().event(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                self.setProperty('pressed', 'true')
                self._update_background()
            except Exception:
                pass
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                self.setProperty('pressed', 'false')
                self._update_background()

                # Ensure hover state is updated after release
                if not self.rect().contains(self.mapFromGlobal(QCursor.pos())):
                    self.setProperty('hover', 'false')
                    self._update_background()

                if getattr(self, 'pinned', False):
                    self.actions_widget.show()
                else:
                    self.actions_widget.hide()
            except Exception:
                pass
            self.clicked.emit(self.content)
        super().mouseReleaseEvent(event)

    def enterEvent(self, event):
        """Handle mouse enter event to set hover state."""
        self.setProperty('hover', 'true')
        self._update_background()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Handle mouse leave event to unset hover state."""
        self.setProperty('hover', 'false')
        self._update_background()
        super().leaveEvent(event)

    def eventFilter(self, obj, event):
        try:
            if obj == getattr(self, 'pin_action_btn', None):
                if getattr(self, 'pinned', False):
                    if event.type() == QEvent.Type.Enter:
                        if getattr(self, '_unpin_icon', None):
                            self.pin_action_btn.setIcon(self._unpin_icon)
                            self.pin_action_btn.setIconSize(QSize(18, 18))
                            self.pin_action_btn.update()
                    elif event.type() == QEvent.Type.Leave:
                        if getattr(self, '_pin_icon', None):
                            self.pin_action_btn.setIcon(self._pin_icon)
                            self.pin_action_btn.setIconSize(QSize(18, 18))
                            self.pin_action_btn.update()
        except Exception:
            pass
        return super().eventFilter(obj, event)
    
    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.content)

    def reset_states(self):
        """Reset hover, copied, and pressed states to their default values."""
        self.setProperty('hover', 'false')
        self.setProperty('copied', 'false')
        self.setProperty('pressed', 'false')
        self._update_background()

    def reset_all_states(self):
        """Reset hover, copied, and pressed states for all ClipItem instances."""
        for child in self.parent().findChildren(ClipItem):
            child.reset_states()

    def reset_states_on_context_change(self):
        """Reset hover, copied, and pressed states when the context changes."""
        self.setProperty('hover', 'false')
        self.setProperty('copied', 'false')
        self.setProperty('pressed', 'false')
        self._update_background()

    def on_context_change(self):
        """Handle context changes (e.g., filter updates) and reset all states."""
        for child in self.parent().findChildren(ClipItem):
            child.reset_states_on_context_change()

    def reset_states_on_filter_change(self):
        """Reset hover, copied, and pressed states for all ClipItem instances when filters change."""
        for child in self.parent().findChildren(ClipItem):
            child.setProperty('hover', 'false')
            child.setProperty('copied', 'false')
            child.setProperty('pressed', 'false')
            child._update_background()

    def on_filter_change(self):
        """Handle filter change and reset all states."""
        self.reset_states_on_filter_change()
        # ...existing code for handling filter change...

    def closeEvent(self, event):
        """Handle window close event and reset states for all ClipItem instances."""
        for child in self.findChildren(ClipItem):
            child.reset_states()
        super().closeEvent(event)