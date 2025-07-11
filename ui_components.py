import os
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QFileDialog,
    QDialog,
    QScrollArea,
    QGridLayout,
    QGraphicsDropShadowEffect,
    QDesktopWidget,
    QStyleOption,
    QStyle,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QApplication, 
    QCheckBox,
    QSpinBox,
    QTabWidget,
    QComboBox,
    QSlider,
    QGroupBox,
    QFormLayout
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QPainterPath
from PyQt5.QtCore import (
    Qt,
    QSize,
    QPoint,
    pyqtSignal,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QRectF,
    QTimer,
)


class LaunchNotificationWidget(QWidget):
    def __init__(self, account_name, icon_pixmap, parent=None, standalone=False):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_DeleteOnClose)
        self.setup_ui(account_name, icon_pixmap)
        self.center_on_screen()
        if standalone:
            QTimer.singleShot(6000, self.close_and_exit)
        else:
            QTimer.singleShot(6000, self.close)

    def close_and_exit(self):
        """Closes the widget and quits the QApplication."""
        self.close()
        app_instance = QApplication.instance()
        if app_instance:
            app_instance.quit()

    def setup_ui(self, name, pixmap):
        self.setFixedSize(300, 350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignCenter)
        
        shadow = QGraphicsDropShadowEffect(blurRadius=25, color=QColor(0, 0, 0, 180), offset=QPoint(0, 5))
        self.setGraphicsEffect(shadow)
        icon_label = QLabel(self)
        icon_label.setPixmap(pixmap.scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label); layout.addSpacing(15)
        
        name_label = QLabel(name, self)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; text-align: center;")
        layout.addWidget(name_label)

    def center_on_screen(self):
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())

class ValueSlider(QWidget):
    valueChanged = pyqtSignal(int)

    def __init__(self, min_val, max_val, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #4f4a4b;
                height: 10px;
                background: #4a4647;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #c89f68;
                border: 2px solid #2c2a2b;
                width: 18px;
                height: 18px;
                margin: -6px 0; 
                border-radius: 9px;
            }
            QSlider::add-page:horizontal {
                background: #4a4647;
            }
            QSlider::sub-page:horizontal {
                background: #c89f68;
                border-radius: 5px;
            }
        """)

        self.spin_box = QSpinBox()
        self.spin_box.setRange(min_val, max_val)
        self.spin_box.setFixedWidth(60)
        self.spin_box.setAlignment(Qt.AlignCenter)
        self.spin_box.setStyleSheet("""
            QSpinBox { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 5px; color: #e0d6d1; font-weight: bold; }
            QSpinBox::up-button, QSpinBox::down-button { width: 0px; border: none; background: transparent; }
        """)

        layout.addWidget(self.slider)
        layout.addWidget(self.spin_box)

        self.slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(self.valueChanged.emit)

    def value(self):
        return self.slider.value()

    def setValue(self, value):
        self.slider.setValue(value)

class RadioButtonGroup(QWidget):
    stateChanged = pyqtSignal(bool)

    def __init__(self, text_true, text_false, parent=None):
        super().__init__(parent)
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignRight)
        
        self.btn_true = QPushButton(text_true)
        self.btn_false = QPushButton(text_false)
        
        self.btn_true.setCheckable(True)
        self.btn_false.setCheckable(True)

        self.btn_true.clicked.connect(lambda: self.set_state(True))
        self.btn_false.clicked.connect(lambda: self.set_state(False))

        common_style = """
            QPushButton { 
                background-color: #4f4a4b; color: #e0d6d1; 
                font-weight: bold; border-radius: 8px; padding: 8px; min-width: 100px; border: 1px solid #3a3637;
            }
            QPushButton:hover {
                border: 1px solid #c89f68;
            }
            QPushButton:pressed {
                background-color: #5a5556;
            }
            QPushButton:checked {
                background-color: #c89f68; color: #2c2a2b; border: 1px solid #d9b68b;
            }
        """
        self.btn_true.setStyleSheet(common_style)
        self.btn_false.setStyleSheet(common_style)
        
        main_layout.addWidget(self.btn_false)
        main_layout.addWidget(self.btn_true)
    
    def set_state(self, is_true):
        self.btn_true.setChecked(is_true)
        self.btn_false.setChecked(not is_true)
        self.stateChanged.emit(is_true)

    def get_state(self):
        return self.btn_true.isChecked()

class ExportIMAMenuDialog(QDialog):
    def __init__(self, accounts_data, parent=None, default_settings=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        self.setMinimumWidth(450)
        default_settings = default_settings or {}
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        container_widget = QWidget(objectName="container")
        container_widget.setStyleSheet("""
            #container {
                background-color: #2c2a2b; 
                border: 1px solid #c89f68;
                border-radius: 15px;
            }
            QLabel { color: white; font-weight: bold; background: transparent; }
            QLineEdit, QListWidget { 
                background-color: #4a4647; 
                border: 1px solid #c89f68; 
                border-radius: 8px; 
                padding: 10px; 
                color: #e0d6d1; 
            }
            QPushButton { 
                background-color: #c89f68; 
                color: #2c2a2b; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 8px; 
                border: none;
            }
            QPushButton:hover { background-color: #d9b68b; }

            QScrollBar:vertical {
                border: none;
                background-color: #2c2a2b; /* Match the main background */
                width: 14px;
                margin: 0px 0 0px 0;
                border-radius: 0px;
            }
            QScrollBar::handle:vertical {
                background-color: #e0d6d1; /* The color of the scroll handle */
                min-height: 30px;
                border-radius: 7px;
                border: 1px solid #c89f68; /* Optional: border for the handle */
            }
            QScrollBar::handle:vertical:hover {
                background-color: #c89f68; /* Handle color on hover */
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px; /* Hide the top and bottom arrows */
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)
        main_layout.addWidget(container_widget)
        
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.title_bar = CustomTitleBar("iMA Menu Shortcut", self, is_dialog=True)
        container_layout.addWidget(self.title_bar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)
        container_layout.addWidget(content_area)

        self.accounts_data = accounts_data
        self.menu_icon_path = default_settings.get("menu_icon_path", "")
        
        content_layout.addWidget(QLabel("Menu Title:"))
        self.title_edit = QLineEdit(default_settings.get("title", "Valorant"))
        content_layout.addWidget(self.title_edit)
        
        content_layout.addWidget(QLabel("Menu Icon:"))
        icon_layout = QHBoxLayout()
        self.icon_path_edit = QLineEdit(self.menu_icon_path)
        self.icon_path_edit.setPlaceholderText("Optional: Select an icon for the main menu")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.select_icon)
        icon_layout.addWidget(self.icon_path_edit)
        icon_layout.addWidget(browse_button)
        content_layout.addLayout(icon_layout)
        
        content_layout.addWidget(QLabel("Arrange Accounts (Drag & Drop):"))
        self.accounts_list = QListWidget()
        self.accounts_list.setDragDropMode(QAbstractItemView.InternalMove)
        self.accounts_list.setIconSize(QSize(32, 32))
        self.populate_accounts(default_settings.get("ordered_accounts"))
        content_layout.addWidget(self.accounts_list)
        
        button_layout = QHBoxLayout()
        export_button = QPushButton("Export")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; 
                color: #2c2a2b; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 8px; 
                border: none;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        export_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 8px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(export_button)
        content_layout.addLayout(button_layout)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.center() - self.rect().center())

    def populate_accounts(self, ordered_list=None):
        if ordered_list is None: ordered_list = sorted(self.accounts_data.keys())
        all_accounts = set(self.accounts_data.keys()); current_accounts = set(ordered_list)
        for name in ordered_list:
            if name in self.accounts_data: self._add_item(name, self.accounts_data[name][0])
        for name in sorted(list(all_accounts - current_accounts)): self._add_item(name, self.accounts_data[name][0])

    def _add_item(self, name, icon_path):
        item = QListWidgetItem(name); item.setIcon(QIcon(icon_path or "")); self.accounts_list.addItem(item)

    def select_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon Files (*.ico *.png)")
        if path: self.menu_icon_path = path; self.icon_path_edit.setText(path)

    def get_settings(self):
        return {"title": self.title_edit.text(), "menu_icon_path": self.menu_icon_path, "ordered_accounts": [self.accounts_list.item(i).text() for i in range(self.accounts_list.count())]}

class PopupDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(True)
        
        self.main_widget = QWidget(objectName="popup_widget")
        self.main_widget.setStyleSheet("#popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #c89f68; } QLabel { color: #FFFFFF; }")
        
        popup_layout = QVBoxLayout(self.main_widget)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)

        self.title_bar = CustomTitleBar(title, self, is_dialog=True)
        popup_layout.addWidget(self.title_bar)
        
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(15, 10, 15, 15)
        popup_layout.addLayout(self.content_layout)

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0,0,0,0)
        main_v_layout.addWidget(self.main_widget)

    def showEvent(self, event):
        super().showEvent(event)
        self.center_on_parent()
        
    def center_on_parent(self):
        if self.parent():
            parent_geom = self.parent().geometry()
            self.move(parent_geom.center() - self.rect().center())

class CustomMessageDialog(PopupDialog):
    def __init__(self, title, message, parent=None):
        super().__init__(title, parent)
        self.setFixedSize(350, 180)
        
        message_label = QLabel(message)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)
        
        ok_button = QPushButton("OK")
        ok_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        self.content_layout.addLayout(button_layout)

class InputDialog(PopupDialog):
    def __init__(self, title, prompt, default_text="", parent=None):
        super().__init__(title, parent)
        self.setFixedSize(350, 180)
        
        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet("color: #e0d6d1;")
        self.content_layout.addWidget(prompt_label)
        
        self.input_field = QLineEdit(default_text)
        self.input_field.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.input_field)
        
        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        save_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        self.content_layout.addLayout(button_layout)

    def get_text(self):
        return self.input_field.text().strip()

class SaveAccountDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Save Account", parent)
        self.setFixedSize(380, 240)

        name_label = QLabel("Enter a name for the current account:")
        name_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        name_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.name_edit)

        self.content_layout.addWidget(QLabel("Select Game:"))
        self.game_combo = QComboBox()
        self.game_combo.setStyleSheet("""
            QComboBox { 
                background-color: #4a4647; 
                border: 1px solid #c89f68; 
                border-radius: 8px; 
                padding: 8px; 
                color: #e0d6d1; 
                font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; 
                border: 1px solid #c89f68; 
                selection-background-color: #c89f68;
                color: #e0d6d1;
                selection-color: #2c2a2b;
                padding: 5px;
            }
        """)
        
        valorant_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "valorant.png")
        lol_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "lol.png")

        if os.path.exists(valorant_icon_path):
            self.game_combo.addItem(QIcon(valorant_icon_path), "Valorant", "valorant")
        else:
            self.game_combo.addItem("Valorant", "valorant")

        if os.path.exists(lol_icon_path):
            self.game_combo.addItem(QIcon(lol_icon_path), "League of Legends", "lol")
        else:
            self.game_combo.addItem("League of Legends", "lol")

        riot_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "Riot.png")
        if os.path.exists(riot_icon_path):
            self.game_combo.addItem(QIcon(riot_icon_path), "Both", "both")
        else:
            self.game_combo.addItem("Both", "both")
            
        self.content_layout.addWidget(self.game_combo)

        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 8px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        cancel_button.clicked.connect(self.reject)

        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        self.content_layout.addLayout(button_layout)

    def get_details(self):
        return self.name_edit.text().strip(), self.game_combo.currentData()

