from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLineEdit, QPushButton, QScrollArea, QLabel, 
                             QGridLayout, QSizePolicy, QApplication)
from PyQt6.QtCore import Qt, QTimer, QThreadPool, QSize, QEvent
from PyQt6.QtGui import QIcon, QPixmap
from pathlib import Path
import os
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
        self.setup_global_shortcut()
        
        self.apply_theme()
        
    def setup_ui(self):
        self.setWindowTitle("Petra")
        self.setFixedSize(515, 680)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        central = QWidget()
        central.setObjectName("main_window")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
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
        
        # Botón cerrar CON "X"
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
        scroll.setWidgetResizable(True)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_layout.addStretch()
        
        scroll.setWidget(self.content_widget)
        # keep a reference so we can call ensureWidgetVisible when navigating
        self.scroll_area = scroll
        main_layout.addWidget(scroll)
    
    def setup_icon_button(self, button, icon_name):
        try:
            icons_folder = self.themes_manager.get_icons_folder() if hasattr(self, 'themes_manager') else 'dark'
            icons_dir = Path(__file__).parent / 'icons' / icons_folder
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
            icons_dir = Path(__file__).parent / 'icons' / icons_folder
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
            
            self.update_filter_styles()
            self.update_styles_recursive(self)
            self.refresh_ui()
            
        except Exception as e:
            print(f"Error aplicando tema: {e}")
    
    def update_header_icons(self):
        """Update header button icons according to current theme"""
        try:
            icons_folder = self.themes_manager.get_icons_folder()
            icons_dir = Path(__file__).parent / 'icons' / icons_folder
            
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
            for child in widget.findChildren(QWidget):
                self.update_styles_recursive(child)
        except Exception:
            pass
    
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
        
        if pinned:
            for clip in pinned:
                self.add_clip_widget(clip)
        
        if unpinned:
            for clip in unpinned:
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
        # Clear selected content to avoid hover state being restored after refresh
        self._selected_content = None
        self._keyboard_selection_active = False
        self.refresh_ui()

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
        
        self.themes_manager.apply_theme_to_widget(self)

    def filter_items(self):
        self.refresh_ui()

    def show_emoji_picker(self):
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        emoji_container = QWidget()
        emoji_layout = QVBoxLayout(emoji_container)
        emoji_layout.setContentsMargins(15, 15, 15, 15)
        emoji_layout.setSpacing(10)
        
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setSpacing(8)
        
        emojis = [
            "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
            "😉", "😊", "😇", "🥰", "😍", "🤩", "😘", "😗", "☺️", "😚",
            "😙", "🥲", "😋", "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭",
            "🤫", "🤔", "🤐", "🤨", "😐", "😑", "😶", "😏", "😒", "🙄",
            "😬", "🤥", "😌", "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕",
            "🤢", "🤮", "🤧", "🥵", "🥶", "🥴", "😵", "🤯", "🤠", "🥳",
            "🥸", "😎", "🤓", "🧐", "😕", "😟", "🙁", "☹️", "😮", "😯",
            "😲", "😳", "🥺", "😦", "😧", "😨", "😰", "😥", "😢", "😭",
            "😱", "😖", "😣", "😞", "😓", "😩", "😫", "🥱", "😤", "😡",
            "😠", "🤬", "😈", "👿", "💀", "☠️", "💩", "🤡", "👹", "👺",
            "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤌", "🤏", "✌️", "🤞",
            "🤟", "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍",
            "👎", "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝",
            "🙏", "✍️", "💅", "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂",
            "🦻", "👃", "🧠", "🫀", "🫁", "🦷", "🦴", "👀", "👁️", "👅",
            "👄", "👶", "🧒", "👦", "👧", "🧑", "👱", "👨", "🧔", "👨‍🦰",
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
            "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮️",
            "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️", "🛐",
            "⛎", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐",
            "♑", "♒", "♓", "🆔", "⚛️", "🉑", "☢️", "☣️", "📴", "📳",
            "🕛", "🕧", "🕐", "🕜", "🕑", "🕝", "🕒", "🕞", "🕓", "🕟",
            "🕔", "🕠", "🕕", "🕡", "🕖", "🕢", "🕗", "🕣", "🕘", "🕤",
            "🕙", "🕥", "🕚", "🕦", "⌛", "⏳", "⌚", "⏰", "⏱️", "⏲️",
            "🕰️", "🌡️", "⛈️", "🌩️", "🌧️", "☀️", "🌤️", "⛅", "🌥️", "☁️",
            "↩️", "↪️", "⚡", "♻️", "📛", "🔰", "🔱", "⭕", "✅", "☑️",
            "✔️", "❌", "❎", "➰", "➿", "〽️", "✳️", "❇️", "▪️", "▫️",
            "◾", "◽", "◼️", "◻️", "⬛", "⬜", "🔶", "🔷", "🔸", "🔹",
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
        self.inserting_emoji = True
        self.last_emoji_inserted = emoji
        self.last_clipboard = emoji
        clipboard = QApplication.clipboard()
        clipboard.setText(emoji)
        
        try:
            self.input_simulator.simulate_alt_tab()
            QTimer.singleShot(150, self.simulate_paste)
            QTimer.singleShot(500, self.clear_emoji_flags)
        except Exception as e:
            print(f"Error al cambiar foco: {e}")

    def clear_emoji_flags(self):
        self.inserting_emoji = False
        self.last_emoji_inserted = None

    def show_window(self):
        """Mostrar ventana centrada y enfocada"""
        try:
            # Guardar ventana activa actual
            if self.display_server == 'x11' and self.detector.is_tool_available('xdotool'):
                proc = subprocess.run(['xdotool', 'getactivewindow'], 
                                    capture_output=True, text=True, timeout=0.2)
                if proc.returncode == 0 and proc.stdout.strip():
                    self.last_active_window = proc.stdout.strip()
        except Exception:
            self.last_active_window = None

        # Mostrar y centrar ventana
        self.center_window()
        self.show()
        self.activateWindow()
        self.raise_()
        # Keyboard selection mode should be inactive when window first appears
        # (no item highlighted). We'll clear visual selection hints here and
        # only enable keyboard selection when a keypress is detected.
        try:
            self._keyboard_selection_active = False
            self._first_nav_after_activation = False
            for w in self.findChildren(ClipItem):
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
        
        # Crear archivo de estado de visibilidad
        try:
            visibility_file = Path("/tmp/petra_visible")
            visibility_file.touch()
        except:
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
        except:
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
            icons_dir = Path(__file__).parent / 'icons' / icons_folder
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
                # Activate keyboard-selection mode on the first keypress (unless
                # the user is typing into the search bar). After activation,
                # selection visuals (hover) will appear.
                try:
                    focus = QApplication.focusWidget()
                    if not (hasattr(self, 'search_bar') and focus is self.search_bar):
                        if not getattr(self, '_keyboard_selection_active', False):
                            self._keyboard_selection_active = True
                            # Mark that the next navigation is the first one after activation
                            self._first_nav_after_activation = True
                            # if we have a previously tracked selected content, try to restore it
                            try:
                                visible = self.get_visible_clip_widgets()
                                if visible:
                                    if getattr(self, '_selected_content', None):
                                        for w in visible:
                                            try:
                                                if getattr(w, 'content', None) == self._selected_content:
                                                    self._set_selected_clip_widget(w)
                                                    break
                                            except Exception:
                                                pass
                                    else:
                                        # no prior selection - pick first visible
                                        self._set_selected_clip_widget(visible[0])
                            except Exception:
                                pass
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
                mods = event.modifiers()
                # emulate press-and-hold for Q -> pin button and W -> clear button
                try:
                    focus = QApplication.focusWidget()
                    # only simulate header buttons when user is not typing into search
                    if not (hasattr(self, 'search_bar') and focus is self.search_bar):
                        # Q down -> press clear button (visual down) until key release
                        # NOTE: 'Q' now performs the delete-all long-press behavior.
                        if k == Qt.Key.Key_Q and not is_repeat:
                            try:
                                if not getattr(self, '_key_q_down', False):
                                    self._key_q_down = True
                                    if hasattr(self, 'clear_btn') and self.clear_btn:
                                        # visually depress the clear button and start
                                        # long-press delete animation (same behavior as mouse)
                                        self.clear_btn.setDown(True)
                                        try:
                                            self.clear_btn.is_actively_pressed = True
                                            self.clear_btn.setProgress(0)
                                        except Exception:
                                            pass
                                        try:
                                            self.start_clear_animation()
                                        except Exception:
                                            pass
                                    # consume the event
                                    return True
                            except Exception:
                                pass
                        # W down -> press pin button (visual down) until key release
                        # NOTE: 'W' now toggles pin on release (same as clicking pin)
                        if k == Qt.Key.Key_W and not is_repeat:
                            try:
                                if not getattr(self, '_key_w_down', False):
                                    self._key_w_down = True
                                    if hasattr(self, 'pin_window_btn') and self.pin_window_btn:
                                        # visually depress pin button
                                        self.pin_window_btn.setDown(True)
                                        # pin press: only show visual 'down' state; do not
                                        # start any clear animation here (that belongs to Q)
                                    # consume the event
                                    return True
                            except Exception:
                                pass
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

                # Escape -> if search has focus, clear it, otherwise hide
                if k == Qt.Key.Key_Escape:
                    try:
                        focus = QApplication.focusWidget()
                        if hasattr(self, 'search_bar') and focus is self.search_bar:
                            try:
                                self.search_bar.clearFocus()
                                return True
                            except Exception:
                                pass
                        # not focusing search -> hide the window
                        self.hide()
                        return True
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

                    # Q release -> finalize pin button press (toggle on release)
                    if k == Qt.Key.Key_Q and not is_repeat:
                        try:
                            if getattr(self, '_key_q_down', False):
                                # Q acts as clear release -> stop animation / reset
                                self._key_q_down = False
                                if hasattr(self, 'clear_btn') and self.clear_btn:
                                    try:
                                        self.clear_btn.setDown(False)
                                        self.cancel_clear_animation()
                                        try:
                                            self.clear_btn.is_actively_pressed = False
                                            self.clear_btn.setProgress(0)
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                            return True
                        except Exception:
                            pass

                    # W release -> cancel visual and stop/complete clear as appropriate
                    if k == Qt.Key.Key_W and not is_repeat:
                        try:
                            if getattr(self, '_key_w_down', False):
                                # W acts as pin release -> toggle on release
                                self._key_w_down = False
                                if hasattr(self, 'pin_window_btn') and self.pin_window_btn:
                                    try:
                                        self.pin_window_btn.setDown(False)
                                        # toggling the pin on release
                                        self.toggle_window_pin()
                                    except Exception:
                                        pass
                            return True
                        except Exception:
                            pass
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

        try:
            visible = list(self.get_visible_clip_widgets())
        except Exception:
            visible = []
        if not visible:
            return

        # If this is the first navigation after keyboard activation, the first
        # item is already selected visually. Don't advance, just clear the flag.
        if getattr(self, '_first_nav_after_activation', False):
            self._first_nav_after_activation = False
            # Ensure first item is selected and return without advancing
            self._set_selected_clip_widget(visible[0])
            return

        current = None
        for i, w in enumerate(visible):
            if w.property('selected') == 'true':
                current = i
                break

        if current is None:
            new = 0
        else:
            new = (current + 1) if current < len(visible) - 1 else 0

        target = visible[new]
        try:
            container = target.parentWidget()
            if hasattr(self, 'scroll_area') and self.scroll_area:
                self.scroll_area.ensureWidgetVisible(container)
        except Exception:
            pass

        self._set_selected_clip_widget(target)

    def switch_filter_left(self):
        try:
            if not getattr(self, 'isVisible', None) or not self.isVisible():
                return
            filters = list(self.filter_buttons.keys())
            current_index = filters.index(self.current_filter) if self.current_filter in filters else 0
            new_index = (current_index - 1) % len(filters)
            self.set_filter(filters[new_index])
            # select first visible after filter change
            visible = self.get_visible_clip_widgets()
            if visible:
                self._set_selected_clip_widget(visible[0])
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
            visible = self.get_visible_clip_widgets()
            if visible:
                self._set_selected_clip_widget(visible[0])
        except Exception:
            pass