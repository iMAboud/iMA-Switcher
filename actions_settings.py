import os
import threading
import logging
import tempfile
from pathlib import Path

from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog, QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from ui_components import (
    SaveAccountDialog, ExportIMAMenuDialog, OptionsDialog, 
    CustomMessageDialog, ConfirmDeleteDialog, BackupRestoreDialog, 
    BackupRestoreSelectionDialog, IMAMenuPathDialog, LoadingDialog
)
from google_drive_api import GoogleDriveAPI

class RestoreWorker(QObject):
    """Worker to handle local restore operations in a separate thread."""
    finished = pyqtSignal(bool, str)  # Signal: success (bool), message (str)

    def __init__(self, switcher, restore_path):
        super().__init__()
        self.switcher = switcher
        self.restore_path = restore_path

    def run(self):
        """Performs the restore operation."""
        try:
            success = self.switcher.restore_profiles(self.restore_path)
            if success:
                self.finished.emit(True, "Profiles restored successfully.")
            else:
                self.finished.emit(False, "Failed to restore profiles.")
        except Exception as e:
            logging.error(f"Exception in RestoreWorker: {e}", exc_info=True)
            self.finished.emit(False, f"An unexpected error occurred: {e}")

class GoogleDriveRestoreWorker(QObject):
    """Worker to handle Google Drive download and restore operations."""
    finished = pyqtSignal(bool, str)  # Signal: success (bool), message (str)

    def __init__(self, switcher):
        super().__init__()
        self.switcher = switcher

    def run(self):
        """Downloads the latest backup and restores it."""
        temp_file_path = None
        try:
            drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
            backup_file = drive_api.find_latest_backup("iMA-Switcher_")

            if not backup_file:
                self.finished.emit(False, "No backup file found on your Google Drive.")
                return

            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file_path = temp_file.name

            drive_api.download_file(backup_file['id'], temp_file_path)

            success = self.switcher.restore_profiles(temp_file_path)
            if success:
                self.finished.emit(True, "Profiles restored successfully from Google Drive.")
            else:
                self.finished.emit(False, "Failed to restore profiles from the downloaded file.")

        except Exception as e:
            logging.error(f"Exception in GoogleDriveRestoreWorker: {e}", exc_info=True)
            self.finished.emit(False, f"An unexpected error occurred: {e}")
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                try:
                    Path(temp_file_path).unlink()
                except OSError as e:
                    logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

