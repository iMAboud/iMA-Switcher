import os
import shutil
import subprocess
import json
import ctypes
import sys
import threading
import time
from zipfile import ZipFile, BadZipFile
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import re
import time
import tempfile
import hashlib
import winreg
import pywintypes # For COM errors
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QEvent

class CustomUpdateEvent(QEvent):
    EVENT_TYPE = QEvent.Type(QEvent.registerEventType())

    def __init__(self, account_name):
        super().__init__(CustomUpdateEvent.EVENT_TYPE)
        self.account_name = account_name
try:
    import requests
except ImportError:
    requests = None
    logging.warning("'requests' library not installed. Rank fetching will not work. Please install it with 'pip install requests'")
try:
    from PIL import Image, UnidentifiedImageError
except ImportError:
    Image = None
    UnidentifiedImageError = None # Define it as None if PIL is not available
    logging.warning("Pillow not installed. Image conversion for icons will not work. Please install it with 'pip install Pillow'")

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
    logging.warning("BeautifulSoup not installed. Rank fetching will not work. Please install it with 'pip install beautifulsoup4'")

from jsonschema import validate, ValidationError

class GameSwitcher:
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "output_dir": {"type": ["string", "null"]},
            "title": {"type": "string"},
            "menu_icon_path": {"type": "string"},
            "ordered_accounts": {"type": "array", "items": {"type": "string"}},
            "last_switched_account": {"type": ["string", "null"]},
            "riot_client_exe_path": {"type": ["string", "null"]},
            "last_graphics_settings_hash": {"type": ["string", "null"]},
            "ima_menu_path": {"type": ["string", "null"]},
            "ui_settings": {
                "type": "object",
                "properties": {
                    "show_game_icons": {"type": "boolean"},
                    "show_rank_tips": {"type": "boolean"},
                    "tip_delay": {"type": "number"},
                    "use_rank_icons": {"type": "boolean"},
                    "show_rank_icon_left": {"type": "boolean"},
                    "show_name_tag": {"type": "boolean"},
                    "auto_rank_update": {"type": "boolean"},
                    "rank_check_region": {"type": "string"},
                    "grid_size": {"type": "integer"},
                    "orientation": {"type": "string"},
                    "show_current_rr": {"type": "boolean"},
                    "show_last_game_rr": {"type": "boolean"}
                },
                "required": [
                    "show_game_icons", "show_rank_tips", "tip_delay", "use_rank_icons",
                    "show_rank_icon_left", "show_name_tag", "auto_rank_update",
                    "rank_check_region", "grid_size", "orientation",
                    "show_current_rr", "show_last_game_rr"
                ],
                "additionalProperties": False
            },
            "graphics_settings": {
                "type": "object",
                "properties": {
                    "display_mode": {"type": "string"},
                    "quality": {"type": "object"},
                    "riot_settings": {"type": "object"},
                    "audio_settings": {"type": "object"}
                },
                "required": ["display_mode", "quality", "riot_settings", "audio_settings"],
                "additionalProperties": False
            },
            "app_install_path": {"type": "string"},
            # These are present at the top level in the provided config.json instance,
            # but ideally should only be nested under graphics_settings.
            # Adding them here to pass validation for the current config.json structure.
            "display_mode": {"type": "string"},
            "quality": {"type": "object"},
            "riot_settings": {"type": "object"},
            "audio_settings": {"type": "object"}
        },
        "required": [
            "title",
            "menu_icon_path",
            "ordered_accounts",
            "last_switched_account",
            "riot_client_exe_path",
            "last_graphics_settings_hash",
            "ui_settings",
            "graphics_settings",
            "app_install_path"
        ],
        "additionalProperties": False
    }
    DEFAULT_CONFIG = {
        "title": "Valorant",
        "menu_icon_path": "",
        "ordered_accounts": [],
        "last_switched_account": None,
        "riot_client_exe_path": None,
        "last_graphics_settings_hash": None,
        "ima_menu_path": None,
        "ui_settings": {
            "show_game_icons": True,
            "show_rank_tips": True,
            "tip_delay": 1.0,
            "use_rank_icons": False,
            "show_rank_icon_left": True,
            "show_name_tag": True,
            "auto_rank_update": True,
            "rank_check_region": "eu",
            "grid_size": 4,
            "orientation": "vertical",
            "show_current_rr": True,
            "show_last_game_rr": True
        },
        "graphics_settings": {
            "display_mode": "Default",
            "quality": {
                "sg.ViewDistanceQuality": 3, "sg.AntiAliasingQuality": 3, "sg.ShadowQuality": 3,
                "sg.PostProcessQuality": 3, "sg.TextureQuality": 3, "sg.EffectsQuality": 3,
                "sg.FoliageQuality": 3, "sg.ShadingQuality": 3
            },
            "riot_settings": {},
            "audio_settings": {}
        },
        "app_install_path": ""
    }
    def __init__(self, base_directory=None):
        logging.debug("GameSwitcher: Initializing")
        self.app_data_path = os.getenv('LOCALAPPDATA')
        
        # Base directory for application assets (where the executable is or _MEIPASS)
        if base_directory:
            self.base_dir = Path(base_directory)
        else:
            self.base_dir = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.resolve()
        
        # Persistent directory for user profiles and configuration
        self.user_data_dir = Path(self.app_data_path) / "iMA Switcher"
        
        self.profiles_dir = self.user_data_dir / "profiles"
        self.config_path = self.user_data_dir / "config.json"
        
        # Initialize config once at startup
        self.config = self._load_config()
        self._account_game_configs_cache = {}
        self._icon_cache = {}
        self._saved_accounts_cache = None
        self.switch_counter = 0
        self._cleanup_valorant_temp_files()

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
        os.makedirs(self.profiles_dir, exist_ok=True) # Ensure profiles directory exists
        self._cleanup_valorant_temp_files()

    def _cleanup_valorant_temp_files(self):
        # Clean up CrashReportClient
        crash_report_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Config" / "CrashReportClient"
        if crash_report_path.exists():
            try:
                shutil.rmtree(crash_report_path)
                logging.info(f"Successfully cleaned up {crash_report_path}")
            except OSError as e:
                logging.error(f"Failed to clean up {crash_report_path}: {e}")

        # Clean up log files
        logs_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Logs"
        if logs_path.exists():
            for filename in os.listdir(logs_path):
                if filename.startswith("ShooterGame-backup") and filename.endswith(".log"):
                    try:
                        (logs_path / filename).unlink()
                        logging.info(f"Successfully deleted log file: {filename}")
                    except OSError as e:
                        logging.error(f"Failed to delete log file {filename}: {e}")

    def is_admin(self):
        try: return ctypes.windll.shell32.IsUserAnAdmin()
        except pywintypes.error as e:
            logging.error(f"Error checking admin privileges: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred while checking admin privileges: {e}")
            return False

    def _load_config(self, force_reload=False):
        # Recursively update config with loaded values
        def deep_update(target, source):
            for k, v in source.items():
                if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                    target[k] = deep_update(target[k], v)
                else:
                    target[k] = v
            return target

        config = self.DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                config = deep_update(config, loaded_config)

                # Validate the merged config against the schema
                validate(instance=config, schema=self.CONFIG_SCHEMA)

            except FileNotFoundError:
                logging.warning(f"config.json not found at {self.config_path}. Using defaults.")
                QMessageBox.critical(None, "Configuration Error", "config.json not found. Using default settings.")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.warning(f"config.json is corrupted or has encoding issues. Using defaults. Error: {e}")
                QMessageBox.critical(None, "Configuration Error", f"Your config.json file is corrupted or unreadable. Using default settings. Error: {e}")
            except ValidationError as e:
                logging.warning(f"config.json validation failed. Using defaults. Error: {e.message}")
                QMessageBox.critical(None, "Configuration Error", f"Your config.json file is invalid: {e.message}. Using default settings.")
            except Exception as e:
                logging.error(f"An unexpected error occurred while loading config: {e}")
                QMessageBox.critical(None, "Configuration Error", f"An unexpected error occurred while loading config: {e}. Using default settings.")
        return config

    def _save_config(self):
        try:
            with self.config_path.open('w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except IOError as e:
            logging.error(f"Failed to save config to {self.config_path}: {e}")
            QMessageBox.critical(None, "Save Error", f"Failed to save configuration: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while saving config: {e}")
            QMessageBox.critical(None, "Save Error", f"An unexpected error occurred while saving configuration: {e}")

    def get_ima_config(self):
        return self.config

    def set_ima_config(self, settings):
        self.config.update(settings)
        self._save_config()

    def initialize_riot_client_paths(self, riot_client_exe_path=None):

        exe_path = riot_client_exe_path
        if not exe_path or not Path(exe_path).exists():
            exe_path = self.config.get("riot_client_exe_path")

        if not exe_path or not Path(exe_path).exists():
            exe_path = self._find_riot_client_path()

        self.riot_games_config["ExeLocationDefault"] = str(exe_path) if exe_path and Path(exe_path).exists() else ""
        self.riot_client_data_path = Path(self.app_data_path) / "Riot Games" / "Riot Client"
        self.riot_games_config.update(self._load_riot_games_config_defaults())

    def _find_riot_client_from_registry(self):
        try:
            # Check the uninstall information
            uninstall_key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Riot Game valorant.live"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, uninstall_key_path) as key:
                install_location, _ = winreg.QueryValueEx(key, "InstallLocation")
                if install_location and os.path.isdir(install_location):
                    exe_path = os.path.join(install_location, "RiotClientServices.exe")
                    if os.path.exists(exe_path):
                        return exe_path
        except FileNotFoundError:
            pass  # Key not found, continue
        except OSError as e: # Catching OSError for registry access issues
            logging.error(f"Error reading registry for uninstall info: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading registry for uninstall info: {e}")

        try:
            # Check the Riot Games key
            riot_games_key_path = r"SOFTWARE\Riot Games\Riot Client"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, riot_games_key_path) as key:
                exe_path, _ = winreg.QueryValueEx(key, "ExecutablePath")
                if exe_path and os.path.exists(exe_path):
                    return exe_path
        except FileNotFoundError:
            pass  # Key not found, continue
        except OSError as e: # Catching OSError for registry access issues
            logging.error(f"Error reading registry for Riot Games info: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading registry for Riot Games info: {e}")

        return None

    def _find_riot_client_path(self):
        # First, try to find the path in the registry
        registry_path = self._find_riot_client_from_registry()
        if registry_path:
            return registry_path

        # If not found in registry, fall back to common paths
        common_paths = [
            Path("C:") / "Riot Games" / "Riot Client" / "RiotClientServices.exe",
            Path(os.getenv('PROGRAMFILES')) / "Riot Games" / "Riot Client" / "RiotClientServices.exe",
            Path(os.getenv('PROGRAMFILES(X86)')) / "Riot Games" / "Riot Client" / "RiotClientServices.exe",
        ]
        for path in common_paths:
            if path.exists():
                return str(path)
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

    def _get_account_path(self, account_name): return self.profiles_dir / account_name

    def _terminate_processes(self):
        logging.info("Terminating Riot and game processes...")
        all_processes = self.GAMES['valorant']["processes_to_kill"] + self.GAMES['lol']["processes_to_kill"]
        for exe in all_processes:
            try:
                subprocess.run(f"taskkill /f /im {exe}", shell=True, check=True, capture_output=True, text=True)
                logging.info(f"Terminated process: {exe}")
            except subprocess.CalledProcessError as e:
                logging.debug(f"Process {exe} not running or could not be terminated: {e.stderr.strip()}")
            except Exception as e:
                logging.error(f"Error terminating process {exe}: {e}")

    def _create_junction(self, source, link_name):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            subprocess.run(['cmd', '/c', 'mklink', '/J', link_name, source], check=True, startupinfo=startupinfo, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create junction from {source} to {link_name}: {e.stderr.strip()}")
            raise
        except FileNotFoundError:
            logging.error("mklink command not found. Ensure cmd.exe is in your PATH.")
            raise
        except Exception as e:
            logging.error(f"An unexpected error occurred while creating junction: {e}")
            raise

    def _remove_junction_or_dir(self, path):
        logging.debug(f"Attempting to remove: {path}")
        if not path.exists(): # Use path.exists for general check
            logging.debug(f"Path does not exist, no removal needed: {path}")
            return
        try:
            if os.path.islink(path): # Explicitly check for symbolic links first
                logging.debug(f"Removing symbolic link/junction: {path}")
                os.remove(path)
            elif os.path.isfile(path):
                logging.debug(f"Removing file: {path}")
                os.remove(path)
            elif os.path.isdir(path): # If it's a directory (and not a symlink)
                try:
                    logging.debug(f"Attempting to remove empty directory or junction with os.rmdir: {path}")
                    os.rmdir(path) # Try rmdir for empty directories or junctions
                except OSError as e:
                    # If rmdir fails (e.g., directory not empty), then use rmtree
                    logging.debug(f"os.rmdir failed for {path} ({e}), falling back to shutil.rmtree.")
                    logging.debug(f"Removing directory and its contents: {path}")
                    shutil.rmtree(path)
            logging.debug(f"Successfully removed: {path}")
        except PermissionError as e:
            logging.error(f"Permission denied when trying to remove {path}: {e}")
            raise # Re-raise to ensure the error is propagated
        except OSError as e:
            logging.error(f"OS error when trying to remove {path}: {e}")
            raise # Re-raise to ensure the error is propagated
        except Exception as e:
            logging.error(f"An unexpected error occurred when trying to remove {path}: {e}")
            raise # Re-raise to ensure the error is propagated

    def _load_game_config(self, account_name):
        if account_name in self._account_game_configs_cache:
            return self._account_game_configs_cache[account_name]

        game_config_path = self._get_account_path(account_name) / 'game.json'
        if game_config_path.exists():
            with game_config_path.open('r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    self._account_game_configs_cache[account_name] = data # Cache the loaded data
                    return data
                except json.JSONDecodeError:
                    logging.warning(f"game.json for {account_name} is corrupted. Starting with empty config.")
                    self._account_game_configs_cache[account_name] = {} # Cache empty config for corrupted file
                    return {}
        self._account_game_configs_cache[account_name] = {} # Cache empty config for non-existent file
        return {}

    def _save_game_config(self, account_name, data):
        game_config_path = self._get_account_path(account_name) / 'game.json'
        with game_config_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        self._account_game_configs_cache[account_name] = data # Update the cache

    def get_account_game(self, account_name):
        data = self._load_game_config(account_name)
        return {
            'game': data.get('game', 'valorant'),
            'rank': data.get('rank', None),
            'in_game_name': data.get('in_game_name', None),
            'in_game_tag': data.get('in_game_tag', None),
            'current_rr': data.get('current_rr', None),
            'last_game_rr': data.get('last_game_rr', None)
        }

    def set_account_game(self, account_name, game):
        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False
        data = self._load_game_config(account_name)
        data['game'] = game
        self._save_game_config(account_name, data)
        self._invalidate_saved_accounts_cache()
        return True

    def set_account_rank(self, account_name, rank):
        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False
        data = self._load_game_config(account_name)
        data['rank'] = rank
        self._save_game_config(account_name, data)
        self._invalidate_saved_accounts_cache()
        self.update_ima_menu_if_enabled('update', account_name)
        return True

    def set_account_in_game_name_tag(self, account_name, in_game_name, in_game_tag, current_rr=None, last_game_rr=None):
        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False
        data = self._load_game_config(account_name)
        data['in_game_name'] = in_game_name
        data['in_game_tag'] = in_game_tag
        data['current_rr'] = current_rr
        data['last_game_rr'] = last_game_rr
        self._save_game_config(account_name, data)
        self._invalidate_saved_accounts_cache()
        return True

    def save_account(self, account_name, game='valorant', rank=None, in_game_name=None, in_game_tag=None):
        account_path = self._get_account_path(account_name)
        account_path.mkdir(exist_ok=True)
        for item_name in self.riot_games_config["LoginData"].keys():
            source_path = self.riot_client_data_path / item_name
            dest_path = account_path / item_name
            if not source_path.exists():
                continue
            self._remove_junction_or_dir(dest_path)
            if source_path.is_dir():
                shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
            elif source_path.is_file():
                shutil.copy2(source_path, dest_path)
        self.set_account_game(account_name, game)
        if rank: self.set_account_rank(account_name, rank)
        if in_game_name or in_game_tag: self.set_account_in_game_name_tag(account_name, in_game_name, in_game_tag)
        self._invalidate_saved_accounts_cache()
        self.update_ima_menu_if_enabled('add', account_name)
        return True

    def _perform_post_switch_tasks(self, account_name, game, on_update_callback):
        """Handles tasks that can be performed after the game has been launched,
        to avoid delaying the game launch itself."""
        time.sleep(10) # Delay to prioritize game launch
        # Update graphics settings if Valorant was launched
        if game == 'valorant':
            graphics_settings = self.get_graphics_settings()
            self.update_all_game_user_settings(graphics_settings)

        # Fetch rank data if enabled
        ui_settings = self.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True):
            self.fetch_and_update_rank_data(account_name, False, on_update_callback)

        # Update the last switched account in the config
        self.config["last_switched_account"] = account_name
        self._save_config()

    def switch_account(self, account_name, selected_game=None, on_update_callback=None):
        if not self.is_admin():
            return False, "Administrator rights are required to switch accounts.", None

        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False, f"Profile for '{account_name}' not found.", None

        account_game_data = self.get_account_game(account_name)
        game = account_game_data['game']

        if game == 'both' and selected_game is None:
            return True, "Game selection required.", "both"
        elif game == 'both' and selected_game is not None:
            game = selected_game

        self._terminate_processes()

        backup_paths = {}
        try:
            # 1. Backup phase: Rename existing directories/junctions
            for item_name in self.riot_games_config["LoginData"].keys():
                riot_item_path = self.riot_client_data_path / item_name
                backup_path = self.riot_client_data_path / f"{item_name}.bak"
                
                if riot_item_path.is_symlink() or riot_item_path.exists():
                    if backup_path.is_symlink() or backup_path.exists():
                        self._remove_junction_or_dir(backup_path)
                    riot_item_path.rename(backup_path)
                    backup_paths[item_name] = backup_path

            # 2. Attempt phase: Create new junctions
            for item_name in self.riot_games_config["LoginData"].keys():
                riot_item_path = self.riot_client_data_path / item_name
                profile_item_path = account_path / item_name
                
                if profile_item_path.exists():
                    self._create_junction(str(profile_item_path), str(riot_item_path))

            # 3. Commit phase: Delete backups
            for backup_path in backup_paths.values():
                if backup_path.is_symlink() or backup_path.exists():
                    self._remove_junction_or_dir(backup_path)

        except Exception as e:
            # 4. Rollback phase
            logging.error(f"Account switch failed, rolling back. Error: {e}")
            for item_name, backup_path in backup_paths.items():
                riot_item_path = self.riot_client_data_path / item_name
                
                # Clean up the failed/partial new junction/directory
                if riot_item_path.is_symlink() or riot_item_path.exists():
                    self._remove_junction_or_dir(riot_item_path)
                
                # Restore from backup
                if backup_path.is_symlink() or backup_path.exists():
                    backup_path.rename(riot_item_path)
            
            return False, f"Failed to create junction: {e}\nYour previous configuration has been restored.", None

        try:
            launch_args = self.GAMES[game]["launch_args"].split()
            command = [self.riot_games_config["ExeLocationDefault"]] + launch_args
            
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(command, creationflags=creationflags, close_fds=True)

            # Run post-switch tasks in a background thread
            post_switch_thread = threading.Thread(
                target=self._perform_post_switch_tasks,
                args=(account_name, game, on_update_callback),
                daemon=True
            )
            post_switch_thread.start()

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
            riot_item_path = self.riot_client_data_path / item_name
            self._remove_junction_or_dir(riot_item_path)
        try:
            subprocess.Popen([self.riot_games_config["ExeLocationDefault"]])
            return True
        except FileNotFoundError:
            return False

    def _invalidate_saved_accounts_cache(self):
        self._saved_accounts_cache = None

    def get_saved_accounts(self):
        if self._saved_accounts_cache is not None:
            return self._saved_accounts_cache

        accounts_data = {}
        try:
            dirs = [d for d in self.profiles_dir.iterdir() if d.is_dir()]
            for account_dir in sorted(dirs):
                account_name = account_dir.name
                icon_path = account_dir / "icon.png"
                account_game_data = self.get_account_game(account_name)
                accounts_data[account_name] = {
                    "icon_path": str(icon_path) if icon_path.exists() else None,
                    **account_game_data
                }
        except FileNotFoundError:
            self.profiles_dir.mkdir(exist_ok=True)

        self._saved_accounts_cache = accounts_data
        return accounts_data

    def rename_account(self, old_name, new_name):
        old_path, new_path = self._get_account_path(old_name), self._get_account_path(new_name)
        if old_path.exists() and not new_path.exists():
            old_path.rename(new_path)
            if old_name in self._account_game_configs_cache:
                self._account_game_configs_cache[new_name] = self._account_game_configs_cache.pop(old_name)
            self._invalidate_saved_accounts_cache()
            self.update_ima_menu_if_enabled('rename', new_name, old_name=old_name)
            return True
        return False

    def delete_account(self, account_name):
        account_path = self._get_account_path(account_name)
        if account_path.exists():
            shutil.rmtree(account_path)
            if account_name in self._account_game_configs_cache:
                del self._account_game_configs_cache[account_name]
            self._invalidate_saved_accounts_cache()
            self.update_ima_menu_if_enabled('delete', account_name)
            return True
        return False

    def set_account_icon(self, account_name, source_icon_path):
        account_path = self._get_account_path(account_name)
        if not account_path.is_dir(): return False
        dest_icon_path = account_path / "icon.png"
        try:
            if Image:
                pil_image = Image.open(source_icon_path)
                pil_image.save(dest_icon_path, "PNG")
            else:
                shutil.copy(source_icon_path, dest_icon_path)
            # Invalidate cache for this icon
            resolved_dest_icon_path = str(dest_icon_path.resolve())
            if resolved_dest_icon_path in self._icon_cache:
                del self._icon_cache[resolved_dest_icon_path]
            self._invalidate_saved_accounts_cache()
            self.update_ima_menu_if_enabled('update', account_name)
            return True
        except Exception as e:
            logging.error(f"Error setting account icon: {e}")
            return False

    def remove_account_icon(self, account_name):
        account_path = self._get_account_path(account_name)
        icon_path = account_path / "icon.png"
        if icon_path.exists():
            try:
                icon_path.unlink()
                # Invalidate cache for this icon
                resolved_icon_path = str(icon_path.resolve())
                if resolved_icon_path in self._icon_cache:
                    del self._icon_cache[resolved_icon_path]
                self._invalidate_saved_accounts_cache()
                self.update_ima_menu_if_enabled('update', account_name)
                return True
            except Exception as e:
                logging.error(f"Error removing account icon: {e}")
                return False
        return False

    def _create_shortcut(self, shortcut_path, target_path, arguments="", working_dir=None, icon_location=None, description=""):
        try:
            import win32com.client
            from PIL import Image
        except ImportError:
            logging.error("Error: pywin32 and Pillow are required to create shortcuts. Please run 'pip install pywin32 Pillow'.")
            return False

        shortcut_path_p = Path(shortcut_path)
        target_path_p = Path(target_path)
        
        if working_dir is None:
            working_dir_s = str(target_path_p.parent)
        else:
            working_dir_s = str(Path(working_dir))

        icon_location_s = None
        ico_path_p = None

        if icon_location:
            icon_location_p = Path(icon_location)
            if icon_location_p.suffix.lower() == '.png':
                try:
                    img = Image.open(icon_location_p)
                    ico_path_p = self.user_data_dir / (shortcut_path_p.name + ".ico")
                    img.save(ico_path_p, format='ICO', sizes=[(32,32)])
                    icon_location_s = str(ico_path_p)
                except Exception as e:
                    logging.error(f"Failed to convert PNG to ICO: {e}")
                    icon_location_s = str(target_path_p) # Fallback to target exe icon
            else:
                icon_location_s = str(icon_location_p)
        else:
            icon_location_s = str(target_path_p)

        try:
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path_p))
            shortcut.TargetPath = str(target_path_p)
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = working_dir_s
            shortcut.IconLocation = icon_location_s
            shortcut.Description = description
            shortcut.Save()
            return True
        except Exception as e:
            logging.error(f"Error creating shortcut at {shortcut_path}: {e}")
            return False
        finally:
            pass

    def create_desktop_shortcut(self, account_name):
        desktop_path = Path.home() / "Desktop"
        shortcut_path = desktop_path / f"{account_name}.lnk"

        target_path = sys.executable
        
        if not getattr(sys, 'frozen', False):
            pythonw_path = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
            if os.path.exists(pythonw_path):
                target_path = pythonw_path
            main_script_path = os.path.abspath(os.path.join(self.base_dir, "main.pyw"))
            arguments = f'"{main_script_path}" --switch "{account_name}"'
        else:
            arguments = f'--switch "{account_name}"'

        account_data = self.get_saved_accounts().get(account_name)
        game = account_data['game']
        rank = account_data['rank']
        description = f"Launch {game.capitalize()} with {account_name} account"

        ui_settings = self.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)

        icon_location = self.get_icon_path_for_account(account_name, rank, use_rank_icons)

        return self._create_shortcut(shortcut_path, target_path, arguments=arguments, icon_location=icon_location, description=description)

    def get_icon_path_for_account(self, account_name, rank=None, use_rank_icons=False):
        icon_path_to_use = None
        account_data = self.get_saved_accounts().get(account_name)
        account_icon_path = account_data['icon_path'] if account_data else None

        if use_rank_icons and rank:
            app_install_path = Path(self.get_ima_config().get("app_install_path", self.base_dir))
            rank_icon_candidate_path = app_install_path / "Assets" / f"{rank.lower().replace(" ", "_")}.png"
            if rank_icon_candidate_path.exists():
                icon_path_to_use = rank_icon_candidate_path
        
        if icon_path_to_use is None and account_icon_path and Path(account_icon_path).exists():
            icon_path_to_use = Path(account_icon_path)

        if icon_path_to_use is None:
            app_install_path = Path(self.get_ima_config().get("app_install_path", self.base_dir))
            icon_path_to_use = app_install_path / "logo.png"
        
        return str(icon_path_to_use.resolve())

    def get_backup_filename(self):
        now = datetime.now()
        timestamp = now.strftime("iMA-Switcher_%M-%H_%d-%m-%y")
        return timestamp

    def backup_profiles(self, backup_file_path):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                # 1. Copy profiles and config to a 'UserData' folder in temp_dir
                user_data_backup_path = temp_dir_path / "UserData"
                user_data_backup_path.mkdir()
                shutil.copytree(self.profiles_dir, user_data_backup_path / "profiles")
                shutil.copy2(self.config_path, user_data_backup_path / "config.json")

                # 2. Copy Riot Games and VALORANT data to a 'RiotData' folder in temp_dir
                riot_data_backup_path = temp_dir_path / "RiotData"
                riot_data_backup_path.mkdir()
                
                riot_client_path = Path(self.app_data_path) / "Riot Games" / "Riot Client"
                if riot_client_path.exists():
                    shutil.copytree(riot_client_path, riot_data_backup_path / "Riot Client")

                valorant_path = Path(self.app_data_path) / "VALORANT"
                if valorant_path.exists():
                    shutil.copytree(valorant_path, riot_data_backup_path / "VALORANT")

                # 3. Create the zip archive from the temp_dir
                shutil.make_archive(base_name=str(backup_file_path).replace('.zip', ''),
                                    format='zip',
                                    root_dir=temp_dir)
            return True
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False

    def _robust_rmtree(self, path, max_retries=3, delay=1):
        path = Path(path)
        for i in range(max_retries):
            try:
                if path.exists():
                    shutil.rmtree(path)
                    logging.info(f"Successfully removed directory: {path}")
                return
            except OSError as e:
                logging.warning(f"Attempt {i+1}/{max_retries} to remove {path} failed: {e}")
                if i < max_retries - 1:
                    time.sleep(delay)
                else:
                    logging.error(f"Failed to remove {path} after {max_retries} attempts.")
                    raise

    def restore_profiles(self, backup_file_path):
        try:
            self._terminate_processes()
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                with ZipFile(backup_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir_path)

                user_data_source = temp_dir_path / "UserData"
                if user_data_source.exists():
                    backup_config_path = user_data_source / "config.json"
                    if backup_config_path.exists():
                        shutil.copy2(backup_config_path, self.config_path)
                        self.config = self._load_config(force_reload=True)

                    backup_profiles_dir = user_data_source / "profiles"
                    if backup_profiles_dir.exists():
                        for account_name in os.listdir(backup_profiles_dir):
                            source_account_path = backup_profiles_dir / account_name
                            dest_account_path = self.profiles_dir / account_name
                            if source_account_path.is_dir():
                                self._robust_rmtree(dest_account_path)
                                shutil.copytree(source_account_path, dest_account_path)

                riot_data_source = temp_dir_path / "RiotData"
                if riot_data_source.exists():
                    riot_client_dest = Path(self.app_data_path) / "Riot Games" / "Riot Client"
                    self._robust_rmtree(riot_client_dest)
                    if (riot_data_source / "Riot Client").exists():
                        shutil.move(str(riot_data_source / "Riot Client"), str(riot_client_dest))

                    valorant_dest = Path(self.app_data_path) / "VALORANT"
                    self._robust_rmtree(valorant_dest)
                    if (riot_data_source / "VALORANT").exists():
                        shutil.move(str(riot_data_source / "VALORANT"), str(valorant_dest))
            
            logging.info("Clearing caches after restore...")
            self._icon_cache.clear()
            self._account_game_configs_cache.clear()
            self._invalidate_saved_accounts_cache()
            logging.info("Caches cleared.")

            self.update_ima_menu_if_enabled('restore', list(self.get_saved_accounts().keys()))
            return True
        except Exception as e:
            logging.error(f"Restore failed: {e}", exc_info=True)
            return False

    def update_ima_menu_if_enabled(self, action, name=None, old_name=None):
        ima_config = self.get_ima_config()
        ima_menu_path_str = ima_config.get("ima_menu_path")
        if not ima_menu_path_str: return

        ima_menu_path = Path(ima_menu_path_str)
        output_dir = ima_menu_path / "imports"
        if not output_dir.exists():
            logging.warning(f"iMA Menu imports directory not found at {output_dir}. Auto-update skipped.")
            return
        
        logging.info(f"iMA Auto-Update: Action='{action}', Name='{name}'")
        
        current_ordered_list = ima_config.get("ordered_accounts", [])
        if action == 'add' and name and name not in current_ordered_list: current_ordered_list.append(name)
        elif action == 'delete' and name and name in current_ordered_list: current_ordered_list.remove(name)
        elif action == 'rename' and name and old_name and old_name in current_ordered_list: current_ordered_list[current_ordered_list.index(old_name)] = name
        elif action == 'restore':
            # On restore, the ordered list is loaded from the restored config, so we just need to trigger an update.
            pass
        
        ima_config["ordered_accounts"] = current_ordered_list
        self.set_ima_config(ima_config)
        
        try:
            self.generate_ima_menu_script(
                output_dir=str(output_dir),
                title=ima_config["title"],
                ordered_accounts=ima_config["ordered_accounts"],
                menu_icon_path=ima_config.get("menu_icon_path", ""),
                save_config=False  
            )
            self.update_ima_shell_script(ima_menu_path)
            logging.info("Auto-update of valo.nss and shell.nss successful.")
        except Exception as e:
            logging.error(f"Automatic iMA menu update failed: {e}")

    def update_ima_shell_script(self, ima_menu_path):
        shell_nss_path = Path(ima_menu_path) / 'shell.nss'
        import_line = "import 'imports/valo.nss'"

        if not shell_nss_path.exists():
            logging.error(f"shell.nss not found at {shell_nss_path}")
            return False, f"shell.nss not found at the specified path."

        try:
            with open(shell_nss_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Check if the import line already exists
            if any(import_line in line for line in lines):
                logging.info(f"'{import_line}' already exists in {shell_nss_path}. No changes needed.")
                return True, "Import already exists."

            # Add the import line at the end
            with open(shell_nss_path, 'a', encoding='utf-8') as f:
                f.write(f'\n{import_line}')
            
            logging.info(f"Successfully added '{import_line}' to {shell_nss_path}")
            return True, "Successfully updated shell.nss."

        except IOError as e:
            logging.error(f"Error reading/writing shell.nss: {e}")
            return False, f"Error accessing shell.nss: {e}"
        except Exception as e:
            logging.error(f"An unexpected error occurred while updating shell.nss: {e}")
            return False, f"An unexpected error occurred: {e}"

    def generate_ima_menu_script(self, output_dir, title, ordered_accounts, menu_icon_path="", save_config=False):
        if save_config:
            self.set_ima_config({"output_dir": output_dir, "title": title, "menu_icon_path": menu_icon_path, "ordered_accounts": ordered_accounts})
        
        script_path = Path(output_dir) / 'valo.nss'
        icons_dir = Path(output_dir) / "icons"; icons_dir.mkdir(exist_ok=True)
        menu_icon_arg = ""
        if menu_icon_path and Path(menu_icon_path).exists():
            try:
                base_icon_name = Path(menu_icon_path).name
                dest_icon_path = icons_dir / base_icon_name
                shutil.copy(menu_icon_path, dest_icon_path)
                ima_icon_path = fr"@app.dir\imports\icons\{base_icon_name}"
                menu_icon_arg = f" icon='{ima_icon_path}'"
            except Exception as e:
                logging.error(f"Could not copy menu icon: {e}")
        
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
            account_data = accounts_data.get(account_name)
            icon_source_path = account_data['icon_path']
            game = account_data['game']
            rank = account_data['rank']
            
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
        valorant_config_path = Path(os.getenv('LOCALAPPDATA')) / "VALORANT" / "Saved" / "Config"
        ini_files = []
        logging.debug(f"Searching for GameUserSettings.ini in: {valorant_config_path}")
        if not valorant_config_path.exists():
            logging.warning(f"Valorant config path does not exist: {valorant_config_path}")
            return []

        for root, dirs, files in os.walk(valorant_config_path):
            if "GameUserSettings.ini" in files and Path(root).name == "Windows":
                ini_file_path = Path(root) / "GameUserSettings.ini"
                ini_files.append(ini_file_path)
                logging.debug(f"Found: {ini_file_path}")
        if not ini_files:
            logging.info("No GameUserSettings.ini files found.")
        return ini_files

    def _find_riot_user_settings_files(self):
        valorant_config_path = Path(os.getenv('LOCALAPPDATA')) / "VALORANT" / "Saved" / "Config"
        ini_files = []
        logging.debug(f"Searching for RiotUserSettings.ini in: {valorant_config_path}")
        if not valorant_config_path.exists():
            logging.warning(f"Valorant config path does not exist: {valorant_config_path}")
            return []

        for root, dirs, files in os.walk(valorant_config_path):
            if "RiotUserSettings.ini" in files and Path(root).name == "Windows":
                ini_file_path = Path(root) / "RiotUserSettings.ini"
                ini_files.append(ini_file_path)
                logging.debug(f"Found: {ini_file_path}")
        if not ini_files:
            logging.info("No RiotUserSettings.ini files found.")
        return ini_files

    def get_graphics_settings(self):
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
            with ini_files[0].open('r', encoding='utf-8') as f:
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
            with ini_files[0].open('r', encoding='utf-8') as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line.startswith("EAres") and "=" in stripped_line:
                        key, value = stripped_line.split("=", 1)
                        settings[key.strip()] = value.strip()
            return settings, None
        except Exception as e:
            return None, f"Error reading {ini_files[0]}: {e}"

    def update_all_game_user_settings(self, graphics_settings):
        # Calculate a hash of the settings to avoid unnecessary file writes.
        settings_str = json.dumps(graphics_settings, sort_keys=True)
        current_hash = hashlib.sha256(settings_str.encode('utf-8')).hexdigest()

        last_hash = self.config.get("last_graphics_settings_hash")
        if last_hash and last_hash == current_hash:
            logging.info("Graphics settings are already up to date. Skipping file I/O.")
            return True, "Settings already up to date."

        game_user_ini_files = self._find_game_user_settings_files()
        riot_user_ini_files = self._find_riot_user_settings_files()
        all_success = True

        if not game_user_ini_files:
            logging.info("No GameUserSettings.ini files found to update.")
        else:
            display_mode = graphics_settings.get("display_mode", "Default")
            quality_settings = graphics_settings.get("quality", {})
            
            for ini_file_path in game_user_ini_files:
                try:
                    with ini_file_path.open('r', encoding='utf-8') as f: lines = f.readlines()
                    
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

                    with ini_file_path.open('w', encoding='utf-8') as f: f.writelines(temp_lines)
                    logging.info(f"Successfully updated: {ini_file_path}")
                except Exception as e:
                    logging.error(f"Error updating {ini_file_path}: {e}")
                    all_success = False

        if not riot_user_ini_files:
            logging.info("No RiotUserSettings.ini files found to update.")
        else:
            riot_settings = graphics_settings.get("riot_settings", {})
            audio_settings = graphics_settings.get("audio_settings", {})
            all_settings_to_apply = {**riot_settings, **audio_settings}

            for ini_file_path in riot_user_ini_files:
                try:
                    with ini_file_path.open('r', encoding='utf-8') as f: lines = f.readlines()
                    
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

                    with ini_file_path.open('w', encoding='utf-8') as f: f.writelines(temp_lines)
                    logging.info(f"Successfully updated: {ini_file_path}")
                except Exception as e:
                    logging.error(f"Error updating {ini_file_path}: {e}")
                    all_success = False
        
        if all_success:
            self.config["last_graphics_settings_hash"] = current_hash
            self._save_config()

        return all_success, None if all_success else "One or more files failed to update."

    def get_icon_from_cache(self, icon_path):
        """Gets an icon from the cache. Returns None if not found."""
        return self._icon_cache.get(icon_path)

    def get_placeholder_qicon(self):
        """Returns a generic placeholder QIcon for async loading."""
        placeholder_path = "placeholder_loading"
        if placeholder_path in self._icon_cache:
            return self._icon_cache[placeholder_path]

        from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QIcon
        from PyQt5.QtCore import Qt
        pixmap = QPixmap(128, 128)
        pixmap.fill(QColor("#3a3637"))
        p = QPainter(pixmap)
        p.setPen(QColor("#c89f68"))
        p.setFont(QFont("Segoe UI", 28, QFont.Bold))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "...")
        p.end()
        icon = QIcon(pixmap)
        self._icon_cache[placeholder_path] = icon
        return icon

    def get_qicon_from_path(self, icon_path):
        if icon_path in self._icon_cache:
            return self._icon_cache[icon_path]

        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
        from PyQt5.QtCore import Qt, QSize, QRectF
        from io import BytesIO
        try:
            from PIL import Image
        except ImportError:
            Image = None
            logging.warning("Pillow not installed. Image conversion for icons will not work. Please install it with 'pip install Pillow'")

        if icon_path and Path(icon_path).exists():
            try:
                if Image:
                    pil_image = Image.open(icon_path)
                    pil_image = pil_image.convert("RGBA")
                    byte_array = BytesIO()
                    pil_image.save(byte_array, format="PNG")
                    byte_array.seek(0)
                    
                    pixmap = QPixmap()
                    pixmap.loadFromData(byte_array.getvalue(), "PNG")
                    icon = QIcon(pixmap)
                else:
                    icon = QIcon(icon_path)
                self._icon_cache[icon_path] = icon
                return icon
            except Exception as e:
                logging.error(f"Error loading icon from {icon_path}: {e}. Using default icon.")
        
        # Default icon for errors or missing files
        pixmap = QPixmap(128, 128)
        pixmap.fill(QColor("#c89f68"))
        p = QPainter(pixmap)
        p.setPen(QColor("#2c2a2b"))
        p.setFont(QFont("Segoe UI", 56, QFont.Bold))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "?")
        p.end()
        icon = QIcon(pixmap)
        self._icon_cache[icon_path] = icon # Cache the error icon against the path
        return icon

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

    def fetch_and_update_rank_data(self, account_name, is_manual_refresh=False, on_update_callback=None):
        if not requests:
            logging.warning("Rank fetching skipped: 'requests' library not installed.")
            return

        logging.debug(f"fetch_and_update_rank_data called for {account_name}. Manual refresh: {is_manual_refresh}")
        ui_settings = self.get_ima_config().get("ui_settings", {})
        auto_rank_update_enabled = ui_settings.get("auto_rank_update", True)

        if not auto_rank_update_enabled and not is_manual_refresh:
            logging.debug(f"Rank update skipped for {account_name}: auto_rank_update disabled and not manual refresh.")
            return

        account_data = self.get_saved_accounts().get(account_name)
        if not account_data:
            logging.debug(f"Account data not found for {account_name}.")
            return

        rank = account_data['rank']
        in_game_name = account_data['in_game_name']
        in_game_tag = account_data['in_game_tag']
        current_rr = account_data['current_rr']
        last_game_rr = account_data['last_game_rr']

        if not in_game_name or not in_game_tag:
            logging.debug(f"Skipping rank fetch for {account_name}: missing in-game name or tag.")
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
        logging.debug(f"Fetching rank from URL: {url}")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            html_content = response.text
            logging.debug(f"Successfully fetched HTML for {account_name}.")

            new_rank, new_current_rr, new_last_game_rr = self._parse_rank_data(html_content)
            logging.debug(f"Parsed rank data for {account_name}: Rank={new_rank}, CurrentRR={new_current_rr}, LastGameRR={new_last_game_rr}")

            if new_rank and new_current_rr is not None and new_last_game_rr is not None:
                if new_rank.lower() == 'unrated':
                    new_rank = 'Unranked'
                if new_rank != rank or new_current_rr != current_rr or new_last_game_rr != last_game_rr:
                    logging.debug(f"Rank data changed for {account_name}. Updating...")
                    self.set_account_in_game_name_tag(account_name, in_game_name, in_game_tag, new_current_rr, new_last_game_rr)
                    self.set_account_rank(account_name, new_rank)
                    if on_update_callback:
                        logging.debug(f"Calling on_update_callback for {account_name}.")
                        on_update_callback(account_name)
                    
            else:
                logging.debug(f"No significant rank data change for {account_name}.")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error for {account_name}: {e}")
        except requests.exceptions.Timeout as e:
            logging.error(f"Timeout error for {account_name}: {e}")
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error for {account_name}: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"RequestException for {account_name}: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred fetching rank for {account_name}: {e}")

    def fetch_and_update_all_accounts(self, on_update_callback=None):
        logging.debug("Fetching and updating all accounts.")
        ui_settings = self.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True):
            accounts = list(self.get_saved_accounts().keys())
            # Use ThreadPoolExecutor for concurrent requests with a limited number of workers
            with ThreadPoolExecutor(max_workers=5) as executor:
                for account_name in accounts:
                    executor.submit(self.fetch_and_update_rank_data, account_name, False, on_update_callback)

    def _run_rank_update_loop(self, on_update_callback=None):
        while True:
            ui_settings = self.get_ima_config().get("ui_settings", {})
            if ui_settings.get("auto_rank_update", True):
                accounts = list(self.get_saved_accounts().keys())
                with ThreadPoolExecutor(max_workers=5) as executor:
                    for account_name in accounts:
                        executor.submit(self.fetch_and_update_rank_data, account_name, False, on_update_callback)
            time.sleep(3600) # Wait an hour before the next cycle

    def start_rank_update_scheduler(self, on_update_callback=None):
        scheduler_thread = threading.Thread(target=self._run_rank_update_loop, args=(on_update_callback,), daemon=True)
        scheduler_thread.start()