from input_simulator import InputSimulator

# FilterManager: Maneja el estado del filtro actual
# Nota: show_emoji_picker() se implementa en window.py con funcionalidad completa
# Los emojis están centralizados en emoji_keywords.py

class FilterManager:
    def __init__(self):
        self.current_filter = "all"
        self.filter_buttons = {}
        self.input_simulator = InputSimulator()

    def set_filter(self, filter_id):
        """Cambia el filtro actual. Sobreescrito en window.py."""
        self.current_filter = filter_id
        self.update_filter_styles()
        if filter_id == "emoji":
            self.show_emoji_picker()
            return
        self.refresh_ui()

    def update_filter_styles(self):
        """Actualiza estilos de botones. Implementado en window.py."""
        pass

    def filter_items(self):
        """Filtra items. Sobreescrito en window.py."""
        self.refresh_ui()

    def show_emoji_picker(self):
        """Muestra el selector de emojis. Implementado completamente en window.py."""
        pass