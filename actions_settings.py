import os
import threading
import logging
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from ui_components import (
    SaveAccountDialog, ExportIMAMenuDialog, OptionsDialog, 
    CustomMessageDialog, ConfirmDeleteDialog, BackupRestoreDialog, 
    BackupRestoreSelectionDialog, IMAMenuPathDialog, UpdateDialog
)
import tempfile
import importlib
from pathlib import Path

class GoogleDriveBackupWorker(QThread):
    finished = pyqtSignal(bool, str)
    
    def __init__(self, switcher, temp_file_path, backup_filename_zip):
        super().__init__()
        self.switcher = switcher
        self.temp_file_path = temp_file_path
        self.backup_filename_zip = backup_filename_zip

    def run(self):
        try:
            if not self.switcher.backup_profiles(self.temp_file_path):
                raise Exception("Failed to create the local zip archive for backup.")
            from google_drive_api import GoogleDriveAPI
            drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
            drive_api.upload_file(self.temp_file_path, self.backup_filename_zip)
            self.finished.emit(True, self.backup_filename_zip)
        except Exception as e:
            self.finished.emit(False, str(e))

class GoogleDriveRestoreWorker(QThread):
    finished = pyqtSignal(bool, object, str)

    def __init__(self, switcher):
        super().__init__()
        self.switcher = switcher

    def run(self):
        try:
            from google_drive_api import GoogleDriveAPI
            drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
            backup_file = drive_api.find_latest_backup("iMA-Switcher_")
            if backup_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                    temp_file_path = temp_file.name
                drive_api.download_file(backup_file['id'], temp_file_path)
                self.finished.emit(True, backup_file, temp_file_path)
            else:
                self.finished.emit(True, None, None)
        except Exception as e:
            self.finished.emit(False, None, str(e))

