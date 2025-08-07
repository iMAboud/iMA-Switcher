import os
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

class BaseWorker(QObject):
    finished = pyqtSignal(bool, str)

    def __init__(self, switcher):
        super().__init__()
        self.switcher = switcher

class BackupWorker(BaseWorker):
    def __init__(self, switcher, backup_path):
        super().__init__(switcher)
        self.backup_path = backup_path

    def run(self):
        try:
            success = self.switcher.backup_profiles(self.backup_path)
            message = "Profiles backed up successfully." if success else "Failed to back up profiles."
            self.finished.emit(success, message)
        except Exception as e:
            logging.error(f"Exception in BackupWorker: {e}", exc_info=True)
            self.finished.emit(False, f"An unexpected error occurred: {e}")

class GoogleDriveBackupWorker(BaseWorker):
    def run(self):
        temp_file_path = None
        try:
            backup_filename_base = self.switcher.get_backup_filename()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
                temp_file_path = temp_file.name

            if self.switcher.backup_profiles(temp_file_path):
                drive_api = GoogleDriveAPI(self.switcher.user_data_dir)
                drive_api.upload_file(temp_file_path, f"{backup_filename_base}.zip")
                self.finished.emit(True, "Profiles backed up to Google Drive.")
            else:
                self.finished.emit(False, "Failed to create local backup file for upload.")
        except Exception as e:
            logging.error(f"Exception in GoogleDriveBackupWorker: {e}", exc_info=True)
            self.finished.emit(False, f"An unexpected error occurred: {e}")
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                try: Path(temp_file_path).unlink()
                except OSError as e: logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

class RestoreWorker(BaseWorker):
    def __init__(self, switcher, restore_path):
        super().__init__(switcher)
        self.restore_path = restore_path

    def run(self):
        try:
            success = self.switcher.restore_profiles(self.restore_path)
            message = "Profiles restored successfully." if success else "Failed to restore profiles."
            self.finished.emit(success, message)
        except Exception as e:
            logging.error(f"Exception in RestoreWorker: {e}", exc_info=True)
            self.finished.emit(False, f"An unexpected error occurred: {e}")

class GoogleDriveRestoreWorker(BaseWorker):
    def run(self):
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
            message = "Profiles restored from Google Drive." if success else "Failed to restore from downloaded file."
            self.finished.emit(success, message)
        except Exception as e:
            logging.error(f"Exception in GoogleDriveRestoreWorker: {e}", exc_info=True)
            self.finished.emit(False, f"An unexpected error occurred: {e}")
        finally:
            if temp_file_path and Path(temp_file_path).exists():
                try: Path(temp_file_path).unlink()
                except OSError as e: logging.error(f"Failed to clean up temp file {temp_file_path}: {e}")

class SettingsActions:
    def __init__(self, parent):
        self.parent = parent
        self.switcher = parent.switcher
        self.worker = None
        self.thread = None
        self.loading_dialog = None

    def _launch_worker(self, worker_class, *args):
        self.thread = QThread()
        self.worker = worker_class(self.switcher, *args)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self._on_operation_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_operation_finished(self, success, message):
        if self.loading_dialog:
            self.loading_dialog.close()
            self.loading_dialog = None

        operation_type = "Operation"
        if isinstance(self.worker, (BackupWorker, GoogleDriveBackupWorker)):
            operation_type = "Backup"
        elif isinstance(self.worker, (RestoreWorker, GoogleDriveRestoreWorker)):
            operation_type = "Restore"

        if success:
            CustomMessageDialog(f"{operation_type} Successful", message, self.parent).exec_()
            self.parent.status_label.setText(f"{operation_type} complete.")
            if operation_type == "Restore":
                self.parent.load_accounts()
                self.parent.status_label.setText("Accounts reloaded.")
        else:
            QMessageBox.critical(self.parent, f"{operation_type} Failed", message)
            self.parent.status_label.setText(f"{operation_type} failed.")

    def backup_restore_profiles(self):
        selection_dialog = BackupRestoreSelectionDialog(self.parent)
        if selection_dialog.exec_() != QDialog.Accepted: return
        selection = selection_dialog.get_selection()
        if not selection: return

        dialog = BackupRestoreDialog(self.parent, mode=selection)
        if dialog.exec_() != QDialog.Accepted: return
        backup_type = dialog.get_selection()
        if not backup_type: return

        action_map = {
            ("backup", "local"): self._backup_local,
            ("backup", "google_drive"): self._backup_google_drive,
            ("restore", "local"): self._restore_local,
            ("restore", "google_drive"): self._restore_google_drive,
        }
        action_map.get((selection, backup_type))()

    def _backup_local(self):
        backup_filename = f"{self.switcher.get_backup_filename()}.zip"
        path, _ = QFileDialog.getSaveFileName(self.parent, "Save Backup", backup_filename, "ZIP Files (*.zip)")
        if not path: return

        self.loading_dialog = LoadingDialog("Backing Up", "Backing up profiles...", self.parent)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        QApplication.processEvents()
        self._launch_worker(BackupWorker, path)

    def _backup_google_drive(self):
        self.loading_dialog = LoadingDialog("Backing Up", "Backing up to Google Drive...", self.parent)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        QApplication.processEvents()
        self._launch_worker(GoogleDriveBackupWorker)

    def _restore_local(self):
        path, _ = QFileDialog.getOpenFileName(self.parent, "Select Backup", "", "ZIP Files (*.zip)")
        if not path: return

        if ConfirmDeleteDialog(account_name="", parent=self.parent, title="Confirm Restore", message="Are you sure you want to overwrite\ncurrent settings with this backup?").exec_() != QDialog.Accepted:
            return

        self.loading_dialog = LoadingDialog("Restoring", "Restoring profiles...", self.parent)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        QApplication.processEvents()
        self._launch_worker(RestoreWorker, path)

    def _restore_google_drive(self):
        if ConfirmDeleteDialog(account_name="", parent=self.parent, title="Confirm Restore", message="This will find the latest backup on your\nGoogle Drive and overwrite current settings.\nContinue?").exec_() != QDialog.Accepted:
            return

        self.loading_dialog = LoadingDialog("Restoring", "Downloading from Google Drive...", self.parent)
        self.loading_dialog.setModal(True)
        self.loading_dialog.show()
        QApplication.processEvents()
        self._launch_worker(GoogleDriveRestoreWorker)

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

    def add_account(self):
        # This seems to be a duplicate or part of an incomplete feature.
        # For now, it just starts a thread that does nothing.
        # This should be reviewed.
        pass
