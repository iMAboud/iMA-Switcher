import sys
import os
import math
import ctypes
import shutil 
import subprocess 
import time
import threading 

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

def generate_icon(name, account_icon_path=None, rank=None, use_rank_icons=False, base_dir=None):
    """Generates a QIcon based on account settings, rank, or a default one."""
    if base_dir is None:
        base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))

    icon_path_to_use = None

    if use_rank_icons and rank:
        rank_icon_name = rank.lower().replace(" ", "_") if rank.lower() != 'unranked' else 'unranked'
        rank_icon_path = os.path.join(base_dir, "Assets", f"{rank_icon_name}.png")
        if os.path.exists(rank_icon_path):
            icon_path_to_use = rank_icon_path

    if icon_path_to_use is None and account_icon_path and os.path.exists(account_icon_path):
        icon_path_to_use = account_icon_path

    if icon_path_to_use is None:
        logo_path = os.path.join(base_dir, "logo.png")
        if os.path.exists(logo_path):
            icon_path_to_use = logo_path

    if icon_path_to_use and os.path.exists(icon_path_to_use):
        try:
            if Image:
                pil_image = Image.open(icon_path_to_use)
                pil_image = pil_image.convert("RGBA")
                from io import BytesIO
                byte_array = BytesIO()
                pil_image.save(byte_array, format="PNG")
                byte_array.seek(0)
                
                pixmap = QPixmap()
                pixmap.loadFromData(byte_array.getvalue(), "PNG")
                return QIcon(pixmap)
            else:
                return QIcon(icon_path_to_use)
        except Exception as e:
            print(f"Error loading icon from {icon_path_to_use}: {e}. Using default icon.")
    
    # Default icon if all else fails
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

            # Copy Assets folder to the permanent install location
            source_assets_path = os.path.join(sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)), "Assets")
            destination_assets_path = os.path.join(install_path, "Assets")
            if os.path.exists(source_assets_path):
                shutil.copytree(source_assets_path, destination_assets_path, dirs_exist_ok=True)

            riot_games_exe_path = dialog.get_riot_games_path()
            switcher_instance = GameSwitcher(base_directory=install_path) 
            if riot_games_exe_path:
                switcher_instance.set_riot_client_paths(riot_games_exe_path)
            
            # Save the permanent install path to config.json
            switcher_instance.set_ima_config({"app_install_path": install_path})

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
    account_updated = pyqtSignal(str) # New signal

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.switcher = GameSwitcher()
        self.switcher._ensure_initialized()
        # self.switcher.start_rank_update_scheduler() # Removed this line 
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

        # New: Connect signal and start scheduler
        self.account_updated.connect(self.on_account_updated)
        self.switcher.start_rank_update_scheduler(on_update_callback=self.account_updated.emit)
        self.initial_rank_fetch()


    def init_ui(self):
        self.setWindowTitle("iMA Switcher")
        self.setWindowIcon(generate_icon("V", base_dir=self.switcher.base_dir))
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
        self.title_bar.refresh_button.clicked.connect(self.refresh_accounts)
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
        
        # Add remaining accounts that are not in the ordered list
        for name in sorted(accounts.keys()):
            if name not in account_names_in_order:
                account_names_in_order.append(name)

        show_game_icons = self.switcher.get_ima_config().get("ui_settings", {}).get("show_game_icons", True)
        use_rank_icons = self.switcher.get_ima_config().get("ui_settings", {}).get("use_rank_icons", False)
        show_name_tag = self.switcher.get_ima_config().get("ui_settings", {}).get("show_name_tag", False)

        # A single loop to create all account widgets
        for name in account_names_in_order:
            icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = accounts[name]
            icon = generate_icon(name, icon_path, rank, use_rank_icons, self.switcher.base_dir)
            widget = AccountWidget(name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, self.grid_container)
            widget.selected.connect(self.on_account_selected)
            widget.double_clicked.connect(self.on_account_double_clicked)
            widget.context_menu_requested.connect(self.show_context_menu)
            widget.set_show_game_icon(show_game_icons)
            widget.set_show_rank_icon(self.switcher.get_ima_config().get("ui_settings", {}).get("show_rank_icon_left", False))
            widget.set_show_name_tag(show_name_tag)
            widget.set_show_current_rr(self.switcher.get_ima_config().get("ui_settings", {}).get("show_current_rr", True))
            widget.set_show_last_game_rr(self.switcher.get_ima_config().get("ui_settings", {}).get("show_last_game_rr", True))
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
        
        # The account_widgets dictionary is already ordered correctly from load_accounts
        for i, name in enumerate(self.account_widgets.keys()):
            widget = self.account_widgets.get(name)
            if widget: self.grid_layout.addWidget(widget, i // num_columns, i % num_columns)

    def update_window_size(self):
        num_accounts = len(self.account_widgets)
        COLS = 4
        if num_accounts == 0:
            self.setFixedSize(300, 200)
            return

        # Get the height of a single account widget (which can vary)
        sample_widget = next(iter(self.account_widgets.values()), None)
        if sample_widget:
            W_H = sample_widget.height() # Use actual widget height
        else:
            W_H = 140 # Default if no accounts

        W_W, S, H_M, V_M, T_B, B_B = 120, 10, 20, 20, 40, 60

        num_rows = max(1, math.ceil(num_accounts / COLS))
        display_rows = min(num_rows, 4) # Max 4 rows visible without scrolling

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

    def closeEvent(self, event):
        # Ensure the iMA menu script is updated with current settings on close
        ima_config = self.switcher.get_ima_config()
        if ima_config.get("output_dir"):
            try:
                self.switcher.generate_ima_menu_script(
                    output_dir=ima_config["output_dir"],
                    title=ima_config["title"],
                    ordered_accounts=ima_config["ordered_accounts"],
                    menu_icon_path=ima_config.get("menu_icon_path", ""),
                    save_config=False  # Already saved by OptionsDialog or other actions
                )
                print("iMA menu script updated on application close.")
            except Exception as e:
                print(f"Error updating iMA menu script on close: {e}")
        event.accept()
    
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

    def on_account_updated(self, account_name):
        """
        Slot to handle updates for a single account widget.
        """
        print(f"UI received update for: {account_name}")
        self.load_accounts()
        self.status_label.setText(f"Updated: {account_name}")

    def initial_rank_fetch(self):
        """
        Fetches ranks for all accounts in separate threads after UI is shown.
        """
        self.refresh_accounts()

    def refresh_accounts(self):
        """        Fetches ranks for all accounts and updates the UI.
        """
        self.status_label.setText("Refreshing ranks...")
        accounts = self.switcher.get_saved_accounts()
        for name in accounts:
            threading.Thread(
                target=self.switcher.fetch_and_update_rank_data,
                args=(name, self.account_updated.emit),
                daemon=True
            ).start()

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
        
        set_rank_menu = QMenu("Set Rank", self)
        set_rank_menu.setIcon(QIcon(os.path.join(os.path.dirname(__file__), "Assets", "radiant.png"))) # Set Radiant icon for the main "Set Rank" menu

        # Add Unranked as a direct option
        unranked_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "unranked.png")
        unranked_action = QAction("Unranked", self)
        if os.path.exists(unranked_icon_path):
            unranked_action.setIcon(QIcon(unranked_icon_path))
        unranked_action.triggered.connect(lambda checked, r="Unranked": self.context_handler.set_rank(r))
        set_rank_menu.addAction(unranked_action)

        ranks_with_tiers = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal"]
        for rank_name in ranks_with_tiers:
            rank_tier_menu = QMenu(rank_name, self)
            # Use the first tier icon for the submenu
            first_tier_icon_path = os.path.join(os.path.dirname(__file__), "Assets", f"{rank_name.lower()}_1.png")
            if os.path.exists(first_tier_icon_path):
                rank_tier_menu.setIcon(QIcon(first_tier_icon_path))
            
            for i in range(1, 4): # Tiers 1, 2, 3
                full_rank_name = f"{rank_name} {i}"
                rank_icon_path = os.path.join(os.path.dirname(__file__), "Assets", f"{rank_name.lower()}_{i}.png")
                
                action = QAction(full_rank_name, self)
                if os.path.exists(rank_icon_path):
                    action.setIcon(QIcon(rank_icon_path))
                action.triggered.connect(lambda checked, r=full_rank_name: self.context_handler.set_rank(r))
                rank_tier_menu.addAction(action)
            set_rank_menu.addMenu(rank_tier_menu)

        # Add Radiant as a direct option
        radiant_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "radiant.png")
        radiant_action = QAction("Radiant", self)
        if os.path.exists(radiant_icon_path):
            radiant_action.setIcon(QIcon(radiant_icon_path))
        radiant_action.triggered.connect(lambda checked, r="Radiant": self.context_handler.set_rank(r))
        set_rank_menu.addAction(radiant_action)

        

        menu.addMenu(set_rank_menu)
        
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
        account_icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = account_data if account_data else (None, None, None, None, None, None, None)
        
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)

        account_icon = generate_icon(name, account_icon_path, rank, use_rank_icons, self.switcher.base_dir)
        account_icon_pixmap = account_icon.pixmap(account_icon.actualSize(QSize(180, 180)))

        self.status_label.setText(f"Switching to '{name}'...")
        QApplication.processEvents()

        result, message, game_type_or_selected_game = self.switcher.switch_account(name, selected_game=selected_game)

        if game_type_or_selected_game == "both":
            # If game is 'both', show selection dialog
            self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=False) # Show temporary notification
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
                self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons)
                self.launch_notification.show()
                QApplication.processEvents()
                self.refresh_accounts() # Refresh after successful switch
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
        account_icon_path, game_type, rank, in_game_name, in_game_tag, current_rr, last_game_rr = accounts_data.get(account_name, (None, None, None, None, None, None, None))
        
        ui_settings = switcher.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)
        game_icon = generate_icon(account_name, account_icon_path, rank, use_rank_icons, switcher.base_dir)
        pixmap = game_icon.pixmap(game_icon.actualSize(QSize(180, 180)))

        if game_type == "both":
            selection_dialog = GameSelectionDialog(account_name, pixmap)
            selected_game = None
            if selection_dialog.exec_() == QDialog.Accepted:
                selected_game = selection_dialog.game_selected_value
            
            if selected_game:
                result, _, _ = switcher.switch_account(account_name, selected_game=selected_game)
                if result:
                    notification = LaunchNotificationWidget(account_name, pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=True)
                    notification.show()
                    sys.exit(app.exec_())
                else:
                    sys.exit(1)
            else:
                sys.exit(0) # User cancelled game selection
        else:
            result, _, _ = switcher.switch_account(account_name)
            if result:
                notification = LaunchNotificationWidget(account_name, pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=True)
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