class SettingsActions:
    def __init__(self, parent):
        """
        Initializes the actions handler for the settings menu.
        :param parent: A reference to the main ModernValorantSwitcher window.
        """
        self.parent = parent
        self.switcher = parent.switcher

    def add_account(self):
        self.parent.status_label.setText("Preparing for new account...")
        threading.Thread(target=self._add_account_thread, daemon=True).start()

    def save_current_account(self):
        dialog = SaveAccountDialog(self.parent, switcher_instance=self.switcher)
        if dialog.exec_() == QDialog.Accepted:
            name, game, in_game_name, in_game_tag, puuid = dialog.get_details()
            if not name:
                self.parent.status_label.setText("Account name cannot be empty.")
                return
            if name in self.switcher.get_saved_accounts():
                logging.warning(f"Attempted to save account '{name}', but an account with that name already exists.")
                QMessageBox.warning(self.parent, "Account Exists", f'An account named "{name}" already exists. Please choose a different name.')
                return
            self.switcher.save_account(name, game, in_game_name=in_game_name, in_game_tag=in_game_tag, puuid=puuid)
            self.parent.status_label.setText(f"Account '{name}' saved for {game.capitalize()}. ")
            self.parent.load_accounts()

    def _add_account_thread(self):
        success = self.switcher.add_account_flow()
        self.parent.add_account_finished.emit(success)

    def backup_restore_profiles(self):
        selection_dialog = BackupRestoreSelectionDialog(self.parent)
        if selection_dialog.exec_() == QDialog.Accepted:
            selection = selection_dialog.get_selection()
            if selection == "backup":
                self._handle_backup_selection()
            elif selection == "restore":
                self._handle_restore_selection()

    def _handle_backup_selection(self):
        dialog = BackupRestoreDialog(self.parent, mode='backup')
        if dialog.exec_() == QDialog.Accepted:
            backup_type = dialog.get_selection()
            if backup_type == "local":
                self._backup_local()
            elif backup_type == "google_drive":
                self._backup_google_drive()

    def _backup_local(self):
        backup_filename = f"{self.switcher.get_backup_filename()}.zip"
        path, _ = QFileDialog.getSaveFileName(self.parent, "Save Backup", backup_filename, "ZIP Files (*.zip)")
        if path:
            if self.switcher.backup_profiles(path):
                msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up locally.", self.parent)
                msg_dialog.exec_()
                logging.info(f"Profiles backed up to {path}")
            else:
                self.parent.status_label.setText("Backup failed.")
                logging.error(f"Failed to backup profiles to {path}")

    def _backup_google_drive(self):
        self.parent.status_label.setText("Preparing backup for Google Drive...")
        backup_filename_base = self.switcher.get_backup_filename()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            temp_file_path = temp_file.name
        
        backup_filename_zip = f"{backup_filename_base}.zip"
        self.backup_worker = GoogleDriveBackupWorker(self.switcher, temp_file_path, backup_filename_zip)
        self.backup_worker.finished.connect(self._on_backup_google_drive_finished)
        self.backup_worker.start()

    def _on_backup_google_drive_finished(self, success, result):
        if success:
            msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up to Google Drive.", self.parent)
            msg_dialog.exec_()
            self.parent.status_label.setText("Backup to Google Drive complete.")
            logging.info(f"Profiles backed up to Google Drive: {result}")
        else:
            self.parent.status_label.setText("Google Drive backup failed.")
            logging.error(f"Google Drive backup failed: {result}")
            QMessageBox.critical(self.parent, "Google Drive Error", f"Error: {result}")
        
        if hasattr(self, 'backup_worker') and self.backup_worker.temp_file_path:
            if Path(self.backup_worker.temp_file_path).exists():
                try:
                    Path(self.backup_worker.temp_file_path).unlink()
                except OSError:
                    pass

    def _handle_restore_selection(self):
        dialog = BackupRestoreDialog(self.parent, mode='restore')
        if dialog.exec_() == QDialog.Accepted:
            restore_type = dialog.get_selection()
            if restore_type == "local":
                self._restore_local()
            elif restore_type == "google_drive":
                self._restore_google_drive()

    def _restore_local(self):
        path, _ = QFileDialog.getOpenFileName(self.parent, "Select Backup", "", "ZIP Files (*.zip)")
        if path:
            self._confirm_and_restore(path)

    def _restore_google_drive(self):
        self.parent.status_label.setText("Connecting to Google Drive...")
        self.restore_worker = GoogleDriveRestoreWorker(self.switcher)
        self.restore_worker.finished.connect(self._on_restore_google_drive_finished)
        self.restore_worker.start()

    def _on_restore_google_drive_finished(self, success, backup_file, error_msg_or_path):
        if success:
            if backup_file:
                temp_file_path = error_msg_or_path
                self.parent.status_label.setText("Restoring from Google Drive...")
                self._confirm_and_restore(temp_file_path, backup_file.get('modifiedTime'))
                if Path(temp_file_path).exists():
                    try:
                        Path(temp_file_path).unlink()
                    except OSError:
                        pass
                self.parent.status_label.setText("Ready.")
            else:
                self.parent.status_label.setText("Ready.")
                QMessageBox.warning(self.parent, "No Backup Found", "No backup file found on your Google Drive.")
        else:
            self.parent.status_label.setText("Google Drive restore failed.")
            logging.error(f"Google Drive restore failed: {error_msg_or_path}")
            QMessageBox.critical(self.parent, "Google Drive Error", f"Error: {error_msg_or_path}")

    def _confirm_and_restore(self, path, modified_time=None):
        message = "Are you sure you want to overwrite\ncurrent settings?"
        if modified_time:
            message = f"Restore from backup created on\n{modified_time}?"
        
        dialog = ConfirmDeleteDialog(
            account_name="", 
            parent=self.parent,
            title="Confirm Restore",
            message=message
        )
        if dialog.exec_() == QDialog.Accepted:
            if self.switcher.restore_profiles(path):
                msg_dialog = CustomMessageDialog("Restore Successful", "Profiles restored successfully.", self.parent)
                msg_dialog.exec_()
                self.parent.load_accounts()
                logging.info(f"Profiles restored from {path}")
            else:
                self.parent.status_label.setText("Restore failed.")
                logging.error(f"Failed to restore profiles from {path}")

    def open_profiles_folder(self):
        os.startfile(str(self.switcher.profiles_dir))

    def export_ima_menu(self):
        accounts_data = self.switcher.get_saved_accounts()
        if not accounts_data:
            QMessageBox.warning(self.parent, "No Accounts", "You must save at least one account before exporting.")
            return

        ima_config = self.switcher.get_ima_config()
        saved_path = ima_config.get("ima_menu_path")
        ima_menu_path = self.switcher.find_ima_menu_path(saved_path=saved_path)

        valo_nss_exists = False
        if ima_menu_path and (ima_menu_path / "imports" / "valo.nss").exists():
            valo_nss_exists = True

        if not valo_nss_exists or not ima_config.get("menu_icon_path"):
            default_icon_path = Path(self.switcher.base_dir) / "Assets" / "valorant" / "5.png"
            if default_icon_path.exists():
                ima_config["menu_icon_path"] = str(default_icon_path)

        dialog = ExportIMAMenuDialog(accounts_data, self.parent, default_settings=ima_config)
        if dialog.exec_() != QDialog.Accepted:
            return

        settings = dialog.get_settings()

        if not ima_menu_path:
            default_prompt_path = saved_path or r"C:\Program Files\iMA Menu"
            path_dialog = IMAMenuPathDialog(self.parent, default_path=default_prompt_path)
            if path_dialog.exec_() == QDialog.Accepted:
                new_path_str = path_dialog.get_path()
                if not new_path_str or not (Path(new_path_str) / "shell.nss").exists():
                    QMessageBox.critical(self.parent, "Path Error", "The selected path is invalid or does not contain shell.nss.")
                    return
                ima_menu_path = Path(new_path_str)
            else:
                return

        ui_settings = ima_config.get("ui_settings", {})
        ui_settings["show_rank_tips"] = settings.get("show_rank_tips", False)
        ui_settings["show_rr_in_tip"] = settings.get("show_rr_in_tip", False)
        ui_settings["tip_delay"] = settings.get("tip_delay", 1.0)

        # All checks passed, now save all settings together
        self.switcher.set_ima_config({
            "title": settings["title"],
            "menu_icon_path": settings["menu_icon_path"],
            "ordered_accounts": settings["ordered_accounts"],
            "ima_menu_path": str(ima_menu_path), # Save the validated path
            "ui_settings": ui_settings
        })

        output_dir = ima_menu_path / "imports"
        output_dir.mkdir(exist_ok=True)

        try:
            # Generate the valo.nss script
            self.switcher.generate_ima_menu_script(
                output_dir=str(output_dir), 
                title=settings["title"], 
                ordered_accounts=settings["ordered_accounts"], 
                menu_icon_path=settings["menu_icon_path"], 
                save_config=False # Config is already saved
            )
            
            # Update the shell.nss script
            success, message = self.switcher.update_ima_shell_script(ima_menu_path)
            if not success:
                QMessageBox.warning(self.parent, "Shell Script Warning", message)

            self.parent.load_accounts() # Refresh accounts in UI after export
            self.parent.status_label.setText("Accounts added to iMA Menu.")
            QTimer.singleShot(3000, lambda: self.parent.status_label.setText("Ready."))
            logging.info(f"Successfully exported iMA Menu script to {output_dir}")

        except (IOError, OSError) as e:
            logging.error(f"An error occurred during iMA Menu export: {e}")
            QMessageBox.critical(self.parent, "Export Failed", f"An error occurred during export: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred during iMA Menu export: {e}")
            QMessageBox.critical(self.parent, "Export Failed", f"An unexpected error occurred: {e}")

    def open_options_dialog(self):
        self.options_dialog = OptionsDialog(self.switcher, self.parent)
        self.options_dialog.settings_applied.connect(self.parent.load_accounts)
        self.options_dialog.show()

    def open_update_dialog(self):
        self.update_dialog = UpdateDialog(self.switcher, self.parent)
        self.update_dialog.show()

