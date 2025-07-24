import sys
import os
import math
import ctypes
import shutil 
import subprocess 
import threading 
import logging 

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
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool

from game_switcher import GameSwitcher
from ui_components import (
    CustomTitleBar,
    AccountWidget,
    HoverButton,
    SettingsDialog,
    LaunchNotificationWidget,
    InstallerDialog, 
    GameSelectionDialog,
    RiotClientNotFoundDialog
)
from game_switcher import CustomUpdateEvent
from actions_settings import SettingsActions
from actions_context import ContextActions

class IconLoaderSignals(QObject):
    finished = pyqtSignal(str, QIcon)

class IconLoader(QRunnable):
    """Worker thread for loading icons asynchronously."""
    def __init__(self, switcher, account_name, icon_path):
        super().__init__()
        self.switcher = switcher
        self.account_name = account_name
        self.icon_path = icon_path
        self.signals = IconLoaderSignals()

    def run(self):
        """Load the icon and emit a signal when done."""
        icon = self.switcher.get_qicon_from_path(self.icon_path)
        self.signals.finished.emit(self.account_name, icon)

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
        logging.error(f"Error creating shortcut {shortcut_path}: {e}")
        return False

def run_installer():
    app = QApplication(sys.argv)
    dialog = InstallerDialog()
    if dialog.exec_() == QDialog.Accepted:
        install_path = dialog.get_install_path()
        current_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])

        def install_thread():
            try:
                os.makedirs(install_path, exist_ok=True)

                destination_exe_path = os.path.join(install_path, "iMA Switcher.exe")
                shutil.copy2(current_exe, destination_exe_path)

                source_assets_path = os.path.join(sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)), "Assets")
                destination_assets_path = os.path.join(install_path, "Assets")
                if os.path.exists(source_assets_path):
                    shutil.copytree(source_assets_path, destination_assets_path, dirs_exist_ok=True)

                riot_games_exe_path = dialog.get_riot_games_path()
                switcher_instance = GameSwitcher(base_directory=install_path)
                if riot_games_exe_path:
                    switcher_instance.set_riot_client_paths(riot_games_exe_path)

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
                # Give the launched application a moment to start before the installer quits
                time.sleep(2) 
                sys.exit(0)

            except Exception as e:
                logging.critical(
                    None,
                    "Installation Error",
                    f"An error occurred during installation:\n{e}"
                )
                QApplication.instance().quit()

        thread = threading.Thread(target=install_thread)
        thread.start()
        app.exec_()

    else:
        sys.exit(0)


