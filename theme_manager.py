import os
import json
import logging
from PyQt5.QtWidgets import QApplication

THEMES = {
    "dark_gold": {
        "name": "Dark Gold (Default)",
        "bg_main": "#2c2a2b",
        "bg_secondary": "#3a3637",
        "bg_tertiary": "#232122",
        "bg_input": "#4a4647",
        "bg_card": "#3a3637",
        "bg_card_hover": "#454142",
        "accent": "#c89f68",
        "accent_hover": "#d9b68b",
        "accent_pressed": "#b88f58",
        "border": "#4f4a4b",
        "border_focus": "#c89f68",
        "text_primary": "#FFFFFF",
        "text_secondary": "#e0d6d1",
        "text_muted": "#b0a8a8",
        "text_on_accent": "#2c2a2b",
        "danger": "#f38ba8",
        "danger_hover": "#e67e80",
    },
    "catppuccin_mocha": {
        "name": "Catppuccin Mocha",
        "bg_main": "#1e1e2e",
        "bg_secondary": "#24273a",
        "bg_tertiary": "#181825",
        "bg_input": "#313244",
        "bg_card": "#313244",
        "bg_card_hover": "#45475a",
        "accent": "#cba6f7",
        "accent_hover": "#f5c2e7",
        "accent_pressed": "#b4befe",
        "border": "#45475a",
        "border_focus": "#cba6f7",
        "text_primary": "#cdd6f4",
        "text_secondary": "#bac2de",
        "text_muted": "#a6adc8",
        "text_on_accent": "#11111b",
        "danger": "#f38ba8",
        "danger_hover": "#f5a9b8",
    },
    "dark_slate": {
        "name": "Dark Grey / Slate",
        "bg_main": "#181a1f",
        "bg_secondary": "#21252b",
        "bg_tertiary": "#15181e",
        "bg_input": "#2c313a",
        "bg_card": "#21252b",
        "bg_card_hover": "#2c313a",
        "accent": "#61afef",
        "accent_hover": "#7ec7ff",
        "accent_pressed": "#4b8fcc",
        "border": "#3b4048",
        "border_focus": "#61afef",
        "text_primary": "#abb2bf",
        "text_secondary": "#c8ccd4",
        "text_muted": "#5c6370",
        "text_on_accent": "#181a1f",
        "danger": "#e06c75",
        "danger_hover": "#f0808a",
    },
    "light_mode": {
        "name": "Light Mode",
        "bg_main": "#dce0e5",
        "bg_secondary": "#e9ecef",
        "bg_tertiary": "#cfd4da",
        "bg_input": "#ffffff",
        "bg_card": "#ffffff",
        "bg_card_hover": "#f8f9fa",
        "accent": "#2b5278",
        "accent_hover": "#3a6896",
        "accent_pressed": "#1c3854",
        "border": "#b0b8c2",
        "border_focus": "#2b5278",
        "text_primary": "#0f172a",
        "text_secondary": "#1e293b",
        "text_muted": "#475569",
        "text_on_accent": "#ffffff",
        "danger": "#e11d48",
        "danger_hover": "#f43f5e",
    },
    "oled_black": {
        "name": "OLED Black",
        "bg_main": "#000000",
        "bg_secondary": "#121212",
        "bg_tertiary": "#1a1a1a",
        "bg_input": "#222222",
        "bg_card": "#121212",
        "bg_card_hover": "#1e1e1e",
        "accent": "#8e9aaf",
        "accent_hover": "#b8c0ec",
        "accent_pressed": "#6c757d",
        "border": "#333333",
        "border_focus": "#8e9aaf",
        "text_primary": "#ffffff",
        "text_secondary": "#e0e0e0",
        "text_muted": "#a0a0a0",
        "text_on_accent": "#000000",
        "danger": "#cf6679",
        "danger_hover": "#e58597",
    },
    "emerald": {
        "name": "Emerald Night",
        "bg_main": "#0f1715",
        "bg_secondary": "#172421",
        "bg_tertiary": "#0a0f0e",
        "bg_input": "#20332f",
        "bg_card": "#172421",
        "bg_card_hover": "#223531",
        "accent": "#10b981",
        "accent_hover": "#34d399",
        "accent_pressed": "#059669",
        "border": "#27473f",
        "border_focus": "#10b981",
        "text_primary": "#ecfdf5",
        "text_secondary": "#d1fae5",
        "text_muted": "#6ee7b7",
        "text_on_accent": "#064e3b",
        "danger": "#ef4444",
        "danger_hover": "#f87171",
    }
}

