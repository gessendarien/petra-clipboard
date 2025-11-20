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
                    'button_bg': '#4C2B4C',
                    'button_hover': '#5C3B5C',
                    'clip_bg': '#3C1B3C',
                    'clip_hover': '#4A273A'
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
                    'clip_hover': '#3A3A3A'
                }
            },
            'zorin': {
                'name': 'Zorin',
                'colors': {
                    'primary': '#0E79C9',
                    'secondary': '#0A5A9D',
                    'background': '#2D2D2D',
                    'header': '#1D1D1D',
                    'accent': '#0E79C9',
                    'text_primary': '#ffffff',
                    'text_secondary': '#b0b0b0',
                    'button_bg': '#3D3D3D',
                    'button_hover': '#4D4D4D',
                    'clip_bg': '#2D2D2D',
                    'clip_hover': '#3D3D3D'
                }
            },
            'elementary': {
                'name': 'Elementary',
                'colors': {
                    'primary': '#D8B609',
                    'secondary': '#EAB710',
                    'background': '#EAE6DD',
                    'header': '#DDD1C1',
                    'accent': '#EDB312',
                    'text_primary': '#282828',
                    'text_secondary': '#aaaaaa',
                    'button_bg': '#A3EDDE',
                    'button_hover': '#D89029',
                    'clip_bg': '#DC1E87',
                    'clip_hover': '#FA0000'
                }
            },
            'dark': {
                'name': 'Dark',
                'colors': {
                    'primary': '#BB86FC',
                    'secondary': '#03DAC6',
                    'background': '#121212',
                    'header': '#1E1E1E',
                    'accent': '#BB86FC',
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#AAAAAA',
                    'button_bg': '#2D2D2D',
                    'button_hover': '#3D3D3D',
                    'clip_bg': '#1E1E1E',
                    'clip_hover': '#2D2D2D'
                }
            },
            'light': {
                'name': 'Light',
                'colors': {
                    'primary': '#C8C7C3',
                    'secondary': '#DEDDDA',
                    'background': '#DBD4C5',
                    'header': '#E8E8E8',
                    'accent': '#D0D0D0',
                    'text_primary': '#333333',
                    'text_secondary': '#666666',
                    'button_bg': '#E0E0E0',
                    'button_hover': '#D0D0D0',
                    'clip_bg': '#F8F8F8',
                    'clip_hover': '#E8E8E8'
                }
            }
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
    
    def get_theme_stylesheet(self, theme_id=None):
        """Generar hoja de estilos CSS para un tema específico"""
        if theme_id is None:
            theme_id = self.current_theme
            
        theme = self.available_themes.get(theme_id, self.available_themes['ubuntu'])
        colors = theme['colors']
        
        return f"""
            /* Tema: {theme['name']} */
            
            /* Ventana principal */
            QWidget {{
                background-color: {colors['background']};
                border-radius: 12px;
            }}
            
            /* Header */
            QWidget#header {{
                background-color: {colors['header']};
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }}
            
            /* Botones de configuración */
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
                background-color: {colors['primary']};
            }}
            
            /* Botón borrar todo */
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
            
            /* Botón cerrar */
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
                background-color: {colors['primary']};
            }}
            
            /* Botón fijar ventana */
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
                background-color: {colors['primary']};
            }}
            
            /* Barra de búsqueda */
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
                border: 1px solid {colors['primary']};
            }}
            
            /* Área de scroll */
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 6px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {colors['button_bg']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {colors['button_hover']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            /* Items del clipboard */
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
                color: {colors['text_primary']};
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }}
            
            QLabel#clip_text_link {{
                color: {colors['text_primary']};
                font-size: 14px;
                font-weight: 500;
                background-color: transparent;
            }}
            
            /* Tiempo de items */
            QLabel#clip_time {{
                color: {colors['text_secondary']};
                font-size: 11px;
                background-color: transparent;
            }}
            
            /* Botones de acción en items */
            QPushButton#pin_action_button {{
                background-color: transparent;
                border-radius: 6px;
                color: {colors['text_primary']};
                font-size: 16px;
                border: none;
            }}
            QPushButton#pin_action_button:hover {{
                background-color: {colors['accent']};
            }}
            
            QPushButton#delete_action_button {{
                background-color: rgba(76, 43, 76, 0.8);
                border-radius: 6px;
                color: {colors['text_primary']};
                font-size: 18px;
                border: none;
            }}
            QPushButton#delete_action_button:hover {{
                background-color: #ff4444;
            }}
            
            /* Botones de filtro activos */
            QPushButton#filter_button_active {{
                background-color: {colors['accent']};
                border-radius: 22px;
                border: none;
                color: {colors['text_primary']};
                font-size: 18px;
            }}
            QPushButton#filter_button_active:hover {{
                background-color: {colors['primary']};
            }}
            
            /* Botones de filtro inactivos */
            QPushButton#filter_button_inactive {{
                background-color: transparent;
                border: 2px solid {colors['button_bg']};
                border-radius: 22px;
                color: {colors['text_primary']};
                font-size: 18px;
            }}
            QPushButton#filter_button_inactive:hover {{
                background-color: {colors['button_bg']};
            }}
            QPushButton#filter_button_inactive:pressed {{
                background-color: {colors['button_hover']};
            }}
            
            /* Botones de emoji */
            QPushButton#emoji_button {{
                background-color: {colors['header']};
                border: none;
                border-radius: 8px;
                font-size: 28px;
            }}
            QPushButton#emoji_button:hover {{
                background-color: {colors['button_bg']};
            }}
            QPushButton#emoji_button:pressed {{
                background-color: {colors['accent']};
            }}
            
            /* Diálogo de configuración */
            QLabel#settings_title {{
                color: {colors['text_primary']};
                font-size: 16px;
                font-weight: 600;
            }}
            
            QLabel#settings_label {{
                color: {colors['text_primary']};
            }}
            
            QCheckBox#settings_checkbox {{
                color: {colors['text_primary']};
            }}
            
            QPushButton#settings_save_button {{
                background-color: {colors['accent']};
                color: {colors['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }}
            QPushButton#settings_save_button:hover {{
                background-color: {colors['primary']};
            }}
            
            QPushButton#settings_close_button {{
                background-color: {colors['button_bg']};
                color: {colors['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }}
            QPushButton#settings_close_button:hover {{
                background-color: {colors['button_hover']};
            }}
        """
    
    def apply_theme_to_widget(self, widget, theme_id=None):
        """Aplicar tema a un widget específico"""
        stylesheet = self.get_theme_stylesheet(theme_id)
        widget.setStyleSheet(stylesheet)