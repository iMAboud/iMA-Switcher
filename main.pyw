import sys
import os
from pathlib import Path
import math
import ctypes
import shutil 
import subprocess 
import threading 
import logging 

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    sys.path.append(str(Path(sys._MEIPASS)))

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
    QGraphicsDropShadowEffect,
)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QFont, QColor, QImage
from PyQt5.QtCore import Qt, QSize, QPoint, pyqtSignal, QTimer, QObject, QRunnable, QThreadPool

from game_switcher import GameSwitcher
from ui_components import (
    CustomTitleBar,
    AccountWidget,
    HoverButton,
    SettingsDialog,
    SettingsDropdownMenu,
    LaunchNotificationWidget,
    InstallerDialog, 
    GameSelectionDialog,
    RiotClientNotFoundDialog
)
from game_switcher import CustomUpdateEvent
from actions_settings import SettingsActions
from actions_context import ContextActions
from theme_manager import apply_theme_to_app, set_active_theme

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



def wait_for_pid(pid, timeout=15):
    """Wait for parent process to exit cleanly before replacing files."""
    try:
        pid = int(pid)
        import time
        start_time = time.time()
        if os.name == 'nt':
            import ctypes
            SYNCHRONIZE = 0x00100000
            handle = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
            if handle:
                ctypes.windll.kernel32.WaitForSingleObject(handle, int(timeout * 1000))
                ctypes.windll.kernel32.CloseHandle(handle)
                return
        while time.time() - start_time < timeout:
            try:
                os.kill(pid, 0)
                time.sleep(0.3)
            except OSError:
                break
    except Exception as e:
        logging.warning(f"Error waiting for PID {pid}: {e}")

def run_update_installer():
    parent_pid = None
    target_dir = None
    
    for i in range(len(sys.argv)):
        if sys.argv[i] == "--pid" and i + 1 < len(sys.argv):
            parent_pid = sys.argv[i + 1]
        elif sys.argv[i] == "--target-dir" and i + 1 < len(sys.argv):
            target_dir = sys.argv[i + 1]

    if parent_pid:
        wait_for_pid(parent_pid)

    current_exe = Path(sys.executable) if getattr(sys, 'frozen', False) else Path(sys.argv[0]).resolve()
    
    if not target_dir:
        try:
            switcher_instance = GameSwitcher()
            target_dir = switcher_instance.get_ima_config().get("app_install_path", "")
        except Exception:
            pass
    
    if not target_dir:
        target_dir = current_exe.parent

    target_dir_p = Path(target_dir)
    target_dir_p.mkdir(parents=True, exist_ok=True)
    destination_exe_path = target_dir_p / "iMA Switcher.exe"

    try:
        import time
        time.sleep(0.5)
        shutil.copy2(current_exe, destination_exe_path)

        source_assets_path = Path(sys._MEIPASS if getattr(sys, 'frozen', False) else Path(__file__).parent) / "Assets"
        destination_assets_path = target_dir_p / "Assets"
        if source_assets_path.exists():
            shutil.copytree(source_assets_path, destination_assets_path, dirs_exist_ok=True)

        source_maps_path = Path(sys._MEIPASS if getattr(sys, 'frozen', False) else Path(__file__).parent) / "maps"
        destination_maps_path = target_dir_p / "maps"
        if source_maps_path.exists():
            shutil.copytree(source_maps_path, destination_maps_path, dirs_exist_ok=True)
    except Exception as err:
        logging.error(f"Failed to update files in target directory: {err}")

    try:
        creationflags = 0x00000008 | 0x00000200 if os.name == 'nt' else 0  # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(
            [str(destination_exe_path)],
            cwd=str(target_dir_p),
            creationflags=creationflags
        )
    except Exception as err:
        logging.error(f"Failed to launch updated executable: {err}")

    sys.exit(0)

