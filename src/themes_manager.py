import json
from pathlib import Path

class ThemesManager:
    def __init__(self):
        self.available_themes = {}
        
        # Load themes from JSON files in src/themes/
        themes_dir = Path(__file__).parent / 'themes'
        if themes_dir.exists() and themes_dir.is_dir():
            for theme_file in themes_dir.glob('*.json'):
                try:
                    with open(theme_file, 'r', encoding='utf-8') as f:
                        theme_data = json.load(f)
                        theme_id = theme_file.stem
                        self.available_themes[theme_id] = theme_data
                except Exception:
                    # Ignore invalid files silently
                    pass
        
        # Default theme logic
        if 'zorin' in self.available_themes:
            self.current_theme = 'zorin'
        elif self.available_themes:
            self.current_theme = next(iter(self.available_themes))
        else:
            self.current_theme = 'dark' # True fallback

    def get_theme_names(self):
        """Obtener lista de nombres de temas para el ComboBox en un orden específico"""
        # Definir el orden de prioridad
        priority = {
            'dark': 0,
            'light': 10,
            'ubuntu': 20,
            'ubuntu_aubergine': 21,
            'mint': 22,
            'elementary': 23,
            'zorin': 24,
            'dracula': 25,
            'solarized': 26,
            'sunset': 27
        }

        def sort_key(item):
            theme_id, theme_data = item
            
            # Caso especial para variantes
            if theme_id == 'dark':
                return (priority['dark'], "")
            if theme_id.startswith('dark_'):
                return (priority['dark'], theme_id)
            
            if theme_id == 'light':
                return (priority['light'], "")
            if theme_id.startswith('light_'):
                return (priority['light'], theme_id)
            
            # Otros temas con prioridad fija
            if theme_id in priority:
                return (priority[theme_id], theme_id)
            
            # Fallback para cualquier otro tema
            return (100, theme_id)

        sorted_themes = sorted(self.available_themes.items(), key=sort_key)
        return [(theme_id, theme_data['name']) for theme_id, theme_data in sorted_themes]
    
    def set_theme(self, theme_id):
        """Establecer tema actual"""
        if theme_id in self.available_themes:
            self.current_theme = theme_id
            return True
        return False
    
    def get_current_theme(self):
        """Obtener tema actual"""
        return self.available_themes.get(self.current_theme, self.available_themes['dark'])
    
    def get_theme_colors(self, theme_id=None):
        """Obtener colores de un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
        return self.available_themes.get(theme_id, self.available_themes['dark'])['colors']
    
    def get_icons_folder(self, theme_id=None):
        """Obtener la carpeta de iconos del tema actual"""
        if theme_id is None:
            theme_id = self.current_theme
        return self.available_themes.get(theme_id, self.available_themes['dark']).get('icons_folder', 'dark')
    
    
    def get_theme_stylesheet(self, theme_id=None):
        """Generar hoja de estilos CSS para un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
            
        theme = self.available_themes.get(theme_id, self.available_themes['dark'])
        colors = theme['colors']
    
        def _to_rgba(color_str, alpha=0.18):
            try:
                s = color_str.strip()
                if s.startswith('rgba'):
                    # replace existing alpha with our alpha
                    inside = s[s.find('(')+1:s.find(')')]
                    parts = [p.strip() for p in inside.split(',')]
                    if len(parts) >= 3:
                        r = int(parts[0]); g = int(parts[1]); b = int(parts[2])
                        return f'rgba({r}, {g}, {b}, {max(0, min(1, alpha))})'
                if s.startswith('#') and len(s) in (7, 4):
                    # handle #RRGGBB or #RGB
                    if len(s) == 7:
                        r = int(s[1:3], 16); g = int(s[3:5], 16); b = int(s[5:7], 16)
                    else:
                        r = int(s[1]*2, 16); g = int(s[2]*2, 16); b = int(s[3]*2, 16)
                    return f'rgba({r}, {g}, {b}, {max(0, min(1, alpha))})'
            except Exception:
                pass
            # fallback
            return f'rgba(0, 0, 0, {max(0, min(1, alpha))})'

        copied_fill = _to_rgba(colors.get('clip_hover_bg', '#00D6D6'), alpha=0.18)

        return f"""
            QMainWindow {{
                background-color: {colors['background']} !important;
                border-radius: 12px;
            }}
            
            QWidget {{
                background-color: {colors['background']} !important;
                border-radius: 12px;
            }}
            
            /* ========== HEADER ========== */
            QWidget#header {{
                background-color: {colors['header']} !important;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            
            /* Header buttons */
            QPushButton#settings_button {{
                background-color: {colors['header_buttons']} !important;
                border-radius: 8px;
                color: {colors['text_primary']} !important;
                font-size: 18px;
                border: none;
            }}
            QPushButton#settings_button:hover {{
                background-color: {colors['button_hover']} !important;
            }}
            QPushButton#settings_button:pressed {{
                background-color: {colors['header_buttons_click']} !important;
            }}
            
            /* Clear all button */
            QPushButton#clear_button {{
                background-color: {colors['header_buttons']} !important;
                border-radius: 19px;
                color: {colors['text_primary']} !important;
                font-size: 18px;
                border: none;
            }}
            QPushButton#clear_button:hover {{
                background-color: {colors['button_hover']} !important;
                border: none;
            }}
            
            QPushButton#close_button {{
                background-color: {colors['header_buttons']} !important;
                border-radius: 8px;
                color: {colors['text_primary']} !important;
                font-size: 20px;
                font-weight: bold;
                border: none;
            }}
            QPushButton#close_button:hover {{
                background-color: {colors['button_hover']} !important;
            }}
            QPushButton#close_button:pressed {{
                background-color: {colors['header_buttons_click']} !important;
            }}
            
            QPushButton#pin_button {{
                background-color: {colors['header_buttons']} !important;
                border-radius: 19px;
                color: {colors['text_primary']} !important;
                font-size: 18px;
                border: none;
            }}
            QPushButton#pin_button:hover {{
                background-color: {colors['button_hover']} !important;
            }}
            QPushButton#pin_button:pressed {{
                background-color: {colors['header_buttons_click']} !important;
            }}
            
            /* ========== SEARCH BAR ========== */
            QLineEdit#search_bar {{
                background-color: {colors['filters_background']} !important;
                color: {colors['text_primary']} !important;
                border: none;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 14px;
            }}
            QLineEdit#search_bar:focus {{
                background-color: {colors['filters_background']} !important;
                border: 2px solid {colors['search_input_focus']} !important;
            }}
            
            /* ========== FILTERS ========== */
            QPushButton#filter_button_active {{
                background-color: {colors['filter_selected']} !important;
                border-radius: 22px;
                border: none;
                color: {colors['text_primary']} !important;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton#filter_button_active:hover {{
                background-color: {colors['filter_hover']} !important;
            }}
            
            QPushButton#filter_button_inactive {{
                background-color: {colors['filters_background']} !important;
                border: 2px solid {colors['button_bg']} !important;
                border-radius: 22px;
                color: {colors['text_primary']} !important;
                font-size: 18px;
            }}
            QPushButton#filter_button_inactive:hover {{
                background-color: {colors['filter_hover']} !important;
            }}
            QPushButton#filter_button_inactive:pressed {{
                background-color: {colors['filter_click']} !important;
            }}
            
            /* ========== SCROLL AREA ========== */
            QScrollArea#main_scroll_area {{
                border: none;
                background-color: {colors['background']};
            }}
            
            QScrollBar:horizontal {{
                height: 0px;
                background: transparent;
            }}
            
            QScrollBar:vertical {{
                background: {colors['scrollbar_bg']};
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            
            QScrollBar::handle:vertical {{
                background: {colors['scrollbar_handle']};
                border-radius: 4px;
                min-height: 30px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {colors['element_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QFrame#clip_item {{
                background-color: {colors['background']} !important;
                border-radius: 10px;
                margin: 0px;
            }}
            
            QFrame#clip_item:hover {{
                /* prefer solid hover color so it's always visible */
                background-color: {colors['clip_hover_bg']} !important;
            }}
            
            QFrame#clip_item:pressed {{
                background-color: {colors['element_click']} !important;
            }}

            /* hover/pressed via dynamic properties (for children-mouse cases) */
            QFrame#clip_item[hover="true"] {{
                background-color: {colors['clip_hover_bg']} !important;
            }}

            QFrame#clip_item[pressed="true"] {{
                background-color: {colors['element_click']} !important;
            }}
            
            /* Card when copied/selected */

            /* copied state: use existing clip_hover_bg for fill so it remains visible
               and keep a strong primary border. The old copied_* keys were unused. */
            QFrame#clip_item[copied="true"] {{
                /* copied-only: subtle translucent fill so it's visually distinct from hover */
                background-color: {copied_fill} !important;
            }}

            QFrame#clip_item[copied="true"]:hover {{
                background-color: {colors['clip_hover_bg']} !important;
            }}

            QFrame#clip_item[copied="true"][hover="true"] {{
                /* when copied and hovered (mouse over children) */
                background-color: {colors['clip_hover_bg']} !important;
            }}

            QFrame#clip_item[copied="true"]:pressed {{
                /* use element_click for pressed look when a copied card is pressed */
                background-color: {colors['element_click']} !important;
            }}

            QFrame#clip_item[copied="true"][pressed="true"] {{
                background-color: {colors['element_click']} !important;
            }}

            /* Item text */
            QLabel#clip_text_normal {{
                color: {colors['card_text']} !important;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }}
            QLabel#clip_text_link {{
                color: {colors['link_color']} !important;
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }}
                QLabel#clip_text_link a,
                QLabel#clip_text_link a:visited,
                QLabel#clip_text_link a:hover,
                QLabel#clip_text_link a:link,
                QLabel#clip_text_link * {{
                    color: {colors['link_color']} !important;
                    background-color: transparent;
                }}
                QLabel#clip_text_link a {{
                    text-decoration: none;
                    background-color: transparent;
                }}
                QLabel#clip_text_link a:hover {{
                    text-decoration: underline;
                    background-color: transparent;
                }}
            QLabel#clip_text_link a:visited {{
                color: {colors['link_color']} !important;
                background-color: transparent;
            }}
            
            QLabel#clip_text_link a:hover {{
                color: {colors['link_color']} !important;
                text-decoration: underline;
                background-color: transparent;
            }}
            
            QLabel#clip_text_link a:link {{
                color: {colors['link_color']} !important;
                background-color: transparent;
            }}
            
            QLabel#clip_time {{
                color: {colors['text_secondary']} !important;
                font-size: 11px;
                background-color: transparent;
            }}
            
            /* ========== ITEM ACTION BUTTONS ========== */
            QPushButton#pin_action_button {{
                background-color: transparent !important;
                border-radius: 6px;
                color: {colors['text_primary']} !important;
                font-size: 16px;
                border: none;
            }}
            
            QPushButton#pin_action_button:hover {{
                background-color: {colors['element_hover']} !important;
            }}
            
            QPushButton#delete_action_button {{
                background-color: transparent !important;
                border-radius: 6px;
                color: {colors['text_primary']} !important;
                font-size: 18px;
                border: none;
            }}
            
            QPushButton#delete_action_button:hover {{
                background-color: {colors['delete_hover']} !important;
            }}

            QPushButton#pin_action_button:pressed {{ 
                background-color: {colors['element_click']} !important; 
            }}
            
            QPushButton#delete_action_button:pressed {{
                background-color: {colors['element_click']} !important;
            }}
            
            /* ========== EMOJIS ========== */
            QPushButton#emoji_button {{
                background-color: {colors['emoji_table']} !important;
                border: none;
                border-radius: 8px;
                font-size: 28px;
            }}
            
            QPushButton#emoji_button:hover {{
                background-color: {colors['element_hover']} !important;
            }}
            
            QPushButton#emoji_button:pressed {{
                background-color: {colors['element_click']} !important;
            }}
            
            /* ========== CONFIGURATION - COMPLETELY FIXED ========== */
            QDialog#SettingsDialog {{
                background-color: {colors['settings_window']} !important;
                border-radius: 12px;
            }}
            
            QLabel#settings_title {{
                color: {colors['settings_text']} !important;
                font-size: 16px;
                font-weight: 600;
            }}
            
            QLabel#settings_label {{
                color: {colors['settings_text']} !important;
                font-size: 14px;
            }}
            
            QCheckBox#settings_checkbox {{
                color: {colors['settings_text']} !important;
                font-size: 14px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_save_button {{
                background-color: #1E1E1E !important;
                color: #FFFFFF !important;
                border: 1px solid #FFFFFF !important;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_save_button:hover {{
                background-color: #333333 !important;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_save_button:pressed {{
                background-color: #333333 !important;
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_save_button:disabled {{
                background-color: #1E1E1E !important;
                color: #888888 !important;
                border: 1px solid #888888 !important;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_close_button {{
                background-color: #1E1E1E !important;
                color: #FFFFFF !important;
                border: 1px solid #FFFFFF !important;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 80px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_close_button:hover {{
                background-color: #333333 !important;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_close_button:pressed {{
                background-color: #333333 !important;
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_quit_button {{
                background-color: #1E1E1E !important;
                color: #FFFFFF !important;
                border: 1px solid #FFFFFF !important;
                padding: 8px 16px;
                border-radius: 4px;
                font-size: 14px;
                min-width: 80px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_quit_button:hover {{
                background-color: #333333 !important;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_quit_button:pressed {{
                background-color: #333333 !important;
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            
            /* ========== FORM ELEMENTS ========== */
            QLineEdit, QSpinBox, QComboBox {{
                background-color: {colors['icon_bg']} !important;
                color: {colors['text_primary']} !important;
                border: 1px solid {colors['input_border']} !important;
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {colors['input_border']} !important;
            }}
            
            /* ========== CLEAR BUTTON WITH ANIMATED BORDER ========== */
            ProgressButton {{
                background-color: {colors['header_buttons']} !important;
                border-radius: 19px;
                color: {colors['text_primary']} !important;
                font-size: 18px;
                border: none;
            }}
            
            ProgressButton:hover {{
                background-color: {colors['button_hover']} !important;
            }}
        """
    
    def apply_theme_to_widget(self, widget, theme_id=None):
        """Aplicar tema a un widget específico"""
        stylesheet = self.get_theme_stylesheet(theme_id)
        widget.setStyleSheet(stylesheet)