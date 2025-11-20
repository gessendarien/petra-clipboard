class ThemesManager:
    def __init__(self):
        self.available_themes = {
            'ubuntu': {
                'name': 'Ubuntu',
                'colors': {
                    'primary': '#E95420',
                    'secondary': '#77216F',
                    'background': '#3C1B3C',
                    'header': '#2C1229',
                    'accent': '#ff6b35',
                    'text_primary': '#ffffff',
                    'text_secondary': '#8b7a9b',
                    
                    # Botones principales
                    'button_bg': '#4C2B4C',
                    'button_hover': '#5C3B5C',
                    
                    # Items del clipboard
                    'clip_bg': '#3C1B3C',
                    'clip_hover': '#4A273A',
                    
                    # Header y ventana
                    'window_main': '#3C1B3C',
                    'header_buttons': '#2C1229',
                    
                    # Búsqueda
                    'search_input_focus': '#ff6b35',
                    
                    # Filtros
                    'filters_background': '#3C1B3C',  # ROSA INTENSO PARA PRUEBA
                    'filter_selected': '#E95420',
                    'filter_hover': '#5C3B5C',
                    'filter_click': '#77216F',
                    
                    # Tarjetas
                    'copied_card': '#3C1B3C',
                    'card_text': '#ffffff',
                    
                    # Elementos varios
                    'element_hover': '#4A273A',
                    'element_click': '#77216F',
                    'emoji_table': '#4A273A',
                    
                    # Botones de acción
                    'delete_button': '#E95420',
                    'pin_button': '#77216F',
                    'delete_hover': '#ff4444',
                    'pin_hover': '#5C3B5C',
                    
                    # Enlaces
                    'link_color': '#E95420',
                    
                    # Configuración
                    'settings_window': '#3C1B3C',
                    'settings_text': '#ffffff',
                    'input_border': '#E95420',
                    'save_button': '#E95420',
                    'close_button': '#77216F',
                    
                    # Scrollbars
                    'scrollbar_bg': '#4C2B4C',
                    'scrollbar_handle': '#5C3B5C',
                    
                    # Iconos
                    'icon_bg': '#4C2B4C',
                    
                    # Estados de botones header
                    'header_buttons_click': '#77216F'
                }
            },
            'mint': {
                'name': 'Mint',
                'colors': {
                    'primary': '#87CF3E',
                    'secondary': '#2D6A45',
                    'background': '#2A2A2A',
                    'header': '#1A1A1A',
                    'accent': '#87CF3E',
                    'text_primary': '#ffffff',
                    'text_secondary': '#aaaaaa',
                    'button_bg': '#3A3A3A',
                    'button_hover': '#4A4A4A',
                    'clip_bg': '#2A2A2A',
                    'clip_hover': '#3A3A3A',
                    'window_main': '#2A2A2A',
                    'header_buttons': '#1A1A1A',
                    'search_input_focus': '#87CF3E',
                    'filters_background': '#2A2A2A',
                    'filter_selected': '#87CF3E',
                    'filter_hover': '#A4D65E',
                    'filter_click': '#2D6A45',
                    'copied_card': '#2A2A2A',
                    'card_text': '#ffffff',
                    'element_hover': '#3A3A3A',
                    'element_click': '#2D6A45',
                    'emoji_table': '#3A3A3A',
                    'delete_button': '#87CF3E',
                    'pin_button': '#2D6A45',
                    'delete_hover': '#ff4444',
                    'pin_hover': '#4A4A4A',
                    'link_color': '#87CF3E',
                    'settings_window': '#2A2A2A',
                    'settings_text': '#ffffff',
                    'input_border': '#87CF3E',
                    'save_button': '#87CF3E',
                    'close_button': '#2D6A45',
                    'scrollbar_bg': '#3A3A3A',
                    'scrollbar_handle': '#4A4A4A',
                    'icon_bg': '#3A3A3A',
                    'header_buttons_click': '#2D6A45'
                }
            },
            # ... (otros temas con el mismo patrón)
        }
        
        self.current_theme = 'ubuntu'
    
    def get_theme_names(self):
        """Obtener lista de nombres de temas para el ComboBox"""
        return [(theme_id, theme_data['name']) for theme_id, theme_data in self.available_themes.items()]
    
    def set_theme(self, theme_id):
        """Establecer tema actual"""
        if theme_id in self.available_themes:
            self.current_theme = theme_id
            return True
        return False
    
    def get_current_theme(self):
        """Obtener tema actual"""
        return self.available_themes.get(self.current_theme, self.available_themes['ubuntu'])
    
    def get_theme_colors(self, theme_id=None):
        """Obtener colores de un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
        return self.available_themes.get(theme_id, self.available_themes['ubuntu'])['colors']
    
    def get_theme_stylesheet(self, theme_id=None):
        """Generar hoja de estilos CSS para un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
            
        theme = self.available_themes.get(theme_id, self.available_themes['ubuntu'])
        colors = theme['colors']
        
        return f"""
            /* ========== VENTANA PRINCIPAL ========== */
            QMainWindow {{
                background-color: {colors['background']};
                border-radius: 12px;
            }}
            
            QWidget {{
                background-color: {colors['background']};
                border-radius: 12px;
            }}
            
            /* ========== HEADER ========== */
            QWidget#header {{
                background-color: {colors['header']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            
            /* Botones del header */
            QPushButton#settings_button {{
                background-color: {colors['button_bg']};
                border-radius: 8px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            QPushButton#settings_button:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton#settings_button:pressed {{
                background-color: {colors['header_buttons_click']};
            }}
            
            QPushButton#clear_button {{
                background-color: {colors['button_bg']};
                border-radius: 19px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            QPushButton#clear_button:hover {{
                background-color: {colors['button_hover']};
            }}
            
            QPushButton#close_button {{
                background-color: {colors['button_bg']};
                border-radius: 8px;
                color: {colors['text_primary']};
                font-size: 20px;
                font-weight: bold;
                border: none;
            }}
            QPushButton#close_button:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton#close_button:pressed {{
                background-color: {colors['header_buttons_click']};
            }}
            
            QPushButton#pin_button {{
                background-color: {colors['button_bg']};
                border-radius: 19px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            QPushButton#pin_button:hover {{
                background-color: {colors['button_hover']};
            }}
            QPushButton#pin_button:pressed {{
                background-color: {colors['header_buttons_click']};
            }}
            
            /* ========== BARRA DE BÚSQUEDA ========== */
            QLineEdit#search_bar {{
                background-color: {colors['header']};
                color: {colors['text_primary']};
                border: none;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 14px;
            }}
            QLineEdit#search_bar:focus {{
                background-color: {colors['header']};
                border: 2px solid {colors['search_input_focus']};
            }}
            
            /* ========== FILTROS ========== */
            QPushButton#filter_button_active {{
                background-color: {colors['filter_selected']};
                border-radius: 22px;
                border: none;
                color: {colors['text_primary']};
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton#filter_button_active:hover {{
                background-color: {colors['filter_hover']};
            }}
            
            QPushButton#filter_button_inactive {{
                background-color: {colors['filters_background']};
                border: 2px solid {colors['button_bg']};
                border-radius: 22px;
                color: {colors['text_primary']};
                font-size: 18px;
            }}
            QPushButton#filter_button_inactive:hover {{
                background-color: {colors['filter_hover']};
            }}
            QPushButton#filter_button_inactive:pressed {{
                background-color: {colors['filter_click']};
            }}
            
            /* ========== ÁREA DE SCROLL ========== */
            QScrollArea {{
                border: none;
                background-color: transparent;
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
                background: {colors['button_hover']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* ========== ITEMS DEL CLIPBOARD ========== */
            ClipItem {{
                background-color: {colors['clip_bg']};
                border-radius: 10px;
                margin: 0px;
            }}
            
            ClipItem:hover {{
                background-color: {colors['clip_hover']};
            }}
            
            /* Texto de items */
            QLabel#clip_text_normal {{
                color: {colors['card_text']};
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }}
            
            QLabel#clip_text_link {{
                color: {colors['link_color']};
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }}
            
            QLabel#clip_time {{
                color: {colors['text_secondary']};
                font-size: 11px;
                background-color: transparent;
            }}
            
            /* ========== BOTONES DE ACCIÓN EN ITEMS ========== */
            QPushButton#pin_action_button {{
                background-color: {colors['pin_button']};
                border-radius: 6px;
                color: {colors['text_primary']};
                font-size: 16px;
                border: none;
            }}
            
            QPushButton#pin_action_button:hover {{
                background-color: {colors['pin_hover']};
            }}
            
            QPushButton#delete_action_button {{
                background-color: {colors['delete_button']};
                border-radius: 6px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            
            QPushButton#delete_action_button:hover {{
                background-color: {colors['delete_hover']};
            }}
            
            /* ========== EMOJIS ========== */
            QPushButton#emoji_button {{
                background-color: {colors['emoji_table']};
                border: none;
                border-radius: 8px;
                font-size: 28px;
            }}
            
            QPushButton#emoji_button:hover {{
                background-color: {colors['element_hover']};
            }}
            
            QPushButton#emoji_button:pressed {{
                background-color: {colors['accent']};
            }}
            
            /* ========== CONFIGURACIÓN ========== */
            QDialog {{
                background-color: {colors['settings_window']};
                border-radius: 12px;
            }}
            
            QLabel#settings_title {{
                color: {colors['settings_text']};
                font-size: 16px;
                font-weight: 600;
            }}
            
            QLabel#settings_label {{
                color: {colors['settings_text']};
                font-size: 14px;
            }}
            
            QCheckBox#settings_checkbox {{
                color: {colors['settings_text']};
                font-size: 14px;
            }}
            
            QPushButton#settings_save_button {{
                background-color: {colors['save_button']};
                color: {colors['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            
            QPushButton#settings_save_button:hover {{
                background-color: {colors['primary']};
            }}
            
            QPushButton#settings_close_button {{
                background-color: {colors['close_button']};
                color: {colors['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }}
            
            QPushButton#settings_close_button:hover {{
                background-color: {colors['button_hover']};
            }}
            
            /* ========== ELEMENTOS DE FORMULARIO ========== */
            QLineEdit, QSpinBox, QComboBox {{
                background-color: {colors['header']};
                color: {colors['text_primary']};
                border: 1px solid {colors['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {colors['input_border']};
            }}
        """
    
    def apply_theme_to_widget(self, widget, theme_id=None):
        """Aplicar tema a un widget específico"""
        stylesheet = self.get_theme_stylesheet(theme_id)
        widget.setStyleSheet(stylesheet)