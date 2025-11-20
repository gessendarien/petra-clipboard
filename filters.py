from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QPushButton, 
                             QLabel, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
import subprocess

# ELIMINAR esta línea:
# from themes import apply_theme

from input_simulator import InputSimulator

class FilterManager:
    def __init__(self):
        self.current_filter = "all"
        self.filter_buttons = {}
        self.input_simulator = InputSimulator()

    def set_filter(self, filter_id):
        self.current_filter = filter_id
        self.update_filter_styles()
        if filter_id == "emoji":
            self.show_emoji_picker()
            return
        self.refresh_ui()

    def update_filter_styles(self):
        # Los estilos ahora se manejan desde window.py con el sistema de temas
        # Este método se mantiene para la lógica, pero los estilos se aplican en window.py
        pass

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
            # Caras y emociones
            "😀", "😃", "😄", "😁", "😆", "😅", "🤣", "😂", "🙂", "🙃",
            "😉", "😊", "😇", "😍", "🤩", "😘", "😗", "😚", "😙", "😋",
            "😛", "😜", "🤪", "😝", "🤑", "🤗", "🤭", "🤫", "🤔", "🤐",
            "🤨", "😐", "😑", "😶", "😏", "😒", "🙄", "😬", "🤥", "😌",
            "😔", "😪", "🤤", "😴", "😷", "🤒", "🤕", "🤢", "🤮", "🤧",
            "😵", "🤯", "🤠", "😎", "🤓", "🧐", "😕", "😟", "🙁", "☹️",
            "😮", "😯", "😲", "😳", "😦", "😧", "😨", "😰", "😥", "😢",
            "😭", "😱", "😖", "😣", "😞", "😓", "😩", "😫", "😤", "😡",
            # Gestos y manos
            "👋", "🤚", "🖐️", "✋", "🖖", "👌", "🤏", "✌️", "🤞", "🤟",
            "🤘", "🤙", "👈", "👉", "👆", "🖕", "👇", "☝️", "👍", "👎",
            "✊", "👊", "🤛", "🤜", "👏", "🙌", "👐", "🤲", "🤝", "🙏",
            "✍️", "💅", "🤳", "💪", "🦾", "🦿", "🦵", "🦶", "👂", "🦻",
            # Corazones y símbolos
            "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔",
            "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝", "💟", "☮️",
            "✝️", "☪️", "🕉️", "☸️", "✡️", "🔯", "🕎", "☯️", "☦️", "🛐",
            "⛎", "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐",
            # Objetos tecnológicos
            "📱", "📲", "💻", "⌨️", "🖥️", "🖨️", "🖱️", "🖲️", "🕹️", "💽",
            "💾", "💿", "📀", "📼", "📷", "📸", "📹", "🎥", "📽️", "🎞️",
            # Símbolos útiles
            "✅", "✔️", "☑️", "❌", "❎", "✖️", "➕", "➖", "➗", "✳️",
            "✴️", "❇️", "‼️", "⁉️", "❓", "❔", "❕", "❗", "⭐", "🌟",
            "💫", "💥", "💢", "💯", "🔥", "⚡", "🌈", "☀️", "⭕", "🚫",
        ]
        
        row, col = 0, 0
        for emoji in emojis:
            btn = QPushButton(emoji)
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # ELIMINAR: apply_theme(btn, 'emoji_button')
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2C1229;
                    border: none;
                    border-radius: 8px;
                    font-size: 28px;
                }
                QPushButton:hover {
                    background-color: #4C2B4C;
                }
                QPushButton:pressed {
                    background-color: #ff6b35;
                }
            """)
            btn.clicked.connect(lambda checked, e=emoji: self.insert_emoji(e))
            grid.addWidget(btn, row, col)
            col += 1
            if col > 7:
                col = 0
                row += 1
        
        emoji_layout.addWidget(grid_widget)
        self.content_layout.insertWidget(0, emoji_container)