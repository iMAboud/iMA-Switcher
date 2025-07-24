import os
import threading
import logging
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog
from ui_components import SaveAccountDialog, ExportIMAMenuDialog, OptionsDialog, CustomMessageDialog, ConfirmDeleteDialog
from PyQt5.QtCore import QTimer

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
        threading.Thread(target=self.switcher.add_account_flow, daemon=True).start()
        QTimer.singleShot(1000, self.save_current_account)

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

    def backup_profiles(self):
        suggested_filename = self.switcher.get_backup_filename()
        path, _ = QFileDialog.getSaveFileName(self.parent, "Save Backup", suggested_filename, "ZIP Files (*.zip)")
        if path:
            if not path.endswith(".zip"): path += ".zip"
            if self.switcher.backup_profiles(path):
                self.parent.status_label.setText(f"Profiles backed up successfully.")
                logging.info(f"Profiles backed up to {path}")
            else:
                self.parent.status_label.setText("Backup failed.")
                logging.error(f"Failed to backup profiles to {path}")

    def restore_profiles(self):
        path, _ = QFileDialog.getOpenFileName(self.parent, "Select Backup", "", "ZIP Files (*.zip)")
        if path:
            dialog = ConfirmDeleteDialog(
                account_name="", 
                parent=self.parent,
                title="Confirm Restore",
                message="""Are you sure you want to overwrite
current settings?"""
            )
            if dialog.exec_() == QDialog.Accepted:
                if self.switcher.restore_profiles(path):
                    self.parent.status_label.setText("Profiles restored successfully.")
                    self.parent.load_accounts()
                    logging.info(f"Profiles restored from {path}")
                else:
                    self.parent.status_label.setText("Restore failed.")
                    logging.error(f"Failed to restore profiles from {path}")

    def open_profiles_folder(self):
        os.startfile(self.switcher.profiles_dir)

    def export_ima_menu(self):
        accounts_data = self.switcher.get_saved_accounts()
        if not accounts_data:
            QMessageBox.warning(self.parent, "No Accounts", "You must save at least one account before exporting.")
            return

        ima_config = self.switcher.get_ima_config()
        if not ima_config.get("menu_icon_path"):
            default_ico = r"C:\Program Files\iMA Menu\icons\valorant.ico"
            if os.path.exists(default_ico): ima_config["menu_icon_path"] = default_ico

        dialog = ExportIMAMenuDialog(accounts_data, self.parent, default_settings=ima_config)
        
        if dialog.exec_() == QDialog.Accepted:
            settings = dialog.get_settings()
            output_dir = ima_config.get("output_dir") or r"C:\Program Files\iMA Menu\imports"
            if not os.path.isdir(output_dir):
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