class ModernValorantSwitcher(QMainWindow):
    account_updated = pyqtSignal(str) # New signal
    status_message_requested = pyqtSignal(str)
    
    switch_account_finished = pyqtSignal(bool, str, str, QPixmap, str, str, str, bool)
    
    
    

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.switcher = GameSwitcher()

        if not self.switcher.is_admin():
            logging.critical("Application started without administrator privileges. Exiting.")
            QMessageBox.critical(
                self,
                "Administrator Rights Required",
                "This application requires administrator privileges for fast account switching.\n\nPlease restart as administrator.",
            )

        self.settings_handler = SettingsActions(self)
        self.context_handler = ContextActions(self)

        self.account_widgets = {}
        self.selected_account_name = None
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(QThreadPool.globalInstance().maxThreadCount()) # Use a reasonable number of threads
        self.init_ui()
        self.load_accounts()
        self.center_on_screen()

        # New: Connect signal and start scheduler
        self.account_updated.connect(self.on_account_updated)
        self.status_message_requested.connect(self.status_label.setText)
        
        self.switch_account_finished.connect(self.on_switch_account_finished)
        
        
        
        
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True):
            self.switcher.start_rank_update_scheduler(on_update_callback=self.account_updated.emit)
            QTimer.singleShot(100, self.initial_rank_fetch)

        

        


    def init_ui(self):
        self.setWindowTitle("iMA Switcher")
        self.setWindowIcon(self.switcher.get_qicon_from_path(os.path.join(self.switcher.base_dir, "logo.png")))
        self.setStyleSheet(
            """#main_widget { background-color: #2c2a2b; border-radius: 15px; border: 1px solid #4f4a4b; } 
               QScrollArea { border: none; background-color: transparent; } 
               QScrollArea QScrollBar:vertical { border: none; background: transparent; width: 0px; }
               QScrollArea QScrollBar:horizontal { border: none; background: transparent; height: 0px; }
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
        content_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.addLayout(content_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QScrollBar:vertical { border: none; background: transparent; width: 0px; } QScrollBar:horizontal { border: none; background: transparent; height: 0px; }")
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

        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        show_game_icons = ui_settings.get("show_game_icons", True)
        use_rank_icons = ui_settings.get("use_rank_icons", False)
        show_name_tag = ui_settings.get("show_name_tag", False)

        # A single loop to create all account widgets
        for name in account_names_in_order:
            icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = accounts[name]
            icon_path_to_use = self.switcher.get_icon_path_for_account(name, rank, use_rank_icons)
            
            # Check cache first, otherwise load async
            cached_icon = self.switcher.get_icon_from_cache(icon_path_to_use)
            if cached_icon:
                icon = cached_icon
            else:
                icon = self.switcher.get_placeholder_qicon()
                self.load_icon_async(name, icon_path_to_use)

            widget = AccountWidget(name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, self.grid_container, switcher_instance=self.switcher)
            widget.selected.connect(self.on_account_selected)
            widget.double_clicked.connect(self.on_account_double_clicked)
            widget.context_menu_requested.connect(self.show_context_menu)
            widget.set_show_game_icon(show_game_icons)
            widget.set_show_rank_icon(ui_settings.get("show_rank_icon_left", False))
            widget.set_show_name_tag(show_name_tag)
            widget.set_show_current_rr(ui_settings.get("show_current_rr", True))
            widget.set_show_last_game_rr(ui_settings.get("show_last_game_rr", True))
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

        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        num_accounts = len(self.account_widgets)
        if num_accounts <= 3:
            num_columns = num_accounts
        else:
            num_columns = ui_settings.get("grid_size", 4)

        # The account_widgets dictionary is already ordered correctly from load_accounts
        for i, name in enumerate(self.account_widgets.keys()):
            widget = self.account_widgets.get(name)
            if widget: self.grid_layout.addWidget(widget, i // num_columns, i % num_columns)

    def update_window_size(self):
        num_accounts = len(self.account_widgets)
        if num_accounts == 0:
            self.setFixedSize(300, 200)
            return

        sample_widget = next(iter(self.account_widgets.values()), None)
        if sample_widget:
            W_H = sample_widget.height()
            W_W = sample_widget.width()
        else:
            W_H = 140
            W_W = 120

        S, H_M, V_M, T_B, B_B = 10, 20, 20, 40, 60 # Adjusted V_M and T_B for better spacing

        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        num_columns = ui_settings.get("grid_size", 4)
        num_rows_needed = math.ceil(num_accounts / num_columns)
        display_rows = num_rows_needed # Use actual needed rows

        grid_width = (num_columns * W_W) + ((num_columns - 1) * S) + H_M
        grid_height = (display_rows * W_H) + ((display_rows - 1) * S) + V_M
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setFixedSize(grid_width + 20, grid_height + T_B + B_B)
        self.scroll_area.widget().setMinimumSize(grid_width, grid_height) # Ensure scroll area content is large enough

    def load_icon_async(self, account_name, icon_path):
        """Creates and runs an IconLoader task in the thread pool."""
        worker = IconLoader(self.switcher, account_name, icon_path)
        worker.signals.finished.connect(self.on_icon_loaded)
        self.thread_pool.start(worker)

    def on_icon_loaded(self, account_name, icon):
        """Slot to handle the finished signal from the IconLoader."""
        if account_name in self.account_widgets:
            self.account_widgets[account_name].set_icon(icon, 70) # Assuming 70 is the default size

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
            "Save Account": (self.settings_handler.save_current_account, "Save.png"),
            "Backup": (self.settings_handler.backup_profiles, "Backup.png"),
            "Restore": (self.settings_handler.restore_profiles, "Restore.png"),
            "Open Folder": (self.settings_handler.open_profiles_folder, "Open.png"),
            "iMA Menu": (self.settings_handler.export_ima_menu, "ima.png"),
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
                logging.info("iMA menu script updated on application close.")
            except Exception as e:
                logging.error(f"Error updating iMA menu script on close: {e}")
        event.accept()
    
    def create_gear_icon(self, color):
        from PyQt5.QtCore import QRectF, Qt
        from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QColor, QFont
        pixmap = QPixmap(64, 64); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(color)
        p.translate(32, 32)
        for _ in range(8): p.drawRect(QRectF(-3, -28, 6, 12)); p.rotate(45)
        path = QPainterPath(); path.addEllipse(QRectF(-16, -16, 32, 32)); path.addEllipse(QRectF(-10, -10, 20, 20))
        path.setFillRule(Qt.OddEvenFill); p.drawPath(path); p.end()
        return QIcon(pixmap)

    def create_add_icon(self, plus_color, bg_color):
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPixmap, QPainter, QColor
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
        QApplication.processEvents()  # Process any pending events
        if account_name in self.account_widgets:
            updated_account_data = self.switcher.get_saved_accounts().get(account_name)
            if updated_account_data:
                icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = updated_account_data
                ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
                use_rank_icons = ui_settings.get("use_rank_icons", False)
                icon_path_to_use = self.switcher.get_icon_path_for_account(account_name, rank, use_rank_icons)
                
                # Asynchronously load the new icon
                cached_icon = self.switcher.get_icon_from_cache(icon_path_to_use)
                if cached_icon:
                    icon = cached_icon
                else:
                    icon = self.switcher.get_placeholder_qicon()
                    self.load_icon_async(account_name, icon_path_to_use)

                self.account_widgets[account_name].update_data(account_name, icon, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr, ui_settings)
                self.update_window_size() # Recalculate window size if visibility of elements changed
            else:
                # If account data is not found, it means the account was likely deleted.
                # Remove the widget from the UI and from our tracking.
                widget_to_remove = self.account_widgets.pop(account_name)
                self.grid_layout.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
                self.rearrange_grid() # Re-arrange the grid after removal
                self.update_window_size() # Update window size after removal

    

    def initial_rank_fetch(self):
        """
        Fetches ranks for all accounts in separate threads after UI is shown,
        but only if auto_rank_update is enabled.
        """
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True):
            self.status_label.setText("Fetching all ranks...")
            threading.Thread(target=self.switcher.fetch_and_update_all_accounts, args=(self.account_updated.emit,), daemon=True).start()
        else:
            logging.info("Initial rank fetch skipped: Auto rank update is disabled.")

    

    

    def refresh_accounts(self):
        """
        Fetches ranks for all accounts and updates the UI.
        """
        self.status_label.setText("Refreshing ranks...")
        threading.Thread(
            target=self.switcher.fetch_and_update_all_accounts,
            args=(self.account_updated.emit,),
            daemon=True
        ).start()

    def event(self, event):
        if event.type() == CustomUpdateEvent.EVENT_TYPE:
            self.on_account_updated(event.account_name)
            return True
        return super().event(event)

    def show_context_menu(self, name, pos):
        self.on_account_selected(name)
        menu = QMenu(self)
        actions = {
            "Switch Account": (self.switch_to_selected_account, "Switch.png"),
            "Rename": (self.context_handler.rename, "Rename.png"),
            "Change Icon": (self.context_handler.change_icon, "Change.png"),
        }

        actions["Create Desktop Shortcut"] = (self.context_handler.create_shortcut, "Create.png")
        
        set_rank_menu = QMenu("Set Rank", self)
        set_rank_menu.setIcon(self.switcher.get_qicon_from_path(os.path.join(os.path.dirname(__file__), "Assets", "radiant.png"))) # Set Radiant icon for the main "Set Rank" menu

        # Add Unranked as a direct option
        unranked_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "unranked.png")
        unranked_action = QAction("Unranked", self)
        if os.path.exists(unranked_icon_path):
            unranked_action.setIcon(self.switcher.get_qicon_from_path(unranked_icon_path))
        unranked_action.triggered.connect(lambda checked, r="Unranked": self.context_handler.set_rank(r))
        set_rank_menu.addAction(unranked_action)

        ranks_with_tiers = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal"]
        for rank_name in ranks_with_tiers:
            rank_tier_menu = QMenu(rank_name, self)
            # Use the first tier icon for the submenu
            first_tier_icon_path = os.path.join(os.path.dirname(__file__), "Assets", f"{rank_name.lower()}_1.png")
            if os.path.exists(first_tier_icon_path):
                rank_tier_menu.setIcon(self.switcher.get_qicon_from_path(first_tier_icon_path))
            
            for i in range(1, 4): # Tiers 1, 2, 3
                full_rank_name = f"{rank_name} {i}"
                rank_icon_path = os.path.join(os.path.dirname(__file__), "Assets", f"{rank_name.lower()}_{i}.png")
                
                action = QAction(full_rank_name, self)
                if os.path.exists(rank_icon_path):
                    action.setIcon(self.switcher.get_qicon_from_path(rank_icon_path))
                action.triggered.connect(lambda checked, r=full_rank_name: self.context_handler.set_rank(r))
                rank_tier_menu.addAction(action)
            set_rank_menu.addMenu(rank_tier_menu)

        # Add Radiant as a direct option
        radiant_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "radiant.png")
        radiant_action = QAction("Radiant", self)
        if os.path.exists(radiant_icon_path):
            radiant_action.setIcon(self.switcher.get_qicon_from_path(radiant_icon_path))
        radiant_action.triggered.connect(lambda checked, r="Radiant": self.context_handler.set_rank(r))
        set_rank_menu.addAction(radiant_action)

        

        menu.addMenu(set_rank_menu)
        
        change_game_menu = QMenu("Change Game", self)
        change_game_menu.setIcon(self.switcher.get_qicon_from_path(os.path.join(os.path.dirname(__file__), "Assets", "Riot.png")))
        valorant_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "valorant.png")
        lol_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "lol.png")
        
        if os.path.exists(valorant_icon_path):
            change_game_menu.addAction(QAction(self.switcher.get_qicon_from_path(valorant_icon_path), "Valorant", self, triggered=lambda: self.context_handler.change_game('valorant')))

        if os.path.exists(lol_icon_path):
            change_game_menu.addAction(QAction(self.switcher.get_qicon_from_path(lol_icon_path), "League of Legends", self, triggered=lambda: self.context_handler.change_game('lol')))

        riot_icon_path = os.path.join(os.path.dirname(__file__), "Assets", "Riot.png")
        if os.path.exists(riot_icon_path):
            change_game_menu.addAction(QAction(self.switcher.get_qicon_from_path(riot_icon_path), "Both", self, triggered=lambda: self.context_handler.change_game('both')))

        menu.addMenu(change_game_menu)
        menu.addSeparator()
        actions["Delete Account"] = (self.context_handler.delete, "Delete.png")

        for text, data in actions.items():
            if text:
                func, icon_name = data
                icon_path = os.path.join(os.path.dirname(__file__), "Assets", icon_name)
                if os.path.exists(icon_path):
                    menu.addAction(QAction(self.switcher.get_qicon_from_path(icon_path), text, self, triggered=func))
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

        self.status_label.setText(f"Switching to '{name}'...")
        QApplication.processEvents()

        # --- NEW: Show notification immediately ---
        account_data = self.switcher.get_saved_accounts().get(name)
        if account_data:
            _, game, rank, in_game_name, in_game_tag, _, _ = account_data
            ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
            use_rank_icons = ui_settings.get("use_rank_icons", False)
            
            # If the game is 'both' and we don't have a selection yet, handle it
            if game == 'both' and selected_game is None:
                account_icon_path_str = self.switcher.get_icon_path_for_account(name, rank, use_rank_icons)
                account_icon = self.switcher.get_qicon_from_path(account_icon_path_str)
                pixmap = account_icon.pixmap(account_icon.actualSize(QSize(180, 180)))
                
                selection_dialog = GameSelectionDialog(name, pixmap, self, switcher_instance=self.switcher)
                # The selection dialog will re-call this method with the selected_game
                selection_dialog.game_selected.connect(lambda game: self.switch_to_selected_account(selected_game=game))
                selection_dialog.exec_()
                return # Stop execution here, the dialog will trigger the next step

            # If we have a game (or one was just selected), show the notification and launch
            try:
                account_icon_path_str = self.switcher.get_icon_path_for_account(name, rank, use_rank_icons)
                account_icon = self.switcher.get_qicon_from_path(account_icon_path_str)
                account_icon_pixmap = account_icon.pixmap(account_icon.actualSize(QSize(180, 180)))
                self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, switcher_instance=self.switcher)
                self.launch_notification.show()
                QApplication.processEvents()
            except Exception as e:
                logging.error(f"Could not create notification: {e}")
        # --- End of new section ---

        threading.Thread(target=self._switch_account_thread, args=(name, selected_game), daemon=True).start()

    

    

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
            # Show the LaunchNotificationWidget after successful game selection
            account_data = self.switcher.get_saved_accounts().get(account_name)
            if account_data:
                _, _, rank, in_game_name, in_game_tag, current_rr, last_game_rr = account_data
                ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
                use_rank_icons = ui_settings.get("use_rank_icons", False)
                account_icon_path_str = self.switcher.get_icon_path_for_account(account_name, rank, use_rank_icons)
                account_icon = self.switcher.get_qicon_from_path(account_icon_path_str)
                account_icon_pixmap = account_icon.pixmap(account_icon.actualSize(QSize(180, 180)))

                try:
                    self.launch_notification = LaunchNotificationWidget(account_name, account_icon_pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=False, switcher_instance=self.switcher)
                    self.launch_notification.show()
                    QApplication.processEvents()
                except Exception as e:
                    logging.error(f"Could not create notification: {e}")
        self.refresh_accounts()

    def _switch_account_thread(self, account_name, selected_game):
        success, message, game_type = self.switcher.switch_account(account_name, selected_game=selected_game, on_update_callback=self.account_updated.emit)
        
        account_data = self.switcher.get_saved_accounts().get(account_name)
        account_icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = account_data if account_data else (None, None, None, None, None, None, None)
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)
        account_icon_path_str = self.switcher.get_icon_path_for_account(account_name, rank, use_rank_icons)
        account_icon = self.switcher.get_qicon_from_path(account_icon_path_str)
        account_icon_pixmap = account_icon.pixmap(account_icon.actualSize(QSize(180, 180)))

        self.switch_account_finished.emit(success, message, game_type, account_icon_pixmap, in_game_name, in_game_tag, rank, use_rank_icons)

    def on_switch_account_finished(self, success, message, game_type, account_icon_pixmap, in_game_name, in_game_tag, rank, use_rank_icons):
        name = self.get_selected_account_name()
        if not name: return

        if game_type == "both":
            selection_dialog = GameSelectionDialog(name, account_icon_pixmap, self, switcher_instance=self.switcher)
            selection_dialog.game_selected.connect(lambda game: self._handle_game_selection(name, game))
            selection_dialog.exec_()

        elif not success:
            if "Riot Client not found" in message:
                dialog = RiotClientNotFoundDialog(self)
                if dialog.exec_() == QDialog.Accepted:
                    new_path = dialog.get_path()
                    if new_path and os.path.exists(new_path):
                        self.switcher.set_riot_client_paths(new_path)
                        self.switch_to_selected_account() # Retry switching
            else:
                self.status_label.setText(f"Failed to switch to '{name}'.")
                QMessageBox.critical(self, "Switch Failed", message)
            if hasattr(self, "launch_notification"): self.launch_notification.close()
        else:
            try:
                self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, switcher_instance=self.switcher)
                self.launch_notification.show()
                QApplication.processEvents()
            except Exception as e:
                logging.error(f"Could not create notification: {e}")
        self.refresh_accounts() # Refresh after any switch attempt

    

    

def _handle_game_selection_standalone(switcher, account_name, game, pixmap):
    # This method is called when a game is selected from the GameSelectionDialog in standalone mode
    result, _, _ = switcher.switch_account(account_name, selected_game=game)
    if result:
        ui_settings = switcher.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True):
            switcher.fetch_and_update_all_accounts()
        
        account_data = switcher.get_saved_accounts().get(account_name)
        _, _, rank, in_game_name, in_game_tag, _, _ = account_data if account_data else (None, None, None, None, None, None, None)
        ui_settings = switcher.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)

        notification = LaunchNotificationWidget(account_name, pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=True, switcher_instance=switcher)
        notification.show()
    else:
        sys.exit(1)


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
        game_icon_path = switcher.get_icon_path_for_account(account_name, rank, use_rank_icons)
        game_icon = switcher.get_qicon_from_path(game_icon_path)
        pixmap = game_icon.pixmap(game_icon.actualSize(QSize(180, 180)))

        if game_type == "both":
            selection_dialog = GameSelectionDialog(account_name, pixmap)
            selection_dialog.game_selected.connect(lambda game: _handle_game_selection_standalone(switcher, account_name, game, pixmap))
            selection_dialog.show() # Use show() for non-modal behavior
            sys.exit(app.exec_()) # Keep the app running until dialog is closed or game launched

        else:
            result, _, _ = switcher.switch_account(account_name, on_update_callback=None)
            if result:
                account_data = switcher.get_saved_accounts().get(account_name)
                _, _, rank, in_game_name, in_game_tag, _, _ = account_data if account_data else (None, None, None, None, None, None, None)
                ui_settings = switcher.get_ima_config().get("ui_settings", {})
                use_rank_icons = ui_settings.get("use_rank_icons", False)

                notification = LaunchNotificationWidget(account_name, pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=True, switcher_instance=switcher)
                notification.show()
                
                ui_settings = switcher.get_ima_config().get("ui_settings", {})
                if ui_settings.get("auto_rank_update", True):
                    # Defer the rank update check slightly to not block the notification
                    QTimer.singleShot(100, lambda: switcher.fetch_and_update_all_accounts())
                    

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