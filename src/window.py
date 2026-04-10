from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, 
                             QGridLayout, QSizePolicy, QApplication, QGraphicsOpacityEffect,
                             QSystemTrayIcon)
from PyQt6.QtCore import Qt, QTimer, QThreadPool, QSize, QEvent
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor, QPen, QLinearGradient
from pathlib import Path
import os
import subprocess

from widgets import ProgressButton, ClipItem
from clipboard import ClipboardManager
from filters import FilterManager
from config import ConfigManager
from global_shortcut_multi import GlobalShortcutManager
from themes_manager import ThemesManager
from emoji_picker import EmojiPickerMixin, EmojiCarousel
from keyboard_handler import KeyboardHandlerMixin
from tray_manager import TrayManagerMixin


class PetraClipboard(QMainWindow, ClipboardManager, FilterManager, ConfigManager,
                     EmojiPickerMixin, KeyboardHandlerMixin, TrayManagerMixin):
    # MRO: EmojiPickerMixin.show_emoji_picker overrides FilterManager.show_emoji_picker (intentional)
    # MRO: KeyboardHandlerMixin.eventFilter overrides QObject.eventFilter (intentional)
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
        # self._setup_update_checker()

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
        """Toggle window visibility — called by the shortcut manager.

        Using isActiveWindow() is unreliable on Cinnamon because focus may not
        be delivered by the WM before the second shortcut press arrives.
        Instead we track _last_shown_time: if the window is visible and enough
        time has passed since it was shown (i.e. the user is intentionally
        closing it), we hide it.  If it was just shown (< 400 ms ago) the
        shortcut is likely still being held and we do nothing, letting the WM
        finish delivering focus.
        """
        if self.isVisible():
            elapsed = getattr(self, '_last_shown_time', 0)
            import time
            now = time.monotonic() * 1000  # ms
            if now - elapsed < 400:
                # Window just appeared; ignore this press to avoid double-fire
                return
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
            QTimer.singleShot(0, self.save_pinned)
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
        
        QTimer.singleShot(0, self.save_pinned)
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
        import time
        self._last_shown_time = time.monotonic() * 1000  # ms – used by _handle_shortcut_toggle
        
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

