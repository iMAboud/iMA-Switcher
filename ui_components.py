import logging
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
    QFormLayout,
    QDoubleSpinBox,
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
    QPointF,
    pyqtProperty,
)


def get_asset_path(filename):
    return os.path.join(os.path.dirname(__file__), "Assets", filename)

def get_icon_path(filename):
    return os.path.join(os.path.dirname(__file__), "icons", filename)

def get_icon_paths_from_folder(folder_path):
    """
    Retrieves all image file paths from the specified folder.
    """
    icon_paths = []
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.ico')):
                icon_paths.append(file_path)
    return icon_paths


class LaunchNotificationWidget(QWidget):
    def __init__(self, account_name, icon_pixmap, in_game_name=None, in_game_tag=None, rank=None, use_rank_icons=False, parent=None, standalone=False, switcher_instance=None):
        super().__init__(parent)
        self.switcher_instance = switcher_instance
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool | Qt.CustomizeWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground); self.setAttribute(Qt.WA_DeleteOnClose)
        self.setup_ui(account_name, icon_pixmap, in_game_name, in_game_tag, rank, use_rank_icons)
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

    def setup_ui(self, name, pixmap, in_game_name, in_game_tag, rank, use_rank_icons):
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
        
        name_layout = QHBoxLayout()
        name_layout.setAlignment(Qt.AlignCenter)

        # Rank icon next to name
        if rank and not use_rank_icons: # Only show if not already using rank icon as main icon
            rank_icon_path = get_asset_path(f"{rank.lower().replace(" ", "_")}.png")
            if os.path.exists(rank_icon_path):
                rank_pixmap = self.switcher_instance.get_qicon_from_path(rank_icon_path).pixmap(24, 24)
                rank_label = QLabel(self)
                rank_label.setPixmap(rank_pixmap)
                name_layout.addWidget(rank_label)

        name_label = QLabel(name, self)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold; text-align: center;")
        name_layout.addWidget(name_label)
        layout.addLayout(name_layout)

        if in_game_name and in_game_tag:
            in_game_label = QLabel(f"{in_game_name}#{in_game_tag}", self)
            in_game_label.setAlignment(Qt.AlignCenter)
            in_game_label.setStyleSheet("color: #b0a8a8; font-size: 16px; text-align: center;")
            layout.addWidget(in_game_label)
        elif in_game_name:
            in_game_label = QLabel(in_game_name, self)
            in_game_label.setAlignment(Qt.AlignCenter)
            in_game_label.setStyleSheet("color: #b0a8a8; font-size: 16px; text-align: center;")
            layout.addWidget(in_game_label)

    def center_on_screen(self):
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())

