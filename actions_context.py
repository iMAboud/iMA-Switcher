from PyQt5.QtWidgets import QMessageBox, QDialog
from ui_components import InputDialog, ConfirmDeleteDialog, IconPickerDialog
import logging
from pathlib import Path

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

        # Get current in-game name and tag for pre-filling
        _game, _rank, current_in_game_name, current_in_game_tag, _rr, _last_rr = self.switcher.get_account_game(old_name)

        dialog = InputDialog(
            "Rename Account", 
            f"Enter a new name for '{old_name}':", 
            old_name, 
            in_game_name_default=current_in_game_name or "", 
            in_game_tag_default=current_in_game_tag or "", 
            parent=self.parent
        )
        if dialog.exec_() == QDialog.Accepted:
            result = dialog.get_text()
            if isinstance(result, tuple):
                new_name, new_in_game_name, new_in_game_tag = result
            else:
                new_name = result
                new_in_game_name = current_in_game_name
                new_in_game_tag = current_in_game_tag

            # Ensure empty strings are converted to None for storage consistency
            if new_in_game_name == "": new_in_game_name = None
            if new_in_game_tag == "": new_in_game_tag = None

            if not new_name or (new_name == old_name and new_in_game_name == current_in_game_name and new_in_game_tag == current_in_game_tag): return
            
            if new_name != old_name and new_name in self.switcher.get_saved_accounts():
                logging.warning(f"Attempted to rename account '{old_name}' to '{new_name}', but an account with that name already exists.")
                QMessageBox.warning(self.parent, "Account Exists", f'An account named "{new_name}" already exists. Please choose a different name.')
                return
            
            if new_name != old_name:
                if not self.switcher.rename_account(old_name, new_name):
                    logging.error(f"Failed to rename account '{old_name}' to '{new_name}'. Switcher returned False.")
                    QMessageBox.critical(self.parent, "Rename Failed", f"Failed to rename '{old_name}' to '{new_name}'. Please try again.")
                    return
                self.parent.status_label.setText(f"Renamed '{old_name}' to '{new_name}'.")
                self.parent.selected_account_name = new_name
            else:
                self.parent.status_label.setText(f"Updated in-game name/tag for '{new_name}'.")

            self.switcher.set_account_in_game_name_tag(new_name, new_in_game_name, new_in_game_tag)
            self.parent.load_accounts()

    def delete(self):
        name = self.parent.get_selected_account_name()
        if not name: return
        
        dialog = ConfirmDeleteDialog(name, self.parent)
        if dialog.exec_() == QDialog.Accepted:
            if self.switcher.delete_account(name):
                self.parent.status_label.setText(f"Account '{name}' deleted.")
                self.parent.load_accounts()

    def change_icon(self):
        name = self.parent.get_selected_account_name()
        if not name: return

        current_icon_path, _, _, _, _, _, _ = self.switcher.get_saved_accounts().get(name, (None, None, None, None, None, None, None))
        
        dialog = IconPickerDialog(self.switcher, current_icon_path, self.parent)
        if dialog.exec_() == QDialog.Accepted:
            new_icon_path = dialog.get_selected_icon_path()
            if new_icon_path:
                if self.switcher.set_account_icon(name, Path(new_icon_path)):
                    self.parent.status_label.setText(f"Icon updated for '{name}'.")
                    self.parent.on_account_updated(name)
                else:
                    self.parent.status_label.setText(f"Failed to update icon for '{name}'.")
            else: # No icon path means remove
                if self.switcher.remove_account_icon(name):
                    self.parent.status_label.setText(f"Icon removed for '{name}'.")
                    self.parent.on_account_updated(name)
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
                self.parent.on_account_updated(name)
            else:
                self.parent.status_label.setText(f"Failed to set game for '{name}'.")

    def set_rank(self, rank):
        name = self.parent.get_selected_account_name()
        if not name: return
        
        if self.switcher.set_account_rank(name, rank):
            self.parent.status_label.setText(f"Rank for '{name}' set to {rank or 'None'}.")
            self.parent.on_account_updated(name)
        else:
            self.parent.status_label.setText(f"Failed to set rank for '{name}'.")
