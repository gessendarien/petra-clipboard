#!/usr/bin/env python3
import sys
import argparse
import faulthandler
from PyQt6.QtWidgets import QApplication
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