class ValueSlider(QWidget):
    valueChanged = pyqtSignal(float)

    def __init__(self, min_val, max_val, step=0.1, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        self.scale_factor = 100 # To handle floats with 2 decimal places
        self.min_val_scaled = int(min_val * self.scale_factor)
        self.max_val_scaled = int(max_val * self.scale_factor)
        self.step_scaled = int(step * self.scale_factor)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(self.min_val_scaled, self.max_val_scaled)
        self.slider.setSingleStep(self.step_scaled)
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

        self.spin_box = QDoubleSpinBox() # Use QDoubleSpinBox for float values
        self.spin_box.setRange(min_val, max_val)
        self.spin_box.setSingleStep(step)
        self.spin_box.setDecimals(1) # Display one decimal place
        self.spin_box.setFixedWidth(60)
        self.spin_box.setAlignment(Qt.AlignCenter)
        self.spin_box.setStyleSheet("""
            QDoubleSpinBox { background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 5px; color: #e0d6d1; font-weight: bold; }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button { width: 0px; border: none; background: transparent; }
        """)

        layout.addWidget(self.slider)
        layout.addWidget(self.spin_box)

        self.slider.valueChanged.connect(lambda val: self.spin_box.setValue(val / self.scale_factor))
        self.spin_box.valueChanged.connect(lambda val: self.slider.setValue(int(val * self.scale_factor)))
        self.slider.valueChanged.connect(lambda val: self.valueChanged.emit(val / self.scale_factor))

    def value(self):
        return self.slider.value() / self.scale_factor

    def setValue(self, value):
        self.slider.setValue(int(value * self.scale_factor))

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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

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
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        export_button = QPushButton("Export")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        export_button.clicked.connect(self.accept)
        button_layout.addWidget(export_button)
        
        button_layout.addStretch()
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
        item = QListWidgetItem(name); item.setIcon(self.parent().switcher.get_qicon_from_path(icon_path or "")); self.accounts_list.addItem(item)

    def select_icon(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon Files (*.ico *.png)")
        if path: self.menu_icon_path = path; self.icon_path_edit.setText(path)

    def get_settings(self):
        return {"title": self.title_edit.text(), "menu_icon_path": self.menu_icon_path, "ordered_accounts": [self.accounts_list.item(i).text() for i in range(self.accounts_list.count())]}

class PopupDialog(QDialog):
    def __init__(self, title, parent):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground)

        
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
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        ok_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

class InputDialog(PopupDialog):
    def __init__(self, title, prompt, default_text="", in_game_name_default="", in_game_tag_default="", parent=None):
        super().__init__(title, parent)
        
        self.in_game_name_edit = None
        self.in_game_tag_edit = None

        prompt_label = QLabel(prompt)
        prompt_label.setStyleSheet("color: #e0d6d1;")
        self.content_layout.addWidget(prompt_label)
        
        self.input_field = QLineEdit(default_text)
        self.input_field.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.input_field)

        if in_game_name_default is not None or in_game_tag_default is not None:
            self.content_layout.addWidget(QLabel("In-game Name and Tag (optional):"))
            in_game_name_tag_layout = QHBoxLayout()
            in_game_name_tag_layout.setContentsMargins(0,0,0,0)
            in_game_name_tag_layout.setSpacing(5)

            self.in_game_name_edit = QLineEdit(in_game_name_default)
            self.in_game_name_edit.setPlaceholderText("In-game Name")
            self.in_game_name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
            in_game_name_tag_layout.addWidget(self.in_game_name_edit)
            
            in_game_name_tag_layout.addWidget(QLabel("#"))

            self.in_game_tag_edit = QLineEdit(in_game_tag_default)
            self.in_game_tag_edit.setPlaceholderText("Tag")
            self.in_game_tag_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
            in_game_name_tag_layout.addWidget(self.in_game_tag_edit)
            self.content_layout.addLayout(in_game_name_tag_layout)
            self.setFixedSize(350, 250) # Adjust size for two inputs
        else:
            self.setFixedSize(350, 180) # Original size for one input
        
        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        save_button.clicked.connect(self.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

    def get_text(self):
        if self.in_game_name_edit and self.in_game_tag_edit:
            return self.input_field.text().strip(), self.in_game_name_edit.text().strip(), self.in_game_tag_edit.text().strip()
        return self.input_field.text().strip()

class SaveAccountDialog(PopupDialog):
    def __init__(self, parent=None, switcher_instance=None):
        super().__init__("Save Account", parent)
        self.setFixedSize(380, 300)
        self.switcher_instance = switcher_instance

        name_label = QLabel("Enter a name for the current account:")
        name_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        name_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        self.content_layout.addWidget(self.name_edit)

        self.content_layout.addWidget(QLabel("Enter in-game name and tag (optional):"))
        in_game_name_tag_layout = QHBoxLayout()
        in_game_name_tag_layout.setContentsMargins(0,0,0,0)
        in_game_name_tag_layout.setSpacing(5)

        self.in_game_name_edit = QLineEdit()
        self.in_game_name_edit.setPlaceholderText("In-game Name")
        self.in_game_name_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        in_game_name_tag_layout.addWidget(self.in_game_name_edit)
        
        in_game_name_tag_layout.addWidget(QLabel("#"))

        self.in_game_tag_edit = QLineEdit()
        self.in_game_tag_edit.setPlaceholderText("Tag")
        self.in_game_tag_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 10px; color: #e0d6d1;")
        in_game_name_tag_layout.addWidget(self.in_game_tag_edit)
        self.content_layout.addLayout(in_game_name_tag_layout)

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
            QComboBox::down-arrow { image: none; /* Can add a custom arrow icon here */ }
            QComboBox QAbstractItemView { 
                background-color: #3a3637; 
                border: 1px solid #c89f68; 
                selection-background-color: #c89f68;
                color: #e0d6d1;
                selection-color: #2c2a2b;
                padding: 5px;
            }
        """)
        
        valorant_icon_path = get_asset_path("valorant.png")
        lol_icon_path = get_asset_path("lol.png")

        if os.path.exists(valorant_icon_path):
            self.game_combo.addItem(self.switcher_instance.get_qicon_from_path(valorant_icon_path), "Valorant", "valorant")
        else:
            self.game_combo.addItem("Valorant", "valorant")

        if os.path.exists(lol_icon_path):
            self.game_combo.addItem(self.switcher_instance.get_qicon_from_path(lol_icon_path), "League of Legends", "lol")
        else:
            self.game_combo.addItem("League of Legends", "lol")

        riot_icon_path = get_asset_path("Riot.png")
        if os.path.exists(riot_icon_path):
            self.game_combo.addItem(self.switcher_instance.get_qicon_from_path(riot_icon_path), "Both", "both")
        else:
            self.game_combo.addItem("Both", "both")
            
        self.content_layout.addWidget(self.game_combo)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

    def get_details(self):
        return self.name_edit.text().strip(), self.game_combo.currentData(), self.in_game_name_edit.text().strip(), self.in_game_tag_edit.text().strip()

class SettingsDialog(PopupDialog):
    def __init__(self, actions, parent):
        super().__init__("Settings", parent)
        # Removed the global stylesheet for QPushButton to avoid interfering with CustomTitleBar
        self.content_layout.setSpacing(10)
        button_style = """QPushButton { background-color: #c89f68; color: #2c2a2b; font-size: 15px; font-weight: bold; border: none; border-radius: 12px; padding: 8px 15px; text-align: left; } QPushButton:hover { background-color: #d9b68b; } QPushButton::icon { width: 24px; height: 24px; } """
        for text, (action_func, icon_name) in actions.items():
            icon_path = get_asset_path(icon_name)
            button = QPushButton(text)
            button.setStyleSheet(button_style) # Apply style directly to each button
            if os.path.exists(icon_path):
                button.setIcon(QIcon(icon_path))
            button.clicked.connect(lambda _, func=action_func: (self.close(), func()))
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
            QLabel { color: #e0d6d1; font-weight: normal; }
            QGroupBox {
                color: #FFFFFF; /* This is for the content of the groupbox, not the title */
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #c89f68; /* Coffee colored border */
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                color: #FFFFFF; /* Explicitly white for the title */
            }
        """)

        self.content_layout.setSpacing(10)
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #4f4a4b; border-top: 1px solid #4f4a4b; border-radius: 8px; }
            QTabBar::tab { 
                background-color: #3a3637; color: #e0d6d1; padding: 8px 12px; font-weight: bold;
                border: 1px solid #4f4a4b; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px;
            }
            QTabBar::tab:hover { background-color: #4f4a4b; }
            QTabBar::tab:selected { background-color: #c89f68; color: #2c2a2b; }
        """)
        self.content_layout.addWidget(self.tab_widget)

        self.setup_ui_tab()
        self.setup_account_tab()
        self.setup_graphics_tab()
        self.setup_audio_tab()
        self.setup_advanced_tab()

        self.original_tab_icons = []
        for i in range(self.tab_widget.count()):
            self.original_tab_icons.append(self.tab_widget.tabIcon(i))

        self.tab_widget.setIconSize(QSize(32, 32))
        self.hovered_tab_index = -1
        self.tab_widget.tabBar().setMouseTracking(True)
        self.tab_widget.tabBar().installEventFilter(self)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #e0d6d1; font-size: 12px; padding-top: 5px;")
        self.content_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        apply_button = QPushButton("Apply")
        apply_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        apply_button.clicked.connect(self.apply_settings)
        button_layout.addWidget(apply_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

        self.load_current_settings()

    def setup_account_tab(self):
        account_tab = QWidget()
        main_layout = QVBoxLayout(account_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        rank_update_group = QGroupBox("Rank Update Settings")
        rank_update_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #c89f68;
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                color: #FFFFFF;
            }
        """)
        rank_update_layout = QGridLayout(rank_update_group)
        rank_update_layout.setSpacing(10)

        self.auto_rank_update_toggle = RadioButtonGroup("On", "Off")
        rank_update_layout.addWidget(QLabel("Auto Rank Update:"), 0, 0)
        rank_update_layout.addWidget(self.auto_rank_update_toggle, 0, 1)

        rank_update_layout.addWidget(QLabel("Rank Check Region:"), 1, 0)
        self.rank_check_region_combo = QComboBox()
        self.rank_check_region_combo.addItem("Europe (eu)", "eu")
        self.rank_check_region_combo.addItem("North America (na)", "na")
        self.rank_check_region_combo.addItem("Asia Pacific (ap)", "ap")
        self.rank_check_region_combo.addItem("Brazil (br)", "br")
        self.rank_check_region_combo.addItem("Korea (kr)", "kr")
        self.rank_check_region_combo.addItem("Latin America (latam)", "latam")
        self.rank_check_region_combo.setStyleSheet("""
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
        rank_update_layout.addWidget(self.rank_check_region_combo, 1, 1)
        main_layout.addWidget(rank_update_group)

        main_layout.addStretch()
        self.tab_widget.addTab(account_tab, QIcon(get_asset_path("Settings.png")), "Account")

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
        self.tab_widget.addTab(graphics_tab, QIcon(get_asset_path("Graphics.png")), "Graphics")

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
        self.tab_widget.addTab(audio_tab, QIcon(get_asset_path("Audio.png")), "Audio")

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
        self.tab_widget.addTab(advanced_tab, QIcon(get_asset_path("Advanced.png")), "Advanced")

    def setup_ui_tab(self):
        ui_tab = QWidget()
        main_layout = QVBoxLayout(ui_tab)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignTop)

        # Top Group (Show in UI)
        top_group = QGroupBox("Show in UI")
        top_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #c89f68; /* Coffee colored border */
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                color: #FFFFFF; /* Explicitly white for the title */
            }
        """)
        top_layout = QGridLayout(top_group)
        top_layout.setSpacing(10)

        self.show_game_icons_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Game Icon:"), 0, 0)
        top_layout.addWidget(self.show_game_icons_toggle, 0, 1)

        self.show_rank_icon_left_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Rank Icon:"), 1, 0)
        top_layout.addWidget(self.show_rank_icon_left_toggle, 1, 1)

        self.show_name_tag_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Name#Tag:"), 2, 0)
        top_layout.addWidget(self.show_name_tag_toggle, 2, 1)

        self.show_current_rr_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Current RR:"), 3, 0)
        top_layout.addWidget(self.show_current_rr_toggle, 3, 1)

        self.show_last_game_rr_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Last Game's RR:"), 4, 0)
        top_layout.addWidget(self.show_last_game_rr_toggle, 4, 1)
        
        self.use_rank_icons_toggle = RadioButtonGroup("On", "Off")
        top_layout.addWidget(QLabel("Use Rank for Account Icon:"), 5, 0)
        top_layout.addWidget(self.use_rank_icons_toggle, 5, 1)

        # Bottom Group (Menu & Rank Settings)
        bottom_group = QGroupBox("Menu & Rank Settings")
        bottom_group.setStyleSheet("""
            QGroupBox {
                color: #FFFFFF;
                font-size: 14px;
                font-weight: bold;
                border: 1px solid #c89f68; /* Coffee colored border */
                border-radius: 8px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 10px;
                left: 10px;
                color: #FFFFFF; /* Explicitly white for the title */
            }
        """)
        bottom_layout = QGridLayout(bottom_group)
        bottom_layout.setSpacing(10)

        self.show_rank_tips_toggle = RadioButtonGroup("On", "Off")
        bottom_layout.addWidget(QLabel("Show Rank Tips (iMA Menu):"), 0, 0)
        bottom_layout.addWidget(self.show_rank_tips_toggle, 0, 1)

        self.tip_delay_slider = ValueSlider(0.0, 2.0, 0.1)
        bottom_layout.addWidget(QLabel("Tip Delay (seconds):"), 1, 0)
        bottom_layout.addWidget(self.tip_delay_slider, 1, 1)

        bottom_layout.addWidget(QLabel("Grid Size (Columns):"), 2, 0)
        self.grid_size_combo = QComboBox()
        self.grid_size_combo.addItems(["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"])
        self.grid_size_combo.setStyleSheet("""
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
        bottom_layout.addWidget(self.grid_size_combo, 2, 1)

        main_layout.addWidget(top_group)
        main_layout.addWidget(bottom_group)
        
        main_layout.addStretch()

        self.tab_widget.setIconSize(QSize(32, 32))
        self.tab_widget.addTab(ui_tab, QIcon(get_asset_path("app_icon.png")), "UI")

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    def on_tab_changed(self, index):
        # When the tab is changed by clicking, restore all icons to their original state
        for i in range(self.tab_widget.count()):
            if self.original_tab_icons and i < len(self.original_tab_icons):
                 self.tab_widget.setTabIcon(i, self.original_tab_icons[i])

    def set_all_qualities(self, value):
        for spin_box in self.spin_boxes.values():
            spin_box.setValue(value)

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
            "show_game_icons": self.show_game_icons_toggle.get_state(),
            "show_rank_tips": self.show_rank_tips_toggle.get_state(),
            "tip_delay": self.tip_delay_slider.value(),
            "use_rank_icons": self.use_rank_icons_toggle.get_state(),
            "show_rank_icon_left": self.show_rank_icon_left_toggle.get_state(),
            "show_name_tag": self.show_name_tag_toggle.get_state(),
            "show_current_rr": self.show_current_rr_toggle.get_state(),
            "show_last_game_rr": self.show_last_game_rr_toggle.get_state(),
            "rank_check_region": self.rank_check_region_combo.currentData(),
            "auto_rank_update": self.auto_rank_update_toggle.get_state(),
            "grid_size": int(self.grid_size_combo.currentText()),
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
        self.switcher.update_ima_menu_if_enabled('update', None)
        
        ima_config = self.switcher.get_ima_config()
        if ima_config.get("output_dir"):
            try:
                self.switcher.generate_ima_menu_script(
                    output_dir=ima_config["output_dir"],
                    title=ima_config["title"],
                    ordered_accounts=ima_config["ordered_accounts"],
                    menu_icon_path=ima_config.get("menu_icon_path", ""),
                    save_config=False
                )
                print("iMA menu script updated due to UI settings change.")
            except Exception as e:
                print(f"Error updating iMA menu script from OptionsDialog: {e}")

        if success:
            self.status_label.setText("Settings applied successfully to all accounts.")
            self.settings_applied.emit()
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
                    if value_str.upper() == 'MAX':
                        control.setValue(100)
                    else:
                        control.setValue(float(value_str) * 100)
                elif key.startswith("EAresIntSettingName::"):
                    control.setValue(int(float(value_str)))
                elif key.startswith("EAresBoolSettingName::"):
                    control.set_state(value_str.lower() == 'true')
        
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        self.show_game_icons_toggle.set_state(ui_settings.get("show_game_icons", True))
        self.show_rank_tips_toggle.set_state(ui_settings.get("show_rank_tips", False))
        self.tip_delay_slider.setValue(ui_settings.get("tip_delay", 1.0))
        self.use_rank_icons_toggle.set_state(ui_settings.get("use_rank_icons", False))
        self.show_rank_icon_left_toggle.set_state(ui_settings.get("show_rank_icon_left", False))
        self.show_name_tag_toggle.set_state(ui_settings.get("show_name_tag", True))
        self.show_current_rr_toggle.set_state(ui_settings.get("show_current_rr", True))
        self.show_last_game_rr_toggle.set_state(ui_settings.get("show_last_game_rr", True))
        self.grid_size_combo.setCurrentText(str(ui_settings.get("grid_size", 4)))
        

        # Account tab settings
        self.auto_rank_update_toggle.set_state(ui_settings.get("auto_rank_update", True))
        saved_region = ui_settings.get("rank_check_region", "eu")
        index = self.rank_check_region_combo.findData(saved_region)
        if index == -1:
            index = self.rank_check_region_combo.findText(saved_region)
        if index != -1:
            self.rank_check_region_combo.setCurrentIndex(index)
        
        self.status_label.setText("Loaded saved settings.")

class CustomTitleBar(QWidget):
    def __init__(self, title, parent, is_dialog=False):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)

        if is_dialog:
            self.setStyleSheet(
"""
background-color: #2c2a2b;
border-top-left-radius: 15px;
border-top-right-radius: 15px;
border-bottom: 1px solid #4f4a4b;
"""
)
        else:
            self.setStyleSheet("background-color: #2c2a2b; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 0, 5, 0)
        layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; background: transparent;")
        layout.addWidget(title_label)

        if not is_dialog:
            refresh_icon_path = get_asset_path("Refresh.png")
            self.refresh_button = QPushButton(QIcon(refresh_icon_path), "")
            self.refresh_button.setFixedSize(QSize(30, 30))
            self.refresh_button.setIconSize(QSize(20, 20))
            self.refresh_button.setStyleSheet("""QPushButton { background-color: #4f4a4b; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }""")
            layout.addWidget(self.refresh_button)

        layout.addStretch() # This stretch should be before minimize and close

        if not is_dialog: # Minimize button only for main app
            self.minimize_button = QPushButton("−")
            self.minimize_button.setFixedSize(QSize(30, 30))
            self.minimize_button.setStyleSheet("""QPushButton { background-color: #4f4a4b; color: #e0d6d1; font-size: 20px; font-weight: bold; border: none; border-radius: 15px; } QPushButton:hover { background-color: #c89f68; }""")
            self.minimize_button.clicked.connect(self.parent_window.showMinimized)
            layout.addWidget(self.minimize_button)
        
        # Removed close button from CustomTitleBar as it's handled by window flags
        # close_button = QPushButton("✕")
        # close_button.setFixedSize(QSize(30, 30))
        # close_button.clicked.connect(self.parent_window.close)
        # close_button.setStyleSheet("QPushButton { background-color: #f38ba8; color: #ffffff; font-size: 18px; font-weight: bold; border: none; border-radius: 15px; } QPushButton:hover { background-color: #e67e80; }")
        # layout.addWidget(close_button)
        
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

    def __init__(self, account_name, account_icon_pixmap, parent=None, switcher_instance=None):
        super().__init__("Select Game", parent)
        self.setFixedSize(400, 450)
        self.account_name = account_name
        self.account_icon_pixmap = account_icon_pixmap
        self.switcher_instance = switcher_instance
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)

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
        """
)
        button.clicked.connect(lambda: self._set_selected_game_and_accept(game_id))

        layout = QVBoxLayout(button)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        icon_path = get_asset_path(icon_filename)
        logging.debug(f"_create_game_button - icon_path: {icon_path}, exists: {os.path.exists(icon_path)}")
        if self.switcher_instance and os.path.exists(icon_path):
            icon_label = QLabel()
            pixmap = self.switcher_instance.get_qicon_from_path(icon_path).pixmap(80, 80).scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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

class IconPickerDialog(PopupDialog):
    def __init__(self, switcher_instance, current_icon_path, parent=None):
        super().__init__("Change Icon", parent)
        self.switcher = switcher_instance
        self.selected_icon_path = current_icon_path
        self.setFixedSize(420, 550)

        # --- Main Layout and Styling ---
        self.content_layout.setSpacing(15)
        self.content_layout.setAlignment(Qt.AlignTop)
        self.main_widget.setStyleSheet("""#popup_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #4f4a4b; }
            QLabel { color: #e0d6d1; font-weight: bold; }
            QScrollArea { background-color: #3a3637; border: 1px solid #4f4a4b; border-radius: 10px; }""")

        # --- Icon Preview Section ---
        preview_container = QWidget()
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setAlignment(Qt.AlignCenter)
        preview_layout.setContentsMargins(0, 10, 0, 10)

        self.icon_display_widget = QWidget()
        self.icon_display_widget.setFixedSize(130, 130)

        # The preview button is a child of the display widget, positioned manually
        self.icon_preview_button = QPushButton(self.icon_display_widget)
        self.icon_preview_button.setFixedSize(120, 120)
        self.icon_preview_button.move(5, 5)  # Centered (130-120)/2
        self.icon_preview_button.clicked.connect(self.select_icon_from_device)

        # The remove button is also a child, moved to the corner and raised
        self.remove_button = QPushButton("✕", self.icon_display_widget)
        self.remove_button.setFixedSize(24, 24)
        self.remove_button.setStyleSheet("""QPushButton { background-color: #f38ba8; color: white; font-size: 14px; font-weight: bold; border-radius: 12px; border: 1px solid transparent; }
            QPushButton:hover { background-color: #e67e80; border-color: white; }""")
        self.remove_button.clicked.connect(self.remove_icon)
        self.remove_button.move(5, 5)  # Top-left corner
        self.remove_button.raise_()

        preview_layout.addWidget(self.icon_display_widget)
        self.content_layout.addWidget(preview_container)

        # --- Icons Grid Section ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        grid_container = QWidget()
        grid_container.setStyleSheet("background-color: #3a3637;")
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setContentsMargins(15, 15, 15, 15)
        scroll_area.setWidget(grid_container)
        
        self.content_layout.addWidget(scroll_area)

        # --- Buttons Section ---
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        button_layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setStyleSheet("""QPushButton { background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b;}
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }""")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("""QPushButton { background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px; }
            QPushButton:hover { background-color: #d9b68b; }""")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

        self.update_preview()
        
        QTimer.singleShot(50, self.populate_icon_grid)

    def populate_icon_grid(self):
        icons_path = os.path.join(self.switcher.base_dir, "icons")
        icon_files = get_icon_paths_from_folder(icons_path)
        
        for i, icon_path in enumerate(icon_files):
            row, col = i // 4, i % 4
            icon_widget = self.create_grid_icon(icon_path)
            self.grid_layout.addWidget(icon_widget, row, col, Qt.AlignCenter)

    def create_grid_icon(self, icon_path):
        icon_button = QPushButton()
        icon_button.setFixedSize(70, 70)
        
        icon = self.switcher.get_qicon_from_path(icon_path)
        pixmap = icon.pixmap(icon.actualSize(QSize(256, 256)))
        
        scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        circular_pixmap = QPixmap(60, 60)
        circular_pixmap.fill(Qt.transparent)
        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addEllipse(0, 0, 60, 60)
        painter.setClipPath(path)
        
        x = (60 - scaled_pixmap.width()) / 2
        y = (60 - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        painter.end()

        icon_button.setIcon(QIcon(circular_pixmap))
        icon_button.setIconSize(QSize(60, 60))
        icon_button.setStyleSheet("QPushButton { border: 2px solid transparent; border-radius: 35px; } QPushButton:hover { border-color: #c89f68; }")
        icon_button.clicked.connect(lambda: self.set_selected_icon(icon_path))
        return icon_button

    def update_preview(self):
        size = 120
        if self.selected_icon_path and os.path.exists(self.selected_icon_path):
            icon = self.switcher.get_qicon_from_path(self.selected_icon_path)
            pixmap = icon.pixmap(icon.actualSize(QSize(256, 256)))
            scaled_pixmap = pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            circular_pixmap = QPixmap(size, size)
            circular_pixmap.fill(Qt.transparent)
            painter = QPainter(circular_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            path = QPainterPath()
            path.addEllipse(0, 0, size, size)
            painter.setClipPath(path)
            x = (size - scaled_pixmap.width()) / 2
            y = (size - scaled_pixmap.height()) / 2
            painter.drawPixmap(int(x), int(y), scaled_pixmap)
            painter.end()

            self.icon_preview_button.setIcon(QIcon(circular_pixmap))
            self.icon_preview_button.setText("")
            self.icon_preview_button.setIconSize(QSize(size, size))
            self.icon_preview_button.setStyleSheet("""QPushButton { border: 2px solid transparent; border-radius: 60px; }
                QPushButton:hover { border-color: #d9b68b; }""")
            self.remove_button.setVisible(True)
        else:
            self.icon_preview_button.setIcon(QIcon())
            self.icon_preview_button.setText("+")
            self.icon_preview_button.setStyleSheet("""QPushButton {
                    border: 2px dashed #c89f68;
                    border-radius: 60px;
                    color: #e0d6d1;
                    font-size: 48px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    border-color: #d9b68b;
                    color: #d9b68b;
                }""")
            self.remove_button.setVisible(False)

    def set_selected_icon(self, path):
        self.selected_icon_path = path
        self.update_preview()

    def select_icon_from_device(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Images (*.png *.jpg *.jpeg *.ico)")
        if path:
            self.set_selected_icon(path)

    def remove_icon(self):
        self.selected_icon_path = None
        self.update_preview()

    def get_selected_icon_path(self):
        return self.selected_icon_path


class RiotClientNotFoundDialog(PopupDialog):
    def __init__(self, parent=None):
        super().__init__("Riot Client Not Found", parent)
        self.setFixedSize(400, 250)
        
        message_label = QLabel("Could not find RiotClientServices.exe.\nPlease locate it manually.")
        message_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Path to RiotClientServices.exe")
        self.path_edit.setStyleSheet("background-color: #4a4647; border: 1px solid #c89f68; border-radius: 8px; padding: 8px; color: #e0d6d1;")
        self.content_layout.addWidget(self.path_edit)

        button_layout = QHBoxLayout()
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        browse_button.clicked.connect(self.browse)
        button_layout.addWidget(browse_button)

        save_button = QPushButton("Save")
        save_button.setStyleSheet("background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 8px;")
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        self.content_layout.addLayout(button_layout)

    def browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select RiotClientServices.exe", "", "Executable Files (*.exe)")
        if path:
            self.path_edit.setText(path)

    def get_path(self):
        return self.path_edit.text()

class ConfirmDeleteDialog(PopupDialog):
    def __init__(self, account_name, parent=None, title="Confirm Delete", message=None):
        super().__init__(title, parent)
        self.setFixedSize(350, 180)
        
        if message is None:
            message = f"Delete '{account_name}'?"

        message_label = QLabel(message)
        message_label.setStyleSheet("color: #e0d6d1; font-size: 16px; font-weight: bold; text-align: center;")
        message_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(message_label)
        
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15) # Increased spacing between buttons
        button_layout.addStretch()

        no_button = QPushButton("No")
        no_button.setStyleSheet("""
            QPushButton {
                background-color: #4f4a4b; color: #e0d6d1; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px; border: 1px solid #4f4a4b; /* Increased padding */
            }
            QPushButton:hover { background-color: #5a5556; border: 1px solid #c89f68; }
            QPushButton:pressed { background-color: #454142; }
        """
)
        no_button.clicked.connect(self.reject)
        button_layout.addWidget(no_button)

        yes_button = QPushButton("Yes")
        yes_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """
)
        yes_button.clicked.connect(self.accept)
        button_layout.addWidget(yes_button)
        
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

class AccountWidget(QWidget):
    selected = pyqtSignal(str)
    double_clicked = pyqtSignal(str)
    context_menu_requested = pyqtSignal(str, QPoint)

    def __init__(self, account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, parent=None, is_add_button=False, switcher_instance=None):
        super().__init__(parent)
        self.account_name = account_name
        self.game = game
        self.rank = rank
        self.in_game_name = in_game_name
        self.in_game_tag = in_game_tag
        self.current_rr = current_rr
        self.last_game_rr = last_game_rr
        self.setObjectName("AccountWidget")
        self.setFixedSize(120, 140)
        self.is_selected, self.is_hovered = False, False
        self.is_add_button = is_add_button
        self.icon = icon  # Store the icon
        self.setStyleSheet("""QWidget#AccountWidget { background-color: #3a3637; border-radius: 15px; border: 3px solid transparent; } 
                              QWidget#AccountWidget[selected="true"] { border-color: #c89f68; } 
                              QLabel#NameLabel { color: #e0d6d1; font-size: 13px; font-weight: bold; } 
                              QWidget#AccountWidget[selected="true"] QLabel#NameLabel { color: #c89f68; } 
                              QWidget#AccountWidget[is_add_button="true"] { background-color: #4f4a4b; border: 3px dashed #c89f68; } 
                              QWidget#AccountWidget[is_add_button="true"]:hover { background-color: #5a5556; } 
                              QWidget#AccountWidget[is_add_button="true"] QLabel#NameLabel { color: #c89f68; }""")
        self.init_ui(icon)

        self.icon_anim = QPropertyAnimation(self, b"iconSize")
        self.icon_anim.setDuration(150)
        self.icon_anim.setEasingCurve(QEasingCurve.OutQuad)

    def _get_icon_size(self):
        return self.icon_label.size()

    def _set_icon_size(self, size):
        self.set_icon(self.icon, size.width())

    iconSize = pyqtProperty(QSize, _get_icon_size, _set_icon_size)

    def init_ui(self, icon):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(0)
        self.main_layout.setAlignment(Qt.AlignCenter)

        self.current_rr_label = QLabel(self)
        self.current_rr_label.setAlignment(Qt.AlignCenter)
        self.current_rr_label.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        self.main_layout.addWidget(self.current_rr_label)

        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.set_icon(icon, 70)
        self.main_layout.addWidget(self.icon_label)

        self.name_label = QLabel(self.account_name, self, objectName="NameLabel")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.name_label)

        self.in_game_name_tag_label = QLabel(self)
        self.in_game_name_tag_label.setAlignment(Qt.AlignCenter)
        self.in_game_name_tag_label.setStyleSheet("color: #b0a8a8; font-size: 11px;")
        self.main_layout.addWidget(self.in_game_name_tag_label)

        self.last_game_rr_label = QLabel(self)
        self.last_game_rr_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.last_game_rr_label)
        
        if self.is_add_button:
            self.setProperty("is_add_button", "true")
            self.name_label.setStyleSheet("color: #c89f68; font-size: 16px; font-weight: bold;")
            self.icon_label.setStyleSheet("color: #c89f68;")
            self.in_game_name_tag_label.setVisible(False)
            self.current_rr_label.setVisible(False)
            self.last_game_rr_label.setVisible(False)
        else:
            self.game_icon_label = QLabel(self)
            game_icon_size = 24
            self.game_icon_label.setFixedSize(game_icon_size, game_icon_size)
            self.game_icon_label.setAlignment(Qt.AlignCenter)
            self.game_icon_label.move(self.width() - game_icon_size - 10, 10) # Top right
            
            valorant_icon_path = get_asset_path("valorant.png")
            lol_icon_path = get_asset_path("lol.png")
            riot_icon_path = get_asset_path("Riot.png")

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

            self.rank_icon_label = QLabel(self)
            self.rank_icon_label.setFixedSize(game_icon_size, game_icon_size)
            self.rank_icon_label.setAlignment(Qt.AlignCenter)
            self.rank_icon_label.move(10, 10) # Top left
            self.rank_icon_label.setVisible(False) # Hide by default

            if self.rank:
                rank_icon_path = get_asset_path(f"{self.rank.lower().replace(" ", "_")}.png")
                if os.path.exists(rank_icon_path):
                    pixmap = QPixmap(rank_icon_path).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.rank_icon_label.setPixmap(pixmap)

        self.update_content() # Initial content update

    def update_content(self):
        # Update RR labels
        if self.current_rr is not None:
            self.current_rr_label.setText(str(self.current_rr))
        else:
            self.current_rr_label.setText("")

        if self.last_game_rr is not None:
            rr_text = f"+{self.last_game_rr}" if self.last_game_rr > 0 else str(self.last_game_rr)
            rr_color = "#a6e3a1" if self.last_game_rr > 0 else ("#f38ba8" if self.last_game_rr < 0 else "#e0d6d1")
            self.last_game_rr_label.setText(f"({rr_text})")
            self.last_game_rr_label.setStyleSheet(f"color: {rr_color}; font-size: 11px;")
        else:
            self.last_game_rr_label.setText("")

        # Update in-game name/tag label
        in_game_text = ""
        if self.in_game_name and self.in_game_tag:
            in_game_text = f"{self.in_game_name}#{self.in_game_tag}"
        elif self.in_game_name:
            in_game_text = self.in_game_name
        self.in_game_name_tag_label.setText(in_game_text)

        self.main_layout.invalidate() # Invalidate layout to trigger recalculation
        self.update() # Repaint the widget

    def set_icon(self, icon, size):
        self.icon = icon
        self.icon_label.setFixedSize(QSize(size, size))
        
        # Create a circular pixmap
        circular_pixmap = QPixmap(size, size)
        circular_pixmap.fill(Qt.transparent)

        painter = QPainter(circular_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Define the circular path
        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        # Get the source pixmap and scale it correctly
        source_pixmap = icon.pixmap(icon.actualSize(QSize(256, 256))) # Get a high-res version
        scaled_pixmap = source_pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        # Draw the pixmap centered in the circle
        x = (size - scaled_pixmap.width()) / 2
        y = (size - scaled_pixmap.height()) / 2
        painter.drawPixmap(int(x), int(y), scaled_pixmap)
        painter.end()
        
        self.icon_label.setPixmap(circular_pixmap)

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

    def set_show_rank_icon(self, show): # New method
        if hasattr(self, 'rank_icon_label'):
            self.rank_icon_label.setVisible(show and self.rank is not None)

    def set_show_name_tag(self, show):
        if hasattr(self, 'in_game_name_tag_label'):
            self.in_game_name_tag_label.setVisible(show and bool(self.in_game_name or self.in_game_tag))
            # The parent widget (ModernValorantSwitcher) handles resizing based on content.
            # No need to call setFixedSize here directly.
            if self.parentWidget() and hasattr(self.parentWidget(), 'update_window_size'):
                self.parentWidget().update_window_size()

    def set_show_current_rr(self, show):
        if hasattr(self, 'current_rr_label'):
            self.current_rr_label.setVisible(show and self.current_rr is not None)

    def set_show_last_game_rr(self, show):
        if hasattr(self, 'last_game_rr_label'):
            self.last_game_rr_label.setVisible(show and self.last_game_rr is not None)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.selected.emit(self.account_name)

    def mouseDoubleClickEvent(self, event):
        if self.is_add_button: return
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self.account_name)

    def enterEvent(self, event):
        if not self.is_add_button:
            self.icon_anim.setStartValue(self.icon_label.size())
            self.icon_anim.setEndValue(QSize(80, 80))
            self.icon_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.is_add_button:
            self.icon_anim.setStartValue(self.icon_label.size())
            self.icon_anim.setEndValue(QSize(70, 70))
            self.icon_anim.start()
        super().leaveEvent(event)

    def contextMenuEvent(self, event):
        if self.is_add_button: return
        self.context_menu_requested.emit(self.account_name, self.mapToGlobal(event.pos()))

    def update_data(self, account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, ui_settings): # Added ui_settings parameter
        self.account_name = account_name
        self.game = game
        self.rank = rank
        self.in_game_name = in_game_name
        self.in_game_tag = in_game_tag
        self.current_rr = current_rr
        self.last_game_rr = last_game_rr

        # Redraw the entire widget with new data
        self.set_icon(icon, 70)
        self.name_label.setText(self.account_name)

        # Update visibility based on ui_settings
        self.set_show_game_icon(ui_settings.get("show_game_icons", True))
        self.set_show_rank_icon(ui_settings.get("show_rank_icon_left", False))
        self.set_show_name_tag(ui_settings.get("show_name_tag", True))
        self.set_show_current_rr(ui_settings.get("show_current_rr", True))
        self.set_show_last_game_rr(ui_settings.get("show_last_game_rr", True))

        if self.current_rr is not None:
            self.current_rr_label.setText(str(self.current_rr))
        if self.last_game_rr is not None:
            rr_text = f"+{self.last_game_rr}" if self.last_game_rr > 0 else str(self.last_game_rr)
            rr_color = "#a6e3a1" if self.last_game_rr > 0 else ("#f38ba8" if self.last_game_rr < 0 else "#e0d6d1") # White for 0
            self.last_game_rr_label.setText(f"({rr_text})")
            self.last_game_rr_label.setStyleSheet(f"color: {rr_color}; font-size: 11px;")
        
        # Update rank icon based on new rank data
        game_icon_size = 24 # Assuming this is consistent
        if self.rank:
            rank_icon_path = get_asset_path(f"{self.rank.lower().replace(" ", "_")}.png")
            if os.path.exists(rank_icon_path):
                pixmap = QPixmap(rank_icon_path).scaled(game_icon_size, game_icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.rank_icon_label.setPixmap(pixmap)
            else:
                self.rank_icon_label.clear() # Clear if path doesn't exist
        else:
            self.rank_icon_label.clear() # Clear if no rank

        self.update()

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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window) 
        
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
            self.riot_path_warning_label.setText("Please select 'RiotClientServices.exe'.")

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
        install_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        install_button.clicked.connect(self.accept);
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(install_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)
        
    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Installation Folder")
        if folder_path:
            self.path_edit.setText(folder_path)

    def select_riot_games_folder(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select RiotClientServices.exe", "", "Executable Files (*.exe)")
        if file_path:
            self.riot_path_edit.setText(file_path)
            self.riot_path_warning_label.setText("") # Clear warning if user manually selects

    def find_riot_client_path(self):
        common_paths = [
            os.path.join("C:", os.sep, "Riot Games", "Riot Client", "RiotClientServices.exe"),
            os.path.join(os.getenv('PROGRAMFILES'), "Riot Games", "Riot Client", "RiotClientServices.exe"),
            os.path.join(os.getenv('PROGRAMFILES(X86)'), "Riot Games", "Riot Client", "RiotClientServices.exe"),
        ]
        
        found_path = None
        for path in common_paths:
            if os.path.exists(path):
                found_path = path
                break
        
        if found_path:
            self.riot_path_edit.setText(found_path)
            self.riot_path_warning_label.setText("")
        else:
            self.riot_path_edit.setText("")
            self.riot_path_warning_label.setText("RiotClientServices.exe not found. Please locate it manually.")

    def get_install_path(self):
        return self.path_edit.text()

    def get_riot_games_path(self):
        return self.riot_path_edit.text()

    def should_add_desktop_shortcut(self):
        return self.desktop_shortcut_checkbox.isChecked()

    def should_add_start_menu_shortcut(self):
        return self.start_menu_shortcut_checkbox.isChecked()
        self.desktop_shortcut_checkbox.setChecked(True)
        self.desktop_shortcut_checkbox.setStyleSheet("color: #FFFFFF;")
        self.content_layout.addWidget(self.desktop_shortcut_checkbox)

        self.start_menu_shortcut_checkbox = QCheckBox("Add shortcut to Start Menu (Optional)")
        self.start_menu_shortcut_checkbox.setChecked(True)
        self.start_menu_shortcut_checkbox.setStyleSheet("color: #FFFFFF;")
        self.content_layout.addWidget(self.start_menu_shortcut_checkbox)

        self.content_layout.addStretch()
        
        install_button = QPushButton("Install")
        install_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d9b68b; /* Brighter coffee color */
            }
        """)
        install_button.clicked.connect(self.accept);
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(install_button)
        button_layout.addStretch()
        self.content_layout.addLayout(button_layout)

    



from game_switcher import GameSwitcher

class BackupRestoreDialog(PopupDialog):
    def __init__(self, parent=None, mode=None):
        title = "Backup Profiles" if mode == "backup" else "Restore Profiles"
        super().__init__(title, parent)
        self.setFixedSize(350, 200)
        self.selection = None

        label_text = "Choose backup location:" if mode == "backup" else "Choose restore location:"
        message_label = QLabel(label_text)
        message_label.setAlignment(Qt.AlignCenter)
        message_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        self.content_layout.addWidget(message_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        local_button = QPushButton("Local")
        local_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        local_button.clicked.connect(lambda: self.set_selection("local"))
        button_layout.addWidget(local_button)

        drive_button = QPushButton("Google Drive")
        drive_button.setStyleSheet("""
            QPushButton {
                background-color: #c89f68; color: #2c2a2b; font-weight: bold; 
                border-radius: 8px; padding: 10px 20px;
            }
            QPushButton:hover { background-color: #d9b68b; }
        """)
        drive_button.clicked.connect(lambda: self.set_selection("google_drive"))
        button_layout.addWidget(drive_button)

        self.content_layout.addLayout(button_layout)

    def set_selection(self, selection):
        self.selection = selection
        self.accept()

    def get_selection(self):
        return self.selection