def run_installer():
    app = QApplication(sys.argv)
    apply_theme_to_app(app)
    dialog = InstallerDialog()
    if dialog.exec_() == QDialog.Accepted:
        install_path = dialog.get_install_path()
        current_exe = Path(sys.executable) if getattr(sys, 'frozen', False) else Path(sys.argv[0]).resolve()

        def install_thread():
            try:
                install_path_p = Path(install_path)
                install_path_p.mkdir(parents=True, exist_ok=True)

                destination_exe_path = install_path_p / "iMA Switcher.exe"
                shutil.copy2(current_exe, destination_exe_path)

                source_assets_path = Path(sys._MEIPASS if getattr(sys, 'frozen', False) else Path(__file__).parent) / "Assets"
                destination_assets_path = install_path_p / "Assets"
                if source_assets_path.exists():
                    shutil.copytree(source_assets_path, destination_assets_path, dirs_exist_ok=True)

                source_maps_path = Path(sys._MEIPASS if getattr(sys, 'frozen', False) else Path(__file__).parent) / "maps"
                destination_maps_path = install_path_p / "maps"
                if source_maps_path.exists():
                    shutil.copytree(source_maps_path, destination_maps_path, dirs_exist_ok=True)

                riot_games_exe_path = dialog.get_riot_games_path()
                switcher_instance = GameSwitcher(base_directory=install_path)
                if riot_games_exe_path:
                    switcher_instance.set_riot_client_paths(riot_games_exe_path)

                switcher_instance.set_ima_config({"app_install_path": install_path})

                if dialog.should_add_desktop_shortcut():
                    desktop_path = Path.home() / "Desktop"
                    shortcut_path = desktop_path / "iMA Switcher.lnk"
                    if not switcher_instance._create_shortcut(str(shortcut_path), str(destination_exe_path)):
                        logging.error("Failed to create desktop shortcut.")

                if dialog.should_add_start_menu_shortcut():
                    start_menu_path = Path(os.getenv("APPDATA")) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                    shortcut_path = start_menu_path / "iMA Switcher.lnk"
                    if not switcher_instance._create_shortcut(str(shortcut_path), str(destination_exe_path)):
                        logging.error("Failed to create Start Menu shortcut.")

                subprocess.Popen([destination_exe_path])
                QApplication.instance().quit()

            except (IOError, OSError) as e:
                logging.critical(
                    f"Installation Error: File system operation failed: {e}"
                )
                QMessageBox.critical(
                    None,
                    "Installation Error",
                    f"A file system error occurred during installation:\n{e}"
                )
                QApplication.instance().quit()
            except subprocess.CalledProcessError as e:
                logging.critical(
                    f"Installation Error: Subprocess failed: {e.cmd} -> {e.stderr}"
                )
                QMessageBox.critical(
                    None,
                    "Installation Error",
                    f"A command failed during installation:\n{e.cmd}\n{e.stderr}"
                )
                QApplication.instance().quit()
            except Exception as e:
                logging.critical(
                    f"Installation Error: An unexpected error occurred: {e}"
                )
                QMessageBox.critical(
                    None,
                    "Installation Error",
                    f"An unexpected error occurred during installation:\n{e}"
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
    rank_fetch_finished = pyqtSignal()
    
    switch_account_finished = pyqtSignal(bool, str, str, QPixmap, str, str, str, bool)
    add_account_finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.switcher = GameSwitcher()
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        saved_theme = ui_settings.get("theme", "dark_gold")
        apply_theme_to_app(self, saved_theme)

        if not self.switcher.is_admin():
            logging.critical("Application started without administrator privileges. Exiting.")
            QMessageBox.critical(
                self,
                "Administrator Rights Required",
                "This application requires administrator privileges for fast account switching.\n\nPlease restart as administrator.",
            )
            sys.exit(1)

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
        self.rank_fetch_finished.connect(self.on_rank_fetch_finished)
        
        self.switch_account_finished.connect(self.on_switch_account_finished)
        self.add_account_finished.connect(self.on_add_account_finished)

        def _deferred_background_tasks():
            import updater
            updater.cleanup_old_exe()
            updater.start_background_auto_updater(
                on_update_found_callback=lambda current_sha, remote_sha, url, notes: self.status_message_requested.emit(f"Update available: {remote_sha[:7]}")
            )
            ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
            if ui_settings.get("auto_rank_update", True):
                self.switcher.start_rank_update_scheduler(on_update_callback=self.account_updated.emit)
                self.initial_rank_fetch()

        QTimer.singleShot(250, _deferred_background_tasks)

        

        


    def init_ui(self):
        self.setWindowTitle("iMA Switcher")
        self.setWindowIcon(self.switcher.get_qicon_from_path(str(self.switcher.base_dir / "logo.png")))

        self.main_widget = QWidget(objectName="main_widget")
        self.setCentralWidget(self.main_widget)

        main_layout = QVBoxLayout(self.main_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(0)
        
        self.title_bar = CustomTitleBar(self)
        self.title_bar.refresh_button.clicked.connect(self.refresh_accounts)
        self.title_bar.settings_button.clicked.connect(self.show_settings_dialog)
        if hasattr(self.title_bar, 'add_account_button'):
            self.title_bar.add_account_button.clicked.connect(self.settings_handler.add_account)
        self.status_label = self.title_bar.status_label
        main_layout.addWidget(self.title_bar)
        
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addLayout(content_layout)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; } QScrollBar:vertical { border: none; background: transparent; width: 0px; } QScrollBar:horizontal { border: none; background: transparent; height: 0px; }")
        content_layout.addWidget(self.scroll_area)
        

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
            widget.set_show_last_match_info(ui_settings.get("show_last_match_info", True))
            widget.set_show_map_background(ui_settings.get("show_map_background", False))
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
            self.setFixedSize(320, 220)
            return

        sample_widget = next(iter(self.account_widgets.values()), None)
        W_W = sample_widget.width() if sample_widget else 148
        W_H = sample_widget.height() if sample_widget else 188

        S, H_M, V_M, T_B = 10, 20, 20, 44

        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        num_columns = ui_settings.get("grid_size", 4)
        display_cols = min(num_accounts, num_columns) if num_accounts > 0 else 1
        num_rows_needed = math.ceil(num_accounts / display_cols)

        grid_width = (display_cols * W_W) + ((display_cols - 1) * S) + H_M
        grid_height = (num_rows_needed * W_H) + ((num_rows_needed - 1) * S) + V_M

        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setFixedSize(grid_width + 2, grid_height + T_B + 2)
        if self.scroll_area.widget():
            self.scroll_area.widget().setFixedSize(grid_width, grid_height)

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
        if hasattr(self, 'settings_dropdown') and self.settings_dropdown is not None and self.settings_dropdown.isVisible():
            self.settings_dropdown.close_animated()
            return

        self.settings_dropdown = SettingsDropdownMenu(
            settings_button=self.title_bar.settings_button,
            actions_handler=self.settings_handler,
            parent=self
        )
        self.settings_dropdown.show_animated()

    def open_options_dialog(self):
        dialog = OptionsDialog(self.switcher, self)
        dialog.settings_applied.connect(self.load_accounts)
        dialog.exec_()

    def get_settings_actions(self):
        return {
            "Add Account": (self.settings_handler.add_account, "Add.png"),
            "Save Account": (self.settings_handler.save_current_account, "Save.png"),
            "Backup | Restore": (self.settings_handler.backup_restore_profiles, "Backup.png"),
            "Open Folder": (self.settings_handler.open_profiles_folder, "Open.png"),
            "iMA Menu": (self.settings_handler.export_ima_menu, "ima.png"),
            "Options": (self.settings_handler.open_options_dialog, "Options.png"),
        }

    def center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            self.move(screen.availableGeometry().center() - self.frameGeometry().center())

    def closeEvent(self, event):
        ima_config = self.switcher.get_ima_config()
        ima_menu_path = self.switcher.find_ima_menu_path(saved_path=ima_config.get("ima_menu_path"))
        if ima_menu_path:
            output_dir = ima_menu_path / "imports"
            output_dir.mkdir(parents=True, exist_ok=True)
            try:
                self.switcher.generate_ima_menu_script(
                    output_dir=str(output_dir),
                    title=ima_config.get("title", "Valorant"),
                    ordered_accounts=ima_config.get("ordered_accounts", []),
                    menu_icon_path=ima_config.get("menu_icon_path", ""),
                    save_config=False
                )
                self.switcher.update_ima_shell_script(ima_menu_path)
                logging.info("iMA menu script updated on application close.")
            except Exception as e:
                logging.error(f"Error updating iMA menu script on close: {e}")
        event.accept()
    
    def create_gear_icon(self, color=None):
        from PyQt5.QtCore import QRectF, Qt
        from PyQt5.QtGui import QPixmap, QPainterPath, QPainter, QColor
        from theme_manager import get_theme
        t = get_theme()
        icon_color = QColor(t['text_secondary']) if color is None else color
        pixmap = QPixmap(64, 64); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(icon_color)
        p.translate(32, 32)
        for _ in range(8): p.drawRect(QRectF(-3, -28, 6, 12)); p.rotate(45)
        path = QPainterPath(); path.addEllipse(QRectF(-16, -16, 32, 32)); path.addEllipse(QRectF(-10, -10, 20, 20))
        path.setFillRule(Qt.OddEvenFill); p.drawPath(path); p.end()
        return QIcon(pixmap)

    def create_add_icon(self, plus_color=None, bg_color=None):
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QPixmap, QPainter, QColor
        from theme_manager import get_theme
        t = get_theme()
        p_col = QColor(t['text_on_accent']) if plus_color is None else plus_color
        b_col = QColor(t['accent']) if bg_color is None else bg_color
        pixmap = QPixmap(64, 64); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(b_col)
        p.drawEllipse(0, 0, 64, 64)
        p.setBrush(p_col)
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
        if account_name in self.account_widgets:
            updated_account_data = self.switcher.get_saved_accounts().get(account_name)
            if updated_account_data:
                icon_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = updated_account_data
                ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
                use_rank_icons = ui_settings.get("use_rank_icons", False)
                icon_path_to_use = self.switcher.get_icon_path_for_account(account_name, rank, use_rank_icons)
                
                # Synchronously load the new icon for immediate update
                icon = self.switcher.get_qicon_from_path(icon_path_to_use)

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

    

    def on_rank_fetch_finished(self):
        self.status_label.setText("Ready")

    def initial_rank_fetch(self):
        """
        Fetches ranks for all accounts in separate threads after UI is shown,
        but only if auto_rank_update is enabled.
        """
        ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True):
            self.status_label.setText("Fetching all ranks...")
            def _fetch():
                self.switcher.fetch_and_update_all_accounts(self.account_updated.emit)
                self.rank_fetch_finished.emit()
            threading.Thread(target=_fetch, daemon=True).start()
        else:
            logging.info("Initial rank fetch skipped: Auto rank update is disabled.")

    def refresh_accounts(self):
        self.status_label.setText("Refreshing accounts...")
        def _fetch():
            self.switcher.fetch_and_update_all_accounts(self.account_updated.emit, is_manual_refresh=True)
            self.rank_fetch_finished.emit()
        threading.Thread(target=_fetch, daemon=True).start()

    def event(self, event):
        if event.type() == CustomUpdateEvent.EVENT_TYPE:
            self.on_account_updated(event.account_name)
            return True
        return super().event(event)

    def _create_styled_menu(self, title=None):
        menu = QMenu(title, self) if title else QMenu(self)
        menu.setWindowFlags(menu.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        menu.setAttribute(Qt.WA_TranslucentBackground)
        return menu

    def show_context_menu(self, name, pos):
        self.on_account_selected(name)
        menu = self._create_styled_menu()
        actions = {
            "Switch Account": (self.switch_to_selected_account, "Switch.png"),
            "Customize": (self.context_handler.customize_account, "Settings.png"),
            "History": (self.context_handler.show_history, "history.png"),
            "Create Desktop Shortcut": (self.context_handler.create_shortcut, "Create.png"),
        }
        
        set_rank_menu = self._create_styled_menu("Set Rank")
        set_rank_menu.setIcon(self.switcher.get_qicon_from_path(str(Path(__file__).parent / "Assets" / "radiant.png")))

        unranked_icon_path = Path(__file__).parent / "Assets" / "unranked.png"
        unranked_action = QAction("Unranked", self)
        if unranked_icon_path.exists():
            unranked_action.setIcon(self.switcher.get_qicon_from_path(str(unranked_icon_path)))
        unranked_action.triggered.connect(lambda checked, r="Unranked": self.context_handler.set_rank(r))
        set_rank_menu.addAction(unranked_action)

        ranks_with_tiers = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal"]
        for rank_name in ranks_with_tiers:
            rank_tier_menu = self._create_styled_menu(rank_name)
            first_tier_icon_path = Path(__file__).parent / "Assets" / f"{rank_name.lower()}_1.png"
            if first_tier_icon_path.exists():
                rank_tier_menu.setIcon(self.switcher.get_qicon_from_path(str(first_tier_icon_path)))
            
            for i in range(1, 4):
                full_rank_name = f"{rank_name} {i}"
                rank_icon_path = Path(__file__).parent / "Assets" / f"{rank_name.lower()}_{i}.png"
                
                action = QAction(full_rank_name, self)
                if rank_icon_path.exists():
                    action.setIcon(self.switcher.get_qicon_from_path(str(rank_icon_path)))
                action.triggered.connect(lambda checked, r=full_rank_name: self.context_handler.set_rank(r))
                rank_tier_menu.addAction(action)
            set_rank_menu.addMenu(rank_tier_menu)

        radiant_icon_path = Path(__file__).parent / "Assets" / "radiant.png"
        radiant_action = QAction("Radiant", self)
        if radiant_icon_path.exists():
            radiant_action.setIcon(self.switcher.get_qicon_from_path(str(radiant_icon_path)))
        radiant_action.triggered.connect(lambda checked, r="Radiant": self.context_handler.set_rank(r))
        set_rank_menu.addAction(radiant_action)

        menu.addMenu(set_rank_menu)
        
        change_game_menu = self._create_styled_menu("Change Game")
        change_game_menu.setIcon(self.switcher.get_qicon_from_path(str(Path(__file__).parent / "Assets" / "Riot.png")))
        valorant_icon_path = Path(__file__).parent / "Assets" / "valorant.png"
        lol_icon_path = Path(__file__).parent / "Assets" / "lol.png"
        
        if valorant_icon_path.exists():
            change_game_menu.addAction(QAction(self.switcher.get_qicon_from_path(str(valorant_icon_path)), "Valorant", self, triggered=lambda: self.context_handler.change_game('valorant')))

        if lol_icon_path.exists():
            change_game_menu.addAction(QAction(self.switcher.get_qicon_from_path(str(lol_icon_path)), "League of Legends", self, triggered=lambda: self.context_handler.change_game('lol')))

        riot_icon_path = Path(__file__).parent / "Assets" / "Riot.png"
        if riot_icon_path.exists():
            change_game_menu.addAction(QAction(self.switcher.get_qicon_from_path(str(riot_icon_path)), "Both", self, triggered=lambda: self.context_handler.change_game('both')))

        menu.addMenu(change_game_menu)
        menu.addSeparator()
        actions["Delete Account"] = (self.context_handler.delete, "Delete.png")

        for text, data in actions.items():
            if text:
                func, icon_name = data
                icon_path = Path(__file__).parent / "Assets" / icon_name
                if icon_path.exists():
                    menu.addAction(QAction(self.switcher.get_qicon_from_path(str(icon_path)), text, self, triggered=func))
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

        threading.Thread(target=self._switch_account_thread, args=(name, selected_game), daemon=True).start()

    def _handle_game_selection(self, account_name, game):
        # Called when a game is selected from GameSelectionDialog
        self.switch_to_selected_account(selected_game=game)

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
                found_path = self.switcher._find_riot_client_path()
                if found_path:
                    self.switcher.set_riot_client_paths(found_path)
                    self.status_label.setText("Riot Client path found automatically. Retrying switch...")
                    self.switch_to_selected_account()
                else:
                    dialog = RiotClientNotFoundDialog(self)
                    if dialog.exec_() == QDialog.Accepted:
                        new_path = dialog.get_path()
                        if new_path and os.path.exists(new_path):
                            self.switcher.set_riot_client_paths(new_path)
                            self.switch_to_selected_account()
            else:
                self.status_label.setText(f"Failed to switch to '{name}'.")
                QMessageBox.critical(self, "Switch Failed", message)
            if hasattr(self, "launch_notification"): self.launch_notification.close()
        else:
            if hasattr(self, "launch_notification") and self.launch_notification:
                try:
                    self.launch_notification.close()
                except RuntimeError:
                    pass
            ui_settings = self.switcher.get_ima_config().get("ui_settings", {})
            if ui_settings.get("show_splash_notification", True):
                try:
                    self.launch_notification = LaunchNotificationWidget(name, account_icon_pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, switcher_instance=self.switcher)
                    self.launch_notification.show()
                except Exception as e:
                    logging.error(f"Could not create notification: {e}")
        self.refresh_accounts() # Refresh after any switch attempt

    def on_add_account_finished(self, success):
        if success:
            self.status_label.setText("New account detected. Please save it.")
            # Bring window to front
            self.showNormal()
            self.activateWindow()
            self.raise_()
            self.settings_handler.save_current_account()
        else:
            self.status_label.setText("Add account flow failed or was cancelled.")

    

    

def _handle_game_selection_standalone(switcher, account_name, game, pixmap):
    # This method is called when a game is selected from the GameSelectionDialog in standalone mode
    result, _, _ = switcher.switch_account(account_name, selected_game=game)
    if result:
        account_data = switcher.get_saved_accounts().get(account_name)
        _, _, rank, in_game_name, in_game_tag, _, _ = account_data if account_data else (None, None, None, None, None, None, None)
        ui_settings = switcher.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)

        if ui_settings.get("show_splash_notification", True):
            notification = LaunchNotificationWidget(account_name, pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=True, switcher_instance=switcher)
            notification.show()
    else:
        sys.exit(1)


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    current_exe_name = os.path.basename(sys.executable if getattr(sys, 'frozen', False) else sys.argv[0])
    
    if "--update" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "--update"):
        run_update_installer()
    elif "--map-planner" in sys.argv or (len(sys.argv) > 1 and sys.argv[1] == "--map-planner"):
        from map_planner import launch_standalone_map_planner
        launch_standalone_map_planner()
    elif "Installer" in current_exe_name: 
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

                if ui_settings.get("show_splash_notification", True):
                    notification = LaunchNotificationWidget(account_name, pixmap, in_game_name=in_game_name, in_game_tag=in_game_tag, rank=rank, use_rank_icons=use_rank_icons, standalone=True, switcher_instance=switcher)
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
