import sys
from PyQt6.QtWidgets import QApplication
sys.path.append('.')
from main import PetraClipboard

app = QApplication(sys.argv)
try:
    window = PetraClipboard()
    print("Window created")
    window.set_filter("emoji")
    print("Emoji filter set successfully")
except Exception as e:
    import traceback
    traceback.print_exc()
