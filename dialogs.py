from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QCheckBox, QPushButton, QWidget, QComboBox, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QDesktopServices
from PyQt6.QtCore import QUrl
from pathlib import Path
import os
import sys

from widgets import ShortcutEdit
from themes_manager import ThemesManager


def get_autostart_path():
    """Obtener la ruta del archivo .desktop en autostart"""
    return Path.home() / ".config" / "autostart" / "petra.desktop"


def is_autostart_enabled():
    """Verificar si el autostart está habilitado"""
    return get_autostart_path().exists()


def enable_autostart():
    """Crear el archivo .desktop para autostart"""
    autostart_dir = Path.home() / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    
    # Obtener la ruta del ejecutable
    if getattr(sys, 'frozen', False):
        # Si es un ejecutable compilado
        exec_path = sys.executable
    else:
        # Si se ejecuta como script de Python
        main_script = Path(__file__).parent / "main.py"
        exec_path = f"python3 {main_script}"
    
    desktop_content = f"""[Desktop Entry]
Type=Application
Name=Petra Clipboard
Comment=Clipboard manager with emoji support
Exec={exec_path} --hidden
Icon=accessories-clipboard
Terminal=false
Categories=Utility;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""
    
    desktop_file = get_autostart_path()
    with open(desktop_file, 'w') as f:
        f.write(desktop_content)
    
    # Hacer el archivo ejecutable
    os.chmod(desktop_file, 0o755)


def disable_autostart():
    """Eliminar el archivo .desktop de autostart"""
    desktop_file = get_autostart_path()
    if desktop_file.exists():
        desktop_file.unlink()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.themes_manager = ThemesManager()
        self.setWindowTitle("Configuración")
        self.setFixedSize(400, 420)  # Aumentado para incluir nueva opción
        self.setModal(True)

        self.apply_dark_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Title removed per user request
        title = QLabel("")
        title.setObjectName("settings_title")
        layout.addWidget(title)

        # Language selector
        lang_row = QWidget()
        lhl = QHBoxLayout(lang_row)
        lhl.setContentsMargins(0, 0, 0, 0)
        lhl.setSpacing(8)
        
        self.lang_label = QLabel("")
        self.lang_label.setObjectName("settings_label")
        lhl.addWidget(self.lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.lang_combo.setMinimumWidth(160)
        self.lang_combo.addItem("Español", 'es')
        self.lang_combo.addItem("English", 'en')
        lhl.addWidget(self.lang_combo)
        lhl.addStretch()
        layout.addWidget(lang_row)

        # Theme selector (NUEVO)
        theme_row = QWidget()
        thl = QHBoxLayout(theme_row)
        thl.setContentsMargins(0, 0, 0, 0)
        thl.setSpacing(8)
        
        self.theme_label = QLabel("Tema:")
        self.theme_label.setObjectName("settings_label")
        thl.addWidget(self.theme_label)
        
        self.theme_combo = QComboBox()
        self.theme_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.theme_combo.setMinimumWidth(160)
        
        # Agregar temas disponibles
        themes = self.themes_manager.get_theme_names()
        for theme_id, theme_name in themes:
            self.theme_combo.addItem(theme_name, theme_id)
            
        thl.addWidget(self.theme_combo)
        thl.addStretch()
        layout.addWidget(theme_row)

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

        # Open position selector
        open_pos_row = QWidget()
        ophl = QHBoxLayout(open_pos_row)
        ophl.setContentsMargins(0, 0, 0, 0)
        ophl.setSpacing(8)
        
        self.open_pos_label = QLabel("Abrir desde:")
        self.open_pos_label.setObjectName("settings_label")
        ophl.addWidget(self.open_pos_label)
        
        self.open_pos_combo = QComboBox()
        self.open_pos_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.open_pos_combo.setMinimumWidth(160)
        self.open_pos_combo.addItem("Posición del mouse", 'mouse')
        self.open_pos_combo.addItem("Centro de pantalla", 'center')
        self.open_pos_combo.addItem("Izquierda de pantalla", 'left')
        self.open_pos_combo.addItem("Derecha de pantalla", 'right')
        ophl.addWidget(self.open_pos_combo)
        ophl.addStretch()
        layout.addWidget(open_pos_row)

        # Shortcut input
        sc_row = QWidget()
        scl = QHBoxLayout(sc_row)
        scl.setContentsMargins(0, 0, 0, 0)
        scl.setSpacing(8)
        
        self.shortcut_label = QLabel("Shortcut (ej. Alt + v):")
        self.shortcut_label.setObjectName("settings_label")
        scl.addWidget(self.shortcut_label)
        
        self.shortcut_edit = ShortcutEdit()
        self.shortcut_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.shortcut_edit.setMinimumWidth(140)
        scl.addWidget(self.shortcut_edit)
        layout.addWidget(sc_row)

        # Buttons
        btn_row = QWidget()
        brl = QHBoxLayout(btn_row)
        brl.setContentsMargins(0, 0, 0, 0)
        
        # GitHub icon button (left side)
        self.github_btn = QPushButton()
        self.github_btn.setFixedSize(36, 36)
        self.github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.github_btn.setToolTip("GitHub")
        self.github_btn.setStyleSheet("QPushButton { border: none; background: transparent; }")
        self.github_btn.clicked.connect(self.open_github)
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

        # Max images spinbox (added last before buttons)
        h = QWidget()
        hl = QHBoxLayout(h)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(8)
        
        self.max_images_label = QLabel("Máx. imágenes en caché:")
        self.max_images_label.setObjectName("settings_label")
        hl.addWidget(self.max_images_label)
        
        self.max_images_sb = QSpinBox()
        self.max_images_sb.setRange(1, 100)
        hl.addWidget(self.max_images_sb)

        layout.addWidget(h)
        layout.addStretch()
        layout.addWidget(btn_row)

        self.initialize_values()
        self.setup_translations()
        self.apply_translations(self.lang_combo.currentData())
        self.lang_combo.currentIndexChanged.connect(lambda i: self.apply_translations(self.lang_combo.itemData(i)))
        
        # Update GitHub icon based on current applied theme
        self.update_github_icon()
        
        # Aplicar tema al diálogo
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
        
        icon_path = Path(__file__).parent / "icons" / icon_folder / "code.png"
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
                
                lang = getattr(parent, 'language', 'en')
                idx = self.lang_combo.findData(lang)
                if idx >= 0:
                    self.lang_combo.setCurrentIndex(idx)
                    
                # Nuevo: cargar tema
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
                
                # Verificar si autostart está habilitado
                self.autostart_cb.setChecked(is_autostart_enabled())
                
                sc = getattr(parent, 'shortcut', 'Control + Shift + v')
                if sc:
                    self.shortcut_edit.setText(str(sc))
        except Exception:
            pass

    def setup_translations(self):
        self.translations = {
            'es': {
                'title': 'Configuración',
                'max_images': 'Máx. imágenes en caché:',
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
                'shortcut': "Atajo (ej. Control+Shift+v):"
            },
            'en': {
                'title': 'Settings',
                'max_images': 'Max images in cache:',
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
                'shortcut': "Shortcut (e.g. Control+Shift+v):"
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
                parent.language = self.lang_combo.currentData()
                
                # Nuevo: guardar tema
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
                
                # Manejar autostart
                if self.autostart_cb.isChecked():
                    enable_autostart()
                else:
                    disable_autostart()
                        
                parent.shortcut = str(self.shortcut_edit.text()).strip() if hasattr(self, 'shortcut_edit') else getattr(parent, 'shortcut', 'Super + v')
                
                parent.config['language'] = parent.language
                parent.config['max_images'] = parent.max_images
                parent.config['shortcut'] = getattr(parent, 'shortcut', 'Super + v')
                parent.config['theme'] = parent.theme  # Nuevo
                
                parent.save_config()
                
                # Aplicar el nuevo tema
                if hasattr(parent, 'apply_theme'):
                    parent.apply_theme()
                
                if hasattr(parent, 'register_global_hotkey'):
                    parent.register_global_hotkey(parent.shortcut)
        except Exception as e:
            print(f"DEBUG: Error saving settings: {e}")
        self.accept()

    def apply_translations(self, code):
        t = self.translations.get(code, self.translations.get('es'))
        try:
            self.setWindowTitle(t.get('title', 'Configuración'))
            
            if hasattr(self, 'max_images_label'):
                self.max_images_label.setText(t.get('max_images', self.max_images_label.text()))
                
            if hasattr(self, 'show_clear_cb'):
                self.show_clear_cb.setText(t.get('show_clear', self.show_clear_cb.text()))
                
            if hasattr(self, 'shortcut_label'):
                self.shortcut_label.setText(t.get('shortcut', self.shortcut_label.text()))
                
            if hasattr(self, 'lang_label'):
                self.lang_label.setText(t.get('language', self.lang_label.text()))
                
            # Nuevo: traducir etiqueta de tema
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
        from PyQt6.QtWidgets import QApplication, QMessageBox
        
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
        
        msg = QMessageBox(self)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.setIcon(QMessageBox.Icon.Question)
        yes_btn = msg.addButton(yes_text, QMessageBox.ButtonRole.YesRole)
        no_btn = msg.addButton(no_text, QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(no_btn)
        msg.exec()
        
        if msg.clickedButton() == yes_btn:
            self.reject()
            if self.parent() and hasattr(self.parent(), 'quit_application'):
                self.parent().quit_application()
            else:
                QApplication.quit()
    
    def open_github(self):
        """Open the GitHub repository in the default browser"""
        QDesktopServices.openUrl(QUrl("https://github.com/gessendarien/petra-clipboard"))