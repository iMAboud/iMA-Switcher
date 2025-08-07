import os
import threading
import logging
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog, QApplication
from ui_components import (
    SaveAccountDialog, ExportIMAMenuDialog, OptionsDialog, 
    CustomMessageDialog, ConfirmDeleteDialog, BackupRestoreDialog, 
    BackupRestoreSelectionDialog, IMAMenuPathDialog, LoadingDialog
)
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

    def backup_restore_profiles(self):
        selection_dialog = BackupRestoreSelectionDialog(self.parent)
        if selection_dialog.exec_() != QDialog.Accepted:
            return

        selection = selection_dialog.get_selection()
        if not selection:
            return

        dialog = BackupRestoreDialog(self.parent, mode=selection)
        if dialog.exec_() != QDialog.Accepted:
            return

        backup_type = dialog.get_selection()
        if not backup_type:
            return

        if selection == "backup":
            if backup_type == "local":
                self._backup_local()
            elif backup_type == "google_drive":
                threading.Thread(target=self._backup_google_drive, daemon=True).start()
        elif selection == "restore":
            if backup_type == "local":
                self._restore_local()
            elif backup_type == "google_drive":
                threading.Thread(target=self._restore_google_drive, daemon=True).start()

    def _backup_local(self):
        backup_filename = f"{self.switcher.get_backup_filename()}.zip"
        path, _ = QFileDialog.getSaveFileName(self.parent, "Save Backup", backup_filename, "ZIP Files (*.zip)")
        if not path:
            return

        loading_dialog = LoadingDialog("Backing Up", "Backing up profiles...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()

        if self.switcher.backup_profiles(path):
            loading_dialog.close()
            msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up locally.", self.parent)
            msg_dialog.exec_()
            logging.info(f"Profiles backed up to {path}")
        else:
            loading_dialog.close()
            self.parent.status_label.setText("Backup failed.")
            logging.error(f"Failed to backup profiles to {path}")

    def _backup_google_drive(self):
        loading_dialog = LoadingDialog("Backing Up", "Backing up profiles to Google Drive...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()

        temp_file_path = None
        try:
            backup_filename_base = self.switcher.get_backup_filename()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file_path = temp_file.name

            if self.switcher.backup_profiles(temp_file_path):
                drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
                backup_filename_zip = f"{backup_filename_base}.zip"
                drive_api.upload_file(temp_file_path, backup_filename_zip)

                loading_dialog.close()
                msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up to Google Drive.", self.parent)
                msg_dialog.exec_()
                logging.info(f"Profiles backed up to Google Drive: {backup_filename_zip}")
            else:
                loading_dialog.close()
                self.parent.status_label.setText("Backup failed.")
                logging.error("Failed to create backup file.")
                QMessageBox.critical(self.parent, "Backup Failed", "Could not create the backup file.")

        except (IOError, ConnectionAbortedError) as e:
            loading_dialog.close()
            self.parent.status_label.setText("Google Drive backup failed.")
            logging.error(f"Google Drive backup failed: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", str(e))
        except Exception as e:
            loading_dialog.close()
            self.parent.status_label.setText("Google Drive backup failed.")
            logging.error(f"An unexpected error occurred during Google Drive backup: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", f"An unexpected error occurred: {e}")
        finally:
            loading_dialog.close()
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logging.info(f"Successfully cleaned up temp file: {temp_file_path}")
                except OSError as e:
                    logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

    def _restore_local(self):
        path, _ = QFileDialog.getOpenFileName(self.parent, "Select Backup", "", "ZIP Files (*.zip)")
        if path:
            threading.Thread(target=self._run_restore, args=(path,)).start()

    def _run_restore(self, path, modified_time=None):
        loading_dialog = LoadingDialog("Restoring", "Restoring profiles...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()
        self._confirm_and_restore(path, modified_time)
        loading_dialog.close()

    def _restore_google_drive(self):
        threading.Thread(target=self._run_restore_google_drive).start()

    def _run_restore_google_drive(self):
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
            loading_dialog = LoadingDialog("Backing Up", "Backing up profiles...", self.parent)
            loading_dialog.show()
            QApplication.processEvents()
            if self.switcher.backup_profiles(path):
                loading_dialog.close()
                msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up locally.", self.parent)
                msg_dialog.exec_()
                logging.info(f"Profiles backed up to {path}")
            else:
                loading_dialog.close()
                self.parent.status_label.setText("Backup failed.")
                logging.error(f"Failed to backup profiles to {path}")

    def _backup_google_drive(self):
        loading_dialog = LoadingDialog("Backing Up", "Backing up profiles to Google Drive...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()

        temp_file_path = None
        try:
            backup_filename_base = self.switcher.get_backup_filename()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file_path = temp_file.name
            
            if self.switcher.backup_profiles(temp_file_path):
                drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
                backup_filename_zip = f"{backup_filename_base}.zip"
                drive_api.upload_file(temp_file_path, backup_filename_zip)
                
                loading_dialog.close()
                msg_dialog = CustomMessageDialog("Backup Successful", "Profiles backed up to Google Drive.", self.parent)
                msg_dialog.exec_()
                logging.info(f"Profiles backed up to Google Drive: {backup_filename_zip}")
            else:
                loading_dialog.close()
                self.parent.status_label.setText("Backup failed.")
                logging.error("Failed to create backup file.")
                QMessageBox.critical(self.parent, "Backup Failed", "Could not create the backup file.")

        except (IOError, ConnectionAbortedError) as e:
            loading_dialog.close()
            self.parent.status_label.setText("Google Drive backup failed.")
            logging.error(f"Google Drive backup failed: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", str(e))
        except Exception as e:
            loading_dialog.close()
            self.parent.status_label.setText("Google Drive backup failed.")
            logging.error(f"An unexpected error occurred during Google Drive backup: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", f"An unexpected error occurred: {e}")
        finally:
            loading_dialog.close()
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logging.info(f"Successfully cleaned up temp file: {temp_file_path}")
                except OSError as e:
                    logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

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
            threading.Thread(target=self._run_restore, args=(path,)).start()

    def _run_restore(self, path, modified_time=None):
        loading_dialog = LoadingDialog("Restoring", "Restoring profiles...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()
        self._confirm_and_restore(path, modified_time)
        loading_dialog.close()

    def _restore_google_drive(self):
        threading.Thread(target=self._run_restore_google_drive).start()

    def _run_restore_google_drive(self):
        loading_dialog = LoadingDialog("Restoring", "Restoring profiles from Google Drive...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()

        temp_file_path = None
        try:
            drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
            backup_file = drive_api.find_latest_backup("iMA-Switcher_")
            if backup_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                    temp_file_path = temp_file.name
                
                drive_api.download_file(backup_file['id'], temp_file_path)
                self._confirm_and_restore(temp_file_path, backup_file['modifiedTime'])
                loading_dialog.close()
            else:
                loading_dialog.close()
                QMessageBox.warning(self.parent, "No Backup Found", "No backup file found on your Google Drive.")
        except (IOError, ConnectionAbortedError) as e:
            loading_dialog.close()
            self.parent.status_label.setText("Google Drive restore failed.")
            logging.error(f"Google Drive restore failed: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", str(e))
        except Exception as e:
            loading_dialog.close()
            self.parent.status_label.setText("Google Drive restore failed.")
            logging.error(f"An unexpected error occurred during Google Drive restore: {e}")
            QMessageBox.critical(self.parent, "Google Drive Error", f"An unexpected error occurred: {e}")
        finally:
            loading_dialog.close()
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                    logging.info(f"Successfully cleaned up temp file: {temp_file_path}")
                except OSError as e:
                    logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")
                except Exception as e:
                    logging.error(f"An unexpected error occurred while cleaning up temp file {temp_file_path}: {e}")

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
                logging.info("Calling load_accounts after restore.")
                self.parent.load_accounts()
                logging.info(f"Profiles restored from {path}. UI should be refreshed.")
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

        # Dialog to get settings from user
        dialog = ExportIMAMenuDialog(accounts_data, self.parent, default_settings=ima_config)
        if dialog.exec_() != QDialog.Accepted:
            return

        settings = dialog.get_settings()

        # Determine and validate iMA Menu path
        ima_menu_path_str = ima_config.get("ima_menu_path") or r"C:\Program Files\iMA Menu"
        ima_menu_path = Path(ima_menu_path_str)

        if not (ima_menu_path / "shell.nss").exists():
            path_dialog = IMAMenuPathDialog(self.parent, default_path=ima_menu_path_str)
            if path_dialog.exec_() == QDialog.Accepted:
                new_path_str = path_dialog.get_path()
                if not new_path_str or not (Path(new_path_str) / "shell.nss").exists():
                    QMessageBox.critical(self.parent, "Path Error", "The selected path is invalid or does not contain shell.nss.")
                    return
                ima_menu_path = Path(new_path_str)
            else:
                return # User cancelled

        # All checks passed, now save all settings together
        self.switcher.set_ima_config({
            "title": settings["title"],
            "menu_icon_path": settings["menu_icon_path"],
            "ordered_accounts": settings["ordered_accounts"],
            "ima_menu_path": str(ima_menu_path) # Save the validated path
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

            msg_dialog = CustomMessageDialog("Export Successful", "Accounts added to iMA Menu", self.parent)
            msg_dialog.exec_()
            self.parent.load_accounts() # Refresh accounts in UI after export
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

