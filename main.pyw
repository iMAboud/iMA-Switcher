import sys
import os
import math
import ctypes
import shutil 
import subprocess 

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.append(sys._MEIPASS)

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QGridLayout,
    QDesktopWidget,
    QMenu,
    QAction,
    QDialog,
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QColor, QImage
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal

from game_switcher import GameSwitcher
from ui_components import (
    CustomTitleBar,
    AccountWidget,
    HoverButton,
    SettingsDialog,
    LaunchNotificationWidget,
    InstallerDialog, 
    GameSelectionDialog
)
from actions_settings import SettingsActions
from actions_context import ContextActions

def create_shortcut(target_path, shortcut_path):
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.WorkingDirectory = os.path.dirname(target_path)
        shortcut.IconLocation = target_path 
        shortcut.save()
        return True
    except Exception as e:
        print(f"Error creating shortcut {shortcut_path}: {e}")
        return False

try:
    from PIL import Image
except ImportError:
    Image = None
    print("Warning: Pillow not installed. Image conversion for icons will not work. Please install it with 'pip install Pillow'")

def generate_icon(name, path=None):
    """Generates a QIcon from a path or creates a default one with the account's first letter."""
    if path and os.path.exists(path):
        try:
            if Image:
                pil_image = Image.open(path)
                pil_image = pil_image.convert("RGBA")
                from io import BytesIO
                byte_array = BytesIO()
                pil_image.save(byte_array, format="PNG")
                byte_array.seek(0)
                
                pixmap = QPixmap()
                pixmap.loadFromData(byte_array.getvalue(), "PNG")
                return QIcon(pixmap)
            else:
                return QIcon(path)
        except Exception as e:
            print(f"Error loading icon from {path}: {e}. Using default icon.")
    
    pixmap = QPixmap(128, 128)
    pixmap.fill(QColor("#c89f68"))
    p = QPainter(pixmap)
    p.setPen(QColor("#2c2a2b"))
    p.setFont(QFont("Segoe UI", 56, QFont.Bold))
    p.drawText(pixmap.rect(), Qt.AlignCenter, name[0].upper())
    p.end()
    return QIcon(pixmap)

def run_installer():
    app = QApplication(sys.argv)
    dialog = InstallerDialog()
    if dialog.exec_() == QDialog.Accepted:
        install_path = dialog.get_install_path()
        current_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        
        try:
            os.makedirs(install_path, exist_ok=True)
            
            destination_exe_path = os.path.join(install_path, "iMA Switcher.exe")
            shutil.copy2(current_exe, destination_exe_path)

            riot_games_exe_path = dialog.get_riot_games_path()
            switcher_instance = GameSwitcher(base_directory=install_path) 
            if riot_games_exe_path:
                switcher_instance.set_riot_client_paths(riot_games_exe_path)

            if dialog.should_add_desktop_shortcut():
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop_path, "iMA Switcher.lnk")
                create_shortcut(destination_exe_path, shortcut_path)

            if dialog.should_add_start_menu_shortcut():
                start_menu_path = os.path.join(os.getenv("APPDATA"), "Microsoft", "Windows", "Start Menu", "Programs")
                shortcut_path = os.path.join(start_menu_path, "iMA Switcher.lnk")
                create_shortcut(destination_exe_path, shortcut_path)
            
            subprocess.Popen([destination_exe_path])
            sys.exit(0)
            
        except Exception as e:
            QMessageBox.critical(
                None, 
                "Installation Error",
                f"An error occurred during installation:\n{e}"
            )
            sys.exit(1)
    else:
        sys.exit(0) 


class ModernValorantSwitcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.switcher = GameSwitcher()
        self.switcher._ensure_initialized() 
        if not self.switcher.is_admin():
            QMessageBox.critical(
                self,
                "Administrator Rights Required",
                "This application requires administrator privileges for fast account switching.\n\nPlease restart as administrator.",
            )

        self.settings_handler = SettingsActions(self)
        self.context_handler = ContextActions(self)

        self.account_widgets = {}
        self.selected_account_name = None
        self.init_ui()
        self.load_accounts()
        self.center_on_screen()

    def init_ui(self):
        self.setWindowTitle("iMA Switcher")
        self.setWindowIcon(generate_icon("V"))
        self.setStyleSheet(
            """#main_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #4f4a4b; } 
               QScrollArea { border: none; background-color: transparent; } 
               QWidget#grid_container { background-color: transparent; } 
               QMenu { background-color: #3a3637; color: #e0d6d1; border: 1px solid #4f4a4b; border-radius: 8px; } 
               QMenu::item { padding: 8px 20px; border-radius: 5px; } 
               QMenu::item:selected { background-color: #c89f68; color: #2c2a2b; }"""
        )

        self.main_widget = QWidget(objectName="main_widget")
        self.setCentralWidget(self.main_widget)

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar("iMA Switcher", self)
        main_layout.addWidget(self.title_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.addLayout(content_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        content_layout.addWidget(self.scroll_area)

        bottom_layout = QGridLayout()
        content_layout.addLayout(bottom_layout)

        self.status_label = QLabel(
            "Ready", styleSheet="color: #e0d6d1; font-size: 12px; padding-top: 5px;"
        )
        bottom_layout.addWidget(self.status_label, 0, 0, Qt.AlignLeft)

        self.add_account_button = HoverButton()
        self.add_account_button.setIcon(self.create_add_icon(QColor("#e0d6d1"), QColor("#c89f68")))
        self.add_account_button.clicked.connect(self.settings_handler.add_account)
        self.add_account_button.setFixedSize(40, 40)
        self.add_account_button.setIconSize(QSize(24, 24))
        self.add_account_button.setStyleSheet(
            "QPushButton {background-color: #4f4a4b; border-radius: 20px;} QPushButton:hover { background-color: #d9b68b; }"
        )
        bottom_layout.addWidget(self.add_account_button, 0, 1, Qt.AlignCenter)

        self.settings_button = HoverButton()
        self.settings_button.setIcon(self.create_gear_icon(QColor("#e0d6d1")))
        self.settings_button.clicked.connect(self.show_settings_dialog)
        self.settings_button.setFixedSize(40, 40)
        self.settings_button.setIconSize(QSize(24, 24))
        self.settings_button.setStyleSheet(
            "QPushButton {background-color: #4f4a4b; border-radius: 20px;} QPushButton:hover { background-color: #c89f68; }"
        )
        bottom_layout.addWidget(self.settings_button, 0, 2, Qt.AlignRight)

        bottom_layout.setColumnStretch(0, 1)
        bottom_layout.setColumnStretch(1, 0)
        bottom_layout.setColumnStretch(2, 1)
        

    def setup_grid_container(self):
        if hasattr(self, "grid_container") and self.grid_container:
            self.grid_container.deleteLater()
        self.grid_container = QWidget(objectName="grid_container")
        
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(10)

        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll_area.setWidget(self.grid_container)

    def load_accounts(self):
        previously_selected = self.selected_account_name
        self.setup_grid_container()
        self.account_widgets.clear()
        accounts = self.switcher.get_saved_accounts()

        ordered_accounts = self.switcher.get_ima_config().get("ordered_accounts", [])
        account_names_in_order = [name for name in ordered_accounts if name in accounts]

        show_game_icons = self.switcher.get_ima_config().get("ui_settings", {}).get("show_game_icons", True)

        for name in account_names_in_order:
            icon_path, game = accounts[name]
            icon = generate_icon(name, icon_path)
            widget = AccountWidget(name, icon, game, self.grid_container)
            widget.selected.connect(self.on_account_selected)
            widget.double_clicked.connect(self.on_account_double_clicked)
            widget.context_menu_requested.connect(self.show_context_menu)
            widget.set_show_game_icon(show_game_icons)
            self.account_widgets[name] = widget

        for name, (icon_path, game) in accounts.items():
            if name not in self.account_widgets:
                icon = generate_icon(name, icon_path)
                widget = AccountWidget(name, icon, game, self.grid_container)
                widget.selected.connect(self.on_account_selected)
                widget.double_clicked.connect(self.on_account_double_clicked)
                widget.context_menu_requested.connect(self.show_context_menu)
                widget.set_show_game_icon(show_game_icons)
                self.account_widgets[name] = widget

        self.rearrange_grid()
        self.update_window_size()

        if previously_selected and previously_selected in self.account_widgets:
            self.on_account_selected(previously_selected)
        elif accounts:
            first_account_name = next(iter(account_names_in_order), None)
            if first_account_name:
                self.on_account_selected(first_account_name)
        else:
            self.selected_account_name = None
            self.status_label.setText("No accounts found.")

    def rearrange_grid(self):
        if not self.account_widgets: return
        num_columns = 4
        
        ordered_names = list(self.switcher.get_ima_config().get("ordered_accounts", []))
        
        current_account_names = set(self.account_widgets.keys())
        for name in sorted(list(current_account_names - set(ordered_names))):
            ordered_names.append(name)

        for i, name in enumerate(ordered_names):
            widget = self.account_widgets.get(name)
            if widget: self.grid_layout.addWidget(widget, i // num_columns, i % num_columns)

    def update_window_size(self):
        num_accounts = len(self.account_widgets)
        COLS, W_W, W_H, S, H_M, V_M, T_B, B_B = 4, 120, 140, 10, 20, 20, 40, 60
        if num_accounts == 0: self.setFixedSize(300, 200); return
        num_rows = max(1, math.ceil(num_accounts / COLS))
        display_rows = min(num_rows, 4)
        grid_width = (COLS * W_W) + ((COLS - 1) * S) + H_M
        grid_height = (display_rows * W_H) + ((display_rows - 1) * S) + V_M
        self.setFixedSize(grid_width + 20, grid_height + T_B + B_B)

    def show_settings_dialog(self):
        actions = self.get_settings_actions()
        dialog = SettingsDialog(actions, self)
        dialog.exec_()

    def open_options_dialog(self):
        dialog = OptionsDialog(self.switcher, self)
        dialog.settings_applied.connect(self.load_accounts)
        dialog.exec_()

    def get_settings_actions(self):
        return {
            "Add Account": (self.settings_handler.add_account, "Add.png"),
            "Save Current Account": (self.settings_handler.save_current_account, "Save.png"),
            "Backup": (self.settings_handler.backup_profiles, "Backup.png"),
            "Restore": (self.settings_handler.restore_profiles, "Restore.png"),
            "Open Profiles Folder": (self.settings_handler.open_profiles_folder, "Open.png"),
            "Export to iMA Menu": (self.settings_handler.export_ima_menu, "ima.png"),
            "Options": (self.settings_handler.open_options_dialog, "Options.png"),
        }

    def center_on_screen(self):
        self.move(QDesktopWidget().availableGeometry().center() - self.frameGeometry().center())
    
    def create_gear_icon(self, color):
        from PyQt5.QtCore import QRectF
        from PyQt5.QtGui import QPainterPath
        pixmap = QPixmap(64, 64); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(color)
        p.translate(32, 32)
        for _ in range(8): p.drawRect(QRectF(-3, -28, 6, 12)); p.rotate(45)
        path = QPainterPath(); path.addEllipse(QRectF(-16, -16, 32, 32)); path.addEllipse(QRectF(-10, -10, 20, 20))
        path.setFillRule(Qt.OddEvenFill); p.drawPath(path); p.end()
        return QIcon(pixmap)

    def create_add_icon(self, plus_color, bg_color):
        pixmap = QPixmap(64, 64); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(bg_color)
        p.drawEllipse(0, 0, 64, 64)
        p.setBrush(plus_color)
        p.drawRect(18, 28, 28, 8)
        p.drawRect(28, 18, 8, 28)
        p.end()
        return QIcon(pixmap)

    def on_account_selected(self, name):
        self.selected_account_name = name
        for n, w in self.account_widgets.items(): w.set_selected(n == name)
        self.status_label.setText(f"Selected '{name}'.")

    def on_account_double_clicked(self, name):
        self.on_account_selected(name)
        self.switch_to_selected_account()

    def show_context_menu(self, name, pos):
        self.on_account_selected(name)
        menu = QMenu(self)
        actions = {
            "Switch Account": (self.switch_to_selected_account, "Switch.png"),
            "Rename": (self.context_handler.rename, "Rename.png"),
            "Change Icon": (self.context_handler.change_icon, "Change.png"),
        }

        account_data = self.switcher.get_saved_accounts()
        if name in account_data and account_data[name][0]:
            actions["Remove Icon"] = (self.context_handler.remove_icon, "Remove.png")

        actions["Create Desktop Shortcut"] = (self.context_handler.create_shortcut, "Create.png")
        
        change_game_menu = QMenu("Change Game", self)
        change_game_menu.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "Assets", "Riot.png")))
        valorant_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "valorant.png")
        lol_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "lol.png")
        
        if os.path.exists(valorant_icon_path):
            change_game_menu.addAction(QAction(QIcon(valorant_icon_path), "Valorant", self, triggered=lambda: self.context_handler.change_game('valorant')))
        else:
            change_game_menu.addAction(QAction("Valorant", self, triggered=lambda: self.context_handler.change_game('valorant')))

        if os.path.exists(lol_icon_path):
            change_game_menu.addAction(QAction(QIcon(lol_icon_path), "League of Legends", self, triggered=lambda: self.context_handler.change_game('lol')))
        else:
            change_game_menu.addAction(QAction("League of Legends", self, triggered=lambda: self.context_handler.change_game('lol')))

        riot_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "Riot.png")
        if os.path.exists(riot_icon_path):
            change_game_menu.addAction(QAction(QIcon(riot_icon_path), "Both", self, triggered=lambda: self.context_handler.change_game('both')))
        else:
            change_game_menu.addAction(QAction("Both", self, triggered=lambda: self.context_handler.change_game('both')))

        menu.addMenu(change_game_menu)
        menu.addSeparator()
        actions["Delete Account"] = (self.context_handler.delete, "Delete.png")

        for text, data in actions.items():
            if text:
                func, icon_name = data
                icon_path = os.path.join(os.path.dirname(__file__), "Assets", icon_name)
                if os.path.exists(icon_path):
                    menu.addAction(QAction(QIcon(icon_path), text, self, triggered=func))
                else:
                    menu.addAction(QAction(text, self, triggered=func))
        menu.exec_(pos)

    def get_selected_account_name(self):
        if self.selected_account_name: return self.selected_account_name
        QMessageBox.warning(self, "No Account Selected", "Please click on an account to select it first.")
        return None

    def switch_to_selected_account(self, selected_game=None):
        name = self.get_selected_account_name()
        if not name: return

        # Get account data to pass to GameSelectionDialog if needed
        account_data = self.switcher.get_saved_accounts().get(name)
        account_icon_path = account_data[0] if account_data else None
        account_icon_pixmap = QPixmap() # Default empty pixmap
        if account_icon_path and os.path.exists(account_icon_path):
            account_icon = generate_icon(name, account_icon_path)
            account_icon_pixmap = account_icon.pixmap(account_icon.actualSize(QSize(180, 180)))
        else:
            # Generate a default icon if no custom icon is set
            default_icon = generate_icon(name)
            account_icon_pixmap = default_icon.pixmap(default_icon.actualSize(QSize(180, 180)))

        self.status_label.setText(f"Switching to '{name}'...")
        QApplication.processEvents()

        result, message, game_type_or_selected_game = self.switcher.switch_account(name, selected_game=selected_game)

        if game_type_or_selected_game == "both":
            # If game is 'both', show selection dialog
            self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap, standalone=False) # Show temporary notification
            self.launch_notification.show()
            QApplication.processEvents()

            selection_dialog = GameSelectionDialog(name, account_icon_pixmap, self)
            selection_dialog.game_selected.connect(lambda game: self._handle_game_selection(name, game))
            selection_dialog.finished.connect(self.launch_notification.close) # Close notification when dialog is done
            selection_dialog.exec_()

        elif not result:
            self.status_label.setText(f"Failed to switch to '{name}'.")
            QMessageBox.critical(self, "Switch Failed", message)
            if hasattr(self, "launch_notification"): self.launch_notification.close()
        else:
            # If a game was directly launched (not 'both'), show the 6-second notification
            try:
                self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap)
                self.launch_notification.show()
                QApplication.processEvents()
            except Exception as e: print(f"Could not create notification: {e}")

    def _handle_game_selection(self, account_name, game):
        # This method is called when a game is selected from the GameSelectionDialog
        self.status_label.setText(f"Launching {game.capitalize()} for '{account_name}'...")
        QApplication.processEvents()
        result, message, _ = self.switcher.switch_account(account_name, selected_game=game)
        if not result:
            self.status_label.setText(f"Failed to launch {game.capitalize()} for '{account_name}'.")
            QMessageBox.critical(self, "Launch Failed", message)
        else:
            self.status_label.setText(f"Successfully launched {game.capitalize()} for '{account_name}'.")

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    current_exe_name = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
    
    if "Installer" in current_exe_name: 
        run_installer()
    elif len(sys.argv) > 2 and sys.argv[1] == "--switch":
        switcher = GameSwitcher()
        account_name = sys.argv[2]
        
        if not switcher.is_admin():
            ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
            sys.exit(0)
        
        app = QApplication(sys.argv)
        accounts_data = switcher.get_saved_accounts()
        icon_path, game_type = accounts_data.get(account_name, (None, None))
        
        game_icon = generate_icon(account_name, icon_path)
        pixmap = game_icon.pixmap(game_icon.actualSize(QSize(180, 180)))

        if game_type == "both":
            selection_dialog = GameSelectionDialog(account_name, pixmap)
            selected_game = None
            if selection_dialog.exec_() == QDialog.Accepted:
                selected_game = selection_dialog.game_selected_value
            
            if selected_game:
                result, _, _ = switcher.switch_account(account_name, selected_game=selected_game)
                if result:
                    notification = LaunchNotificationWidget(account_name, pixmap, standalone=True)
                    notification.show()
                    sys.exit(app.exec_())
                else:
                    sys.exit(1)
            else:
                sys.exit(0) # User cancelled game selection
        else:
            result, _, _ = switcher.switch_account(account_name)
            if result:
                notification = LaunchNotificationWidget(account_name, pixmap, standalone=True)
                notification.show()
                sys.exit(app.exec_())
            else:
                sys.exit(1)
        
    else:
        app = QApplication(sys.argv)
        ex = ModernValorantSwitcher()
        ex.show()
        sys.exit(app.exec_())

if __name__ == "__main__":
    main()

