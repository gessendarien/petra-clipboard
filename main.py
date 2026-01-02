#!/usr/bin/env python3
import sys
import argparse
import faulthandler
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize
from window import PetraClipboard


def main():
    # Enable faulthandler so Python prints stack traces on crashes (SIGSEGV)
    try:
        faulthandler.enable()
    except Exception:
        pass
    
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description='Petra Clipboard Manager')
    parser.add_argument('--hidden', action='store_true', 
                        help='Iniciar con la ventana oculta (para autostart)')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Establecer el icono de la aplicación ANTES de configurar el nombre
    # Esto es importante para que algunos entornos de escritorio lo detecten correctamente
    icon = QIcon()
    icon_base = Path(__file__).parent / "icons"
    flatpak_base = Path("/app/share/icons/hicolor")
    
    # Añadir múltiples tamaños al ícono para mejor compatibilidad
    icon_sizes = [16, 32, 48, 64, 128, 256]
    icon_loaded = False
    
    # Primero intentar cargar desde la carpeta local de desarrollo
    for size in icon_sizes:
        png_path = icon_base / f"petra-{size}.png"
        if png_path.exists():
            icon.addFile(str(png_path), QSize(size, size))
            icon_loaded = True
    
    # Si no se encontraron los tamaños específicos, usar el PNG o SVG general
    if not icon_loaded:
        if (icon_base / "petra.png").exists():
            icon.addFile(str(icon_base / "petra.png"))
            icon_loaded = True
        elif (icon_base / "petra.svg").exists():
            icon.addFile(str(icon_base / "petra.svg"))
            icon_loaded = True
    
    # Si no se encontró localmente, buscar en rutas de Flatpak
    if not icon_loaded:
        flatpak_paths = [
            flatpak_base / "scalable/apps/io.github.petra.svg",
            flatpak_base / "512x512/apps/io.github.petra.png",
        ]
        for fpath in flatpak_paths:
            if fpath.exists():
                icon.addFile(str(fpath))
                icon_loaded = True
                break
    
    # Establecer el ícono en la aplicación
    if icon_loaded:
        app.setWindowIcon(icon)
    
    # Establecer el nombre de la aplicación y el archivo desktop para asociación de iconos
    # Esto es crítico para que el sistema de escritorio muestre el ícono correcto
    app.setApplicationName("Petra")
    app.setDesktopFileName("io.github.petra")
    
    # Manejar Ctrl+C correctamente
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    window = PetraClipboard()
    
    # Solo mostrar la ventana si no se inició con --hidden
    if not args.hidden:
        window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()