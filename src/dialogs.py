from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, 
                             QSpinBox, QCheckBox, QPushButton, QWidget, QComboBox, QSizePolicy, QAbstractSpinBox,
                             QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QSize, QTimer, QUrl
from PyQt6.QtGui import QIcon, QDesktopServices
from pathlib import Path
import os
import sys

# from widgets import ShortcutEdit
from themes_manager import ThemesManager


def get_autostart_path():
    """Get path to .desktop file in autostart"""
    config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config"))
    return config_base / "autostart" / "petra.desktop"


def is_autostart_enabled():
    """Check if autostart is enabled"""
    return get_autostart_path().exists()


def is_running_in_flatpak():
    """Detect if application is running inside Flatpak"""
    # Check Flatpak environment variable
    if os.environ.get('FLATPAK_ID'):
        return True
    # Check if Flatpak info file exists
    if Path('/.flatpak-info').exists():
        return True
    # Check if running within a Flatpak directory
    if '/app/' in str(Path(__file__).resolve()):
        return True
    return False


def enable_autostart():
    """Create .desktop file for autostart"""
    config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config"))
    autostart_dir = config_base / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine execution command based on environment
    if is_running_in_flatpak():
        # In Flatpak, use 'flatpak run' with app ID
        flatpak_id = os.environ.get('FLATPAK_ID', 'io.github.gessendarien.petra')
        exec_path = f"flatpak run {flatpak_id}"
        icon_name = flatpak_id
    elif os.environ.get("APPIMAGE"):
        # If running as AppImage
        appimage_path = os.environ.get("APPIMAGE")
        exec_path = f'"{appimage_path}"'
        icon_name = "Petra"
    elif getattr(sys, 'frozen', False):
        # If compiled executable
        exec_path = f'"{sys.executable}"'
        icon_name = "accessories-clipboard"
    else:
        # If running as Python script
        main_script = Path(__file__).parent / "main.py"
        exec_path = f'python3 "{main_script}"'
        icon_name = "accessories-clipboard"
    
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=Petra Clipboard
Comment=Clipboard manager with emoji support
Exec={exec_path} --hidden
Icon={icon_name}
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
StartupWMClass=Petra
"""
    
    desktop_file = get_autostart_path()
    with open(desktop_file, 'w') as f:
        f.write(desktop_content)
    
    # Make file executable
    os.chmod(desktop_file, 0o755)


def disable_autostart():
    """Remove .desktop file from autostart"""
    desktop_file = get_autostart_path()
    if desktop_file.exists():
        desktop_file.unlink()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.themes_manager = ThemesManager()
        self.setWindowTitle("Configuración")
        self.setFixedSize(400, 420)  # Increased to include new option
        self.setModal(True)

        self.apply_dark_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Title removed per user request
        title = QLabel("")
        title.setObjectName("settings_title")
        layout.addWidget(title)

        # Grid Layout for aligned selects (Language, Theme, Open from, Shortcut)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        grid_layout.setColumnStretch(1, 0) # Don't stretch input column excessively, use fixed width widgets

        # 1. Language
        self.lang_label = QLabel("")
        self.lang_label.setObjectName("settings_label")
        grid_layout.addWidget(self.lang_label, 0, 0)
        
        self.lang_combo = QComboBox()
        self.lang_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.lang_combo.setFixedWidth(180)
        self.lang_combo.addItem("Español", 'es')
        self.lang_combo.addItem("English", 'en')
        grid_layout.addWidget(self.lang_combo, 0, 1)

        # 2. Theme
        self.theme_label = QLabel("Tema:")
        self.theme_label.setObjectName("settings_label")
        grid_layout.addWidget(self.theme_label, 1, 0)
        
        self.theme_combo = QComboBox()
        self.theme_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.theme_combo.setFixedWidth(180)
        
        # Add available themes
        themes = self.themes_manager.get_theme_names()
        for theme_id, theme_name in themes:
            self.theme_combo.addItem(theme_name, theme_id)
        grid_layout.addWidget(self.theme_combo, 1, 1)

        # 3. Open Position
        self.open_pos_label = QLabel("Abrir desde:")
        self.open_pos_label.setObjectName("settings_label")
        grid_layout.addWidget(self.open_pos_label, 2, 0)
        
        self.open_pos_combo = QComboBox()
        self.open_pos_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.open_pos_combo.setFixedWidth(180)
        self.open_pos_combo.addItem("Posición del mouse", 'mouse')
        self.open_pos_combo.addItem("Centro de pantalla", 'center')
        self.open_pos_combo.addItem("Izquierda de pantalla", 'left')
        self.open_pos_combo.addItem("Derecha de pantalla", 'right')
        grid_layout.addWidget(self.open_pos_combo, 2, 1)

        # 4. Shortcut
        self.shortcut_label = QLabel("Shortcut:")
        self.shortcut_label.setObjectName("settings_label")
        grid_layout.addWidget(self.shortcut_label, 3, 0)
        
        self.shortcut_combo = QComboBox()
        self.shortcut_combo.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.shortcut_combo.setFixedWidth(180)
        
        # Common shortcuts options
        common_shortcuts = [
            "Super + v",
            "Ctrl + Alt + v",
            "Alt + v",
            "Alt + z",
            "Alt + x",
            "Alt + space"
        ]
        self.shortcut_combo.addItems(common_shortcuts)
        grid_layout.addWidget(self.shortcut_combo, 3, 1)

        # Align grid to the left
        grid_container = QWidget()
        gcl = QHBoxLayout(grid_container)
        gcl.setContentsMargins(0, 0, 0, 0)
        gcl.addLayout(grid_layout)
        gcl.addStretch() # Push everything to the left
        
        layout.addWidget(grid_container)

        # 5 & 6. Max History and Max Images (Grid aligned)
        limits_container = QWidget()
        limits_layout = QGridLayout(limits_container)
        limits_layout.setContentsMargins(0, 0, 0, 0)
        limits_layout.setSpacing(10)
        limits_layout.setColumnStretch(2, 1) # Push everything to the left

        # Max History Items (Top)
        self.max_clips_label = QLabel("Máx. elementos en historial:")
        self.max_clips_label.setObjectName("settings_label")
        limits_layout.addWidget(self.max_clips_label, 0, 0)

        self.max_clips_sb = QSpinBox()
        self.max_clips_sb.setRange(10, 100)
        self.max_clips_sb.setFixedWidth(50)
        self.max_clips_sb.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.max_clips_sb.setStyleSheet("padding: 2px;")
        limits_layout.addWidget(self.max_clips_sb, 0, 1)

        # Max Images in Cache (Bottom)
        self.max_images_label = QLabel("Máx. imágenes en caché:")
        self.max_images_label.setObjectName("settings_label")
        limits_layout.addWidget(self.max_images_label, 1, 0)
        
        self.max_images_sb = QSpinBox()
        self.max_images_sb.setRange(1, 100)
        self.max_images_sb.setFixedWidth(50)
        self.max_images_sb.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.max_images_sb.setStyleSheet("padding: 2px;") 
        limits_layout.addWidget(self.max_images_sb, 1, 1)

        layout.addWidget(limits_container)

        # Show/Hide clear-all button
        self.show_clear_cb = QCheckBox("Mostrar botón 'Borrar todo' en la cabecera")
        self.show_clear_cb.setObjectName("settings_checkbox")
        layout.addWidget(self.show_clear_cb)

        # Show/Hide pin-window button
        self.show_pin_cb = QCheckBox("Mostrar botón 'Fijar ventana' en la cabecera")
        self.show_pin_cb.setObjectName("settings_checkbox")
        layout.addWidget(self.show_pin_cb)

        # Start with system (autostart)
        self.autostart_cb = QCheckBox("Iniciar con el sistema")
        self.autostart_cb.setObjectName("settings_checkbox")
        layout.addWidget(self.autostart_cb)
        layout.addStretch()

        # Buttons
        btn_row = QWidget()
        brl = QHBoxLayout(btn_row)
        brl.setContentsMargins(0, 0, 0, 0)
        
        # GitHub icon button (left side)
        self.github_btn = QPushButton()
        self.github_btn.setFixedSize(36, 36)
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.setToolTip("Tienes la última versión")
        self.github_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self.github_btn.clicked.connect(self.open_update_dialog)
        
        # Update animation
        self._update_anim = None
        self._github_btn_rotation = 0.0
        brl.addWidget(self.github_btn)
        
        brl.addStretch()
        
        self.save_btn = QPushButton("Guardar")
        self.save_btn.setObjectName("settings_save_button")
        self.save_btn.clicked.connect(self.save)
        
        self.close_btn = QPushButton("Cancelar")
        self.close_btn.setObjectName("settings_close_button")
        self.close_btn.clicked.connect(self.reject)
        
        self.quit_btn = QPushButton("Salir")
        self.quit_btn.setObjectName("settings_quit_button")
        self.quit_btn.clicked.connect(self.quit_app)
        
        brl.addWidget(self.save_btn)
        brl.addWidget(self.close_btn)
        brl.addWidget(self.quit_btn)

        layout.addWidget(btn_row)

        self.initialize_values()
        self.setup_translations()
        self.apply_translations(self.lang_combo.currentData())
        self.lang_combo.currentIndexChanged.connect(lambda i: self.apply_translations(self.lang_combo.itemData(i)))
        
        # Update GitHub icon based on current applied theme
        self.update_github_icon()
        
        # Apply theme to dialog
        self.apply_dark_theme()

    def update_github_icon(self):
        """Update GitHub icon based on currently applied theme (from parent)"""
        theme = 'dark'
        if self.parent() is not None:
            theme = getattr(self.parent(), 'theme', 'dark') or 'dark'
        
        # Determine icon folder based on theme
        if 'light' in str(theme).lower():
            icon_folder = 'light'
        else:
            icon_folder = 'dark'
        
        icon_path = Path(__file__).parent.parent / "icons" / icon_folder / "code.png"
        if icon_path.exists():
            self.github_btn.setIcon(QIcon(str(icon_path)))
            self.github_btn.setIconSize(QSize(30, 30))

    def apply_dark_theme(self):
        """Force dark theme for settings dialog with borders on inputs."""
        self.setStyleSheet(
            """
            QComboBox, QSpinBox {
                border: 1px solid #FFFFFF;
                border-radius: 4px;
                padding: 4px;
            }
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
            """
        )

    def initialize_values(self):
        try:
            if self.parent() is not None:
                parent = self.parent()
                self.max_images_sb.setValue(int(getattr(parent, 'max_images', 10)))
                self.max_clips_sb.setValue(int(getattr(parent, 'max_clips', 20)))
                
                lang = getattr(parent, 'language', 'en')
                idx = self.lang_combo.findData(lang)
                if idx >= 0:
                    self.lang_combo.setCurrentIndex(idx)
                    
                # New: load theme
                theme = getattr(parent, 'theme', 'dark')
                theme_idx = self.theme_combo.findData(theme)
                if theme_idx >= 0:
                    self.theme_combo.setCurrentIndex(theme_idx)
                    
                self.show_clear_cb.setChecked(bool(getattr(parent, 'show_clear_btn', True)))
                self.show_pin_cb.setChecked(bool(getattr(parent, 'show_pin_btn', False)))
                
                # Open position combo
                open_pos = getattr(parent, 'open_position', 'mouse')
                pos_idx = self.open_pos_combo.findData(open_pos)
                if pos_idx >= 0:
                    self.open_pos_combo.setCurrentIndex(pos_idx)
                
                # Check if autostart is enabled
                self.autostart_cb.setChecked(is_autostart_enabled())
                
                sc = getattr(parent, 'shortcut', 'Alt + space')
                if sc:
                    # Normalize string to match options
                    sc_str = str(sc).strip()
                    index = self.shortcut_combo.findText(sc_str, Qt.MatchFlag.MatchFixedString)
                    if index >= 0:
                        self.shortcut_combo.setCurrentIndex(index)
                    else:
                        # If custom shortcut not in list, add it
                        self.shortcut_combo.addItem(sc_str)
                        self.shortcut_combo.setCurrentIndex(self.shortcut_combo.count() - 1)
        except Exception:
            pass

    def setup_translations(self):
        self.translations = {
            'es': {
                'title': 'Configuración',
                'max_images': 'Máx. imágenes en caché:',
                'max_clips': 'Máx. elementos en historial:',
                'save': 'Guardar',
                'close': 'Cancelar',
                'quit': 'Salir',
                'language': 'Idioma:',
                'theme': 'Tema:',
                'show_clear': "Mostrar botón 'Borrar todo' en la cabecera",
                'show_pin': "Mostrar botón 'Fijar ventana' en la cabecera",
                'open_from': "Abrir desde:",
                'pos_mouse': "Posición del mouse",
                'pos_center': "Centro de pantalla",
                'pos_left': "Izquierda de pantalla",
                'pos_right': "Derecha de pantalla",
                'autostart': "Iniciar con el sistema",
                'shortcut': "⚠ Atajo:",
                'shortcut_tooltip': "Algunos atajos pueden entrar en conflicto con otros programas y hacer que Petra no responda correctamente",
                'tooltip_update': 'Nueva versión disponible',
                'tooltip_no_update': 'Tienes la última versión'
            },
            'en': {
                'title': 'Settings',
                'max_images': 'Max images in cache:',
                'max_clips': 'Max history items:',
                'save': 'Save',
                'close': 'Cancel',
                'quit': 'Quit',
                'language': 'Language:',
                'theme': 'Theme:',
                'show_clear': "Show 'Clear All' button in header",
                'show_pin': "Show 'Pin window' button in header",
                'open_from': "Open from:",
                'pos_mouse': "Mouse position",
                'pos_center': "Center of screen",
                'pos_left': "Left of screen",
                'pos_right': "Right of screen",
                'autostart': "Start with system",
                'shortcut': "⚠ Shortcut:",
                'shortcut_tooltip': "Some shortcuts may conflict with other programs and cause Petra to become unresponsive",
                'tooltip_update': 'New version available',
                'tooltip_no_update': 'You have the latest version'
            }
        }

    def apply_theme(self):
        """Aplicar el tema actual al diálogo"""
        try:
            if self.parent() is not None:
                parent_theme = getattr(self.parent(), 'theme', 'dark')
                self.themes_manager.apply_theme_to_widget(self, parent_theme)
        except Exception:
            pass

    def save(self):
        try:
            parent = self.parent()
            if parent is not None:
                parent.max_images = int(self.max_images_sb.value())
                parent.max_clips = int(self.max_clips_sb.value())
                parent.language = self.lang_combo.currentData()
                
                # New: save theme
                parent.theme = self.theme_combo.currentData()
                
                parent.show_clear_btn = bool(self.show_clear_cb.isChecked())
                if hasattr(parent, 'clear_btn'):
                    if parent.show_clear_btn:
                        parent.clear_btn.show()
                    else:
                        parent.clear_btn.hide()
                        
                parent.show_pin_btn = bool(self.show_pin_cb.isChecked())
                if hasattr(parent, 'pin_window_btn'):
                    if parent.show_pin_btn:
                        parent.pin_window_btn.show()
                    else:
                        parent.pin_window_btn.hide()
                
                parent.open_position = self.open_pos_combo.currentData()
                
                # Handle autostart
                if self.autostart_cb.isChecked():
                    enable_autostart()
                else:
                    disable_autostart()
                        
                parent.shortcut = self.shortcut_combo.currentText()

                
                parent.config['language'] = parent.language
                parent.config['max_images'] = parent.max_images
                parent.config['max_clips'] = parent.max_clips
                parent.config['shortcut'] = getattr(parent, 'shortcut', 'Super + v')
                parent.config['theme'] = parent.theme  # New
                
                parent.save_config()
                
                # Apply new theme
                if hasattr(parent, 'apply_theme'):
                    parent.apply_theme()
                
                if hasattr(parent, 'shortcut_manager'):
                    parent.shortcut_manager.register_global_hotkey(parent.shortcut)
        except Exception as e:
            print(f"DEBUG: Error saving settings: {e}")
        self.accept()

    def apply_translations(self, code):
        t = self.translations.get(code, self.translations.get('es'))
        try:
            self.setWindowTitle(t.get('title', 'Configuración'))
            
            if hasattr(self, 'max_images_label'):
                self.max_images_label.setText(t.get('max_images', self.max_images_label.text()))
                
            if hasattr(self, 'max_clips_label'):
                self.max_clips_label.setText(t.get('max_clips', self.max_clips_label.text()))
                
            if hasattr(self, 'show_clear_cb'):
                self.show_clear_cb.setText(t.get('show_clear', self.show_clear_cb.text()))
                
            if hasattr(self, 'shortcut_label'):
                self.shortcut_label.setText(t.get('shortcut', self.shortcut_label.text()))
                self.shortcut_label.setToolTip(t.get('shortcut_tooltip', ''))
                
            if hasattr(self, 'lang_label'):
                self.lang_label.setText(t.get('language', self.lang_label.text()))
                
            if hasattr(self, 'github_btn'):
                parent_win = self.parent()
                if parent_win and getattr(parent_win, '_pending_update_anim', False):
                    self.github_btn.setToolTip(t.get('tooltip_update', 'Nueva versión disponible'))
                else:
                    self.github_btn.setToolTip(t.get('tooltip_no_update', 'Tienes la última versión'))
                
            # New: translate theme label
            if hasattr(self, 'theme_label'):
                self.theme_label.setText(t.get('theme', self.theme_label.text()))
                
            if hasattr(self, 'show_pin_cb'):
                self.show_pin_cb.setText(t.get('show_pin', self.show_pin_cb.text()))
            
            if hasattr(self, 'open_pos_label'):
                self.open_pos_label.setText(t.get('open_from', self.open_pos_label.text()))
            
            if hasattr(self, 'open_pos_combo'):
                # Update combo items with translations
                self.open_pos_combo.setItemText(0, t.get('pos_mouse', 'Posición del mouse'))
                self.open_pos_combo.setItemText(1, t.get('pos_center', 'Centro de pantalla'))
                self.open_pos_combo.setItemText(2, t.get('pos_left', 'Izquierda de pantalla'))
                self.open_pos_combo.setItemText(3, t.get('pos_right', 'Derecha de pantalla'))
            
            if hasattr(self, 'autostart_cb'):
                self.autostart_cb.setText(t.get('autostart', self.autostart_cb.text()))
                
            if hasattr(self, 'save_btn'):
                self.save_btn.setText(t.get('save', self.save_btn.text()))
            if hasattr(self, 'close_btn'):
                self.close_btn.setText(t.get('close', self.close_btn.text()))
            if hasattr(self, 'quit_btn'):
                self.quit_btn.setText(t.get('quit', self.quit_btn.text()))
        except Exception:
            pass
    
    def quit_app(self):
        """Quit the application completely"""
        from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
        from PyQt6.QtCore import Qt
        
        # Confirmation dialog
        lang = self.lang_combo.currentData() if hasattr(self, 'lang_combo') else 'en'
        if lang == 'es':
            title = "Confirmar"
            text = "¿Estás seguro de que quieres cerrar Petra?"
            yes_text = "Sí"
            no_text = "No"
        else:
            title = "Confirm"
            text = "Are you sure you want to quit Petra?"
            yes_text = "Yes"
            no_text = "No"
        
        # Get themes_manager from parent (main window) which has current theme
        parent_win = self.parent()
        if parent_win and hasattr(parent_win, 'themes_manager'):
            theme = parent_win.themes_manager.get_current_theme()
        else:
            theme = self.themes_manager.get_current_theme() if hasattr(self, 'themes_manager') else {"colors": {}}
        colors = theme.get("colors", {})
        text_color = colors.get("confirm_text", "#FFFFFF")

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setFixedSize(320, 130)
        
        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(20, 20, 20, 20)
        
        lbl = QLabel(text)
        lbl.setStyleSheet(f"color: {text_color}; font-size: 14px; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_layout.setSpacing(20)
        
        btn_style = """
            QPushButton {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #FFFFFF;
                border-radius: 4px;
                padding: 6px 16px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #333333;
            }
        """
        
        btn_no = QPushButton(no_text)
        btn_no.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_no.setStyleSheet(btn_style)
        
        btn_yes = QPushButton(yes_text)
        btn_yes.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_yes.setStyleSheet(btn_style)
        
        btn_no.clicked.connect(dlg.reject)
        btn_yes.clicked.connect(dlg.accept)
        
        btn_layout.addWidget(btn_no)
        btn_layout.addWidget(btn_yes)
        
        layout.addLayout(btn_layout)

        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.reject()
            if self.parent() and hasattr(self.parent(), 'quit_application'):
                self.parent().quit_application()
            else:
                QApplication.quit()
    
    def open_github(self):
        """Open the project website in the default browser"""
        QDesktopServices.openUrl(QUrl("https://gessendarien.github.io/petra-clipboard/"))

    # ── Update animation ──────────────────────────────────────────────

    def start_update_animation(self):
        """Start heartbeat (scale pulse) animation on github_btn."""
        if not hasattr(self, '_original_github_icon'):
            self._original_github_icon = self.github_btn.icon()
            self._original_github_icon_size = self.github_btn.iconSize()

        # Set tooltip based on language
        parent_win = self.parent()
        lang = getattr(parent_win, 'language', 'es') if parent_win else 'es'
        tip = "Nueva versión disponible" if lang == 'es' else "New version available"
        self.github_btn.setToolTip(tip)

        # Heartbeat: expand(1.0→1.2) → contract(1.2→0.85) → restore(0.85→1.0), pause 1s, repeat
        self._hb_scale = 1.0
        self._hb_phase = 0   # 0=expand, 1=contract, 2=restore, 3=pause
        self._hb_pause_count = 0

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(25)  # 40fps
        self._anim_timer.timeout.connect(self._tick_heartbeat)
        self._anim_timer.start()

    def _tick_heartbeat(self):
        speed = 0.02
        if self._hb_phase == 0:  # expand 1.0 → 1.2
            self._hb_scale += speed
            if self._hb_scale >= 1.2:
                self._hb_scale = 1.2
                self._hb_phase = 1
        elif self._hb_phase == 1:  # contract 1.2 → 0.85
            self._hb_scale -= speed
            if self._hb_scale <= 0.85:
                self._hb_scale = 0.85
                self._hb_phase = 2
        elif self._hb_phase == 2:  # restore 0.85 → 1.0
            self._hb_scale += speed
            if self._hb_scale >= 1.0:
                self._hb_scale = 1.0
                self._hb_phase = 3
                self._hb_pause_count = 0
        elif self._hb_phase == 3:  # pause ~1 second
            self._hb_pause_count += 1
            if self._hb_pause_count >= 40:
                self._hb_phase = 0

        self._apply_scale(self._hb_scale)

    def _apply_scale(self, scale):
        if hasattr(self, '_original_github_icon'):
            base_size = self._original_github_icon_size
            new_w = max(1, int(base_size.width() * scale))
            new_h = max(1, int(base_size.height() * scale))
            scaled_size = QSize(new_w, new_h)
            pixmap = self._original_github_icon.pixmap(base_size)
            scaled_pixmap = pixmap.scaled(
                scaled_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.github_btn.setIcon(QIcon(scaled_pixmap))
            self.github_btn.setIconSize(base_size)

    def stop_update_animation(self):
        """Stop animation and restore icon."""
        if hasattr(self, '_anim_timer') and self._anim_timer is not None:
            self._anim_timer.stop()
            self._anim_timer = None
        if hasattr(self, '_original_github_icon'):
            self.github_btn.setIcon(self._original_github_icon)
            self.github_btn.setIconSize(self._original_github_icon_size)

    # ── Update dialog launcher ────────────────────────────────────────

    def open_update_dialog(self):
        """Open the UpdateDialog from the settings window."""
        from updater import detect_install_type, _read_version
        parent_win = self.parent()
        version = getattr(parent_win, '_update_available_version', None) if parent_win else None
        install_type = detect_install_type()
        lang = self.lang_combo.currentData() if hasattr(self, 'lang_combo') else 'es'
        # Get primary color from theme
        primary_color = '#A855F7'
        theme_id = None
        if parent_win and hasattr(parent_win, 'themes_manager'):
            try:
                theme_id = getattr(parent_win, 'theme', 'dark')
                colors = parent_win.themes_manager.get_theme_colors(theme_id)
                primary_color = colors.get('primary', primary_color)
            except Exception:
                pass
        current_version = _read_version()
        # Check if this version was ignored
        ignored = None
        if parent_win and hasattr(parent_win, 'config'):
            ignored = parent_win.config.get('ignored_update')
        dlg = UpdateDialog(parent_win, version, install_type, lang,
                           primary_color, current_version, theme_id, ignored)
        dlg.exec()


class UpdateDialog(QDialog):
    """Dialog shown when user clicks the code/github button in settings."""

    TRANSLATIONS = {
        'es': {
            'window_title': 'Actualización {version}',
            'update_available': 'Nueva versión disponible {version}',
            'up_to_date': 'Tienes la última versión {version}',
            'snap_available': 'Nueva versión {version} disponible en la tienda de aplicaciones',
            'snap_up_to_date': 'Tienes la última versión {version}',
            'no_remind': 'No volver a recordar',
            'credits': 'Créditos',
            'update': 'Actualizar',
            'update_title': 'Actualización',
            'error_title': 'Error',
        },
        'en': {
            'window_title': 'Update {version}',
            'update_available': 'New version available {version}',
            'up_to_date': 'You have the latest version {version}',
            'snap_available': 'New version {version} available in the app store',
            'snap_up_to_date': 'You have the latest version {version}',
            'no_remind': 'Don\'t remind me again',
            'credits': 'Credits',
            'update': 'Update',
            'update_title': 'Update',
            'error_title': 'Error',
        },
    }

    def __init__(self, parent=None, version=None, install_type='deb', lang='es',
                 primary_color='#A855F7', current_version='0.0.1',
                 theme_id=None, ignored_version=None):
        super().__init__(parent)
        self.version = version
        self.install_type = install_type
        self._downloader = None
        self.t = self.TRANSLATIONS.get(lang, self.TRANSLATIONS['es'])
        self._primary_color = primary_color

        # Track if this update was previously ignored
        self._is_ignored = (ignored_version == version) if version else False

        self.setFixedWidth(380)
        self.setModal(True)
        self.setWindowTitle(self.t['window_title'].format(version=current_version))
        self.setObjectName("SettingsDialog")
        self._apply_theme_style(parent, theme_id)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # ── Title label ──
        if version:
            title = QLabel(self.t['update_available'].format(version=version))
        else:
            title = QLabel(self.t['up_to_date'].format(version=current_version))
        title.setObjectName("settings_label")
        title.setStyleSheet("font-weight: bold; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setWordWrap(True)
        layout.addWidget(title)

        # ── Body (depends on install_type) ──
        if install_type == 'snap':
            if version:
                body = QLabel(self.t['snap_available'].format(version=version))
            else:
                body = QLabel(self.t['snap_up_to_date'].format(version=current_version))
            body.setObjectName("settings_label")
            body.setAlignment(Qt.AlignmentFlag.AlignCenter)
            body.setWordWrap(True)
            layout.addWidget(body)

        if version and install_type != 'snap':
            self.ignore_cb = QCheckBox(self.t['no_remind'])
            self.ignore_cb.setObjectName("settings_checkbox")
            if self._is_ignored:
                self.ignore_cb.setChecked(True)
            # Save immediately on toggle
            self.ignore_cb.toggled.connect(self._on_ignore_toggled)
            layout.addWidget(self.ignore_cb)

        layout.addStretch()

        # Buttons row
        btn_row = QHBoxLayout()
        credits_btn = QPushButton(self.t['credits'])
        credits_btn.setObjectName("settings_close_button")
        credits_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        credits_btn.clicked.connect(self._open_credits)
        
        if install_type == 'snap':
            btn_row.addStretch()
            btn_row.addWidget(credits_btn)
            btn_row.addStretch()
            layout.addLayout(btn_row)
        else:
            btn_row.addWidget(credits_btn)
            btn_row.addStretch()

            self.update_btn = QPushButton(self.t['update'])
            self.update_btn.setObjectName("settings_save_button")
            self.update_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.update_btn.clicked.connect(self._start_update)
            if not version:
                self.update_btn.setEnabled(False)
            btn_row.addWidget(self.update_btn)
            layout.addLayout(btn_row)

            # Progress bar (hidden initially)
            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setVisible(False)
            layout.addWidget(self.progress_bar)

        self.adjustSize()

    def _apply_theme_style(self, parent, theme_id):
        """Apply theme from themes_manager (like SettingsDialog), with input styling."""
        pc = self._primary_color
        # Use themes_manager to set base colors (background, text)
        if parent and hasattr(parent, 'themes_manager') and theme_id:
            try:
                parent.themes_manager.apply_theme_to_widget(self, theme_id)
            except Exception:
                pass
        # Override specific widget styles for progress bar
        self.setStyleSheet(self.styleSheet() + f"""
            QProgressBar {{
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                color: palette(text);
                background: rgba(128, 128, 128, 30);
            }}
            QProgressBar::chunk {{
                background-color: {pc};
                border-radius: 3px;
            }}
        """)

    def _on_ignore_toggled(self, checked):
        """Save/clear ignored_update immediately when checkbox is toggled."""
        parent_win = self.parent()
        if parent_win and hasattr(parent_win, 'config') and hasattr(parent_win, 'save_config'):
            if checked and self.version:
                parent_win.config['ignored_update'] = self.version
            else:
                parent_win.config.pop('ignored_update', None)
            parent_win.save_config()

    def _open_credits(self):
        QDesktopServices.openUrl(QUrl("https://gessendarien.github.io/petra-clipboard/"))

    def _start_update(self):
        """Begin downloading and installing the update."""
        from updater import UpdateDownloader

        parent_win = self.parent()
        if parent_win:
            parent_win.setEnabled(False)

        if hasattr(self, 'update_btn'):
            self.update_btn.setVisible(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self._downloader = UpdateDownloader(self.version, self.install_type, self)
        self._downloader.progress.connect(self.progress_bar.setValue)
        self._downloader.finished.connect(self._on_update_finished)
        self._downloader.start()

    def _on_update_finished(self, success, message):
        parent_win = self.parent()
        if success:
            # Clear ignored_update since we just updated
            if parent_win and hasattr(parent_win, 'config') and hasattr(parent_win, 'save_config'):
                parent_win.config.pop('ignored_update', None)
                parent_win.save_config()
            self._restart_application()
        else:
            if message == "cancelled":
                if parent_win:
                    parent_win.setEnabled(True)
                self.progress_bar.setVisible(False)
                if hasattr(self, 'update_btn'):
                    self.update_btn.setVisible(True)
            else:
                QMessageBox.warning(self, self.t['error_title'], message)
                if parent_win:
                    parent_win.setEnabled(True)
                self.progress_bar.setVisible(False)
                if hasattr(self, 'update_btn'):
                    self.update_btn.setVisible(True)

    def _restart_application(self):
        """Restart the application after a successful update."""
        import sys
        import os
        try:
            # If running inside an AppImage, os.environ["APPIMAGE"] holds the path to the AppImage itself.
            appimage_path = os.environ.get("APPIMAGE")
            if appimage_path:
                os.execv(appimage_path, [appimage_path] + sys.argv[1:])
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception as e:
            print(f"Failed to restart: {e}")
            from PyQt6.QtWidgets import QApplication
            QApplication.quit()

    def closeEvent(self, event):
        super().closeEvent(event)


class ImagePreviewDialog(QDialog):
    """Lightweight dialog for image previews.
    
    Features:
    - Max size: 400x400px
    - Closes with: Escape, click outside, click on image
    - Frameless for clean appearance
    - Lightweight on resources
    - Colors adapted to current theme
    """
    
    MAX_SIZE = 400
    
    def __init__(self, image, parent=None):
        """
        Args:
            image: QImage or QPixmap of the image to display
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        
        from PyQt6.QtGui import QPixmap
        
        # Get current theme colors from parent
        bg_color = '#1A1A1A'  # fallback (header color)
        try:
            if parent and hasattr(parent, 'themes_manager'):
                colors = parent.themes_manager.get_theme_colors()
                bg_color = colors.get('header', bg_color)
        except Exception:
            pass
        
        # Configure frameless window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Popup  # Popup closes on focus loss
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Convert QImage to QPixmap if necessary
        if hasattr(image, 'toImage'):  # Is QPixmap
            self.pixmap = image
        else:  # Is QImage
            self.pixmap = QPixmap.fromImage(image)
        
        # Scale image maintaining aspect ratio
        scaled = self.pixmap.scaled(
            self.MAX_SIZE, self.MAX_SIZE,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Container with background and rounded border (using theme colors)
        container = QWidget()
        container.setObjectName("image_preview_container")
        container.setStyleSheet(f"""
            QWidget#image_preview_container {{
                background-color: {bg_color};
                border: none;
                border-radius: 12px;
            }}
        """)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(8, 8, 8, 8)
        
        # Label to display image
        self.image_label = QLabel()
        self.image_label.setPixmap(scaled)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.image_label.setStyleSheet("background-color: transparent;")
        
        container_layout.addWidget(self.image_label)
        layout.addWidget(container)
        
        # Adjust size to content
        self.adjustSize()
        
        # Center on screen or near cursor
        self._center_on_cursor()
    
    def _center_on_cursor(self):
        """Position dialog near mouse cursor."""
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QCursor
        
        cursor_pos = QCursor.pos()
        screen = QApplication.primaryScreen().geometry()
        
        # Calculate position centered on cursor
        x = cursor_pos.x() - self.width() // 2
        y = cursor_pos.y() - self.height() // 2
        
        # Ensure it doesn't go off screen edges
        if x < 10:
            x = 10
        elif x + self.width() > screen.width() - 10:
            x = screen.width() - self.width() - 10
            
        if y < 10:
            y = 10
        elif y + self.height() > screen.height() - 10:
            y = screen.height() - self.height() - 10
        
        self.move(x, y)
    
    def mousePressEvent(self, event):
        """Close dialog when clicking anywhere."""
        self.close()
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        """Close with Escape."""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)