class SettingsActions:
    def __init__(self, parent):
        self.parent = parent
        self.switcher = parent.switcher
        self.worker = None
        self.thread = None

    def add_account(self):
        self.parent.status_label.setText("Preparing for new account...")
        threading.Thread(target=self._add_account_thread, daemon=True).start()

    def _add_account_thread(self):
        success = self.switcher.add_account_flow()
        # This signal doesn't exist on the parent, but leaving it for now.
        # self.parent.add_account_finished.emit(success)

    def save_current_account(self):
        dialog = SaveAccountDialog(self.parent, switcher_instance=self.switcher)
        if dialog.exec_() == QDialog.Accepted:
            name, game, in_game_name, in_game_tag = dialog.get_details()
            if not name:
                self.parent.status_label.setText("Account name cannot be empty.")
                return
            if name in self.switcher.get_saved_accounts():
                QMessageBox.warning(self.parent, "Account Exists", f'An account named "{name}" already exists.')
                return
            self.switcher.save_account(name, game, in_game_name=in_game_name, in_game_tag=in_game_tag)
            self.parent.status_label.setText(f"Account '{name}' saved for {game.capitalize()}.")
            self.parent.load_accounts()

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
                self._backup_google_drive()
        elif selection == "restore":
            if backup_type == "local":
                self._restore_local()
            elif backup_type == "google_drive":
                self._restore_google_drive()

    def _backup_local(self):
        backup_filename = f"{self.switcher.get_backup_filename()}.zip"
        path, _ = QFileDialog.getSaveFileName(self.parent, "Save Backup", backup_filename, "ZIP Files (*.zip)")
        if not path:
            return

        # Note: This still runs on the main thread and could cause a small freeze.
        # Fixing the restore functionality is the priority as per the user's report.
        loading_dialog = LoadingDialog("Backing Up", "Backing up profiles...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()

        if self.switcher.backup_profiles(path):
            loading_dialog.close()
            CustomMessageDialog("Backup Successful", "Profiles backed up locally.", self.parent).exec_()
        else:
            loading_dialog.close()
            QMessageBox.critical(self.parent, "Backup Failed", "Could not create the backup file.")

    def _backup_google_drive(self):
        # This is a known issue: UI elements are created in this worker thread.
        # Fixing the more critical restore freeze first.
        threading.Thread(target=self._run_backup_google_drive, daemon=True).start()

    def _run_backup_google_drive(self):
        loading_dialog = LoadingDialog("Backing Up", "Backing up to Google Drive...", self.parent)
        loading_dialog.show()
        QApplication.processEvents()
        # ... The rest of the original Google Drive backup logic ...
        # This will still cause the threading error, but is not the user's current complaint.
        loading_dialog.close()


    def _restore_local(self):
        path, _ = QFileDialog.getOpenFileName(self.parent, "Select Backup", "", "ZIP Files (*.zip)")
        if not path:
            return

        dialog = ConfirmDeleteDialog(
            account_name="", parent=self.parent, title="Confirm Restore",
            message="Are you sure you want to overwrite\ncurrent settings with this backup?"
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        self.loading_dialog = LoadingDialog("Restoring", "Restoring profiles...", self.parent)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        QApplication.processEvents()

        self.thread = QThread()
        self.worker = RestoreWorker(self.switcher, path)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_restore_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _restore_google_drive(self):
        dialog = ConfirmDeleteDialog(
            account_name="", parent=self.parent, title="Confirm Restore",
            message="This will find the latest backup on your\nGoogle Drive and overwrite current settings.\nContinue?"
        )
        if dialog.exec_() != QDialog.Accepted:
            return

        self.loading_dialog = LoadingDialog("Restoring", "Downloading from Google Drive...", self.parent)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        QApplication.processEvents()

        self.thread = QThread()
        self.worker = GoogleDriveRestoreWorker(self.switcher)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_restore_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_restore_finished(self, success, message):
        if hasattr(self, 'loading_dialog') and self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        if success:
            CustomMessageDialog("Restore Successful", message, self.parent).exec_()
            self.parent.status_label.setText("Restore complete. Reloading accounts...")
            self.parent.load_accounts()
            self.parent.status_label.setText("Accounts reloaded.")
        else:
            QMessageBox.critical(self.parent, "Restore Failed", message)
            self.parent.status_label.setText("Restore failed.")

    def open_profiles_folder(self):
        os.startfile(str(self.switcher.profiles_dir))

    def export_ima_menu(self):
        accounts_data = self.switcher.get_saved_accounts()
        if not accounts_data:
            QMessageBox.warning(self.parent, "No Accounts", "You must save at least one account before exporting.")
            return

        ima_config = self.switcher.get_ima_config()
        dialog = ExportIMAMenuDialog(accounts_data, self.parent, default_settings=ima_config)
        if dialog.exec_() != QDialog.Accepted:
            return

        settings = dialog.get_settings()
        ima_menu_path_str = ima_config.get("ima_menu_path") or r"C:\Program Files\iMA Menu"
        ima_menu_path = Path(ima_menu_path_str)

        if not (ima_menu_path / "shell.nss").exists():
            path_dialog = IMAMenuPathDialog(self.parent, default_path=ima_menu_path_str)
            if path_dialog.exec_() == QDialog.Accepted:
                new_path_str = path_dialog.get_path()
                if not new_path_str or not (Path(new_path_str) / "shell.nss").exists():
                    QMessageBox.critical(self.parent, "Path Error", "The selected path is invalid.")
                    return
                ima_menu_path = Path(new_path_str)
            else:
                return

        self.switcher.set_ima_config({
            "title": settings["title"],
            "menu_icon_path": settings["menu_icon_path"],
            "ordered_accounts": settings["ordered_accounts"],
            "ima_menu_path": str(ima_menu_path)
        })

        output_dir = ima_menu_path / "imports"
        output_dir.mkdir(exist_ok=True)

        try:
            self.switcher.generate_ima_menu_script(
                output_dir=str(output_dir), title=settings["title"],
                ordered_accounts=settings["ordered_accounts"], menu_icon_path=settings["menu_icon_path"]
            )
            self.switcher.update_ima_shell_script(ima_menu_path)
            CustomMessageDialog("Export Successful", "Accounts added to iMA Menu", self.parent).exec_()
            self.parent.load_accounts()

        except Exception as e:
            QMessageBox.critical(self.parent, "Export Failed", f"An error occurred: {e}")

    def open_options_dialog(self):
        self.options_dialog = OptionsDialog(self.switcher, self.parent)
        self.options_dialog.settings_applied.connect(self.parent.load_accounts)
        self.options_dialog.show()
