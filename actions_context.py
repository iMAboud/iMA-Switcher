from PyQt5.QtWidgets import QMessageBox, QFileDialog, QDialog
from ui_components import InputDialog

class ContextActions:
    def __init__(self, parent):
        """
        Initializes the actions handler for the account context menu.
        :param parent: A reference to the main ModernValorantSwitcher window.
        """
        self.parent = parent
        self.switcher = parent.switcher

    def rename(self):
        old_name = self.parent.get_selected_account_name()
        if not old_name: return

        dialog = InputDialog("Rename Account", f"Enter a new name for '{old_name}':", old_name, self.parent)
        if dialog.exec_() == QDialog.Accepted:
            new_name = dialog.get_text()
            if not new_name or new_name == old_name: return
            if new_name in self.switcher.get_saved_accounts():
                QMessageBox.warning(self.parent, "Account Exists", f'An account named "{new_name}" already exists.')
                return
            if self.switcher.rename_account(old_name, new_name):
                self.parent.status_label.setText(f"Renamed '{old_name}' to '{new_name}'.")
                self.parent.selected_account_name = new_name 
                self.parent.load_accounts()

    def delete(self):
        name = self.parent.get_selected_account_name()
        if name and QMessageBox.question(
            self.parent, "Confirm Delete", f"Are you sure you want to delete '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.switcher.delete_account(name):
                self.parent.status_label.setText(f"Account '{name}' deleted.")
                self.parent.load_accounts()

    def change_icon(self):
        name = self.parent.get_selected_account_name()
        if not name: return
        path, _ = QFileDialog.getOpenFileName(
            self.parent, f"Select Icon for {name}", "", "Images (*.png *.jpg *.jpeg *.ico)"
        )
        if path:
            if self.switcher.set_account_icon(name, path):
                self.parent.status_label.setText(f"Icon updated for '{name}'.")
                self.parent.load_accounts()
            else:
                self.parent.status_label.setText(f"Failed to update icon for '{name}'.")

    def remove_icon(self):
        name = self.parent.get_selected_account_name()
        if not name: return
        if QMessageBox.question(
            self.parent, "Remove Icon", f"Are you sure you want to remove the icon for '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if self.switcher.remove_account_icon(name):
                self.parent.status_label.setText(f"Icon removed for '{name}'.")
                self.parent.load_accounts()
            else:
                self.parent.status_label.setText(f"Failed to remove icon for '{name}'.")

    def create_shortcut(self):
        name = self.parent.get_selected_account_name()
        if name:
            if self.switcher.create_desktop_shortcut(name):
                self.parent.status_label.setText(f"Shortcut for '{name}' created on Desktop.")
            else:
                self.parent.status_label.setText(f"Failed to create shortcut for '{name}'.")

    def change_game(self, game):
        name = self.parent.get_selected_account_name()
        if name:
            if self.switcher.set_account_game(name, game):
                self.parent.status_label.setText(f"Set game for '{name}' to {game.capitalize()}. ")
                self.parent.load_accounts()
            else:
                self.parent.status_label.setText(f"Failed to set game for '{name}'.")
