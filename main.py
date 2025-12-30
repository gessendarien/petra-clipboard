#!/usr/bin/env python3
import sys
import faulthandler
from PyQt6.QtWidgets import QApplication
from window import PetraClipboard


def main():
    # Enable faulthandler so Python prints stack traces on crashes (SIGSEGV)
    try:
        faulthandler.enable()
    except Exception:
        pass
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Manejar Ctrl+C correctamente
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    window = PetraClipboard()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()