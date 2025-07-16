import os
import shutil
import subprocess
import json
import ctypes
import sys
import threading
from zipfile import ZipFile
from datetime import datetime
import re
import time
try:
    import requests
except ImportError:
    requests = None
    print("Warning: 'requests' library not installed. Rank fetching will not work. Please install it with 'pip install requests'")
try:
    from PIL import Image
except ImportError:
    Image = None
    print("Warning: Pillow not installed. Image conversion for icons will not work. Please install it with 'pip install Pillow'")

class GameSwitcher:
    def __init__(self, base_directory=None):
        self.app_data_path = os.getenv('LOCALAPPDATA')
        
        # Base directory for application assets (where the executable is or _MEIPASS)
        if base_directory:
            self.base_dir = base_directory
        else:
            self.base_dir = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        
        # Persistent directory for user profiles and configuration
        self.user_data_dir = os.path.join(self.app_data_path, "iMA Switcher")
        
        self.profiles_dir = os.path.join(self.user_data_dir, "profiles")
        self.config_path = os.path.join(self.user_data_dir, "config.json")
        self.config = None

        self.GAMES = {
            "valorant": {
                "launch_args": "--launch-product=valorant --launch-patchline=live",
                "processes_to_kill": ["VALORANT.exe", "RiotClientServices.exe", "VALORANT-Win64-Shipping.exe"],
                "executable_name": "RiotClientServices.exe"
            },
            "lol": {
                "launch_args": "--launch-product=league_of_legends --launch-patchline=live",
                "processes_to_kill": ["LeagueClient.exe", "RiotClientServices.exe", "LeagueClientUx.exe"],
                "executable_name": "LeagueClientUx.exe"
            }
        }

        self.riot_client_data_path = None
        self.riot_games_config = {}
        self.initialize_riot_client_paths()

    def _ensure_initialized(self):
        os.makedirs(self.profiles_dir, exist_ok=True)
        if self.config is None:
            self.config = self._load_config()

    def is_admin(self):
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except: return False

    def _load_config(self):
        defaults = {
            "output_dir": None,
            "title": "Valorant",
            "menu_icon_path": "",
            "ordered_accounts": [],
            "riot_client_exe_path": None,
            "ui_settings": {
                "show_game_icons": True,
                "show_rank_tips": True,
                "tip_delay": 1.0,
                "use_rank_icons": False,
                "show_rank_icon_left": True,
                "show_name_tag": True
            }
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                    # Define all possible top-level deprecated keys
                    deprecated_keys = ["last_switched_account", "save_last_window_size", "last_window_size", "show_game_icons"]
                    for key in deprecated_keys:
                        if key in loaded_config:
                            del loaded_config[key]

                    # Merge ui_settings specifically to preserve new defaults
                    if "ui_settings" in loaded_config and isinstance(loaded_config["ui_settings"], dict):
                        defaults["ui_settings"].update(loaded_config["ui_settings"])
                    loaded_config["ui_settings"] = defaults["ui_settings"] # Ensure ui_settings in loaded_config is the merged one
                    defaults.update(loaded_config)
            except (json.JSONDecodeError, UnicodeDecodeError):
                print("Warning: config.json is corrupted or has encoding issues. Using defaults.")
        return defaults

    def _save_config(self):
        if self.config is None:
            self.config = self._load_config() 
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_ima_config(self):
        self._ensure_initialized() 
        self.config = self._load_config() # Always reload the config to get the latest changes
        return self.config

    def set_ima_config(self, settings):
        self._ensure_initialized() 
        self.config.update(settings)
        self._save_config()

    def initialize_riot_client_paths(self, riot_client_exe_path=None):
        if self.config is None:
            self.config = self._load_config()

        exe_path = riot_client_exe_path
        if not exe_path or not os.path.exists(exe_path):
            exe_path = self.config.get("riot_client_exe_path")

        if not exe_path or not os.path.exists(exe_path):
            exe_path = self._find_riot_client_path()

        self.riot_games_config["ExeLocationDefault"] = exe_path if exe_path and os.path.exists(exe_path) else ""
        self.riot_client_data_path = os.path.join(self.app_data_path, "Riot Games", "Riot Client")
        self.riot_games_config.update(self._load_riot_games_config_defaults())

    def _find_riot_client_path(self):
        common_paths = [
            os.path.join("C:", os.sep, "Riot Games", "Riot Client", "RiotClientServices.exe"),
            os.path.join(os.getenv('PROGRAMFILES'), "Riot Games", "Riot Client", "RiotClientServices.exe"),
            os.path.join(os.getenv('PROGRAMFILES(X86)'), "Riot Games", "Riot Client", "RiotClientServices.exe"),
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
        return None

    def _load_riot_games_config_defaults(self):
        return {
            "LoginData": {"Config": "d", "Data": "d", "Logs": "d"}
        }

    def set_riot_client_paths(self, exe_path):
        self.initialize_riot_client_paths(exe_path)
        if self.config is None:
            self.config = self._load_config() 
        self.config["riot_client_exe_path"] = exe_path
        self._save_config()

    def _get_account_path(self, account_name): return os.path.join(self.profiles_dir, account_name)

    def _terminate_processes(self):
        all_processes = self.GAMES['valorant']["processes_to_kill"] + self.GAMES['lol']["processes_to_kill"]
        for exe in all_processes:
            subprocess.run(f"taskkill /f /im {exe}", shell=True, check=False, capture_output=True)

    def _create_junction(self, source, link_name):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        subprocess.run(['cmd', '/c', 'mklink', '/J', link_name, source], check=True, startupinfo=startupinfo)

    def _remove_junction_or_dir(self, path):
        if not os.path.lexists(path): return
        try:
            if os.path.isdir(path) and not os.path.islink(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except:
            try:
                os.rmdir(path)
            except OSError as e:
                print(f"Failed to remove {path}: {e}")

    def _load_game_config(self, account_name):
        game_config_path = os.path.join(self._get_account_path(account_name), 'game.json')
        if os.path.exists(game_config_path):
            with open(game_config_path, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    print(f"Warning: game.json for {account_name} is corrupted. Starting with empty config.")
                    return {}
        return {}

    def _save_game_config(self, account_name, data):
        game_config_path = os.path.join(self._get_account_path(account_name), 'game.json')
        with open(game_config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_account_game(self, account_name):
        data = self._load_game_config(account_name)
        result = (data.get('game', 'valorant'), data.get('rank', None), data.get('in_game_name', None), data.get('in_game_tag', None), data.get('current_rr', None), data.get('last_game_rr', None))
        print(f"DEBUG: get_account_game for {account_name} returning: {result} (length: {len(result)})")
        return result

    def set_account_game(self, account_name, game):
        account_path = self._get_account_path(account_name)
        if not os.path.exists(account_path):
            return False
        data = self._load_game_config(account_name)
        data['game'] = game
        self._save_game_config(account_name, data)
        return True

    def set_account_rank(self, account_name, rank):
        account_path = self._get_account_path(account_name)
        if not os.path.exists(account_path):
            return False
        data = self._load_game_config(account_name)
        data['rank'] = rank
        self._save_game_config(account_name, data)
        self.update_ima_menu_if_enabled('update', account_name)
        return True

    def set_account_in_game_name_tag(self, account_name, in_game_name, in_game_tag, current_rr=None, last_game_rr=None):
        account_path = self._get_account_path(account_name)
        if not os.path.exists(account_path):
            return False
        data = self._load_game_config(account_name)
        data['in_game_name'] = in_game_name
        data['in_game_tag'] = in_game_tag
        data['current_rr'] = current_rr
        data['last_game_rr'] = last_game_rr
        self._save_game_config(account_name, data)
        return True

    def save_account(self, account_name, game='valorant', rank=None, in_game_name=None, in_game_tag=None):
        account_path = self._get_account_path(account_name)
        os.makedirs(account_path, exist_ok=True)
        for item_name in self.riot_games_config["LoginData"].keys():
            source_path = os.path.join(self.riot_client_data_path, item_name)
            dest_path = os.path.join(account_path, item_name)
            if not os.path.exists(source_path):
                continue
            self._remove_junction_or_dir(dest_path)
            if os.path.isdir(source_path):
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            elif os.path.isfile(source_path):
                shutil.copy2(source_path, dest_path)
        self.set_account_game(account_name, game)
        if rank: self.set_account_rank(account_name, rank)
        if in_game_name or in_game_tag: self.set_account_in_game_name_tag(account_name, in_game_name, in_game_tag)
        self.update_ima_menu_if_enabled('add', account_name)
        return True

    def switch_account(self, account_name, selected_game=None):
        if not self.is_admin():
            return False, "Administrator rights are required to switch accounts.", None
        
        account_path = self._get_account_path(account_name)
        if not os.path.exists(account_path):
            return False, f"Profile for '{account_name}' not found.", None
        
        game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = self.get_account_game(account_name)

        if game == 'both' and selected_game is None:
            return True, "Game selection required.", "both"
        elif game == 'both' and selected_game is not None:
            game = selected_game

        self._terminate_processes()
        
        for item_name in self.riot_games_config["LoginData"].keys():
            riot_item_path = os.path.join(self.riot_client_data_path, item_name)
            profile_item_path = os.path.join(account_path, item_name)
            self._remove_junction_or_dir(riot_item_path)
            if os.path.exists(profile_item_path):
                try:
                    self._create_junction(profile_item_path, riot_item_path)
                except Exception as e:
                    return False, f"Failed to create junction for '{item_name}': {e}\nEnsure you are running as Administrator.", None

        try:
            launch_args = self.GAMES[game]["launch_args"].split()
            command = [self.riot_games_config["ExeLocationDefault"]] + launch_args
            
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            subprocess.Popen(command, creationflags=creationflags, close_fds=True)
            
            if game == 'valorant':
                graphics_settings = self.get_graphics_settings()
                update_thread = threading.Thread(target=self.update_all_game_user_settings, args=(graphics_settings,))
                update_thread.daemon = True
                update_thread.start()
            
            # Fetch rank data after a successful switch
            self.fetch_and_update_rank_data(account_name)

            return True, "Account switched successfully.", game
        except FileNotFoundError:
            return False, f"Riot Client not found at:\n{self.riot_games_config['ExeLocationDefault']}", None
        except Exception as e:
            return False, f"Failed to launch Riot Client: {e}", None

    def add_account_flow(self):
        if not self.is_admin(): return False
        game = 'valorant'  # Default to valorant for this flow
        self._terminate_processes()
        for item_name in self.riot_games_config["LoginData"].keys():
            riot_item_path = os.path.join(self.riot_client_data_path, item_name)
            self._remove_junction_or_dir(riot_item_path)
        try:
            subprocess.Popen([self.riot_games_config["ExeLocationDefault"]])
            return True
        except FileNotFoundError:
            return False

    def get_saved_accounts(self):
        accounts_data = {}
        try:
            dirs = [d for d in os.listdir(self.profiles_dir) if os.path.isdir(os.path.join(self.profiles_dir, d))]
            for account_name in sorted(dirs):
                icon_path = os.path.join(self._get_account_path(account_name), "icon.png")
                game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = self.get_account_game(account_name)
                accounts_data[account_name] = (icon_path if os.path.exists(icon_path) else None, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr)
                print(f"DEBUG: get_saved_accounts for {account_name} adding: {accounts_data[account_name]} (length: {len(accounts_data[account_name])})")
        except FileNotFoundError:
            os.makedirs(self.profiles_dir, exist_ok=True)
        return accounts_data

    def rename_account(self, old_name, new_name):
        old_path, new_path = self._get_account_path(old_name), self._get_account_path(new_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            os.rename(old_path, new_path)
            self.update_ima_menu_if_enabled('rename', new_name, old_name=old_name)
            return True
        return False

    def delete_account(self, account_name):
        account_path = self._get_account_path(account_name)
        if os.path.exists(account_path):
            shutil.rmtree(account_path)
            self.update_ima_menu_if_enabled('delete', account_name)
            return True
        return False

    def set_account_icon(self, account_name, source_icon_path):
        account_path = self._get_account_path(account_name)
        if not os.path.isdir(account_path): return False
        dest_icon_path = os.path.join(account_path, "icon.png")
        try:
            if Image:
                img = Image.open(source_icon_path)
                img.save(dest_icon_path, "PNG")
            else:
                shutil.copy(source_icon_path, dest_icon_path)
            self.update_ima_menu_if_enabled('update', account_name)
            return True
        except Exception as e:
            print(f"Error setting account icon: {e}")
            return False

    def remove_account_icon(self, account_name):
        account_path = self._get_account_path(account_name)
        icon_path = os.path.join(account_path, "icon.png")
        if os.path.exists(icon_path):
            try:
                os.remove(icon_path)
                self.update_ima_menu_if_enabled('update', account_name)
                return True
            except Exception as e:
                print(f"Error removing account icon: {e}")
                return False
        return False

    def create_desktop_shortcut(self, account_name):
        try:
            import win32com.client
        except ImportError:
            print("Error: pywin32 is required to create shortcuts. Please run 'pip install pywin32'.")
            return False

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut_path = os.path.join(desktop_path, f"{account_name}.lnk")

        target_path = sys.executable
        working_dir = os.path.dirname(target_path)

        if not getattr(sys, 'frozen', False):
            main_script_path = os.path.abspath(os.path.join(self.base_dir, "main.pyw"))
            arguments = f'"{main_script_path}" --switch "{account_name}"'
        else:
            arguments = f'--switch "{account_name}"'

        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.TargetPath = target_path
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = working_dir
            game = self.get_account_game(account_name)
            shortcut.Description = f"Launch {game.capitalize()} with {account_name} account"

            account_data = self.get_saved_accounts()
            account_icon_path, _, rank, _, _, _, _ = account_data.get(account_name)
            
            ui_settings = self.get_ima_config().get("ui_settings", {})
            use_rank_icons = ui_settings.get("use_rank_icons", False)

            icon_to_use = None

            if use_rank_icons and rank:
                app_install_path = self.get_ima_config().get("app_install_path", self.base_dir)
                rank_icon_candidate_path = os.path.join(app_install_path, "Assets", f"{rank.lower().replace(" ", "_")}.png")
                if os.path.exists(rank_icon_candidate_path):
                    icon_to_use = rank_icon_candidate_path
            
            if icon_to_use is None and account_icon_path and os.path.exists(account_icon_path):
                icon_to_use = account_icon_path

            if icon_to_use is None:
                app_install_path = self.get_ima_config().get("app_install_path", self.base_dir)
                icon_to_use = os.path.abspath(os.path.join(app_install_path, "logo.png"))

            shortcut.IconLocation = icon_to_use
            
            shortcut.Save()
            return True
        except Exception as e:
            print(f"Error creating shortcut: {e}")
            return False

    def get_backup_filename(self):
        now = datetime.now()
        timestamp = now.strftime("GameAccountBackup_%H%M_%d%m%Y")
        return timestamp

    def backup_profiles(self, backup_file_path):
        try: 
            shutil.make_archive(base_name=backup_file_path.replace('.zip', ''), format='zip', root_dir=self.base_dir, base_dir='profiles')
            return True
        except Exception as e:
            print(f"Backup failed: {e}"); return False
            
    def restore_profiles(self, backup_file_path):
        try:
            if os.path.exists(self.profiles_dir): shutil.rmtree(self.profiles_dir)
            with ZipFile(backup_file_path, 'r') as zip_ref: zip_ref.extractall(self.base_dir)
            self.update_ima_menu_if_enabled('restore', list(self.get_saved_accounts().keys()))
            return True
        except Exception as e:
            print(f"Restore failed: {e}"); return False

    def update_ima_menu_if_enabled(self, action, name=None, old_name=None):
        ima_config = self.get_ima_config()
        if not ima_config.get("output_dir"): return
        
        print(f"iMA Auto-Update: Action='{action}', Name='{name}'")
        
        current_ordered_list = ima_config.get("ordered_accounts", [])
        if action == 'add' and name and name not in current_ordered_list: current_ordered_list.append(name)
        elif action == 'delete' and name and name in current_ordered_list: current_ordered_list.remove(name)
        elif action == 'rename' and name and old_name and old_name in current_ordered_list: current_ordered_list[current_ordered_list.index(old_name)] = name
        elif action == 'restore': current_ordered_list = sorted(list(self.get_saved_accounts().keys()))
        
        ima_config["ordered_accounts"] = current_ordered_list
        self.set_ima_config(ima_config)
        
        try:
            self.generate_ima_menu_script(
                output_dir=ima_config["output_dir"],
                title=ima_config["title"],
                ordered_accounts=ima_config["ordered_accounts"],
                menu_icon_path=ima_config.get("menu_icon_path", ""),
                save_config=False  
            )
            print("Auto-update of valo.nss successful.")
        except Exception as e:
            print(f"Automatic iMA menu update failed: {e}")

    def generate_ima_menu_script(self, output_dir, title, ordered_accounts, menu_icon_path="", save_config=False):
        if save_config:
            self.set_ima_config({"output_dir": output_dir, "title": title, "menu_icon_path": menu_icon_path, "ordered_accounts": ordered_accounts})
        
        script_path = os.path.join(output_dir, 'valo.nss')
        icons_dir = os.path.join(output_dir, "icons"); os.makedirs(icons_dir, exist_ok=True)
        menu_icon_arg = ""
        if menu_icon_path and os.path.exists(menu_icon_path):
            try:
                base_icon_name = os.path.basename(menu_icon_path)
                dest_icon_path = os.path.join(icons_dir, base_icon_name)
                shutil.copy(menu_icon_path, dest_icon_path)
                ima_icon_path = fr"@app.dir\imports\icons\{base_icon_name}"
                menu_icon_arg = f" icon='{ima_icon_path}'"
            except Exception as e:
                print(f"Could not copy menu icon: {e}")
        
        script_content = [f"menu(where=sel.count>0 type='namespace|back' mode='multiple' title='{title}'{menu_icon_arg})", "{"]
        main_app_path = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        accounts_data = self.get_saved_accounts()
        
        ui_settings = self.get_ima_config().get("ui_settings", {})
        show_rank_tips = ui_settings.get("show_rank_tips", False)
        tip_delay = ui_settings.get("tip_delay", 1.0)
        use_rank_icons = ui_settings.get("use_rank_icons", False)

        rank_order = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
        
        for account_name in ordered_accounts:
            if account_name not in accounts_data: continue
            icon_source_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = accounts_data.get(account_name)
            
            item_icon_arg = ""
            icon_to_use_for_menu = None

            if use_rank_icons and rank:
                app_install_path = self.get_ima_config().get("app_install_path", self.base_dir)
                rank_icon_path = os.path.join(app_install_path, "Assets", f"{rank.lower().replace(" ", "_")}.png")
                if os.path.exists(rank_icon_path):
                    icon_to_use_for_menu = rank_icon_path
            
            if icon_to_use_for_menu is None and icon_source_path and os.path.exists(icon_source_path):
                icon_to_use_for_menu = icon_source_path

            if icon_to_use_for_menu is None:
                app_install_path = self.get_ima_config().get("app_install_path", self.base_dir)
                logo_path = os.path.join(app_install_path, "Assets", "logo.png")
                if os.path.exists(logo_path):
                    icon_to_use_for_menu = logo_path

            if icon_to_use_for_menu:
                item_icon_arg = f" icon='{icon_to_use_for_menu.replace(os.sep, '\\')}'"
            
            tip_arg = ""
            if show_rank_tips and rank:
                rank_index = rank_order.index(rank) if rank in rank_order else 0
                tip_arg = f" tip=['{rank}', tip.info, {tip_delay}]"
            
            cmd_executable = f'"{main_app_path}"'
            cmd_args = f'--switch "{account_name}"'
            item_line = f"    item(title='{account_name}'{tip_arg} cmd='{cmd_executable}' args='{cmd_args}'{item_icon_arg})"
            script_content.append(item_line)
            
        script_content.append("}")
        final_script = "\n".join(script_content)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(final_script)

    def _find_game_user_settings_files(self):
        valorant_config_path = os.path.join(os.getenv('LOCALAPPDATA'), "VALORANT", "Saved", "Config")
        ini_files = []
        print(f"Searching for GameUserSettings.ini in: {valorant_config_path}")
        if not os.path.exists(valorant_config_path):
            print(f"Valorant config path does not exist: {valorant_config_path}")
            return []

        for root, dirs, files in os.walk(valorant_config_path):
            if "GameUserSettings.ini" in files and os.path.basename(root) == "Windows":
                ini_file_path = os.path.join(root, "GameUserSettings.ini")
                ini_files.append(ini_file_path)
                print(f"Found: {ini_file_path}")
        if not ini_files:
            print("No GameUserSettings.ini files found.")
        return ini_files

    def _find_riot_user_settings_files(self):
        valorant_config_path = os.path.join(os.getenv('LOCALAPPDATA'), "VALORANT", "Saved", "Config")
        ini_files = []
        print(f"Searching for RiotUserSettings.ini in: {valorant_config_path}")
        if not os.path.exists(valorant_config_path):
            print(f"Valorant config path does not exist: {valorant_config_path}")
            return []

        for root, dirs, files in os.walk(valorant_config_path):
            if "RiotUserSettings.ini" in files and os.path.basename(root) == "Windows":
                ini_file_path = os.path.join(root, "RiotUserSettings.ini")
                ini_files.append(ini_file_path)
                print(f"Found: {ini_file_path}")
        if not ini_files:
            print("No RiotUserSettings.ini files found.")
        return ini_files

    def get_graphics_settings(self):
        self._ensure_initialized()
        if "graphics_settings" not in self.config or not self.config.get("graphics_settings"):
            quality_settings, _ = self._get_global_game_user_settings_from_file()
            if not quality_settings:
                quality_settings = {
                    "sg.ViewDistanceQuality": 3, "sg.AntiAliasingQuality": 3, "sg.ShadowQuality": 3,
                    "sg.PostProcessQuality": 3, "sg.TextureQuality": 3, "sg.EffectsQuality": 3,
                    "sg.FoliageQuality": 3, "sg.ShadingQuality": 3
                }
            riot_settings, _ = self._get_global_riot_user_settings_from_file()
            if not riot_settings:
                riot_settings = {}
            
            graphics_settings = {
                "display_mode": "Default",
                "quality": {k: v for k, v in quality_settings.items() if k.startswith("sg.")},
                "riot_settings": {k: v for k, v in riot_settings.items() if "EAresIntSettingName::" in k},
                "audio_settings": {k: v for k, v in riot_settings.items() if "EAresFloatSettingName::" in k or "EAresBoolSettingName::" in k}
            }
            self.config["graphics_settings"] = graphics_settings
            self._save_config()
        return self.config["graphics_settings"]

    def save_graphics_settings(self, settings):
        self._ensure_initialized()
        # Extract ui_settings if present
        ui_settings = settings.pop("ui_settings", None)
        if ui_settings is not None:
            self.config["ui_settings"] = ui_settings
        self.config["graphics_settings"] = settings
        self._save_config()

    def _get_global_game_user_settings_from_file(self):
        ini_files = self._find_game_user_settings_files()
        if not ini_files: return None, "No GameUserSettings.ini files found to load settings from."
        settings = {}
        try:
            with open(ini_files[0], 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip().startswith("sg.") and "=" in line:
                        key, value = line.split("=", 1)
                        settings[key.strip()] = value.strip()
            return settings, None
        except Exception as e:
            return None, f"Error reading {ini_files[0]}: {e}"

    def _get_global_riot_user_settings_from_file(self):
        ini_files = self._find_riot_user_settings_files()
        if not ini_files: return None, "No RiotUserSettings.ini files found to load settings from."
        settings = {}
        try:
            with open(ini_files[0], 'r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith("EAres") and "=" in stripped_line:
                        key, value = stripped_line.split("=", 1)
                        settings[key.strip()] = value.strip()
            return settings, None
        except Exception as e:
            return None, f"Error reading {ini_files[0]}: {e}"

    def update_all_game_user_settings(self, graphics_settings):
        game_user_ini_files = self._find_game_user_settings_files()
        riot_user_ini_files = self._find_riot_user_settings_files()
        all_success = True

        if not game_user_ini_files:
            print("No GameUserSettings.ini files found to update.")
        else:
            display_mode = graphics_settings.get("display_mode", "Default")
            quality_settings = graphics_settings.get("quality", {})
            
            for ini_file_path in game_user_ini_files:
                try:
                    with open(ini_file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
                    
                    temp_lines = []
                    settings_to_update = {}
                    if display_mode == "Fullscreen":
                        settings_to_update = {
                            "ResolutionSizeX": "1920", "ResolutionSizeY": "1080",
                            "LastUserConfirmedResolutionSizeX": "1920", "LastUserConfirmedResolutionSizeY": "1080",
                            "WindowPosX": "0", "WindowPosY": "0",
                            "LastConfirmedFullscreenMode": "0", "PreferredFullscreenMode": "0"
                        }
                    elif display_mode == "Windowed Fullscreen":
                        settings_to_update = {
                            "ResolutionSizeX": "1920", "ResolutionSizeY": "1080",
                            "LastUserConfirmedResolutionSizeX": "1280", "LastUserConfirmedResolutionSizeY": "720",
                            "WindowPosX": "0", "WindowPosY": "0",
                            "LastConfirmedFullscreenMode": "1", "PreferredFullscreenMode": "1"
                        }
                    elif display_mode == "Windowed":
                        settings_to_update = {
                            "ResolutionSizeX": "1920", "ResolutionSizeY": "1032",
                            "LastUserConfirmedResolutionSizeX": "1280", "LastUserConfirmedResolutionSizeY": "720",
                            "WindowPosX": "0", "WindowPosY": "24",
                            "LastConfirmedFullscreenMode": "2", "PreferredFullscreenMode": "1"
                        }

                    for line in lines:
                        stripped = line.strip()
                        key_to_update = next((key for key in settings_to_update if stripped.startswith(key + "=")), None)
                        if key_to_update:
                            temp_lines.append(f"{key_to_update}={settings_to_update[key_to_update]}\n")
                            del settings_to_update[key_to_update]
                            continue
                        
                        if stripped.startswith("sg."):
                            key = stripped.split('=')[0]
                            if key in quality_settings:
                                temp_lines.append(f"{key}={quality_settings[key]}\n")
                                continue

                        if display_mode != "Default" and stripped.startswith("FullscreenMode="):
                            continue

                        temp_lines.append(line)

                    if display_mode != "Default":
                        if display_mode in ["Windowed", "Windowed Fullscreen"]:
                            fs_val = "1" if display_mode == "Windowed Fullscreen" else "2"
                            hdr_idx = next((i for i, l in enumerate(temp_lines) if l.strip().startswith("HDRDisplayOutputNits=")), -1)
                            if hdr_idx != -1: temp_lines.insert(hdr_idx + 1, f"FullscreenMode={fs_val}\n")

                    with open(ini_file_path, 'w', encoding='utf-8') as f: f.writelines(temp_lines)
                    print(f"Successfully updated: {ini_file_path}")
                except Exception as e:
                    print(f"Error updating {ini_file_path}: {e}"); all_success = False

        if not riot_user_ini_files:
            print("No RiotUserSettings.ini files found to update.")
        else:
            riot_settings = graphics_settings.get("riot_settings", {})
            audio_settings = graphics_settings.get("audio_settings", {})
            all_settings_to_apply = {**riot_settings, **audio_settings}

            for ini_file_path in riot_user_ini_files:
                try:
                    with open(ini_file_path, 'r', encoding='utf-8') as f: lines = f.readlines()
                    
                    temp_lines = []
                    keys_to_process = set(all_settings_to_apply.keys())
                    
                    for line in lines:
                        stripped = line.strip()
                        key_found = next((key for key in keys_to_process if stripped.startswith(key + "=")), None)
                        
                        if key_found:
                            value = all_settings_to_apply[key_found]
                            if value in ["High", "On", "MAX"]:
                                continue
                            else:
                                temp_lines.append(f"{key_found}={value}\n")
                            keys_to_process.remove(key_found)
                        else:
                            temp_lines.append(line)
                    
                    if keys_to_process:
                        last_ea_line_idx = -1
                        for i, line in reversed(list(enumerate(temp_lines))):
                            if line.strip().startswith("EAres"):
                                last_ea_line_idx = i
                                break
                        
                        for key in sorted(list(keys_to_process)):
                            value = all_settings_to_apply[key]
                            if value not in ["High", "On", "MAX"]:
                                insert_line = f"{key}={value}\n"
                                if last_ea_line_idx != -1:
                                    temp_lines.insert(last_ea_line_idx + 1, insert_line)
                                else:
                                    temp_lines.append(insert_line)

                    with open(ini_file_path, 'w', encoding='utf-8') as f: f.writelines(temp_lines)
                    print(f"Successfully updated: {ini_file_path}")
                except Exception as e:
                    print(f"Error updating {ini_file_path}: {e}"); all_success = False

        return all_success, None if all_success else "One or more files failed to update."

    def _parse_rank_data(self, html_content):
        # A more robust parsing method to handle variations in the source HTML
        rank = None
        current_rr = None
        last_game_rr = None

        # Try to find rank, which is typically in brackets. E.g., "[Diamond 1]"
        rank_match = re.search(r'\[(.*?)\]', html_content)
        if rank_match:
            rank = rank_match.group(1).strip()
        elif "unrated" in html_content.lower() or "unranked" in html_content.lower():
            rank = 'Unranked'

        # If a rank was found, look for RR values.
        if rank:
            # Look for current RR, e.g., ": 10 RR" or "55 RR"
            rr_match = re.search(r':?\s*(\d+)\s*RR', html_content)
            if rr_match:
                current_rr = int(rr_match.group(1))
            elif rank.lower() in ['unranked', 'unrated']:
                current_rr = 0

            # Look for last game's RR change, e.g., "[-12]" or "[+25]"
            last_rr_match = re.search(r'\[([+-]?\d+)\]', html_content)
            if last_rr_match:
                last_game_rr = int(last_rr_match.group(1))
            elif rank.lower() in ['unranked', 'unrated']:
                last_game_rr = 0
        
        # Return the found data. Some values might be None if not found.
        return rank, current_rr, last_game_rr

    def fetch_and_update_rank_data(self, account_name, on_update_callback=None):
        account_data = self.get_saved_accounts().get(account_name)
        if not account_data:
            print(f"Account {account_name} not found for rank update.")
            return

        _, _, rank, in_game_name, in_game_tag, current_rr, last_game_rr = account_data

        if not in_game_name or not in_game_tag:
            print(f"Skipping rank update for {account_name}: Missing in-game name or tag.")
            return

        ui_settings = self.get_ima_config().get("ui_settings", {})
        raw_region = ui_settings.get("rank_check_region", "eu")

        # Map full region names to their two-letter codes for URL construction
        region_map = {
            "Europe (eu)": "eu",
            "Asia Pacific (ap)": "ap",
            "Brazil (br)": "br",
            "Korea (kr)": "kr",
            "Latin America (latam)": "latam",
            "North America (na)": "na",
            "eu": "eu",
            "ap": "ap",
            "br": "br",
            "kr": "kr",
            "latam": "latam",
            "na": "na"
        }
        region = region_map.get(raw_region, "eu") # Default to 'eu' if not found

        url = f"https://valorantrank.chat/{region}/{in_game_name}/{in_game_tag}?mmrChange=true"
        print(f"Fetching rank for {account_name} from: {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text

            new_rank, new_current_rr, new_last_game_rr = self._parse_rank_data(html_content)

            if new_rank and new_current_rr is not None and new_last_game_rr is not None:
                if new_rank.lower() == 'unrated':
                    new_rank = 'Unranked'
                if new_rank != rank or new_current_rr != current_rr or new_last_game_rr != last_game_rr:
                    print(f"Updating rank data for {account_name}: Rank={new_rank}, RR={new_current_rr}, Last Game RR={new_last_game_rr}")
                    self.set_account_in_game_name_tag(account_name, in_game_name, in_game_tag, new_current_rr, new_last_game_rr)
                    self.set_account_rank(account_name, new_rank)
                    if on_update_callback:
                        on_update_callback(account_name)
                else:
                    print(f"Rank data for {account_name} is up to date.")
            else:
                print(f"Could not parse rank data for {account_name} from URL: {url}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching rank for {account_name} from {url}: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during rank update for {account_name}: {e}")

    def _run_rank_update_loop(self, on_update_callback=None):
        while True:
            print("Starting scheduled rank update for all accounts...")
            accounts = list(self.get_saved_accounts().keys())
            for account_name in accounts:
                threading.Thread(target=self.fetch_and_update_rank_data, args=(account_name, on_update_callback)).start()
            time.sleep(3600) # Wait an hour before the next cycle

    def start_rank_update_scheduler(self, on_update_callback=None):
        print("DEBUG: start_rank_update_scheduler called.")
        # Initial fetch is now deferred and handled by the main UI thread
        scheduler_thread = threading.Thread(target=self._run_rank_update_loop, args=(on_update_callback,), daemon=True)
        scheduler_thread.start()

