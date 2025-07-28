import os
import threading
import logging
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog
from ui_components import SaveAccountDialog, ExportIMAMenuDialog, OptionsDialog, CustomMessageDialog, ConfirmDeleteDialog, BackupRestoreDialog
from google_drive_api import GoogleDriveAPI
import tempfile
from pathlib import Path

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
            name, game, in_game_name, in_game_tag = dialog.get_details()
            if not name:
                self.parent.status_label.setText("Account name cannot be empty.")
                return
            if name in self.switcher.get_saved_accounts():
                logging.warning(f"Attempted to save account '{name}', but an account with that name already exists.")
                QMessageBox.warning(self.parent, "Account Exists", f'An account named "{name}" already exists. Please choose a different name.')
                return
            self.switcher.save_account(name, game, in_game_name=in_game_name, in_game_tag=in_game_tag)
            self.parent.status_label.setText(f"Account '{name}' saved for {game.capitalize()}. ")
            self.parent.load_accounts()

    def _add_account_thread(self):
        success = self.switcher.add_account_flow()
        self.parent.add_account_finished.emit(success)

    def backup_profiles(self):
        dialog = BackupRestoreDialog(self.parent, mode='backup')
        if dialog.exec_() == QDialog.Accepted:
            backup_type = dialog.get_selection()
            if backup_type == "local":
                self._backup_local()
            elif backup_type == "google_drive":
                self._backup_google_drive()

    def _backup_local(self):
        suggested_filename = self.switcher.get_backup_filename()
        path, _ = QFileDialog.getSaveFileName(self.parent, "Save Backup", suggested_filename, "ZIP Files (*.zip)")
        if path:
            path_p = Path(path)
            if not path_p.suffix == ".zip": path_p = path_p.with_suffix(".zip")
            if self.switcher.backup_profiles(str(path_p)):
                self.parent.status_label.setText(f"Profiles backed up successfully.")
                logging.info(f"Profiles backed up to {path}")
            else:
                self.parent.status_label.setText("Backup failed.")
                logging.error(f"Failed to backup profiles to {path}")

    def _backup_google_drive(self):
        temp_file_path = None
        try:
            drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
            # Delete all old backups
            for old_backup in drive_api.find_all_backups("iMA-Switcher_"):
                drive_api.delete_file(old_backup['id'])

            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file_path = temp_file.name

            if self.switcher.backup_profiles(temp_file_path):
                file_name = Path(self.switcher.get_backup_filename()).name + ".zip"
                drive_api.upload_file(temp_file_path, file_name)
                msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up to Google Drive.", self.parent)
                msg_dialog.exec_()
                logging.info("Profiles backed up to Google Drive.")
            else:
                self.parent.status_label.setText("Backup failed.")
        except Exception as e:
            self.parent.status_label.setText("Google Drive backup failed.")
            logging.error(f"Google Drive backup failed: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", str(e))
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logging.info(f"Successfully cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

    def restore_profiles(self):
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
        temp_file_path = None
        try:
            drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
            backup_file = drive_api.find_latest_backup("iMA-Switcher_")
            if backup_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                    temp_file_path = temp_file.name
                
                drive_api.download_file(backup_file['id'], temp_file_path)
                self._confirm_and_restore(temp_file_path, backup_file['modifiedTime'])
            else:
                QMessageBox.warning(self.parent, "No Backup Found", "No backup file found on your Google Drive.")
        except Exception as e:
            self.parent.status_label.setText("Google Drive restore failed.")
            logging.error(f"Google Drive restore failed: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", str(e))
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logging.info(f"Successfully cleaned up temp file: {temp_file_path}")
                except Exception as e:
                    logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

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
        if not ima_config.get("menu_icon_path"):
            default_ico = Path(r"C:\Program Files\iMA Menu\icons\valorant.ico")
            if default_ico.exists(): ima_config["menu_icon_path"] = str(default_ico)

        dialog = ExportIMAMenuDialog(accounts_data, self.parent, default_settings=ima_config)
        
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            output_dir = ima_config.get("output_dir") or r"C:\Program Files\iMA Menu\imports"
            if not Path(output_dir).is_dir():
                output_dir = QFileDialog.getExistingDirectory(self.parent, "Could not find default iMA Menu path. Please locate the 'imports' folder.")
                if not output_dir: return
            if not output_dir: return # Added this line to handle cancellation
            try:
                self.switcher.generate_ima_menu_script(**settings, output_dir=output_dir, save_config=True)
                msg_dialog = CustomMessageDialog("Export Successful", "Accounts added to iMA Menu", self.parent)
                msg_dialog.exec_()
                self.parent.load_accounts() # Refresh accounts in UI after export
                logging.info(f"Successfully exported iMA Menu script to {output_dir}")
            except Exception as e:
                logging.error(f"An error occurred during iMA Menu export: {e}")
                QMessageBox.critical(self.parent, "Export Failed", f"An error occurred: {e}")

    def open_options_dialog(self):
        self.options_dialog = OptionsDialog(self.switcher, self.parent)
        self.options_dialog.settings_applied.connect(self.parent.load_accounts)
        self.options_dialog.show()