class SettingsDialog(PopupDialog):
    def __init__(self, actions, parent):
        super().__init__("Settings", parent)
        # Removed the global stylesheet for QPushButton to avoid interfering with CustomTitleBar
        self.content_layout.setSpacing(10)
        button_style = """QPushButton { background-color: #c89f68; color: #2c2a2b; font-size: 15px; font-weight: bold; border: none; border-radius: 12px; padding: 8px 15px; text-align: left; } QPushButton:hover { background-color: #d9b68b; } QPushButton::icon { width: 24px; height: 24px; } """
        for text, (action, icon_name) in actions.items():
            icon_path = os.path.join(os.path.dirname(__file__), "Assets", icon_name)
            button = QPushButton(text)
            button.setStyleSheet(button_style) # Apply style directly to each button
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
            button.clicked.connect(lambda _, a=action: (self.close(), a()))
            self.content_layout.addWidget(button)

class OptionsDialog(PopupDialog):
    settings_applied = pyqtSignal() # New signal

    def __init__(self, switcher_instance, parent=None):
        super().__init__("Options", parent)
        self.switcher = switcher_instance
        self.setFixedSize(600, 700)

        self.quality_settings_map = {
            "sg.ViewDistanceQuality": "View Distance", "sg.AntiAliasingQuality": "Anti-Aliasing",
            "sg.ShadowQuality": "Shadows", "sg.PostProcessQuality": "Post-Processing",
            "sg.TextureQuality": "Textures", "sg.EffectsQuality": "Effects",
            "sg.FoliageQuality": "Foliage", "sg.ShadingQuality": "Shading",
        }
        self.riot_quality_settings_map = {
            "EAresIntSettingName::MaterialQuality": "Material Quality",
            "EAresIntSettingName::TextureQuality": "Texture Quality",
            "EAresIntSettingName::DetailQuality": "Detail Quality",
            "EAresIntSettingName::UIQuality": "UI Quality",
            "EAresIntSettingName::NvidiaReflexLowLatencySetting": "Nvidia Reflex",
        }
        self.audio_settings_map = {
            "EAresFloatSettingName::OverallVolume": "Main Volume",
            "EAresFloatSettingName::SoundEffectsVolume": "Sound Effects",
            "EAresFloatSettingName::VoiceOverVolume": "Voice-Over",
            "EAresFloatSettingName::VideoVolume": "Store Video",
            "EAresFloatSettingName::AllMusicOverallVolume": "All Music",
            "EAresFloatSettingName::MenuAndLobbyMusicVolume": "Menu & Lobby Music",
            "EAresFloatSettingName::CharacterSelectMusicVolume": "Agent Select Music",
            "EAresIntSettingName::MicVolume": "Mic Volume",
            "EAresIntSettingName::VoiceVolume": "Incoming Volume",
            "EAresBoolSettingName::PushToTalkEnabled": "Party Voice Activation",
            "EAresBoolSettingName::EnableHRTF": "HRTF"
        }
        self.riot_combo_boxes = {}
        self.audio_controls = {}
        self.spin_boxes = {}

        self.main_widget.setStyleSheet("""
            #popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #4f4a4b; }
            QLabel { color: #FFFFFF; font-weight: normal; }
            QGroupBox { 
                color: #c89f68; 
                font-size: 14px;
                font-weight: bold; 
                border: 1px solid #4f4a4b; 
                border-radius: 8px; 
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
            }
        """)

        self.content_layout.setSpacing(10)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #4f4a4b; border-top: 1px solid #4f4a4b; border-radius: 8px; }
            QTabBar::tab { 
                background-color: #3a3637; color: #e0d6d1; padding: 10px 15px; font-weight: bold;
                border: 1px solid #4f4a4b; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
            }
            QTabBar::tab:selected { background-color: #c89f68; color: #2c2a2b; }
        """)
        self.content_layout.addWidget(self.tab_widget)

        self.setup_graphics_tab()
        self.setup_audio_tab()
        self.setup_advanced_tab()
        self.setup_ui_tab()

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e0d6d1; font-size: 12px; padding-top: 5px;")
        self.content_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        apply_button = QPushButton("Apply")
        close_button = QPushButton("Close")
        
        button_style = """
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 10px; border: 1px solid #c89f68;
            }
            QPushButton:hover { background-color: #d9b68b; padding-bottom: 9px; border-width: 2px;}
            QPushButton:pressed { background-color: #b88f58; padding-bottom: 10px; border-width: 1px;}
        """
        apply_button.setStyleSheet(button_style)
        
        close_button_style = """
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """
        close_button.setStyleSheet(close_button_style)

        apply_button.clicked.connect(self.apply_settings)
        close_button.clicked.connect(self.close)

        button_layout.addStretch()
        button_layout.addWidget(close_button)
        button_layout.addWidget(apply_button)
        self.content_layout.addLayout(button_layout)

        self.load_current_settings()

    def setup_graphics_tab(self):
        graphics_tab = QWidget()
        layout = QVBoxLayout(graphics_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)
        
        combo_style = """
            QComboBox { 
                background-color: #4a4647; 
                border: 1px solid #c89f68; 
                border-radius: 8px; 
                padding: 8px; 
                color: #e0d6d1; 
                font-weight: bold;
            }
            QComboBox:hover { border: 1px solid #d9b68b; }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; /* Can add a custom arrow icon here */ }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; 
                border: 1px solid #c89f68; 
                selection-background-color: #c89f68;
                color: #e0d6d1;
                selection-color: #2c2a2b;
                padding: 5px;
            }
        """

        self.display_mode_combo = QComboBox()
        self.display_mode_combo.addItems(["Default", "Fullscreen", "Windowed Fullscreen", "Windowed"])
        self.display_mode_combo.setStyleSheet(combo_style)
        form_layout.addRow(QLabel("Display Mode:"), self.display_mode_combo)
        
        quality_keys = [
            "EAresIntSettingName::MaterialQuality", "EAresIntSettingName::TextureQuality",
            "EAresIntSettingName::DetailQuality", "EAresIntSettingName::UIQuality",
            "EAresIntSettingName::NvidiaReflexLowLatencySetting"
        ]
        for key in quality_keys:
            combo_box = QComboBox()
            if key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                combo_box.addItems(["Off", "On", "On + Boost"])
            else:
                combo_box.addItems(["Low", "Med", "High"])
            
            combo_box.setStyleSheet(combo_style)
            self.riot_combo_boxes[key] = combo_box
            form_layout.addRow(QLabel(self.riot_quality_settings_map[key] + ":"), combo_box)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        self.tab_widget.addTab(graphics_tab, QIcon(os.path.join(os.path.dirname(__file__), "Assets", "Graphics.png")), "Graphics")

    def setup_audio_tab(self):
        audio_tab = QWidget()
        main_layout = QVBoxLayout(audio_tab)
        main_layout.setContentsMargins(15, 5, 15, 15)
        main_layout.setSpacing(10)
        main_layout.setAlignment(Qt.AlignTop)

        general_group = QGroupBox("General Volume")
        general_layout = QFormLayout(general_group)
        general_layout.setSpacing(10)
        general_keys = ["EAresFloatSettingName::OverallVolume", "EAresFloatSettingName::SoundEffectsVolume", "EAresFloatSettingName::VoiceOverVolume", "EAresFloatSettingName::VideoVolume"]
        for key in general_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            general_layout.addRow(QLabel(self.audio_settings_map[key] + ":"), slider)
        main_layout.addWidget(general_group)

        music_group = QGroupBox("Music")
        music_layout = QFormLayout(music_group)
        music_layout.setSpacing(10)
        music_keys = ["EAresFloatSettingName::AllMusicOverallVolume", "EAresFloatSettingName::MenuAndLobbyMusicVolume", "EAresFloatSettingName::CharacterSelectMusicVolume"]
        for key in music_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            music_layout.addRow(QLabel(self.audio_settings_map[key] + ":"), slider)
        main_layout.addWidget(music_group)
        
        voice_group = QGroupBox("Voice & Communication")
        voice_layout = QFormLayout(voice_group)
        voice_layout.setSpacing(10)
        voice_keys = ["EAresIntSettingName::MicVolume", "EAresIntSettingName::VoiceVolume"]
        for key in voice_keys:
            slider = ValueSlider(0, 100)
            self.audio_controls[key] = slider
            voice_layout.addRow(QLabel(self.audio_settings_map[key] + ":"), slider)
        
        self.audio_controls["EAresBoolSettingName::PushToTalkEnabled"] = RadioButtonGroup("Push to Talk", "Automatic")
        voice_layout.addRow(QLabel(self.audio_settings_map["EAresBoolSettingName::PushToTalkEnabled"] + ":"), self.audio_controls["EAresBoolSettingName::PushToTalkEnabled"])
        
        self.audio_controls["EAresBoolSettingName::EnableHRTF"] = RadioButtonGroup("On", "Off")
        voice_layout.addRow(QLabel(self.audio_settings_map["EAresBoolSettingName::EnableHRTF"] + ":"), self.audio_controls["EAresBoolSettingName::EnableHRTF"])
        main_layout.addWidget(voice_group)

        main_layout.addStretch()
        self.tab_widget.addTab(audio_tab, QIcon(os.path.join(os.path.dirname(__file__), "Assets", "Audio.png")), "Audio")

    def setup_advanced_tab(self):
        advanced_tab = QWidget()
        layout = QVBoxLayout(advanced_tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        preset_buttons_layout = QHBoxLayout()
        recommended_button = QPushButton("Recommended (Low)")
        default_button = QPushButton("Default (High)")
        
        preset_style = """
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 8px; border: 1px solid #c89f68;
            }
            QPushButton:hover { background-color: #d9b68b; }
            QPushButton:pressed { background-color: #b88f58; }
        """
        recommended_button.setStyleSheet(preset_style)
        default_button.setStyleSheet(preset_style)
        
        recommended_button.clicked.connect(lambda: self.set_all_qualities(0))
        default_button.clicked.connect(lambda: self.set_all_qualities(3))

        preset_buttons_layout.addWidget(recommended_button)
        preset_buttons_layout.addWidget(default_button)
        layout.addLayout(preset_buttons_layout)
        layout.addSpacing(15)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        items = list(self.quality_settings_map.items())
        num_rows = (len(items) + 1) // 2 

        for i, (key, display_name) in enumerate(items):
            row, col = i % num_rows, (i // num_rows) * 2
            
            label = QLabel(display_name + ":")
            grid_layout.addWidget(label, row, col)
            
            spin_box = QSpinBox()
            spin_box.setRange(0, 3)
            spin_box.setStyleSheet("QSpinBox { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 5px; color: #e0d6d1; }")
            spin_box.setFixedWidth(60)
            self.spin_boxes[key] = spin_box
            grid_layout.addWidget(spin_box, row, col + 1, Qt.AlignLeft)

        layout.addLayout(grid_layout)
        layout.addStretch()
        self.tab_widget.addTab(advanced_tab, QIcon(os.path.join(os.path.dirname(__file__), "Assets", "Advanced.png")), "Advanced")

    def setup_advanced_tab(self):
        advanced_tab = QWidget()
        layout = QVBoxLayout(advanced_tab)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(10)
        
        preset_buttons_layout = QHBoxLayout()
        recommended_button = QPushButton("Recommended (Low)")
        default_button = QPushButton("Default (High)")
        
        preset_style = """
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 8px; border: 1px solid #c89f68;
            }
            QPushButton:hover { background-color: #d9b68b; }
            QPushButton:pressed { background-color: #b88f58; }
        """
        recommended_button.setStyleSheet(preset_style)
        default_button.setStyleSheet(preset_style)
        
        recommended_button.clicked.connect(lambda: self.set_all_qualities(0))
        default_button.clicked.connect(lambda: self.set_all_qualities(3))

        preset_buttons_layout.addWidget(recommended_button)
        preset_buttons_layout.addWidget(default_button)
        layout.addLayout(preset_buttons_layout)
        layout.addSpacing(15)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        items = list(self.quality_settings_map.items())
        num_rows = (len(items) + 1) // 2 

        for i, (key, display_name) in enumerate(items):
            row, col = i % num_rows, (i // num_rows) * 2
            
            label = QLabel(display_name + ":")
            grid_layout.addWidget(label, row, col)
            
            spin_box = QSpinBox()
            spin_box.setRange(0, 3)
            spin_box.setStyleSheet("QSpinBox { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 5px; color: #e0d6d1; }")
            spin_box.setFixedWidth(60)
            self.spin_boxes[key] = spin_box
            grid_layout.addWidget(spin_box, row, col + 1, Qt.AlignLeft)

        layout.addLayout(grid_layout)
        layout.addStretch()
        self.tab_widget.addTab(advanced_tab, QIcon(os.path.join(os.path.dirname(__file__), "Assets", "Advanced.png")), "Advanced")

    def setup_ui_tab(self):
        ui_tab = QWidget()
        layout = QVBoxLayout(ui_tab)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignTop)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignLeft)
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows)

        self.show_game_icons_toggle = RadioButtonGroup("On", "Off")
        form_layout.addRow(QLabel("Show Game Icons:"), self.show_game_icons_toggle)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        self.tab_widget.addTab(ui_tab, QIcon(os.path.join(os.path.dirname(__file__), "Assets", "Graphics.png")), "UI") # Using Graphics.png as a placeholder icon for now

    def set_all_qualities(self, value):
        for spin_box in self.spin_boxes.values():
            spin_box.setValue(value)

    def load_current_settings(self):
        settings = self.switcher.get_graphics_settings()
        self.display_mode_combo.setCurrentText(settings.get("display_mode", "Default"))
        
        riot_settings = settings.get("riot_settings", {})
        for key, combo_box in self.riot_combo_boxes.items():
            if key == "EAresIntSettingName::MaterialQuality":
                value = riot_settings.get(key, "High")
                if value == "0": combo_box.setCurrentText("Low")
                elif value == "2": combo_box.setCurrentText("Med")
                else: combo_box.setCurrentText("High")
            elif key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                value = riot_settings.get(key, "On")
                if value == "0": combo_box.setCurrentText("Off")
                elif value == "2": combo_box.setCurrentText("On + Boost")
                else: combo_box.setCurrentText("On")
            else: # Texture, Detail, UI Quality
                value = riot_settings.get(key, "High")
                if value == "0": combo_box.setCurrentText("Low")
                elif value == "1": combo_box.setCurrentText("Med")
                else: combo_box.setCurrentText("High")

        audio_settings = settings.get("audio_settings", {})
        for key, control in self.audio_controls.items():
            value_str = audio_settings.get(key)
            if value_str is None: 
                if isinstance(control, ValueSlider):
                    control.setValue(100)
                elif isinstance(control, RadioButtonGroup):
                    is_true_default = (key == "EAresBoolSettingName::PushToTalkEnabled")
                    control.set_state(is_true_default)
            else:
                if key.startswith("EAresFloatSettingName::"):
                    control.setValue(int(float(value_str) * 100))
                elif key.startswith("EAresIntSettingName::"):
                    control.setValue(int(value_str))
                elif key.startswith("EAresBoolSettingName::"):
                    control.set_state(value_str.lower() == 'true')
        
        self.status_label.setText("Loaded saved settings.")

    def apply_settings(self):
        quality_settings = {key: spin_box.value() for key, spin_box in self.spin_boxes.items()}
        
        riot_settings_to_save = {}
        for key, combo_box in self.riot_combo_boxes.items():
            selected_text = combo_box.currentText()
            if key == "EAresIntSettingName::MaterialQuality":
                if selected_text == "Low": riot_settings_to_save[key] = "0"
                elif selected_text == "Med": riot_settings_to_save[key] = "2"
                else: riot_settings_to_save[key] = "High"
            elif key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                if selected_text == "Off": riot_settings_to_save[key] = "0"
                elif selected_text == "On + Boost": riot_settings_to_save[key] = "2"
                else: riot_settings_to_save[key] = "On"
            else:
                if selected_text == "Low": riot_settings_to_save[key] = "0"
                elif selected_text == "Med": riot_settings_to_save[key] = "1"
                else: riot_settings_to_save[key] = "High"

        audio_settings_to_save = {}
        for key, control in self.audio_controls.items():
            special_float_keys = ["EAresFloatSettingName::CharacterSelectMusicVolume", "EAresFloatSettingName::MenuAndLobbyMusicVolume"]
            if isinstance(control, ValueSlider):
                val = control.value()
                if key.startswith("EAresFloatSettingName::"):
                    if val == 100:
                        audio_settings_to_save[key] = "1.000000" if key in special_float_keys else "MAX"
                    else:
                        audio_settings_to_save[key] = f"{val/100:.6f}"
                elif key.startswith("EAresIntSettingName::"):
                    audio_settings_to_save[key] = str(val)
            elif isinstance(control, RadioButtonGroup):
                audio_settings_to_save[key] = "True" if control.get_state() else "False"

        ui_settings_to_save = {
            "show_game_icons": self.show_game_icons_toggle.get_state()
        }

        settings_to_save = {
            "display_mode": self.display_mode_combo.currentText(),
            "quality": quality_settings,
            "riot_settings": riot_settings_to_save,
            "audio_settings": audio_settings_to_save,
            "ui_settings": ui_settings_to_save
        }
        self.switcher.save_graphics_settings(settings_to_save)
        success, message = self.switcher.update_all_game_user_settings(settings_to_save)
        
        if success:
            self.status_label.setText("Settings applied successfully to all accounts.")
            self.settings_applied.emit() # Emit signal on success
        else:
            self.status_label.setText(f"Failed to apply settings: {message}")

    def load_current_settings(self):
        settings = self.switcher.get_graphics_settings()
        self.display_mode_combo.setCurrentText(settings.get("display_mode", "Default"))
        
        riot_settings = settings.get("riot_settings", {})
        for key, combo_box in self.riot_combo_boxes.items():
            if key == "EAresIntSettingName::MaterialQuality":
                value = riot_settings.get(key, "High")
                if value == "0": combo_box.setCurrentText("Low")
                elif value == "2": combo_box.setCurrentText("Med")
                else: combo_box.setCurrentText("High")
            elif key == "EAresIntSettingName::NvidiaReflexLowLatencySetting":
                value = riot_settings.get(key, "On")
                if value == "0": combo_box.setCurrentText("Off")
                elif value == "2": combo_box.setCurrentText("On + Boost")
                else: combo_box.setCurrentText("On")
            else: # Texture, Detail, UI Quality
                value = riot_settings.get(key, "High")
                if value == "0": combo_box.setCurrentText("Low")
                elif value == "1": combo_box.setCurrentText("Med")
                else: combo_box.setCurrentText("High")

        audio_settings = settings.get("audio_settings", {})
        for key, control in self.audio_controls.items():
            value_str = audio_settings.get(key)
            if value_str is None: 
                if isinstance(control, ValueSlider):
                    control.setValue(100)
                elif isinstance(control, RadioButtonGroup):
                    is_true_default = (key == "EAresBoolSettingName::PushToTalkEnabled")
                    control.set_state(is_true_default)
            else:
                if key.startswith("EAresFloatSettingName::"):
                    control.setValue(int(float(value_str) * 100))
                elif key.startswith("EAresIntSettingName::"):
                    control.setValue(int(value_str))
                elif key.startswith("EAresBoolSettingName::"):
                    control.set_state(value_str.lower() == 'true')
        
        ui_settings = self.switcher.config.get("ui_settings", {})
        self.show_game_icons_toggle.set_state(ui_settings.get("show_game_icons", True))
        
        self.status_label.setText("Loaded saved settings.")

class CustomTitleBar(QWidget):
    def __init__(self, title, parent, is_dialog=False):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)

        if is_dialog:
            self.setStyleSheet("""
                background-color: #2c2a2b; 
                border-top-left-radius: 15px; 
                border-top-right-radius: 15px;
                border-bottom: 1px solid #4f4a4b;
            """)
        else:
            self.setStyleSheet("background-color: #2c2a2b; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 5, 0)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; background: transparent;")
        layout.addWidget(title_label)
        layout.addStretch()
        
        close_button = QPushButton("✕")
        close_button.setFixedSize(QSize(30, 30))
        close_button.clicked.connect(self.parent_window.close)
        close_button.setStyleSheet("QPushButton { background-color: #f38ba8; color: #ffffff; font-size: 18px; font-weight: bold; border: none; border-radius: 15px; } QPushButton:hover { background-color: #e67e80; }")
        layout.addWidget(close_button)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent_window.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if hasattr(self.parent_window, "old_pos") and self.parent_window.old_pos is not None:
            delta = QPoint(event.globalPos() - self.parent_window.old_pos)
            self.parent_window.move(self.parent_window.x() + delta.x(), self.parent_window.y() + delta.y())
            self.parent_window.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.parent_window.old_pos = None

class GameSelectionDialog(PopupDialog):
    game_selected = pyqtSignal(str)

    def __init__(self, account_name, account_icon_pixmap, parent=None):
        super().__init__("Select Game", parent)
        self.setFixedSize(400, 450)
        self.account_name = account_name
        self.account_icon_pixmap = account_icon_pixmap

        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(20)
        self.content_layout.setAlignment(Qt.AlignCenter)

        # Game selection buttons
        game_buttons_layout = QHBoxLayout()
        game_buttons_layout.setSpacing(20)
        game_buttons_layout.setAlignment(Qt.AlignCenter)

        self.valorant_button = self._create_game_button("Valorant", "valorant.png", "valorant")
        self.lol_button = self._create_game_button("League of Legends", "lol.png", "lol")

        game_buttons_layout.addWidget(self.valorant_button)
        game_buttons_layout.addWidget(self.lol_button)
        self.content_layout.addLayout(game_buttons_layout)

        # Account info below game selection
        account_info_layout = QVBoxLayout()
        account_info_layout.setAlignment(Qt.AlignCenter)

        account_icon_label = QLabel(self)
        account_icon_label.setPixmap(self.account_icon_pixmap.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        account_icon_label.setAlignment(Qt.AlignCenter)
        account_info_layout.addWidget(account_icon_label)

        account_name_label = QLabel(self.account_name, self)
        account_name_label.setAlignment(Qt.AlignCenter)
        account_name_label.setStyleSheet("color: white; font-size: 20px; font-weight: bold;")
        account_info_layout.addWidget(account_name_label)

        self.content_layout.addLayout(account_info_layout)

    def _create_game_button(self, name, icon_filename, game_id):
        button = QPushButton()
        button.setFixedSize(150, 150)
        button.setStyleSheet("""
            QPushButton { background-color: #3a3637; border-radius: 15px; border: 2px solid #4f4a4b; }
            QPushButton:hover { background-color: #4f4a4b; border-color: #c89f68; }
            QPushButton:pressed { background-color: #2c2a2b; }
        """)
        button.clicked.connect(lambda: self._set_selected_game_and_accept(game_id))

        layout = QVBoxLayout(button)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        icon_path = os.path.join(os.path.dirname(__file__), "Assets", icon_filename)
        if os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = QPixmap(icon_path).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        name_label = QLabel(name)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold;")
        layout.addWidget(name_label)

        return button

    def _set_selected_game_and_accept(self, game_id):
        self.game_selected_value = game_id
        self.game_selected.emit(game_id)
        self.accept()

class AccountWidget(QWidget):
    selected = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    context_menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, account_name, icon, game, parent=None, is_add_button=False):
        super().__init__(parent)
        self.account_name = account_name
        self.game = game
        self.setObjectName("AccountWidget")
        self.setFixedSize(120, 140)
        self.is_selected, self.is_hovered = False, False
        self.is_add_button = is_add_button
        self.setStyleSheet("""QWidget#AccountWidget { background-color: #3a3637; border-radius: 15px; border: 3px solid transparent; } 
                              QWidget#AccountWidget[selected="true"] { border-color: #c89f68; } 
                              QLabel#NameLabel { color: #e0d6d1; font-size: 13px; font-weight: bold; } 
                              QWidget#AccountWidget[selected="true"] QLabel#NameLabel { color: #c89f68; } 
                              QWidget#AccountWidget[is_add_button="true"] { background-color: #4f4a4b; border: 3px dashed #c89f68; } 
                              QWidget#AccountWidget[is_add_button="true"]:hover { background-color: #5a5556; } 
                              QWidget#AccountWidget[is_add_button="true"] QLabel#NameLabel { color: #c89f68; }""")
        self.init_ui(icon)
        self.init_animations()

    def init_ui(self, icon):
        icon_size = 70
        self.icon_label = QLabel(self)
        self.set_icon(icon, icon_size)
        self.name_label = QLabel(self.account_name, self, objectName="NameLabel")
        self.name_label.setAlignment(Qt.AlignCenter | Qt.AlignTop)
        self.name_label.setWordWrap(True)
        
        self.icon_label.setGeometry((self.width() - icon_size) // 2, 15, icon_size, icon_size)
        self.name_label.setGeometry(10, self.icon_label.y() + icon_size + 5, 100, 40)
        self.icon_original_geom, self.name_original_geom = (self.icon_label.geometry(), self.name_label.geometry())
        self.icon_label.setGraphicsEffect(QGraphicsDropShadowEffect(blurRadius=12, color=QColor(0, 0, 0, 80), offset=QPoint(2, 2)))

        if self.is_add_button:
            self.setProperty("is_add_button", "true")
            self.icon_label.setGraphicsEffect(None)
            self.name_label.setStyleSheet("color: #c89f68; font-size: 16px; font-weight: bold;")
            self.icon_label.setStyleSheet("color: #c89f68;")
        else:
            self.game_icon_label = QLabel(self)
            game_icon_size = 24
            self.game_icon_label.setFixedSize(game_icon_size, game_icon_size)
            self.game_icon_label.setAlignment(Qt.AlignCenter)
            self.game_icon_label.move(self.width() - game_icon_size - 10, self.height() - game_icon_size - 10)
            
            valorant_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "valorant.png")
            lol_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "lol.png")
            riot_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "Riot.png")

            self.game_icon_label.setVisible(False) # Hide by default, will be set by load_accounts
            if self.game == 'valorant' and os.path.exists(valorant_icon_path):
                pixmap = QPixmap(valorant_icon_path).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.game_icon_label.setPixmap(pixmap)
            elif self.game == 'lol' and os.path.exists(lol_icon_path):
                pixmap = QPixmap(lol_icon_path).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.game_icon_label.setPixmap(pixmap)
            elif self.game == 'both' and os.path.exists(riot_icon_path):
                pixmap = QPixmap(riot_icon_path).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.game_icon_label.setPixmap(pixmap)

    def init_animations(self):
        self.icon_anim = QPropertyAnimation(self.icon_label, b"geometry", duration=150, easingCurve=QEasingCurve.OutQuad)
        self.name_anim = QPropertyAnimation(self.name_label, b"geometry", duration=150, easingCurve=QEasingCurve.OutQuad)

    def set_icon(self, icon, size):
        source_pixmap = icon.pixmap(QSize(512, 512))
        original_width, original_height = source_pixmap.width(), source_pixmap.height()
        square_side = min(original_width, original_height)
        crop_x, crop_y = (original_width - square_side) // 2, (original_height - square_side) // 2
        cropped_pixmap = source_pixmap.copy(crop_x, crop_y, square_side, square_side)
        scaled_pixmap = cropped_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.transparent)
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)
        x, y = int((size - scaled_pixmap.width()) / 2), int((size - scaled_pixmap.height()) / 2)
        painter.drawPixmap(x, y, scaled_pixmap)
        painter.end()
        self.icon_label.setPixmap(circular_pixmap)

    def enterEvent(self, event):
        if self.is_add_button: return
        self.is_hovered = True
        scale_factor = 1.1
        new_icon_rect = QRectF(0,0,self.icon_original_geom.width() * scale_factor,self.icon_original_geom.height() * scale_factor)
        new_icon_rect.moveCenter(self.icon_original_geom.center())
        self.icon_anim.setEndValue(new_icon_rect.toRect())
        self.icon_anim.start()
        new_name_rect = QRectF(0,0,self.name_original_geom.width()*scale_factor,self.name_original_geom.height()*scale_factor)
        new_name_rect.moveCenter(self.name_original_geom.center())
        self.name_anim.setEndValue(new_name_rect.toRect())
        self.name_anim.start()
        self.update()

    def leaveEvent(self, event):
        if self.is_add_button: return
        self.is_hovered = False
        self.icon_anim.setEndValue(self.icon_original_geom)
        self.icon_anim.start()
        self.name_anim.setEndValue(self.name_original_geom)
        self.name_anim.start()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        opt = QStyleOption()
        opt.initFrom(self)
        self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)

    def set_selected(self, selected):
        self.is_selected = selected
        self.setProperty("selected", "true" if selected else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_show_game_icon(self, show): # New method
        if hasattr(self, 'game_icon_label'):
            self.game_icon_label.setVisible(show)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.account_name)

    def mouseDoubleClickEvent(self, event):
        if self.is_add_button: return
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.account_name)

    def contextMenuEvent(self, event):
        if self.is_add_button: return
        self.context_menu_requested.emit(self.account_name, self.mapToGlobal(event.pos()))

class HoverButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anim = QPropertyAnimation(self, b"iconSize", duration=150, easingCurve=QEasingCurve.OutQuad)

    def enterEvent(self, event):
        self.original_icon_size = self.iconSize()
        self.hover_icon_size = QSize(int(self.original_icon_size.width() * 1.2), int(self.original_icon_size.height() * 1.2))
        self.anim.setEndValue(self.hover_icon_size)
        self.anim.start()

    def leaveEvent(self, event):
        self.anim.setEndValue(self.original_icon_size)
        self.anim.start()

class InstallerDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Install iMA Switcher", parent)
        self.setFixedSize(500, 400) 
        
        self.content_layout.setContentsMargins(20, 10, 20, 20)
        self.content_layout.setSpacing(15)

        self.content_layout.addWidget(QLabel("Choose Installation Folder:"))
        
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        default_path = os.path.join(os.getenv('LOCALAPPDATA'), "iMA Switcher")
        self.path_edit.setText(default_path)
        self.path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        path_layout.addWidget(self.path_edit)
        
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        browse_button.clicked.connect(self.select_folder)
        path_layout.addWidget(browse_button)
        self.content_layout.addLayout(path_layout)
        
        self.content_layout.addWidget(QLabel("Riot Client Executable Path:"))
        riot_path_layout = QHBoxLayout()
        self.riot_path_edit = QLineEdit()
        self.riot_path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        riot_path_layout.addWidget(self.riot_path_edit)
        
        riot_browse_button = QPushButton("Browse")
        riot_browse_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        riot_browse_button.clicked.connect(self.select_riot_games_folder)
        riot_path_layout.addWidget(riot_browse_button)
        self.content_layout.addLayout(riot_path_layout)

        self.riot_path_warning_label = QLabel("")
        self.riot_path_warning_label.setStyleSheet("color: red; font-size: 10px;")
        self.content_layout.addWidget(self.riot_path_warning_label)

        from game_switcher import GameSwitcher
        switcher = GameSwitcher()
        switcher.initialize_riot_client_paths() 
        found_riot_path = switcher.riot_games_config.get("ExeLocationDefault")
        if found_riot_path and os.path.exists(found_riot_path):
            self.riot_path_edit.setText(found_riot_path)
            self.riot_path_warning_label.setText("")
        else:
            self.riot_path_edit.setText("")
            self.riot_path_warning_label.setText("Riot Client not found. Please select 'RiotClientServices.exe'.")

        self.desktop_shortcut_checkbox = QCheckBox("Add shortcut to Desktop")
        self.desktop_shortcut_checkbox.setChecked(True)
        self.desktop_shortcut_checkbox.setStyleSheet("color: #FFFFFF;")
        self.content_layout.addWidget(self.desktop_shortcut_checkbox)

        self.start_menu_shortcut_checkbox = QCheckBox("Add shortcut to Start Menu (Optional)")
        self.start_menu_shortcut_checkbox.setChecked(True)
        self.start_menu_shortcut_checkbox.setStyleSheet("color: #FFFFFF;")
        self.content_layout.addWidget(self.start_menu_shortcut_checkbox)

        self.content_layout.addStretch()
        
        install_button = QPushButton("Install")
        install_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px;")
        install_button.clicked.connect(self.accept);
        self.content_layout.addWidget(install_button)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Installation Folder", self.path_edit.text())
        if folder:
            self.path_edit.setText(folder)

    def select_riot_games_folder(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select RiotClientServices.exe", "", "RiotClientServices.exe (RiotClientServices.exe)")
        if file_path:
            if os.path.basename(file_path).lower() == "riotclientservices.exe":
                self.riot_path_edit.setText(file_path)
                self.riot_path_warning_label.setText("")
            else:
                self.riot_path_warning_label.setText("Please select 'RiotClientServices.exe'.")
                self.riot_path_edit.setText("")

    def get_install_path(self):
        return self.path_edit.text()

    def get_riot_games_path(self):
        return self.riot_path_edit.text()

    def should_add_desktop_shortcut(self):
        return self.desktop_shortcut_checkbox.isChecked()

    def should_add_start_menu_shortcut(self):
        return self.start_menu_shortcut_checkbox.isChecked()
