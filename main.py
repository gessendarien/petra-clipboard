#!/usr/bin/env python3
import sys
import faulthandler
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QFontDatabase
from window import PetraClipboard


def setup_emoji_font(app):
    """
    Configura una fuente de emoji colorida consistente para Linux.
    Funciona tanto en Wayland como en X11.
    """
    # Lista de fuentes de emoji coloridas comunes en Linux (en orden de preferencia)
    emoji_fonts = [
        "Noto Color Emoji",      # Más común en distros modernas (Ubuntu, Fedora, Arch)
        "Twemoji",               # Twitter emoji, muy estético
        "Twitter Color Emoji",   # Nombre alternativo de Twemoji
        "Apple Color Emoji",     # Si está instalada
        "Segoe UI Emoji",        # Para compatibilidad
        "EmojiOne Color",        # Alternativa popular
        "JoyPixels",             # Antes EmojiOne
        "OpenMoji Color",        # Open source
    ]
    
    available_fonts = QFontDatabase.families()
    
    # Buscar la primera fuente de emoji disponible
    emoji_font_name = None
    for font_name in emoji_fonts:
        if font_name in available_fonts:
            emoji_font_name = font_name
            break
    
    if emoji_font_name:
        # Crear una fuente que use la fuente de emoji como fallback
        # Esto permite que el texto normal use la fuente del sistema
        # pero los emojis usen la fuente colorida
        default_font = app.font()
        # Establecer la familia de fuentes con fallback a emoji
        font_families = [default_font.family(), emoji_font_name]
        default_font.setFamilies(font_families)
        app.setFont(default_font)
        print(f"Fuente de emoji configurada: {emoji_font_name}")
    else:
        print("Advertencia: No se encontró una fuente de emoji colorida instalada.")
        print("Instala 'noto-fonts-emoji' o 'fonts-noto-color-emoji' para mejor experiencia.")


def main():
    # Enable faulthandler so Python prints stack traces on crashes (SIGSEGV)
    try:
        faulthandler.enable()
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Configurar fuente de emoji colorida
    setup_emoji_font(app)
    
    # Manejar Ctrl+C correctamente
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    window = PetraClipboard()
    window.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()