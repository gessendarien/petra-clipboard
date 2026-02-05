from input_simulator import InputSimulator

# FilterManager: Handles current filter state
# Note: show_emoji_picker() is implemented in window.py with full functionality
# Emojis are centralized in emoji_keywords.py


class FilterManager:
    def __init__(self):
        self.current_filter = "all"
        self.filter_buttons = {}
        self.input_simulator = InputSimulator()

    def set_filter(self, filter_id):
        """Change current filter. Overridden in window.py."""
        self.current_filter = filter_id
        self.update_filter_styles()
        if filter_id == "emoji":
            self.show_emoji_picker()
            return
        self.refresh_ui()

    def update_filter_styles(self):
        """Update button styles. Implemented in window.py."""
        pass

    def filter_items(self):
        """Filter items. Overridden in window.py."""
        self.refresh_ui()

    def show_emoji_picker(self):
        """Show emoji picker. Fully implemented in window.py."""
        pass