class ThemesManager:
    def __init__(self):
        self.available_themes = {
            'dark': {
                'name': 'Dark',
                'colors': {
                    # Colores principales
                    'primary': '#BB86FC',
                    'secondary': '#03DAC6', 
                    'accent': '#CF6679',
                    
                    # Fondos principales
                    'background': '#121212',
                    'header': '#1E1E1E',
                    'window_main': '#0A0A0A',  # Fondo más oscuro para ventana
                    
                    # Textos
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#AAAAAA',
                    'card_text': '#E0E0E0',  # Texto ligeramente diferente para cards
                    
                    # Botones
                    'button_bg': '#2C2C2C',
                    'button_hover': '#3C3C3C',
                    'header_buttons': '#252525',  # Botones del header diferentes
                    
                    # Items del clipboard
                    'clip_bg': '#1A1A1A',
                    'clip_hover': '#2A2A2A', 
                    'clip_click': '#BB86FC',
                    'copied_card': '#1E1E1E',  # Card cuando está seleccionada
                    
                    # Búsqueda
                    'search_input_focus': '#BB86FC',
                    
                    # Filtros
                    'filters_background': '#181818',  # Fondo específico para área de filtros
                    'filter_selected': '#BB86FC',
                    'filter_hover': '#D0A8FF',
                    'filter_click': '#9A67EA',
                    
                    # Elementos varios
                    'element_hover': '#343434',  # Hover genérico
                    'element_click': '#8A5CEA',  # Click genérico
                    'emoji_table': '#2D2D2D',  # Fondo de tabla de emojis
                    
                    # Botones de acción
                    'delete_button': '#CF6679',
                    'pin_button': '#03DAC6',
                    'delete_hover': '#FF5252',
                    'pin_hover': '#04C5B0',
                    
                    # Enlaces
                    'link_color': '#BB86FC',
                    
                    # Configuración
                    'settings_window': '#151515',
                    'settings_text': '#F0F0F0',
                    'input_border': '#BB86FC',
                    'save_button': '#BB86FC',
                    'close_button': '#03DAC6',
                    
                    # Scrollbars
                    'scrollbar_bg': '#252525',
                    'scrollbar_handle': '#3A3A3A',
                    
                    # Iconos
                    'icon_bg': '#2A2A2A',
                    
                    # Estados especiales
                    'header_buttons_click': '#9A67EA',
                    'clear_button_border': '#CF6679'
                }
            },
            'light': {
                'name': 'Light Soft',
                'colors': {
                    # Colores principales
                    'primary': '#3778B0',
                    'secondary': '#4A9C8E',
                    'accent': '#D87A8A',
                    
                    # Fondos principales
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'window_main': '#FFFFFF',  # Fondo blanco para ventana
                    
                    # Textos
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',  # Texto más oscuro para cards
                    
                    # Botones
                    'button_bg': '#FFFFFF',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',  # Botones del header diferentes
                    
                    # Items del clipboard
                    'clip_bg': '#FFFFFF',
                    'clip_hover': '#F7FAFC',
                    'clip_click': '#1D90C1',
                    'copied_card': '#F0F4F8',  # Card cuando está seleccionada
                    
                    # Búsqueda
                    'search_input_focus': '#53A3C6',
                    
                    # Filtros
                    'filters_background': '#F0F4F8',  # Fondo específico para área de filtros
                    'filter_selected': '#3E60A0',
                    'filter_hover': '#365080',
                    'filter_click': '#4B5E81',
                    
                    # Elementos varios
                    'element_hover': '#E2E8F0',  # Hover genérico
                    'element_click': '#359DBA',  # Click genérico
                    'emoji_table': '#EDF2F7',  # Fondo de tabla de emojis
                    
                    # Botones de acción
                    'delete_button': '#D87A8A',
                    'pin_button': '#4A9C8E',
                    'delete_hover': '#E53E3E',
                    'pin_hover': '#3A8C7E',
                    
                    # Enlaces
                    'link_color': '#7E6BC9',
                    
                    # Configuración
                    'settings_window': '#D20808',
                    'settings_text': '#2D3748',
                    'input_border': '#7E6BC9',
                    'save_button': '#4D9AD8',
                    'close_button': '#4A9C8E',
                    
                    # Scrollbars
                    'scrollbar_bg': '#072041',
                    'scrollbar_handle': '#3D90E9',
                    
                    # Iconos
                    'icon_bg': '#F7FAFC',
                    
                    # Estados especiales
                    'header_buttons_click': '#4D9AD8',
                    'clear_button_border': '#CD3A52'
                }
            }
        }
        
        self.current_theme = 'dark'
    
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
        return self.available_themes.get(self.current_theme, self.available_themes['dark'])
    
    def get_theme_colors(self, theme_id=None):
        """Obtener colores de un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
        return self.available_themes.get(theme_id, self.available_themes['dark'])['colors']
    
    def get_theme_stylesheet(self, theme_id=None):
        """Generar hoja de estilos CSS para un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
            
        theme = self.available_themes.get(theme_id, self.available_themes['dark'])
        colors = theme['colors']
        
        return f"""
            /* ========== VENTANA PRINCIPAL ========== */
            QMainWindow {{
                background-color: {colors['window_main']};
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
                background-color: {colors['header_buttons']};
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
            
            /* Botón borrar todo */
            QPushButton#clear_button {{
                background-color: {colors['header_buttons']};
                border-radius: 19px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            QPushButton#clear_button:hover {{
                background-color: {colors['button_hover']};
                border: none;
            }}
            
            QPushButton#close_button {{
                background-color: {colors['header_buttons']};
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
                background-color: {colors['header_buttons']};
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
                background-color: {colors['filters_background']};
                color: {colors['text_primary']};
                border: none;
                border-radius: 10px;
                padding: 12px 14px;
                font-size: 14px;
            }}
            QLineEdit#search_bar:focus {{
                background-color: {colors['filters_background']};
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
                background: {colors['element_hover']};
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
            
            ClipItem:pressed {{
                background-color: {colors['clip_click']};
            }}
            
            /* Card cuando está copiada/seleccionada */
            ClipItem[copied="true"] {{
                background-color: {colors['copied_card']};
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

            QPushButton#pin_action_button:pressed {{ 
                background-color: {colors['element_click']}; 
            }}
            
            QPushButton#delete_action_button:pressed {{
                background-color: {colors['element_click']};
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
                background-color: {colors['element_click']};
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
                background-color: {colors['icon_bg']};
                color: {colors['text_primary']};
                border: 1px solid {colors['input_border']};
                border-radius: 4px;
                padding: 4px 8px;
            }}
            
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {colors['input_border']};
            }}
            
            /* ========== BOTÓN CLEAR CON BORDE ANIMADO ========== */
            ProgressButton {{
                background-color: {colors['header_buttons']};
                border-radius: 19px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            
            ProgressButton:hover {{
                background-color: {colors['button_hover']};
            }}
        """
    
    def apply_theme_to_widget(self, widget, theme_id=None):
        """Aplicar tema a un widget específico"""
        stylesheet = self.get_theme_stylesheet(theme_id)
        widget.setStyleSheet(stylesheet)