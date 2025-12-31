class ThemesManager:
    def __init__(self):
        self.available_themes = {
            # ==================== DARK (Default - Grayscale) ====================
            'dark': {
                'name': 'Dark',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#606060',
                    'background': '#121212',
                    'header': '#1A1A1A',
                    'text_primary': '#E0E0E0',
                    'text_secondary': '#888888',
                    'card_text': '#D0D0D0',
                    'clip_hover_bg': '#3A3A3A',
                    'element_click': '#4A4A4A',
                    'link_color': '#A0A0A0',
                    'search_input_focus': '#606060',
                    'button_bg': '#2A2A2A',
                    'button_hover': '#3A3A3A',
                    'header_buttons': '#222222',
                    'filters_background': '#1A1A1A',
                    'filter_selected': '#505050',
                    'filter_hover': '#606060',
                    'filter_click': '#404040',
                    'element_hover': '#303030',
                    'emoji_table': '#252525',
                    'delete_button': '#8B4049',
                    'pin_button': '#4A6B5D',
                    'delete_hover': '#A04050',
                    'pin_hover': '#5A7B6D',
                    'settings_window': '#1A1A1A',
                    'settings_text': '#E0E0E0',
                    'input_border': '#505050',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#404040',
                    'icon_bg': '#2A2A2A',
                    'header_buttons_click': '#505050',
                    'clear_button_border': '#606060',
                    'emoji_selection_border': '#707070',
                    'emoji_selection_bg': '#2A2A2A'
                }
            },
            
            # ==================== DARK PURPLE ====================
            'dark_purple': {
                'name': 'Dark Purple',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#BB86FC',
                    'background': '#121212',
                    'header': '#1A1A1A',
                    'text_primary': '#E0E0E0',
                    'text_secondary': '#888888',
                    'card_text': '#D0D0D0',
                    'clip_hover_bg': '#8559BA',
                    'element_click': '#74559A',
                    'link_color': '#BB86FC',
                    'search_input_focus': '#BB86FC',
                    'button_bg': '#2A2A2A',
                    'button_hover': '#3A3A3A',
                    'header_buttons': '#222222',
                    'filters_background': '#1A1A1A',
                    'filter_selected': '#BB86FC',
                    'filter_hover': '#D0A8FF',
                    'filter_click': '#9A67EA',
                    'element_hover': '#303030',
                    'emoji_table': '#252525',
                    'delete_button': '#CF6679',
                    'pin_button': '#03DAC6',
                    'delete_hover': '#FF5252',
                    'pin_hover': '#04C5B0',
                    'settings_window': '#1A1A1A',
                    'settings_text': '#E0E0E0',
                    'input_border': '#BB86FC',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#404040',
                    'icon_bg': '#2A2A2A',
                    'header_buttons_click': '#9A67EA',
                    'clear_button_border': '#9A67EA',
                    'emoji_selection_border': '#BB86FC',
                    'emoji_selection_bg': '#2A2A2A'
                }
            },
            
            # ==================== DARK BLUE ====================
            'dark_blue': {
                'name': 'Dark Blue',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#64B5F6',
                    'background': '#121212',
                    'header': '#1A1A1A',
                    'text_primary': '#E0E0E0',
                    'text_secondary': '#888888',
                    'card_text': '#D0D0D0',
                    'clip_hover_bg': '#1F4A6E',
                    'element_click': '#2D5A7B',
                    'link_color': '#64B5F6',
                    'search_input_focus': '#64B5F6',
                    'button_bg': '#2A2A2A',
                    'button_hover': '#3A3A3A',
                    'header_buttons': '#222222',
                    'filters_background': '#1A1A1A',
                    'filter_selected': '#1F6FEB',
                    'filter_hover': '#388BFD',
                    'filter_click': '#1A5FC9',
                    'element_hover': '#303030',
                    'emoji_table': '#252525',
                    'delete_button': '#DA3633',
                    'pin_button': '#238636',
                    'delete_hover': '#F85149',
                    'pin_hover': '#2EA043',
                    'settings_window': '#1A1A1A',
                    'settings_text': '#E0E0E0',
                    'input_border': '#64B5F6',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#404040',
                    'icon_bg': '#2A2A2A',
                    'header_buttons_click': '#1F6FEB',
                    'clear_button_border': '#1F6FEB',
                    'emoji_selection_border': '#64B5F6',
                    'emoji_selection_bg': '#2A2A2A'
                }
            },
            
            # ==================== DARK GREEN ====================
            'dark_green': {
                'name': 'Dark Green',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#66BB6A',
                    'background': '#121212',
                    'header': '#1A1A1A',
                    'text_primary': '#E0E0E0',
                    'text_secondary': '#888888',
                    'card_text': '#D0D0D0',
                    'clip_hover_bg': '#2E5930',
                    'element_click': '#3D6B3F',
                    'link_color': '#66BB6A',
                    'search_input_focus': '#66BB6A',
                    'button_bg': '#2A2A2A',
                    'button_hover': '#3A3A3A',
                    'header_buttons': '#222222',
                    'filters_background': '#1A1A1A',
                    'filter_selected': '#43A047',
                    'filter_hover': '#66BB6A',
                    'filter_click': '#388E3C',
                    'element_hover': '#303030',
                    'emoji_table': '#252525',
                    'delete_button': '#C75050',
                    'pin_button': '#4DB6AC',
                    'delete_hover': '#E57373',
                    'pin_hover': '#80CBC4',
                    'settings_window': '#1A1A1A',
                    'settings_text': '#E0E0E0',
                    'input_border': '#66BB6A',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#404040',
                    'icon_bg': '#2A2A2A',
                    'header_buttons_click': '#43A047',
                    'clear_button_border': '#43A047',
                    'emoji_selection_border': '#66BB6A',
                    'emoji_selection_bg': '#2A2A2A'
                }
            },
            
            # ==================== DARK RED ====================
            'dark_red': {
                'name': 'Dark Red',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#EF5350',
                    'background': '#121212',
                    'header': '#1A1A1A',
                    'text_primary': '#E0E0E0',
                    'text_secondary': '#888888',
                    'card_text': '#D0D0D0',
                    'clip_hover_bg': '#5C2828',
                    'element_click': '#7A3535',
                    'link_color': '#EF5350',
                    'search_input_focus': '#EF5350',
                    'button_bg': '#2A2A2A',
                    'button_hover': '#3A3A3A',
                    'header_buttons': '#222222',
                    'filters_background': '#1A1A1A',
                    'filter_selected': '#E53935',
                    'filter_hover': '#EF5350',
                    'filter_click': '#C62828',
                    'element_hover': '#303030',
                    'emoji_table': '#252525',
                    'delete_button': '#FF7043',
                    'pin_button': '#26A69A',
                    'delete_hover': '#FF8A65',
                    'pin_hover': '#4DB6AC',
                    'settings_window': '#1A1A1A',
                    'settings_text': '#E0E0E0',
                    'input_border': '#EF5350',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#404040',
                    'icon_bg': '#2A2A2A',
                    'header_buttons_click': '#E53935',
                    'clear_button_border': '#E53935',
                    'emoji_selection_border': '#EF5350',
                    'emoji_selection_bg': '#2A2A2A'
                }
            },
            
            # ==================== DARK PINK ====================
            'dark_pink': {
                'name': 'Dark Pink',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#E91E63',
                    'background': '#121212',
                    'header': '#1A1A1A',
                    'text_primary': '#E0E0E0',
                    'text_secondary': '#888888',
                    'card_text': '#D0D0D0',
                    'clip_hover_bg': '#5C2845',
                    'element_click': '#7A3558',
                    'link_color': '#E91E63',
                    'search_input_focus': '#E91E63',
                    'button_bg': '#2A2A2A',
                    'button_hover': '#3A3A3A',
                    'header_buttons': '#222222',
                    'filters_background': '#1A1A1A',
                    'filter_selected': '#C2185B',
                    'filter_hover': '#E91E63',
                    'filter_click': '#AD1457',
                    'element_hover': '#303030',
                    'emoji_table': '#252525',
                    'delete_button': '#FF7043',
                    'pin_button': '#26A69A',
                    'delete_hover': '#FF8A65',
                    'pin_hover': '#4DB6AC',
                    'settings_window': '#1A1A1A',
                    'settings_text': '#E0E0E0',
                    'input_border': '#E91E63',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#404040',
                    'icon_bg': '#2A2A2A',
                    'header_buttons_click': '#C2185B',
                    'clear_button_border': '#C2185B',
                    'emoji_selection_border': '#E91E63',
                    'emoji_selection_bg': '#2A2A2A'
                }
            },
            
            # ==================== LIGHT ====================
            'light': {
                'name': 'Light',
                'icons_folder': 'light',
                'colors': {
                    'primary': '#4597DF',
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',
                    'clip_hover_bg': '#00D6D6',
                    'search_input_focus': '#53A3C6',
                    'button_bg': '#CCCCCC',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',
                    'filters_background': '#F0F4F8',
                    'filter_selected': '#4597DF',
                    'filter_hover': '#448ECF',
                    'filter_click': '#4076A6',
                    'element_hover': '#E2E8F0',
                    'element_click': '#A8D8D8',
                    'emoji_table': '#EDF2F7',
                    'delete_button': '#D87A8A',
                    'pin_button': '#4A9C8E',
                    'delete_hover': '#E53E3E',
                    'pin_hover': '#3A8C7E',
                    'link_color': '#7E6BC9',
                    'settings_window': '#FFFFFF',
                    'settings_text': '#2D3748',
                    'input_border': '#7E6BC9',
                    'scrollbar_bg': '#E2E8F0',
                    'scrollbar_handle': '#CBD5E0',
                    'icon_bg': '#F7FAFC',
                    'header_buttons_click': '#4D9AD8',
                    'clear_button_border': '#F35642',
                    'emoji_selection_border': '#2E7D32',
                    'emoji_selection_bg': '#E8F5E9'
                }
            },
            
            # ==================== LIGHT PURPLE ====================
            'light_purple': {
                'name': 'Light Purple',
                'icons_folder': 'light',
                'colors': {
                    'primary': '#9C27B0',
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',
                    'clip_hover_bg': '#CE93D8',
                    'element_click': '#BA68C8',
                    'link_color': '#9C27B0',
                    'search_input_focus': '#9C27B0',
                    'button_bg': '#CCCCCC',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',
                    'filters_background': '#F0F4F8',
                    'filter_selected': '#9C27B0',
                    'filter_hover': '#AB47BC',
                    'filter_click': '#7B1FA2',
                    'element_hover': '#E2E8F0',
                    'emoji_table': '#EDF2F7',
                    'delete_button': '#E57373',
                    'pin_button': '#4DB6AC',
                    'delete_hover': '#EF5350',
                    'pin_hover': '#26A69A',
                    'settings_window': '#FFFFFF',
                    'settings_text': '#2D3748',
                    'input_border': '#9C27B0',
                    'scrollbar_bg': '#E2E8F0',
                    'scrollbar_handle': '#CBD5E0',
                    'icon_bg': '#F7FAFC',
                    'header_buttons_click': '#AB47BC',
                    'clear_button_border': '#E91E63',
                    'emoji_selection_border': '#9C27B0',
                    'emoji_selection_bg': '#E8F5E9'
                }
            },
            
            # ==================== LIGHT BLUE ====================
            'light_blue': {
                'name': 'Light Blue',
                'icons_folder': 'light',
                'colors': {
                    'primary': '#1976D2',
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',
                    'clip_hover_bg': '#90CAF9',
                    'element_click': '#64B5F6',
                    'link_color': '#1976D2',
                    'search_input_focus': '#1976D2',
                    'button_bg': '#CCCCCC',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',
                    'filters_background': '#F0F4F8',
                    'filter_selected': '#1976D2',
                    'filter_hover': '#1E88E5',
                    'filter_click': '#1565C0',
                    'element_hover': '#E2E8F0',
                    'emoji_table': '#EDF2F7',
                    'delete_button': '#E57373',
                    'pin_button': '#81C784',
                    'delete_hover': '#EF5350',
                    'pin_hover': '#66BB6A',
                    'settings_window': '#FFFFFF',
                    'settings_text': '#2D3748',
                    'input_border': '#1976D2',
                    'scrollbar_bg': '#E2E8F0',
                    'scrollbar_handle': '#CBD5E0',
                    'icon_bg': '#F7FAFC',
                    'header_buttons_click': '#1E88E5',
                    'clear_button_border': '#F44336',
                    'emoji_selection_border': '#1976D2',
                    'emoji_selection_bg': '#E8F5E9'
                }
            },
            
            # ==================== LIGHT GREEN ====================
            'light_green': {
                'name': 'Light Green',
                'icons_folder': 'light',
                'colors': {
                    'primary': '#388E3C',
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',
                    'clip_hover_bg': '#A5D6A7',
                    'element_click': '#81C784',
                    'link_color': '#388E3C',
                    'search_input_focus': '#388E3C',
                    'button_bg': '#CCCCCC',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',
                    'filters_background': '#F0F4F8',
                    'filter_selected': '#388E3C',
                    'filter_hover': '#43A047',
                    'filter_click': '#2E7D32',
                    'element_hover': '#E2E8F0',
                    'emoji_table': '#EDF2F7',
                    'delete_button': '#E57373',
                    'pin_button': '#4DB6AC',
                    'delete_hover': '#EF5350',
                    'pin_hover': '#26A69A',
                    'settings_window': '#FFFFFF',
                    'settings_text': '#2D3748',
                    'input_border': '#388E3C',
                    'scrollbar_bg': '#E2E8F0',
                    'scrollbar_handle': '#CBD5E0',
                    'icon_bg': '#F7FAFC',
                    'header_buttons_click': '#43A047',
                    'clear_button_border': '#F44336',
                    'emoji_selection_border': '#388E3C',
                    'emoji_selection_bg': '#E8F5E9'
                }
            },
            
            # ==================== LIGHT RED ====================
            'light_red': {
                'name': 'Light Red',
                'icons_folder': 'light',
                'colors': {
                    'primary': '#D32F2F',
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',
                    'clip_hover_bg': '#EF9A9A',
                    'element_click': '#E57373',
                    'link_color': '#D32F2F',
                    'search_input_focus': '#D32F2F',
                    'button_bg': '#CCCCCC',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',
                    'filters_background': '#F0F4F8',
                    'filter_selected': '#D32F2F',
                    'filter_hover': '#E53935',
                    'filter_click': '#C62828',
                    'element_hover': '#E2E8F0',
                    'emoji_table': '#EDF2F7',
                    'delete_button': '#FF7043',
                    'pin_button': '#66BB6A',
                    'delete_hover': '#FF5722',
                    'pin_hover': '#4CAF50',
                    'settings_window': '#FFFFFF',
                    'settings_text': '#2D3748',
                    'input_border': '#D32F2F',
                    'scrollbar_bg': '#E2E8F0',
                    'scrollbar_handle': '#CBD5E0',
                    'icon_bg': '#F7FAFC',
                    'header_buttons_click': '#E53935',
                    'clear_button_border': '#FF5722',
                    'emoji_selection_border': '#D32F2F',
                    'emoji_selection_bg': '#E8F5E9'
                }
            },
            
            # ==================== LIGHT PINK ====================
            'light_pink': {
                'name': 'Light Pink',
                'icons_folder': 'light',
                'colors': {
                    'primary': '#E91E63',
                    'background': '#DFE0E1',
                    'header': '#E9ECEF',
                    'text_primary': '#2D3748',
                    'text_secondary': '#718096',
                    'card_text': '#2A2A2A',
                    'clip_hover_bg': '#F48FB1',
                    'element_click': '#F06292',
                    'link_color': '#E91E63',
                    'search_input_focus': '#E91E63',
                    'button_bg': '#CCCCCC',
                    'button_hover': '#EDF2F7',
                    'header_buttons': '#F8FAFC',
                    'filters_background': '#F0F4F8',
                    'filter_selected': '#E91E63',
                    'filter_hover': '#EC407A',
                    'filter_click': '#C2185B',
                    'element_hover': '#E2E8F0',
                    'emoji_table': '#EDF2F7',
                    'delete_button': '#FF7043',
                    'pin_button': '#66BB6A',
                    'delete_hover': '#FF5722',
                    'pin_hover': '#4CAF50',
                    'settings_window': '#FFFFFF',
                    'settings_text': '#2D3748',
                    'input_border': '#E91E63',
                    'scrollbar_bg': '#E2E8F0',
                    'scrollbar_handle': '#CBD5E0',
                    'icon_bg': '#F7FAFC',
                    'header_buttons_click': '#EC407A',
                    'clear_button_border': '#E91E63',
                    'emoji_selection_border': '#E91E63',
                    'emoji_selection_bg': '#E8F5E9'
                }
            },
            
            # ==================== UBUNTU ====================
            'ubuntu': {
                'name': 'Ubuntu',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#E95420',
                    'background': '#1D1D1D',
                    'header': '#2C2C2C',
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#999999',
                    'card_text': '#F0F0F0',
                    'clip_hover_bg': '#E95420',
                    'element_click': '#C34113',
                    'link_color': '#E95420',
                    'search_input_focus': '#E95420',
                    'button_bg': '#333333',
                    'button_hover': '#444444',
                    'header_buttons': '#2C2C2C',
                    'filters_background': '#262626',
                    'filter_selected': '#E95420',
                    'filter_hover': '#F27249',
                    'filter_click': '#C34113',
                    'element_hover': '#3D3D3D',
                    'emoji_table': '#333333',
                    'delete_button': '#C84646',
                    'pin_button': '#3EB34F',
                    'delete_hover': '#E55555',
                    'pin_hover': '#4FC460',
                    'settings_window': '#2C2C2C',
                    'settings_text': '#FFFFFF',
                    'input_border': '#E95420',
                    'scrollbar_bg': '#1D1D1D',
                    'scrollbar_handle': '#555555',
                    'icon_bg': '#333333',
                    'header_buttons_click': '#C34113',
                    'clear_button_border': '#E95420',
                    'emoji_selection_border': '#E95420',
                    'emoji_selection_bg': '#333333'
                }
            },
            
            # ==================== LINUX MINT ====================
            'mint': {
                'name': 'Linux Mint',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#8FA876',
                    'background': '#1E1E1E',
                    'header': '#2B2B2B',
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#9E9E9E',
                    'card_text': '#E0E0E0',
                    'clip_hover_bg': '#5D6B4D',
                    'element_click': '#4A5640',
                    'link_color': '#8FA876',
                    'search_input_focus': '#8FA876',
                    'button_bg': '#303030',
                    'button_hover': '#404040',
                    'header_buttons': '#2B2B2B',
                    'filters_background': '#252525',
                    'filter_selected': '#8FA876',
                    'filter_hover': '#A3B892',
                    'filter_click': '#6B7D5A',
                    'element_hover': '#383838',
                    'emoji_table': '#303030',
                    'delete_button': '#A65D5D',
                    'pin_button': '#5D8A6B',
                    'delete_hover': '#C07070',
                    'pin_hover': '#6FA080',
                    'settings_window': '#2B2B2B',
                    'settings_text': '#FFFFFF',
                    'input_border': '#8FA876',
                    'scrollbar_bg': '#1E1E1E',
                    'scrollbar_handle': '#4A4A4A',
                    'icon_bg': '#303030',
                    'header_buttons_click': '#6B7D5A',
                    'clear_button_border': '#8FA876',
                    'emoji_selection_border': '#8FA876',
                    'emoji_selection_bg': '#2B2B2B'
                }
            },
            
            # ==================== ELEMENTARY ====================
            'elementary': {
                'name': 'Elementary',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#64BAFF',
                    'background': '#1A1A1A',
                    'header': '#333333',
                    'text_primary': '#FAFAFA',
                    'text_secondary': '#ABACAE',
                    'card_text': '#E0E0E0',
                    'clip_hover_bg': '#2A4A5E',
                    'element_click': '#3A5A6E',
                    'link_color': '#64BAFF',
                    'search_input_focus': '#64BAFF',
                    'button_bg': '#3D3D3D',
                    'button_hover': '#4A4A4A',
                    'header_buttons': '#333333',
                    'filters_background': '#2A2A2A',
                    'filter_selected': '#3689E6',
                    'filter_hover': '#64BAFF',
                    'filter_click': '#2A70C5',
                    'element_hover': '#404040',
                    'emoji_table': '#3D3D3D',
                    'delete_button': '#DA4453',
                    'pin_button': '#68B723',
                    'delete_hover': '#ED5565',
                    'pin_hover': '#7EC833',
                    'settings_window': '#333333',
                    'settings_text': '#FAFAFA',
                    'input_border': '#64BAFF',
                    'scrollbar_bg': '#1A1A1A',
                    'scrollbar_handle': '#4A4A4A',
                    'icon_bg': '#3D3D3D',
                    'header_buttons_click': '#3689E6',
                    'clear_button_border': '#64BAFF',
                    'emoji_selection_border': '#64BAFF',
                    'emoji_selection_bg': '#333333'
                }
            },
            
            # ==================== ZORIN ====================
            'zorin': {
                'name': 'Zorin',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#15A6F0',
                    'background': '#1F2025',
                    'header': '#2A2B30',
                    'text_primary': '#FFFFFF',
                    'text_secondary': '#9A9B9E',
                    'card_text': '#E8E8E8',
                    'clip_hover_bg': '#0D5A80',
                    'element_click': '#0E6A95',
                    'link_color': '#15A6F0',
                    'search_input_focus': '#15A6F0',
                    'button_bg': '#35363B',
                    'button_hover': '#454650',
                    'header_buttons': '#2A2B30',
                    'filters_background': '#25262B',
                    'filter_selected': '#15A6F0',
                    'filter_hover': '#3DB8F5',
                    'filter_click': '#108AC5',
                    'element_hover': '#3A3B40',
                    'emoji_table': '#35363B',
                    'delete_button': '#E04B4B',
                    'pin_button': '#4BB24B',
                    'delete_hover': '#F06060',
                    'pin_hover': '#5CC25C',
                    'settings_window': '#2A2B30',
                    'settings_text': '#FFFFFF',
                    'input_border': '#15A6F0',
                    'scrollbar_bg': '#1F2025',
                    'scrollbar_handle': '#55565B',
                    'icon_bg': '#35363B',
                    'header_buttons_click': '#108AC5',
                    'clear_button_border': '#15A6F0',
                    'emoji_selection_border': '#15A6F0',
                    'emoji_selection_bg': '#2A2B30'
                }
            },
            
            # ==================== DRACULA ====================
            'dracula': {
                'name': 'Dracula',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#BD93F9',
                    'background': '#282A36',
                    'header': '#21222C',
                    'text_primary': '#F8F8F2',
                    'text_secondary': '#6272A4',
                    'card_text': '#F8F8F2',
                    'clip_hover_bg': '#44475A',
                    'element_click': '#6272A4',
                    'link_color': '#8BE9FD',
                    'search_input_focus': '#BD93F9',
                    'button_bg': '#44475A',
                    'button_hover': '#565869',
                    'header_buttons': '#21222C',
                    'filters_background': '#21222C',
                    'filter_selected': '#BD93F9',
                    'filter_hover': '#FF79C6',
                    'filter_click': '#9A6DD7',
                    'element_hover': '#44475A',
                    'emoji_table': '#44475A',
                    'delete_button': '#FF5555',
                    'pin_button': '#50FA7B',
                    'delete_hover': '#FF6E6E',
                    'pin_hover': '#69FF94',
                    'settings_window': '#21222C',
                    'settings_text': '#F8F8F2',
                    'input_border': '#BD93F9',
                    'scrollbar_bg': '#282A36',
                    'scrollbar_handle': '#44475A',
                    'icon_bg': '#44475A',
                    'header_buttons_click': '#FF79C6',
                    'clear_button_border': '#FF79C6',
                    'emoji_selection_border': '#50FA7B',
                    'emoji_selection_bg': '#44475A'
                }
            },
            
            # ==================== SOLARIZED DARK ====================
            'solarized': {
                'name': 'Solarized',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#268BD2',
                    'background': '#002B36',
                    'header': '#073642',
                    'text_primary': '#839496',
                    'text_secondary': '#586E75',
                    'card_text': '#93A1A1',
                    'clip_hover_bg': '#073642',
                    'element_click': '#0A4A5C',
                    'link_color': '#2AA198',
                    'search_input_focus': '#268BD2',
                    'button_bg': '#073642',
                    'button_hover': '#0A4A5C',
                    'header_buttons': '#073642',
                    'filters_background': '#073642',
                    'filter_selected': '#268BD2',
                    'filter_hover': '#2AA198',
                    'filter_click': '#1A6B9C',
                    'element_hover': '#094050',
                    'emoji_table': '#073642',
                    'delete_button': '#DC322F',
                    'pin_button': '#859900',
                    'delete_hover': '#EF4444',
                    'pin_hover': '#98B300',
                    'settings_window': '#073642',
                    'settings_text': '#839496',
                    'input_border': '#268BD2',
                    'scrollbar_bg': '#002B36',
                    'scrollbar_handle': '#586E75',
                    'icon_bg': '#073642',
                    'header_buttons_click': '#2AA198',
                    'clear_button_border': '#CB4B16',
                    'emoji_selection_border': '#859900',
                    'emoji_selection_bg': '#073642'
                }
            },
            
            # ==================== SUNSET ====================
            'sunset': {
                'name': 'Sunset',
                'icons_folder': 'dark',
                'colors': {
                    'primary': '#FF6B6B',
                    'background': '#1A1423',
                    'header': '#251B2E',
                    'text_primary': '#FFF0E5',
                    'text_secondary': '#C9A9A9',
                    'card_text': '#FFE4D6',
                    'clip_hover_bg': '#6B3A5C',
                    'element_click': '#8B4A6C',
                    'link_color': '#FFA07A',
                    'search_input_focus': '#FF6B6B',
                    'button_bg': '#2D2235',
                    'button_hover': '#3D3045',
                    'header_buttons': '#251B2E',
                    'filters_background': '#201828',
                    'filter_selected': '#FF6B6B',
                    'filter_hover': '#FF8E72',
                    'filter_click': '#E05555',
                    'element_hover': '#3A2845',
                    'emoji_table': '#2D2235',
                    'delete_button': '#FF5252',
                    'pin_button': '#FFB347',
                    'delete_hover': '#FF7070',
                    'pin_hover': '#FFC56A',
                    'settings_window': '#251B2E',
                    'settings_text': '#FFF0E5',
                    'input_border': '#FF6B6B',
                    'scrollbar_bg': '#1A1423',
                    'scrollbar_handle': '#6B3A5C',
                    'icon_bg': '#2D2235',
                    'header_buttons_click': '#E05555',
                    'clear_button_border': '#FF6B6B',
                    'emoji_selection_border': '#FFB347',
                    'emoji_selection_bg': '#2D2235'
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
            
            /* Botones del header */
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
            
            /* Botón borrar todo */
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
            
            /* ========== BARRA DE BÚSQUEDA ========== */
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
            
            /* ========== FILTROS ========== */
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
            
            /* ========== ÁREA DE SCROLL ========== */
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
            
            /* Card cuando está copiada/seleccionada */

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

            /* Texto de items */
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
            
            /* ========== BOTONES DE ACCIÓN EN ITEMS ========== */
            QPushButton#pin_action_button {{
                background-color: {colors['pin_button']} !important;
                border-radius: 6px;
                color: {colors['text_primary']} !important;
                font-size: 16px;
                border: none;
            }}
            
            QPushButton#pin_action_button:hover {{
                background-color: {colors['pin_hover']} !important;
            }}
            
            QPushButton#delete_action_button {{
                background-color: {colors['delete_button']} !important;
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
            
            /* ========== CONFIGURACIÓN - CORREGIDO COMPLETAMENTE ========== */
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
                background-color: {colors['primary']} !important;
                color: {colors['text_primary']} !important;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 80px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_save_button:hover {{
                background-color: {colors['button_hover']} !important;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_save_button:pressed {{
                background-color: {colors['button_hover']} !important;
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_close_button {{
                background-color: {colors['delete_button']} !important;
                color: {colors['text_primary']} !important;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
                min-width: 80px;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_close_button:hover {{
                background-color: {colors['delete_hover']} !important;
            }}
            
            QDialog#SettingsDialog QPushButton#settings_close_button:pressed {{
                background-color: {colors['delete_hover']} !important;
                padding-top: 9px;
                padding-bottom: 7px;
            }}
            
            /* ========== ELEMENTOS DE FORMULARIO ========== */
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
            
            /* ========== BOTÓN CLEAR CON BORDE ANIMADO ========== */
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