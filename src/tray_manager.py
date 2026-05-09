"""
Tray manager module — extracted from window.py.

Contains TrayManagerMixin with:
- setup_tray_icon()          — creates the system tray icon and context menu
- on_tray_icon_activated()   — handles tray icon click (toggle window)

MRO NOTE:
  No method name collisions with ClipboardManager, FilterManager, or ConfigManager.
"""

from pathlib import Path

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtCore import Qt


class TrayManagerMixin:
    """Mixin that adds system-tray functionality to PetraClipboard.

    No MRO collisions with existing parent classes.
    """

    def setup_tray_icon(self):
        """Configura el icono de la bandeja del sistema."""
        self.tray_icon = QSystemTrayIcon(self)
        
        icons_root = Path(__file__).parent.parent / 'icons'
        
        # IMPORTANTE PARA FLATPAK/WAYLAND:
        # Crear QIcon desde QPixmap fuerza a Qt a enviar los píxeles (RGBA)
        # por D-Bus (SNI). Si usamos QIcon(str(path)), Qt envía la ruta
        # absoluta que es interna del sandbox de Flatpak ("/app/...") y el
        # host no encuentra la imagen.
        #
        # Load multiple sizes for HiDPI panels — the panel will pick
        # the closest size and avoid blurry scaling.
        from PyQt6.QtCore import QSize
        icon = QIcon()
        sizes_loaded = 0
        for size in [128, 64, 48, 32, 24]:
            candidate = icons_root / f'petra_systray_{size}.png'
            if candidate.exists():
                pixmap = QPixmap(str(candidate))
                if not pixmap.isNull():
                    icon.addPixmap(pixmap)
                    sizes_loaded += 1

        # Fallback: single systray image
        if sizes_loaded == 0:
            for fallback_name in ['petra_systray.png', 'petra.png']:
                fallback = icons_root / fallback_name
                if fallback.exists():
                    pixmap = QPixmap(str(fallback))
                    if not pixmap.isNull():
                        icon = QIcon(pixmap)
                        break
        
        if icon.isNull():
            icons_folder = getattr(self.themes_manager, 'get_icons_folder', lambda: 'dark')()
            fallback = icons_root / icons_folder / 'all.png'
            if fallback.exists():
                icon = QIcon(QPixmap(str(fallback)))
            else:
                icon = self.style().standardIcon(Qt.Style.SP_ComputerIcon)
                
        self.tray_icon.setIcon(icon)
        
        tray_menu = QMenu()
        
        show_action = QAction("Mostrar", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Salir", self)
        quit_action.triggered.connect(self.quit_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """Maneja la activación del icono de la bandeja."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