DEFAULT_THEME = "dark_gold"
_CURRENT_THEME_KEY = DEFAULT_THEME

def get_available_themes():
    return {key: theme["name"] for key, theme in THEMES.items()}

def get_current_theme_key():
    return _CURRENT_THEME_KEY

def get_theme(theme_key=None):
    if not theme_key or theme_key not in THEMES:
        theme_key = _CURRENT_THEME_KEY
    return THEMES[theme_key]

def set_active_theme(theme_key):
    global _CURRENT_THEME_KEY
    if theme_key in THEMES:
        _CURRENT_THEME_KEY = theme_key

def generate_global_qss(theme_key=None):
    t = get_theme(theme_key)
    return f"""
        /* Universal Base Reset & Formatting */
        QWidget {{
            color: {t['text_secondary']};
            font-family: "Segoe UI", Roboto, sans-serif;
        }}

        /* Window & Popup Main Containers */
        #main_widget, #popup_widget, QWidget#container, QWidget#settings_dropdown_widget {{ 
            background-color: {t['bg_main']}; 
            border-radius: 20px; 
            border: 1px solid {t['border']}; 
        }} 

        /* Custom Title Bar */
        QWidget#CustomTitleBar {{ 
            background-color: {t['bg_main']}; 
            border-top-left-radius: 20px; 
            border-top-right-radius: 20px; 
            border-bottom: 1px solid {t['border']};
        }} 
        QLabel#TitleLabel {{ 
            color: {t['text_primary']}; 
            font-size: 15px; 
            font-weight: bold; 
            background: transparent; 
        }} 
        QLabel#StatusLabel {{ 
            color: {t['text_secondary']}; 
            font-size: 12px; 
            font-weight: bold; 
            background: transparent; 
        }}

        /* Title Bar Header Action Buttons */
        QPushButton#HeaderButton {{ 
            background-color: {t['bg_input']}; 
            border: none; 
            border-radius: 15px; 
        }} 
        QPushButton#HeaderButton:hover {{ 
            background-color: {t['accent']}; 
        }} 
        QPushButton#CloseButton {{ 
            background-color: {t['danger']}; 
            border: none; 
            border-radius: 15px; 
        }} 
        QPushButton#CloseButton:hover {{ 
            background-color: {t['danger_hover']}; 
        }}

        /* Account Card Container */
        QWidget#AccountWidget {{ 
            background-color: {t['bg_card']}; 
            border-radius: 20px; 
            border: 3px solid transparent; 
        }} 
        QWidget#AccountWidget[selected="true"] {{ 
            border-color: {t['accent']}; 
        }} 
        QLabel#NameLabel {{ 
            color: {t['text_primary']}; 
            font-size: 14px; 
            font-weight: bold; 
        }} 
        QWidget#AccountWidget[selected="true"] QLabel#NameLabel {{ 
            color: {t['accent']}; 
        }} 
        QWidget#AccountWidget[is_add_button="true"] {{ 
            background-color: {t['bg_tertiary']}; 
            border: 3px dashed {t['accent']}; 
            border-radius: 20px; 
        }} 
        QWidget#AccountWidget[is_add_button="true"]:hover {{ 
            background-color: {t['bg_card_hover']}; 
        }} 
        QWidget#AccountWidget[is_add_button="true"] QLabel#NameLabel {{ 
            color: {t['accent']}; 
        }}

        /* Account Last Match Chip on Main Window Card */
        QLabel#LastMatchLabel {{
            color: {t['text_secondary']};
            font-size: 11px;
            font-weight: bold;
            background-color: {t['bg_tertiary']};
            border-radius: 12px;
            padding: 4px 10px;
            border: 1px solid {t['border']};
        }}

        /* General Labels */
        QLabel {{ 
            color: {t['text_secondary']}; 
            background: transparent;
        }}

        /* Group Boxes */
        QGroupBox {{ 
            color: {t['text_primary']}; 
            font-size: 13px; 
            font-weight: bold; 
            border: 1px solid {t['border']}; 
            border-radius: 14px; 
            margin-top: 12px; 
            padding-top: 10px;
        }} 
        QGroupBox::title {{ 
            subcontrol-origin: margin; 
            subcontrol-position: top left; 
            padding: 0 8px; 
            left: 10px; 
            color: {t['accent']}; 
        }}

        /* Scroll Areas & Bars */
        QScrollArea {{ 
            border: none; 
            background-color: transparent; 
        }} 
        QScrollArea QScrollBar:vertical, QScrollBar:vertical {{ 
            border: none; 
            background: transparent; 
            width: 8px; 
        }}
        QScrollBar::handle:vertical {{
            background: {t['border']};
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {t['accent']};
        }}
        QScrollArea QScrollBar:horizontal {{ 
            border: none; 
            background: transparent; 
            height: 0px; 
        }}
        QWidget#grid_container {{ 
            background-color: transparent; 
        }} 

        /* Options Sidebar List & Page Stack */
        QListWidget {{ 
            background-color: {t['bg_tertiary']}; 
            border: 1px solid {t['border']}; 
            border-radius: 16px; 
            outline: none; 
            padding: 8px; 
            color: {t['text_secondary']};
        }} 
        QListWidget::item {{ 
            color: {t['text_secondary']}; 
            font-size: 13px; 
            font-weight: bold; 
            padding: 10px 14px; 
            border-radius: 12px; 
            margin-bottom: 4px; 
        }} 
        QListWidget::item:hover {{ 
            background-color: {t['bg_card_hover']}; 
            color: {t['text_primary']}; 
        }} 
        QListWidget::item:selected {{ 
            background-color: {t['accent']}; 
            color: {t['text_on_accent']}; 
            border-radius: 12px;
        }}
        QStackedWidget {{ 
            background-color: {t['bg_secondary']}; 
            border: 1px solid {t['border']}; 
            border-radius: 16px; 
        }}

        /* Inputs & Combos */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox {{ 
            background-color: {t['bg_input']}; 
            border: 1px solid {t['border']}; 
            border-radius: 10px; 
            padding: 8px 12px; 
            color: {t['text_primary']}; 
            font-weight: bold;
        }}
        QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ 
            border: 1px solid {t['border_focus']}; 
        }}
        
        /* Modern QComboBox styling without legacy Windows square drop button */
        QComboBox {{ 
            background-color: {t['bg_input']}; 
            border: 1px solid {t['border']}; 
            border-radius: 10px; 
            padding: 8px 12px; 
            color: {t['text_primary']}; 
            font-weight: bold; 
        }}
        QComboBox:hover {{ 
            border: 1px solid {t['accent_hover']}; 
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 30px;
            border-left-width: 0px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            background: transparent;
        }}
        QComboBox::down-arrow {{
            width: 0;
            height: 0;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {t['text_secondary']};
            margin-right: 8px;
        }}
        QComboBox::down-arrow:hover {{
            border-top-color: {t['accent']};
        }}
        QComboBox QAbstractItemView {{ 
            background-color: {t['bg_secondary']}; 
            border: 1px solid {t['border']}; 
            border-radius: 10px;
            selection-background-color: {t['accent']}; 
            color: {t['text_primary']}; 
            selection-color: {t['text_on_accent']}; 
            padding: 6px; 
            outline: none;
        }}

        /* Sliders */
        QSlider::groove:horizontal {{
            border: 1px solid {t['border']};
            height: 8px;
            background: {t['bg_input']};
            border-radius: 4px;
        }}
        QSlider::handle:horizontal {{
            background: {t['accent']};
            border: 2px solid {t['bg_main']};
            width: 18px;
            height: 18px;
            margin: -5px 0; 
            border-radius: 9px;
        }}
        QSlider::add-page:horizontal {{
            background: {t['bg_input']};
            border-radius: 4px;
        }}
        QSlider::sub-page:horizontal {{
            background: {t['accent']};
            border-radius: 4px;
        }}

        /* General Buttons */
        QPushButton {{ 
            background-color: {t['bg_input']}; 
            color: {t['text_secondary']}; 
            font-weight: bold; 
            border-radius: 10px; 
            padding: 8px 16px; 
            border: 1px solid {t['border']}; 
        }}
        QPushButton:hover {{ 
            background-color: {t['bg_card_hover']}; 
            border-color: {t['accent']}; 
            color: {t['text_primary']};
        }}
        QPushButton:pressed {{ 
            background-color: {t['bg_tertiary']}; 
        }}
        QPushButton:checked {{ 
            background-color: {t['accent']}; 
            color: {t['text_on_accent']}; 
            border: 1px solid {t['accent_hover']}; 
        }}

        /* Toggle Option Buttons (On/Off switches in RadioButtonGroup) */
        QPushButton#ToggleOptionButton {{ 
            background-color: {t['bg_input']}; 
            color: {t['text_secondary']}; 
            font-weight: bold; 
            border-radius: 12px; 
            padding: 8px; 
            min-width: 90px; 
            border: 1px solid {t['border']};
        }}
        QPushButton#ToggleOptionButton:hover {{ 
            border: 1px solid {t['accent_hover']}; 
        }}
        QPushButton#ToggleOptionButton:checked {{ 
            background-color: {t['accent']}; 
            color: {t['text_on_accent']}; 
            border: 1px solid {t['accent_hover']}; 
        }}

        /* Accent Action Buttons */
        QPushButton[accent="true"], QPushButton#ApplyButton, QPushButton#PrimaryButton {{ 
            background-color: {t['accent']}; 
            color: {t['text_on_accent']}; 
            font-weight: bold; 
            border-radius: 10px; 
            padding: 10px 20px; 
            border: none;
        }}
        QPushButton[accent="true"]:hover, QPushButton#ApplyButton:hover, QPushButton#PrimaryButton:hover {{ 
            background-color: {t['accent_hover']}; 
        }}
        QPushButton[accent="true"]:pressed, QPushButton#ApplyButton:pressed, QPushButton#PrimaryButton:pressed {{ 
            background-color: {t['accent_pressed']}; 
        }}

        /* Tab Widgets (Pill shaped modern tabs) */
        QTabWidget::pane {{ 
            border: 1px solid {t['border']}; 
            border-radius: 14px; 
            background-color: {t['bg_secondary']}; 
        }}
        QTabBar::tab {{ 
            background: {t['bg_tertiary']}; 
            color: {t['text_secondary']}; 
            padding: 8px 18px; 
            border-radius: 12px; 
            margin-right: 6px;
            font-weight: bold;
        }}
        QTabBar::tab:selected {{ 
            background: {t['accent']}; 
            color: {t['text_on_accent']}; 
            font-weight: bold;
        }}

        /* Context Menu */
        QMenu {{ 
            background-color: {t['bg_secondary']}; 
            color: {t['text_secondary']}; 
            border: 1px solid {t['border']}; 
            border-radius: 14px; 
            padding: 6px; 
        }} 
        QMenu::item {{ 
            padding: 8px 24px 8px 12px; 
            border-radius: 8px; 
            margin: 2px 4px; 
            color: {t['text_secondary']};
        }} 
        QMenu::item:selected {{ 
            background-color: {t['accent']}; 
            color: {t['text_on_accent']}; 
        }}
        QMenu::icon {{ 
            padding-left: 14px; 
        }}

        /* Match History Dialog Components */
        QWidget#HistoryHeaderWidget {{
            background-color: {t['bg_secondary']};
            border-radius: 14px;
            border: 1px solid {t['border']};
        }}
        QWidget#MatchCard {{
            background-color: {t['bg_card']};
            border: 1px solid {t['border']};
            border-radius: 14px;
        }}
        QWidget#MatchCard:hover {{
            border: 1px solid {t['accent']};
            background-color: {t['bg_card_hover']};
        }}
        QWidget#TeamScoreboardBox {{
            background-color: {t['bg_secondary']};
            border-radius: 14px;
            border: 1px solid {t['border']};
        }}
        QWidget#TeamHeaderRow {{
            background-color: {t['bg_tertiary']};
            border-radius: 8px;
            border: none;
        }}
        QWidget#PlayerRow {{
            background-color: {t['bg_card']};
            border-radius: 8px;
            border: none;
        }}
        QWidget#PlayerRow[is_me="true"] {{
            background-color: {t['bg_card_hover']};
            border: 1px solid {t['accent']};
        }}
    """

def apply_theme_to_app(app_or_window, theme_key=None):
    set_active_theme(theme_key)
    qss = generate_global_qss(_CURRENT_THEME_KEY)
    app = QApplication.instance()
    if app:
        app.setStyleSheet(qss)
        for widget in app.topLevelWidgets():
            widget.setStyleSheet(qss)
            if hasattr(widget, 'title_bar') and widget.title_bar:
                if hasattr(widget, 'create_gear_icon') and hasattr(widget.title_bar, 'settings_button'):
                    widget.title_bar.settings_button.setIcon(widget.create_gear_icon())
                if hasattr(widget, 'create_add_icon') and hasattr(widget.title_bar, 'add_account_button'):
                    widget.title_bar.add_account_button.setIcon(widget.create_add_icon())
    if hasattr(app_or_window, 'setStyleSheet') and not isinstance(app_or_window, QApplication):
        app_or_window.setStyleSheet(qss)
