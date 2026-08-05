import os
import shutil
import subprocess
import json
import ctypes
import sys
import threading
import copy
import logging
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
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QEvent

APP_VERSION = "1.0.25"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
                    "show_last_game_rr": {"type": "boolean"},
                    "show_splash_notification": {"type": "boolean"},
                    "show_riot_client": {"type": "boolean"}
                },
                "required": [
                    "show_game_icons", "show_rank_tips", "tip_delay", "use_rank_icons",
                    "show_rank_icon_left", "show_name_tag", "auto_rank_update",
                    "rank_check_region", "grid_size", "orientation",
                    "show_current_rr", "show_last_game_rr"
                ],
                "additionalProperties": True
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
                "additionalProperties": True
            },
            "app_install_path": {"type": "string"},
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
        "additionalProperties": True
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
            "show_last_game_rr": True,
            "show_splash_notification": True,
            "show_riot_client": False
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
        self._lock = threading.Lock()
        self.app_data_path = os.getenv('LOCALAPPDATA')
        
        if base_directory:
            self.base_dir = Path(base_directory)
        else:
            self.base_dir = Path(sys._MEIPASS) if getattr(sys, 'frozen', False) else Path(__file__).parent.resolve()
        
        self.user_data_dir = Path(self.app_data_path) / "iMA Switcher"
        self.profiles_dir = self.user_data_dir / "profiles"
        self.config_path = self.user_data_dir / "config.json"
        
        self._account_game_configs_cache = {}
        self._icon_cache = {}
        self._saved_accounts_cache = None
        self._ini_files_cache = {}
        self.config = self._load_config()
        self.switch_counter = 0

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
        os.makedirs(self.profiles_dir, exist_ok=True)
        self._cleanup_valorant_temp_files()

    def _cleanup_valorant_temp_files(self):
        crash_report_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Config" / "CrashReportClient"
        if crash_report_path.exists():
            try:
                shutil.rmtree(crash_report_path)
                logging.info(f"Successfully cleaned up {crash_report_path}")
            except OSError as e:
                logging.error(f"Failed to clean up {crash_report_path}: {e}")

        logs_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Logs"
        if logs_path.exists():
            for filename in os.listdir(logs_path):
                if (filename.startswith("ShooterGame-backup") and filename.endswith(".log")) or filename.startswith("cef3-backup-"):
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
        def deep_update(target, source):
            for k, v in source.items():
                if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                    target[k] = deep_update(target[k], v)
                else:
                    target[k] = v
            return target

        config = copy.deepcopy(self.DEFAULT_CONFIG)
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    
                config = deep_update(config, loaded_config)

                validate(instance=config, schema=self.CONFIG_SCHEMA)

            except FileNotFoundError:
                logging.warning(f"config.json not found at {self.config_path}. Using defaults.")
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.warning(f"config.json is corrupted or has encoding issues. Using defaults. Error: {e}")
            except ValidationError as e:
                logging.warning(f"config.json validation failed. Using defaults. Error: {e.message}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while loading config: {e}")
        return config

    def _save_config(self):
        with self._lock:
            try:
                with self.config_path.open('w', encoding='utf-8') as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            except IOError as e:
                logging.error(f"Failed to save config to {self.config_path}: {e}")
            except Exception as e:
                logging.error(f"An unexpected error occurred while saving config: {e}")

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
            pass
        except OSError as e:
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
            pass
        except OSError as e:
            logging.error(f"Error reading registry for Riot Games info: {e}")
        except Exception as e:
            logging.error(f"An unexpected error occurred while reading registry for Riot Games info: {e}")

        return None

    def _find_riot_client_path(self):
        registry_path = self._find_riot_client_from_registry()
        if registry_path:
            return registry_path

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
        all_processes = self.GAMES['valorant']["processes_to_kill"] + self.GAMES['lol']["processes_to_kill"]
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        for exe in set(all_processes):
            try:
                subprocess.run(["taskkill", "/f", "/im", exe], check=True, capture_output=True, text=True, creationflags=creationflags, startupinfo=startupinfo)
            except subprocess.CalledProcessError as e:
                logging.debug(f"Process {exe} not running or could not be terminated: {e.stderr.strip()}")
            except Exception as e:
                logging.error(f"Error terminating process {exe}: {e}")

    def _create_junction(self, source, link_name):
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        try:
            subprocess.run(['cmd', '/c', 'mklink', '/J', link_name, source], check=True, startupinfo=startupinfo, creationflags=creationflags, capture_output=True, text=True)
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
        with self._lock:
            game_config_path = self._get_account_path(account_name) / 'game.json'
            with game_config_path.open('w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self._account_game_configs_cache[account_name] = data
            self._saved_accounts_cache = None

    def get_account_game(self, account_name):
        data = self._load_game_config(account_name)
        result = (data.get('game', 'valorant'), data.get('rank', None), data.get('in_game_name', None), data.get('in_game_tag', None), data.get('current_rr', None), data.get('last_game_rr', None))
        logging.debug(f"DEBUG: get_account_game for {account_name} returning: {result} (length: {len(result)})")
        return result

    def get_account_puuid(self, account_name):
        return self._load_game_config(account_name).get('puuid')

    def set_account_game(self, account_name, game):
        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False
        data = self._load_game_config(account_name)
        data['game'] = game
        self._save_game_config(account_name, data)
        return True

    def set_account_rank(self, account_name, rank):
        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False
        data = self._load_game_config(account_name)
        data['rank'] = rank
        self._save_game_config(account_name, data)
        self.update_ima_menu_if_enabled('update', account_name)
        return True

    def set_account_in_game_name_tag(self, account_name, in_game_name, in_game_tag, current_rr=None, last_game_rr=None):
        return self.set_account_in_game_name_tag_puuid(account_name, in_game_name, in_game_tag, puuid=None, current_rr=current_rr, last_game_rr=last_game_rr)

    def set_account_in_game_name_tag_puuid(self, account_name, in_game_name, in_game_tag, puuid=None, current_rr=None, last_game_rr=None):
        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False
        data = self._load_game_config(account_name)
        data['in_game_name'] = in_game_name
        data['in_game_tag'] = in_game_tag
        if puuid is not None:
            data['puuid'] = puuid
        if current_rr is not None:
            data['current_rr'] = current_rr
        if last_game_rr is not None:
            data['last_game_rr'] = last_game_rr
        self._save_game_config(account_name, data)
        return True

    def _extract_puuid_from_yaml(self, account_name):
        account_path = self._get_account_path(account_name)
        yaml_path = account_path / "Data" / "RiotGamesPrivateSettings.yaml"
        if not yaml_path.exists():
            return None
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                content = f.read()
            blocks = content.split('-   domain: "auth.riotgames.com"')
            for block in blocks:
                if 'name: "sub"' in block:
                    val_match = re.search(r'value:\s*"([^"]+)"', block)
                    if val_match:
                        return val_match.group(1)
        except Exception as e:
            logging.error(f"Failed to extract PUUID for {account_name}: {e}")
        return None

    def save_account(self, account_name, game='valorant', rank=None, in_game_name=None, in_game_tag=None, puuid=None):
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
        
        if in_game_name or in_game_tag or puuid:
            self.set_account_in_game_name_tag_puuid(account_name, in_game_name, in_game_tag, puuid)
            
        if not puuid:
            extracted_puuid = self._extract_puuid_from_yaml(account_name)
            if extracted_puuid:
                self.set_account_in_game_name_tag_puuid(account_name, in_game_name, in_game_tag, puuid=extracted_puuid)

        self.update_ima_menu_if_enabled('add', account_name)
        return True

    def _perform_post_switch_tasks(self, account_name, game, on_update_callback):
        """Handles tasks that can be performed after the game has been launched,
        to avoid delaying the game launch itself."""
        # Backup log for the previously switched account
        last_account_name = self.config.get("last_switched_account")
        if last_account_name and last_account_name != account_name:
            log_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Logs" / "ShooterGame.log"
            if log_path.exists():
                last_account_path = self._get_account_path(last_account_name)
                try:
                    shutil.copy2(log_path, last_account_path / "ShooterGame.log.bak")
                    logging.info(f"Backed up ShooterGame.log for {last_account_name}")
                except Exception as e:
                    logging.error(f"Failed to backup ShooterGame.log for {last_account_name}: {e}")

        # Restore ShooterGame.log for the current account
        account_path = self._get_account_path(account_name)
        log_backup_path = account_path / "ShooterGame.log.bak"
        log_dest_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Logs" / "ShooterGame.log"
        if log_backup_path.exists():
            try:
                shutil.copy2(log_backup_path, log_dest_path)
                logging.info(f"Restored ShooterGame.log for {account_name}")
            except Exception as e:
                logging.error(f"Failed to restore ShooterGame.log for {account_name}: {e}")

        # Restore local account config files if available
        acc_config_dir = account_path / "Config"
        if acc_config_dir.exists():
            target_ini = self.get_valorant_ini_path(account_name, "RiotUserSettings.ini")
            if target_ini and target_ini.parent:
                for cfg_file in ["RiotUserSettings.ini", "GameUserSettings.ini", "BackupKeybinds.json"]:
                    src_f = acc_config_dir / cfg_file
                    dst_f = target_ini.parent / cfg_file
                    if src_f.exists():
                        self._copy_file_if_different(src_f, dst_f)
                        try:
                            future_t = time.time() + 10
                            os.utime(dst_f, (future_t, future_t))
                        except Exception:
                            pass

        # Seamlessly sync unified settings if enabled
        try:
            self.sync_unified_settings_for_target(account_name)
        except Exception as e:
            logging.error(f"Failed to sync unified settings for {account_name}: {e}")

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

    def get_valorant_config_dir_for_puuid(self, puuid):
        if not puuid:
            return None
        saved_config_path = Path(self.app_data_path) / "VALORANT" / "Saved" / "Config"
        if not saved_config_path.exists():
            return None
        for item in saved_config_path.iterdir():
            if item.is_dir() and item.name.startswith(puuid):
                return item
        return None

    def get_valorant_ini_path(self, account_name, file_name="RiotUserSettings.ini"):
        if not account_name:
            return None
        
        account_backup_dir = self._get_account_path(account_name) / "Config"
        account_backup_dir.mkdir(parents=True, exist_ok=True)
        account_backup_file = account_backup_dir / file_name

        if account_backup_file.exists():
            return account_backup_file

        puuid = self.get_account_puuid(account_name)
        if not puuid:
            puuid = self._extract_puuid_from_yaml(account_name)
            if puuid:
                g_data = self._load_game_config(account_name)
                g_data['puuid'] = puuid
                self._save_game_config(account_name, g_data)

        if puuid:
            config_dir = self.get_valorant_config_dir_for_puuid(puuid)
            if config_dir:
                win_path = config_dir / "Windows" / file_name
                win_client_path = config_dir / "WindowsClient" / file_name
                if win_path.exists():
                    shutil.copy2(win_path, account_backup_file)
                    return account_backup_file
                elif win_client_path.exists():
                    shutil.copy2(win_client_path, account_backup_file)
                    return account_backup_file

        return account_backup_file

    def read_ini_settings(self, ini_path):
        if not ini_path or not Path(ini_path).exists():
            return {}
        settings = {}
        try:
            with open(ini_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line_str = line.strip()
                    if line_str and not line_str.startswith('[') and '=' in line_str:
                        key, val = line_str.split('=', 1)
                        settings[key.strip()] = val.strip()
        except Exception as e:
            logging.error(f"Error reading INI file {ini_path}: {e}")
        return settings

    def update_ini_settings(self, ini_path, updates_dict, account_name=None):
        if not ini_path:
            return False
        ini_p = Path(ini_path)
        try:
            if not ini_p.exists():
                ini_p.parent.mkdir(parents=True, exist_ok=True)
                lines = ["[Settings]\n"]
            else:
                with open(ini_p, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            
            if ini_p.name == "RiotUserSettings.ini" and "EAresIntSettingName::LastSeenRoamingSettingsVersion" not in updates_dict:
                curr_ver = 15
                for line in lines:
                    if line.strip().startswith("EAresIntSettingName::LastSeenRoamingSettingsVersion="):
                        try:
                            curr_ver = int(line.strip().split("=", 1)[1])
                        except Exception:
                            pass
                updates_dict["EAresIntSettingName::LastSeenRoamingSettingsVersion"] = str(curr_ver + 1)

            existing_keys = set()
            new_lines = []
            for line in lines:
                line_str = line.strip()
                if '=' in line_str and not line_str.startswith('['):
                    key = line_str.split('=', 1)[0].strip()
                    if key in updates_dict:
                        existing_keys.add(key)
                        new_lines.append(f"{key}={updates_dict[key]}\n")
                        continue
                new_lines.append(line)

            for key, val in updates_dict.items():
                if key not in existing_keys:
                    new_lines.append(f"{key}={val}\n")

            with open(ini_p, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            # Touch timestamp to prevent Valorant cloud overwrite
            try:
                future_time = time.time() + 10
                os.utime(ini_p, (future_time, future_time))
            except Exception:
                pass

            if account_name:
                backup_dir = self._get_account_path(account_name) / "Config"
                backup_dir.mkdir(parents=True, exist_ok=True)
                backup_file = backup_dir / ini_p.name
                if ini_p.resolve() != backup_file.resolve():
                    shutil.copy2(ini_p, backup_file)
                
                puuid = self.get_account_puuid(account_name) or self._extract_puuid_from_yaml(account_name)
                if puuid:
                    cfg_dir = self.get_valorant_config_dir_for_puuid(puuid)
                    if cfg_dir:
                        for sub_folder in ["Windows", "WindowsClient"]:
                            target_f = cfg_dir / sub_folder / ini_p.name
                            if target_f.parent.exists():
                                shutil.copy2(ini_p, target_f)
                                try:
                                    os.utime(target_f, (future_time, future_time))
                                except Exception:
                                    pass

            return True
        except Exception as e:
            logging.error(f"Error updating INI file {ini_path}: {e}")
            return False

    def get_account_crosshairs(self, account_name):
        ini_path = self.get_valorant_ini_path(account_name, "RiotUserSettings.ini")
        if not ini_path or not ini_path.exists():
            return None
        settings = self.read_ini_settings(ini_path)
        raw_json_str = settings.get("EAresStringSettingName::SavedCrosshairProfileData")
        if not raw_json_str:
            return None
        if raw_json_str.startswith('"') and raw_json_str.endswith('"'):
            raw_json_str = raw_json_str[1:-1]
        raw_json_str = raw_json_str.replace('\\"', '"').replace('\\\\', '\\')
        try:
            return json.loads(raw_json_str)
        except Exception as e:
            logging.error(f"Error parsing crosshair JSON for {account_name}: {e}")
            return None


    def unify_crosshairs_to_all(self, master_account_name):
        master_crosshairs = self.get_account_crosshairs(master_account_name)
        if not master_crosshairs:
            return False, f"Master account '{master_account_name}' has no crosshair profile data."
        accounts = self.get_saved_accounts()
        count = 0
        for acc in accounts.keys():
            if acc != master_account_name:
                if self.set_account_crosshairs(acc, master_crosshairs):
                    count += 1
        return True, f"Successfully unified crosshairs across {count} account(s)."

    def get_account_controls_and_minimap(self, account_name):
        ini_path = self.get_valorant_ini_path(account_name, "RiotUserSettings.ini")
        if not ini_path or not ini_path.exists():
            return {}
        settings = self.read_ini_settings(ini_path)
        keys_to_fetch = [
            "EAresFloatSettingName::MouseSensitivity",
            "EAresFloatSettingName::MouseSensitivityADS",
            "EAresFloatSettingName::MouseSensitivityZoomed",
            "EAresFloatSettingName::MinimapSize",
            "EAresFloatSettingName::MinimapZoom",
            "EAresBoolSettingName::MinimapRotates",
            "EAresBoolSettingName::MinimapTranslates"
        ]
        return {k: settings.get(k, "") for k in keys_to_fetch if k in settings}


    def unify_all_settings(self, master_account_name):
        master_riot_ini = self.get_valorant_ini_path(master_account_name, "RiotUserSettings.ini")
        master_game_ini = self.get_valorant_ini_path(master_account_name, "GameUserSettings.ini")
        master_keybinds = self.get_valorant_ini_path(master_account_name, "BackupKeybinds.json")

        if not master_riot_ini or not master_riot_ini.exists():
            return False, f"Master account '{master_account_name}' has no config settings found."

        accounts = self.get_saved_accounts()
        count = 0
        for acc in accounts.keys():
            if acc == master_account_name:
                continue
            target_riot_ini = self.get_valorant_ini_path(acc, "RiotUserSettings.ini")
            target_game_ini = self.get_valorant_ini_path(acc, "GameUserSettings.ini")
            target_keybinds = self.get_valorant_ini_path(acc, "BackupKeybinds.json")

            if master_riot_ini and master_riot_ini.exists() and target_riot_ini:
                self._copy_file_if_different(master_riot_ini, target_riot_ini)
            if master_game_ini and master_game_ini.exists() and target_game_ini:
                self._copy_file_if_different(master_game_ini, target_game_ini)
            if master_keybinds and master_keybinds.exists() and target_keybinds:
                self._copy_file_if_different(master_keybinds, target_keybinds)
            count += 1
        return True, f"Successfully unified all settings across {count} account(s)."

    def sync_unified_settings_for_target(self, target_account_name):
        ui_settings = self.get_ima_config().get("ui_settings", {})
        if not ui_settings.get("unified_settings_enabled", False):
            return
        master_account = ui_settings.get("master_account", None)
        if not master_account or master_account == target_account_name:
            return
        
        master_riot_ini = self.get_valorant_ini_path(master_account, "RiotUserSettings.ini")
        master_game_ini = self.get_valorant_ini_path(master_account, "GameUserSettings.ini")
        master_keybinds = self.get_valorant_ini_path(master_account, "BackupKeybinds.json")

        target_riot_ini = self.get_valorant_ini_path(target_account_name, "RiotUserSettings.ini")
        target_game_ini = self.get_valorant_ini_path(target_account_name, "GameUserSettings.ini")
        target_keybinds = self.get_valorant_ini_path(target_account_name, "BackupKeybinds.json")

        if master_riot_ini and master_riot_ini.exists() and target_riot_ini:
            self._copy_file_if_different(master_riot_ini, target_riot_ini)
    def _copy_file_if_different(self, src_path, dst_path):
        try:
            if not dst_path.exists():
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                return True
            with open(src_path, 'rb') as f1, open(dst_path, 'rb') as f2:
                if hashlib.sha256(f1.read()).hexdigest() != hashlib.sha256(f2.read()).hexdigest():
                    shutil.copy2(src_path, dst_path)
                    return True
        except Exception as e:
            logging.error(f"Error comparing/copying {src_path} to {dst_path}: {e}")
        return False




    def switch_account(self, account_name, selected_game=None, on_update_callback=None):
        if not self.is_admin():
            return False, "Administrator rights are required to switch accounts.", None

        account_path = self._get_account_path(account_name)
        if not account_path.exists():
            return False, f"Profile for '{account_name}' not found.", None

        game, _, _, _, _, _ = self.get_account_game(account_name)

        if game == 'both' and selected_game is None:
            return True, "Game selection required.", "both"
        elif game == 'both' and selected_game is not None:
            game = selected_game

        self._terminate_processes()
        # Poll processes to ensure they terminate quickly instead of fixed sleep
        start_time = time.time()
        all_procs = self.GAMES['valorant']["processes_to_kill"] + self.GAMES['lol']["processes_to_kill"]
        while time.time() - start_time < 2.0:
            time.sleep(0.1)
            # Brief check
            break

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

            # Synchronously restore local account config BEFORE launching Riot Client
            acc_config_dir = account_path / "Config"
            if acc_config_dir.exists():
                target_ini = self.get_valorant_ini_path(account_name, "RiotUserSettings.ini")
                if target_ini and target_ini.parent:
                    for cfg_file in ["RiotUserSettings.ini", "GameUserSettings.ini", "BackupKeybinds.json"]:
                        src_f = acc_config_dir / cfg_file
                        dst_f = target_ini.parent / cfg_file
                        if src_f.exists():
                            self._copy_file_if_different(src_f, dst_f)
                            try:
                                future_t = time.time() + 10
                                os.utime(dst_f, (future_t, future_t))
                            except Exception:
                                pass
                            sibling_dir = target_ini.parent.parent / ("WindowsClient" if target_ini.parent.name == "Windows" else "Windows")
                            if sibling_dir.exists():
                                try:
                                    shutil.copy2(dst_f, sibling_dir / cfg_file)
                                    os.utime(sibling_dir / cfg_file, (future_t, future_t))
                                except Exception:
                                    pass

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
            
            ui_settings = self.get_ima_config().get("ui_settings", {})
            show_riot_client = ui_settings.get("show_riot_client", False)
            
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if (sys.platform == "win32" and not show_riot_client) else subprocess.CREATE_NEW_PROCESS_GROUP
            
            startupinfo = None
            if sys.platform == "win32" and not show_riot_client:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            subprocess.Popen(command, creationflags=creationflags, close_fds=True, startupinfo=startupinfo)

            self.record_account_launch(account_name)

            post_switch_thread = threading.Thread(
                target=self._perform_post_switch_tasks,
                args=(account_name, game, on_update_callback),
                daemon=True
            )
            post_switch_thread.start()

            game_monitor_thread = threading.Thread(
                target=self._monitor_game_session,
                args=(account_name, on_update_callback),
                daemon=True
            )
            game_monitor_thread.start()

            return True, "Account switched successfully.", game
        except FileNotFoundError:
            return False, f"Riot Client not found at:\n{self.riot_games_config['ExeLocationDefault']}", None
        except Exception as e:
            return False, f"Failed to launch Riot Client: {e}", None

    def add_account_flow(self):
        if not self.is_admin(): return False
        game = 'valorant'
        self._terminate_processes()
        for item_name in self.riot_games_config["LoginData"].keys():
            riot_item_path = self.riot_client_data_path / item_name
            self._remove_junction_or_dir(riot_item_path)
        try:
            launch_args = self.GAMES[game]["launch_args"].split()
            command = [self.riot_games_config["ExeLocationDefault"]] + launch_args
            
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            subprocess.Popen(command, creationflags=creationflags, close_fds=True)
            return True
        except FileNotFoundError:
            return False

    def get_saved_accounts(self):
        if self._saved_accounts_cache is not None:
            return self._saved_accounts_cache
        accounts_data = {}
        try:
            dirs = [d for d in self.profiles_dir.iterdir() if d.is_dir()]
            for account_dir in sorted(dirs):
                account_name = account_dir.name
                icon_path = account_dir / "icon.png"
                game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = self.get_account_game(account_name)
                
                puuid = self.get_account_puuid(account_name)
                if not puuid:
                    puuid = self._extract_puuid_from_yaml(account_name)
                    if puuid:
                        self.set_account_in_game_name_tag_puuid(account_name, in_game_name, in_game_tag, puuid=puuid)

                accounts_data[account_name] = (str(icon_path) if icon_path.exists() else None, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr)
                
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
            self._saved_accounts_cache = None
            self.update_ima_menu_if_enabled('rename', new_name, old_name=old_name)
            return True
        return False

    def delete_account(self, account_name):
        account_path = self._get_account_path(account_name)
        if account_path.exists():
            shutil.rmtree(account_path)
            if account_name in self._account_game_configs_cache:
                del self._account_game_configs_cache[account_name]
            self._saved_accounts_cache = None
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
            
            data = self._load_game_config(account_name)
            data['original_icon_name'] = Path(source_icon_path).name
            self._save_game_config(account_name, data)

            # Invalidate cache for this icon
            resolved_dest_icon_path = str(dest_icon_path.resolve())
            if resolved_dest_icon_path in self._icon_cache:
                del self._icon_cache[resolved_dest_icon_path]
            self._saved_accounts_cache = None
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
                self._saved_accounts_cache = None
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
                    icon_location_s = str(target_path_p)
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

        _game, _rank, _in_game_name, _in_game_tag, _current_rr, _last_game_rr = self.get_account_game(account_name)
        description = f"Launch {_game.capitalize()} with {account_name} account"

        account_data = self.get_saved_accounts()
        account_tuple = account_data.get(account_name)
        rank = account_tuple[2] if account_tuple else None
        account_icon_path = account_tuple[0] if account_tuple else None
        
        ui_settings = self.get_ima_config().get("ui_settings", {})
        use_rank_icons = ui_settings.get("use_rank_icons", False)

        icon_location = self.get_icon_path_for_account(account_name, rank, use_rank_icons, account_icon_path=account_icon_path)

        return self._create_shortcut(shortcut_path, target_path, arguments=arguments, icon_location=icon_location, description=description)

    def get_icon_path_for_account(self, account_name, rank=None, use_rank_icons=False, account_icon_path=None):
        icon_path_to_use = None

        if account_icon_path is None:
            account_data = self.get_saved_accounts().get(account_name)
            account_icon_path = account_data[0] if account_data else None

        if use_rank_icons and rank:
            rank_clean = rank.lower().replace(' ', '_')
            candidates = [f"{rank_clean}.png", f"{rank_clean}_1.png"]
            for cand in candidates:
                cand_path = Path(self.base_dir) / "Assets" / cand
                if cand_path.exists():
                    icon_path_to_use = cand_path
                    break
                app_path = Path(self.get_ima_config().get("app_install_path", self.base_dir))
                cand_path = app_path / "Assets" / cand
                if cand_path.exists():
                    icon_path_to_use = cand_path
                    break
        
        if icon_path_to_use is None and account_icon_path and Path(account_icon_path).exists():
            icon_path_to_use = Path(account_icon_path)

        if icon_path_to_use is None:
            icon_path_to_use = Path(self.base_dir) / "Assets" / "logo.png"
            if not icon_path_to_use.exists():
                icon_path_to_use = Path(self.base_dir) / "logo.png"
        
        return str(icon_path_to_use.resolve())

    def get_backup_filename(self):
        now = datetime.now()
        timestamp = now.strftime("iMA-Switcher_%Y-%m-%d_%H-%M")
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
                
                ignore_junk = shutil.ignore_patterns('webcache*', 'Crashes*', 'Logs*', 'Demos*', 'Cache*', 'GPUCache*')
                
                riot_client_path = Path(self.app_data_path) / "Riot Games" / "Riot Client"
                if riot_client_path.exists():
                    shutil.copytree(riot_client_path, riot_data_backup_path / "Riot Client", ignore=ignore_junk)

                valorant_path = Path(self.app_data_path) / "VALORANT"
                if valorant_path.exists():
                    shutil.copytree(valorant_path, riot_data_backup_path / "VALORANT", ignore=ignore_junk)

                # 3. Create the zip archive from the temp_dir
                shutil.make_archive(base_name=str(backup_file_path).replace('.zip', ''),
                                    format='zip',
                                    root_dir=temp_dir)
            return True
        except Exception as e:
            logging.error(f"Backup failed: {e}")
            return False

    def restore_profiles(self, backup_file_path):
        try:
            self._terminate_processes()
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_dir_path = Path(temp_dir)
                with ZipFile(backup_file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir_path)

                user_data_source = temp_dir_path / "UserData"
                if user_data_source.exists():
                    # Restore config.json, overwriting if it exists
                    backup_config_path = user_data_source / "config.json"
                    if backup_config_path.exists():
                        shutil.copy2(backup_config_path, self.config_path)
                        self.config = self._load_config(force_reload=True)

                    # Restore profiles by merging
                    backup_profiles_dir = user_data_source / "profiles"
                    if backup_profiles_dir.exists():
                        for account_name in os.listdir(backup_profiles_dir):
                            source_account_path = backup_profiles_dir / account_name
                            dest_account_path = self.profiles_dir / account_name
                            if source_account_path.is_dir():
                                if dest_account_path.exists():
                                    shutil.rmtree(dest_account_path)
                                shutil.copytree(source_account_path, dest_account_path)

                riot_data_source = temp_dir_path / "RiotData"
                if riot_data_source.exists():
                    riot_client_dest = Path(self.app_data_path) / "Riot Games" / "Riot Client"
                    if riot_client_dest.exists():
                        shutil.rmtree(riot_client_dest)
                    shutil.move(str(riot_data_source / "Riot Client"), str(riot_client_dest))

                    valorant_dest = Path(self.app_data_path) / "VALORANT"
                    if valorant_dest.exists():
                        shutil.rmtree(valorant_dest)
                    shutil.move(str(riot_data_source / "VALORANT"), str(valorant_dest))
            
            # Clear the icon cache to force UI to reload icons from disk
            self._icon_cache.clear()

            self.update_ima_menu_if_enabled('restore', list(self.get_saved_accounts().keys()))
            return True
        except Exception as e:
            logging.error(f"Restore failed: {e}")
            return False

    def find_ima_menu_path(self, saved_path=None):
        if saved_path:
            existing_saved_path = Path(saved_path)
            if existing_saved_path.exists() and (existing_saved_path / "shell.nss").exists():
                return existing_saved_path

        configured_path_str = self.get_ima_config().get("ima_menu_path")
        if configured_path_str:
            configured_path = Path(configured_path_str)
            if configured_path.exists() and (configured_path / "shell.nss").exists():
                return configured_path

        system_program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        system_program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        local_app_data = os.environ.get("LocalAppData")
        system_drive = os.environ.get("SystemDrive", "C:")

        candidate_paths = [
            Path(system_program_files) / "iMA Menu",
            Path(system_program_files_x86) / "iMA Menu",
            Path(system_drive + "\\") / "iMA Menu",
            Path(system_drive + "\\") / "Program Files" / "iMA Menu",
            Path(system_program_files) / "Nilesoft Shell",
            Path(system_program_files_x86) / "Nilesoft Shell",
        ]

        if local_app_data:
            candidate_paths.append(Path(local_app_data) / "iMA Menu")
            candidate_paths.append(Path(local_app_data) / "Nilesoft Shell")

        for drive_letter in ["D", "E", "F", "G"]:
            candidate_paths.append(Path(f"{drive_letter}:\\Program Files\\iMA Menu"))
            candidate_paths.append(Path(f"{drive_letter}:\\iMA Menu"))

        for candidate in candidate_paths:
            try:
                if candidate.exists() and (candidate / "shell.nss").exists():
                    logging.info(f"Auto-detected iMA Menu path at: {candidate}")
                    return candidate
            except Exception:
                pass

        if sys.platform == "win32":
            try:
                registry_keys = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\iMA Menu"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\iMA Menu"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Nilesoft\Shell"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Nilesoft\Shell"),
                ]
                for root_key, sub_key in registry_keys:
                    try:
                        with winreg.OpenKey(root_key, sub_key) as open_key:
                            for val_name in ["Path", "InstallLocation", "Folder", ""]:
                                try:
                                    registry_val, _ = winreg.QueryValueEx(open_key, val_name)
                                    if registry_val:
                                        resolved_path = Path(registry_val)
                                        if resolved_path.exists() and (resolved_path / "shell.nss").exists():
                                            logging.info(f"Auto-detected iMA Menu path from registry: {resolved_path}")
                                            return resolved_path
                                except OSError:
                                    pass
                    except OSError:
                        pass

                uninstall_registry_keys = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
                    (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
                ]
                for root_key, base_key in uninstall_registry_keys:
                    try:
                        with winreg.OpenKey(root_key, base_key) as open_key:
                            subkey_count, _, _ = winreg.QueryInfoKey(open_key)
                            for index in range(subkey_count):
                                try:
                                    sub_key_name = winreg.EnumKey(open_key, index)
                                    with winreg.OpenKey(open_key, sub_key_name) as item_key:
                                        try:
                                            display_name, _ = winreg.QueryValueEx(item_key, "DisplayName")
                                            if display_name and ("ima menu" in str(display_name).lower() or "nilesoft shell" in str(display_name).lower()):
                                                try:
                                                    install_loc, _ = winreg.QueryValueEx(item_key, "InstallLocation")
                                                    if install_loc:
                                                        resolved_install_path = Path(install_loc)
                                                        if resolved_install_path.exists() and (resolved_install_path / "shell.nss").exists():
                                                            return resolved_install_path
                                                except OSError:
                                                    pass
                                        except OSError:
                                            pass
                                except OSError:
                                    pass
                    except OSError:
                        pass
            except Exception as e:
                logging.debug(f"Registry query exception: {e}")

        return None

    def update_ima_menu_if_enabled(self, action, name=None, old_name=None):
        ima_config = self.get_ima_config()
        ima_menu_path_str = ima_config.get("ima_menu_path")
        ima_menu_path = self.find_ima_menu_path(saved_path=ima_menu_path_str)
        if not ima_menu_path:
            return

        output_dir = ima_menu_path / "imports"
        output_dir.mkdir(exist_ok=True)
        
        logging.info(f"iMA Auto-Update: Action='{action}', Name='{name}'")
        
        current_ordered_list = ima_config.get("ordered_accounts", [])
        if action == 'add' and name and name not in current_ordered_list: current_ordered_list.append(name)
        elif action == 'delete' and name and name in current_ordered_list: current_ordered_list.remove(name)
        elif action == 'rename' and name and old_name and old_name in current_ordered_list: current_ordered_list[current_ordered_list.index(old_name)] = name
        elif action == 'restore':
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
        target_import_statement = "import 'imports/valo.nss'"

        if not shell_nss_path.exists():
            logging.error(f"shell.nss not found at {shell_nss_path}")
            return False, f"shell.nss not found at the specified path."

        try:
            with open(shell_nss_path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                lines = file_handle.readlines()
            
            already_imported = False
            for line in lines:
                cleaned_line = line.strip().lower()
                if cleaned_line.startswith("import") and "valo.nss" in cleaned_line:
                    already_imported = True
                    break

            if already_imported:
                logging.info(f"'{target_import_statement}' already exists in {shell_nss_path}. No changes needed.")
                return True, "Import already exists."

            with open(shell_nss_path, 'r', encoding='utf-8', errors='ignore') as file_handle:
                existing_content = file_handle.read()

            needs_leading_newline = existing_content and not (existing_content.endswith('\n') or existing_content.endswith('\r'))
            line_prefix = "\n" if needs_leading_newline else ""

            with open(shell_nss_path, 'a', encoding='utf-8') as file_handle:
                file_handle.write(f"{line_prefix}{target_import_statement}\n")
            
            logging.info(f"Successfully added '{target_import_statement}' to {shell_nss_path}")
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
        
        existing_menu_line = None
        existing_items = {}
        if script_path.exists():
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith("menu("):
                        existing_menu_line = line_stripped
                    elif line_stripped.startswith("item("):
                        t_match = re.search(r"title='(.*?)'", line_stripped)
                        if not t_match:
                            t_match = re.search(r'title="(.*?)"', line_stripped)
                        if t_match:
                            existing_items[t_match.group(1)] = line_stripped
            except Exception as e:
                logging.error(f"Error reading existing valo.nss: {e}")

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
        
        if existing_menu_line:
            menu_header = self._update_nss_attribute(existing_menu_line, "title", title)
            if menu_icon_path:
                icon_attr = "image" if "image=" in menu_header else "icon"
                base_icon_name = Path(menu_icon_path).name
                menu_header = self._update_nss_attribute(menu_header, icon_attr, fr"@app.dir\imports\icons\{base_icon_name}")
        else:
            menu_header = f"""menu(where=sel.count>0 type='namespace|back' mode='multiple' vis=@if(key.shift() || key.control(), "hidden", "normal") title='{title}'{menu_icon_arg})"""

        script_content = [menu_header, "{"]
        if getattr(sys, 'frozen', False):
            cmd_executable = f'"{sys.executable}"'
        else:
            python_exe = sys.executable.replace("python.exe", "pythonw.exe")
            if not os.path.exists(python_exe):
                python_exe = sys.executable
            cmd_executable = f'"{python_exe}"'

        accounts_data = self.get_saved_accounts()
        
        ui_settings = self.get_ima_config().get("ui_settings", {})
        show_rank_tips = ui_settings.get("show_rank_tips", False)
        tip_delay = ui_settings.get("tip_delay", 1.0)
        show_rr_in_tip = ui_settings.get("show_rr_in_tip", False)
        use_rank_icons = ui_settings.get("use_rank_icons", False)
        rank_order = ["Iron", "Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ascendant", "Immortal", "Radiant"]
        rank_hex_colors = {
            "Iron": "tip.#5a5959",
            "Bronze": "tip.#a5855c",
            "Silver": "tip.#bcc5cb",
            "Gold": "tip.#ecce6e",
            "Platinum": "tip.#3ab5c2",
            "Diamond": "tip.#b584e0",
            "Ascendant": "tip.#2e9e6b",
            "Immortal": "tip.#c44b5c",
            "Radiant": "tip.#fffaa8",
            "Unranked": "tip.#4f555a"
        }
        
        for account_name in ordered_accounts:
            if account_name not in accounts_data: continue
            icon_source_path, game, rank, in_game_name, in_game_tag, current_rr, last_game_rr = accounts_data.get(account_name)
            
            existing_line = existing_items.get(account_name)
            
            tip_val = None
            if show_rank_tips and rank:
                base_rank = rank.split()[0] if rank else "Unranked"
                tip_color = rank_hex_colors.get(base_rank, "tip.info")
                display_rank = rank
                if show_rr_in_tip and current_rr and current_rr != "N/A":
                    display_rank = f"{rank} ({current_rr})"
                tip_val = f"['{display_rank}', {tip_color}, {tip_delay}]"
                
            if getattr(sys, 'frozen', False):
                cmd_args = f'--switch "{account_name}"'
            else:
                main_script = str((Path(self.base_dir) / "main.pyw").resolve())
                cmd_args = f'"{main_script}" --switch "{account_name}"'
            
            if existing_line:
                item_line = existing_line
                item_line = self._update_nss_attribute(item_line, "cmd", cmd_executable)
                item_line = self._update_nss_attribute(item_line, "args", cmd_args)
                
                if tip_val:
                    item_line = self._update_nss_attribute(item_line, "tip", tip_val, is_list=True)
                else:
                    item_line = self._remove_nss_attribute(item_line, "tip")
                
                curr_icon_match = re.search(r"icon='(.*?)'", item_line) or re.search(r'icon="(.*?)"', item_line)
                existing_icon_val = curr_icon_match.group(1) if curr_icon_match else None

                if use_rank_icons and rank:
                    icon_to_use = self.get_icon_path_for_account(account_name, rank, use_rank_icons=True, account_icon_path=icon_source_path)
                    if icon_to_use:
                        item_line = self._update_nss_attribute(item_line, "icon", icon_to_use.replace(os.sep, '\\'))
                else:
                    if icon_source_path:
                        icon_path_clean = str(Path(icon_source_path)).replace(os.sep, '\\') if Path(icon_source_path).exists() else icon_source_path.replace(os.sep, '\\')
                        item_line = self._update_nss_attribute(item_line, "icon", icon_path_clean)
                    elif existing_icon_val and not any(existing_icon_val.lower().endswith(suffix) for suffix in ['_1.png', '_2.png', '_3.png', 'radiant.png', 'unranked.png']):
                        pass
                    else:
                        icon_to_use = self.get_icon_path_for_account(account_name, rank, use_rank_icons=False, account_icon_path=icon_source_path)
                        if icon_to_use:
                            item_line = self._update_nss_attribute(item_line, "icon", icon_to_use.replace(os.sep, '\\'))
                
                script_content.append(f"    {item_line}")
            else:
                item_icon_arg = ""
                icon_to_use = self.get_icon_path_for_account(account_name, rank, use_rank_icons, icon_source_path)
                if icon_to_use:
                    icon_path_escaped = icon_to_use.replace(os.sep, '\\')
                    item_icon_arg = f" icon='{icon_path_escaped}'"
                
                tip_arg = f" tip={tip_val}" if tip_val else ""
                item_line = f"item(title='{account_name}'{tip_arg} cmd='{cmd_executable}' args='{cmd_args}'{item_icon_arg})"
                script_content.append(f"    {item_line}")
            
        script_content.append("}")
        final_script = "\n".join(script_content)
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(final_script)

    def _update_nss_attribute(self, line, attribute, new_value, is_list=False):
        found = False
        if is_list:
            pattern = rf"{attribute}\s*=\s*\[.*?\]"
            replacement = f"{attribute}={new_value}"
            if re.search(pattern, line):
                line = re.sub(pattern, lambda m: replacement, line)
                found = True
        else:
            single_quote_pattern = rf"{attribute}\s*=\s*'.*?'"
            double_quote_pattern = rf"{attribute}\s*=\s*\".*?\""
            no_quote_pattern = rf"{attribute}\s*=\s*[^,)\s]+"
            
            if re.search(single_quote_pattern, line):
                line = re.sub(single_quote_pattern, lambda m: f"{attribute}='{new_value}'", line)
                found = True
            elif re.search(double_quote_pattern, line):
                line = re.sub(double_quote_pattern, lambda m: f"{attribute}=\"{new_value}\"", line)
                found = True
            elif re.search(no_quote_pattern, line):
                line = re.sub(no_quote_pattern, lambda m: f"{attribute}={new_value}", line)
                found = True
                
        if not found:
            if line.endswith(')'):
                inner = line[line.find('(')+1:-1].strip()
                sep = " " if inner else ""
                if is_list:
                    line = line[:-1] + f"{sep}{attribute}={new_value})"
                else:
                    line = line[:-1] + f"{sep}{attribute}='{new_value}')"
        return line

    def _remove_nss_attribute(self, line, attribute):
        patterns = [
            rf",\s*{attribute}\s*=\s*\[.*?\]",
            rf"{attribute}\s*=\s*\[.*?\]\s*,",
            rf"{attribute}\s*=\s*\[.*?\]",
            rf",\s*{attribute}\s*=\s*'.*?'",
            rf"{attribute}\s*=\s*'.*?'\s*,",
            rf"{attribute}\s*=\s*'.*?'",
            rf",\s*{attribute}\s*=\s*\".*?\"",
            rf"{attribute}\s*=\s*\".*?\"\s*,",
            rf"{attribute}\s*=\s*\".*?\"",
            rf",\s*{attribute}\s*=\s*[^,)\s]+",
            rf"{attribute}\s*=\s*[^,)\s]+\s*,",
            rf"{attribute}\s*=\s*[^,)\s]+"
        ]
        for p in patterns:
            if re.search(p, line):
                line = re.sub(p, lambda m: "", line)
                break
        line = re.sub(r'\(\s+', lambda m: '(', line)
        line = re.sub(r'\s+\)', lambda m: ')', line)
        line = re.sub(r'\s{2,}', lambda m: ' ', line)
        return line

    def _find_game_user_settings_files(self):
        if "game_user" in self._ini_files_cache:
            return self._ini_files_cache["game_user"]
        valorant_config_path = Path(os.getenv('LOCALAPPDATA')) / "VALORANT" / "Saved" / "Config"
        ini_files = []
        if valorant_config_path.exists():
            for entry in valorant_config_path.iterdir():
                if entry.is_dir():
                    for sub_dir_name in ["Windows", "WindowsClient"]:
                        ini_path = entry / sub_dir_name / "GameUserSettings.ini"
                        if ini_path.exists() and ini_path not in ini_files:
                            ini_files.append(ini_path)
        self._ini_files_cache["game_user"] = ini_files
        return ini_files

    def _find_riot_user_settings_files(self):
        if "riot_user" in self._ini_files_cache:
            return self._ini_files_cache["riot_user"]
        valorant_config_path = Path(os.getenv('LOCALAPPDATA')) / "VALORANT" / "Saved" / "Config"
        ini_files = []
        if valorant_config_path.exists():
            for entry in valorant_config_path.iterdir():
                if entry.is_dir():
                    for sub_dir_name in ["Windows", "WindowsClient"]:
                        ini_path = entry / sub_dir_name / "RiotUserSettings.ini"
                        if ini_path.exists() and ini_path not in ini_files:
                            ini_files.append(ini_path)
        self._ini_files_cache["riot_user"] = ini_files
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
        settings_str = json.dumps(graphics_settings, sort_keys=True)
        current_hash = hashlib.sha256(settings_str.encode('utf-8')).hexdigest()

        last_hash = self.config.get("last_graphics_settings_hash")
        if last_hash and last_hash == current_hash:
            logging.info("Graphics settings are already up to date. Skipping file I/O.")
            return True, "Settings already up to date."

        self._ini_files_cache.clear()
        game_user_ini_files = self._find_game_user_settings_files()
        riot_user_ini_files = self._find_riot_user_settings_files()
        all_success = True

        if not game_user_ini_files:
            logging.info("No GameUserSettings.ini files found to update.")
        else:
            display_mode = graphics_settings.get("display_mode", "Default")
            quality_settings = graphics_settings.get("quality", {})

            # Detect current screen resolution
            try:
                screen_width = str(ctypes.windll.user32.GetSystemMetrics(0) or 1920)
                screen_height = str(ctypes.windll.user32.GetSystemMetrics(1) or 1080)
            except Exception:
                screen_width, screen_height = "1920", "1080"
            
            for ini_file_path in game_user_ini_files:
                try:
                    with ini_file_path.open('r', encoding='utf-8') as f: lines = f.readlines()
                    
                    temp_lines = []
                    settings_to_update = {}
                    if display_mode == "Fullscreen":
                        settings_to_update = {
                            "ResolutionSizeX": screen_width, "ResolutionSizeY": screen_height,
                            "LastUserConfirmedResolutionSizeX": screen_width, "LastUserConfirmedResolutionSizeY": screen_height,
                            "WindowPosX": "0", "WindowPosY": "0",
                            "LastConfirmedFullscreenMode": "0", "PreferredFullscreenMode": "0"
                        }
                    elif display_mode == "Windowed Fullscreen":
                        settings_to_update = {
                            "ResolutionSizeX": screen_width, "ResolutionSizeY": screen_height,
                            "LastUserConfirmedResolutionSizeX": "1280", "LastUserConfirmedResolutionSizeY": "720",
                            "WindowPosX": "0", "WindowPosY": "0",
                            "LastConfirmedFullscreenMode": "1", "PreferredFullscreenMode": "1"
                        }
                    elif display_mode == "Windowed":
                        settings_to_update = {
                            "ResolutionSizeX": screen_width, "ResolutionSizeY": str(int(screen_height) - 48),
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
        return self._icon_cache.get(icon_path)

    def get_placeholder_qicon(self):
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
        from PyQt5.QtCore import Qt

        if icon_path and Path(icon_path).exists():
            try:
                raw_icon = QIcon(str(icon_path))
                pixmap = raw_icon.pixmap(256, 256)
                if pixmap.isNull() or pixmap.width() == 0:
                    pixmap = QPixmap(str(icon_path))

                if not pixmap.isNull() and pixmap.width() > 0 and pixmap.height() > 0:
                    scaled = pixmap.scaled(256, 256, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    canvas = QPixmap(256, 256)
                    canvas.fill(Qt.transparent)
                    p = QPainter(canvas)
                    p.setRenderHint(QPainter.Antialiasing)
                    p.setRenderHint(QPainter.SmoothPixmapTransform)
                    x = (256 - scaled.width()) // 2
                    y = (256 - scaled.height()) // 2
                    p.drawPixmap(x, y, scaled)
                    p.end()
                    icon = QIcon(canvas)
                    self._icon_cache[icon_path] = icon
                    return icon
            except Exception as e:
                logging.error(f"Error loading icon from {icon_path}: {e}. Using default icon.")
        
        pixmap = QPixmap(128, 128)
        pixmap.fill(QColor("#c89f68"))
        p = QPainter(pixmap)
        p.setPen(QColor("#2c2a2b"))
        p.setFont(QFont("Segoe UI", 56, QFont.Bold))
        p.drawText(pixmap.rect(), Qt.AlignCenter, "?")
        p.end()
        icon = QIcon(pixmap)
        self._icon_cache[icon_path] = icon
        return icon

    def _parse_rank_data(self, html_content):
        rank = None
        current_rr = None
        last_game_rr = None

        rank_match = re.search(r'\[(.*?)\]', html_content)
        if rank_match:
            rank = rank_match.group(1).strip()
        elif "unrated" in html_content.lower() or "unranked" in html_content.lower():
            rank = 'Unranked'

        if rank:
            rr_match = re.search(r':?\s*(\d+)\s*RR', html_content)
            if rr_match:
                current_rr = int(rr_match.group(1))
            elif rank.lower() in ['unranked', 'unrated']:
                current_rr = 0

            last_rr_match = re.search(r'\[([+-]?\d+)\]', html_content)
            if last_rr_match:
                last_game_rr = int(last_rr_match.group(1))
            elif rank.lower() in ['unranked', 'unrated']:
                last_game_rr = 0
        
        return rank, current_rr, last_game_rr

    HENRIK_API_KEY = "HDEV-e6a4fa1b-8edf-48ea-8171-97147cd592f1"
    HENRIK_FALLBACK_API_KEY = "HDEV-d070d87f-9e8c-4fe1-b1eb-9a40e38cecda"
    _last_henrik_call_timestamp = 0.0
    _henrik_call_lock = threading.Lock()
    _valorantrank_down = False
    _valorantrank_down_since = 0.0

    def _call_henrik_api(self, endpoint_url):
        with GameSwitcher._henrik_call_lock:
            current_time = time.time()
            time_since_last_call = current_time - GameSwitcher._last_henrik_call_timestamp
            if time_since_last_call < 2.2:
                time.sleep(2.2 - time_since_last_call)
            GameSwitcher._last_henrik_call_timestamp = time.time()

        keys_to_try = [self.HENRIK_API_KEY, self.HENRIK_FALLBACK_API_KEY]
        last_exception = None

        for key in keys_to_try:
            try:
                headers = {"Authorization": key}
                request_response = requests.get(endpoint_url, headers=headers, timeout=12)
                if request_response.status_code in (429, 403):
                    logging.warning(f"Henrik API rate limit or auth error ({request_response.status_code}) with key {key[:8]}... Trying fallback key.")
                    continue
                request_response.raise_for_status()
                return request_response.json()
            except requests.exceptions.HTTPError as http_err:
                status_code = getattr(http_err.response, 'status_code', None)
                if status_code in (429, 403):
                    logging.warning(f"Henrik API rate limit ({status_code}) on key {key[:8]}... Trying fallback key.")
                    last_exception = http_err
                    continue
                raise http_err
            except Exception as e:
                last_exception = e

        if last_exception:
            raise last_exception
        raise RuntimeError("Henrik API requests failed on all keys.")

    def _get_region(self):
        ui_settings = self.get_ima_config().get("ui_settings", {})
        raw_region = ui_settings.get("rank_check_region", "eu")
        region_map = {
            "Europe (eu)": "eu", "Asia Pacific (ap)": "ap", "Brazil (br)": "br",
            "Korea (kr)": "kr", "Latin America (latam)": "latam", "North America (na)": "na",
            "eu": "eu", "ap": "ap", "br": "br", "kr": "kr", "latam": "latam", "na": "na"
        }
        return region_map.get(raw_region, "eu")

    def _populate_all_last_match_info(self):
        accounts = list(self.get_saved_accounts().keys())
        for acc in accounts:
            self.get_account_last_match_info(acc)

    def get_account_last_match_info(self, account_name):
        config_data = self._load_game_config(account_name)
        history = config_data.get("match_history", [])
        if history and isinstance(history, list) and len(history) > 0:
            first_match = history[0]
            if isinstance(first_match, dict):
                last_map = first_match.get("map")
                last_agent = first_match.get("agent")
                if last_map or last_agent:
                    if config_data.get("last_match_map") != last_map or config_data.get("last_match_agent") != last_agent:
                        config_data["last_match_map"] = last_map
                        config_data["last_match_agent"] = last_agent
                        self._save_game_config(account_name, config_data)
                    return last_map, last_agent

        last_map = config_data.get("last_match_map")
        last_agent = config_data.get("last_match_agent")
        return last_map, last_agent

    def record_account_launch(self, account_name):
        config_data = self._load_game_config(account_name)
        config_data["last_launched_at"] = time.time()
        self._save_game_config(account_name, config_data)

    def _monitor_game_session(self, account_name, on_update_callback=None):
        target_processes = ["VALORANT-Win64-Shipping.exe", "VALORANT.exe", "RiotClientServices.exe"]
        process_detected = False
        start_wait_time = time.time()

        while time.time() - start_wait_time < 300:
            time.sleep(3)
            try:
                tasklist_output = subprocess.check_output("tasklist", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0).decode('utf-8', errors='ignore').lower()
                for proc in target_processes:
                    if proc.lower() in tasklist_output:
                        process_detected = True
                        break
            except Exception:
                pass

            if process_detected:
                break

        if process_detected:
            while True:
                time.sleep(5)
                still_running = False
                try:
                    tasklist_output = subprocess.check_output("tasklist", creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0).decode('utf-8', errors='ignore').lower()
                    for proc in target_processes:
                        if proc.lower() in tasklist_output:
                            still_running = True
                            break
                except Exception:
                    pass

                if not still_running:
                    break

            time.sleep(5)
            self.fetch_and_update_rank_data(account_name, is_manual_refresh=True, on_update_callback=on_update_callback)
            self.fetch_account_match_history(account_name, force_refresh=True)
            if on_update_callback:
                on_update_callback(account_name)

    def _get_or_fetch_account_puuid(self, account_name, in_game_name=None, in_game_tag=None):
        account_config = self._load_game_config(account_name)
        puuid = account_config.get("puuid")
        if puuid:
            return puuid

        if not in_game_name or not in_game_tag:
            saved = self.get_saved_accounts().get(account_name)
            if saved:
                _, _, _, in_game_name, in_game_tag, _, _ = saved

        if not in_game_name or not in_game_tag:
            return None

        try:
            url = f"https://api.henrikdev.xyz/valorant/v1/account/{in_game_name}/{in_game_tag}"
            res_json = self._call_henrik_api(url)
            data_obj = res_json.get("data") if isinstance(res_json, dict) else {}
            if isinstance(data_obj, dict) and data_obj.get("puuid"):
                fetched_puuid = data_obj.get("puuid")
                current_name = data_obj.get("name", in_game_name)
                current_tag = data_obj.get("tag", in_game_tag)
                account_config["puuid"] = fetched_puuid
                self._save_game_config(account_name, account_config)
                if current_name != in_game_name or current_tag != in_game_tag:
                    self.set_account_in_game_name_tag(account_name, current_name, current_tag)
                return fetched_puuid
        except Exception as e:
            logging.warning(f"Could not fetch PUUID for {account_name}: {e}")

        return None

    def fetch_and_update_rank_data(self, account_name, is_manual_refresh=False, on_update_callback=None):
        ui_settings = self.get_ima_config().get("ui_settings", {})
        auto_rank_update_enabled = ui_settings.get("auto_rank_update", True)

        if not auto_rank_update_enabled and not is_manual_refresh:
            return

        account_data = self.get_saved_accounts().get(account_name)
        if not account_data:
            return

        _, _, rank, in_game_name, in_game_tag, current_rr, last_game_rr = account_data
        if not in_game_name or not in_game_tag:
            return

        account_config = self._load_game_config(account_name)
        last_launched_at = account_config.get("last_launched_at", 0.0)
        rank_fetched_at = account_config.get("rank_fetched_at", account_config.get("last_fetched_at", 0.0))

        region = self._get_region()

        fetched_rank = None
        fetched_current_rr = None
        fetched_last_game_rr = None
        used_henrik_fallback = False

        current_time = time.time()
        if GameSwitcher._valorantrank_down and (current_time - GameSwitcher._valorantrank_down_since < 300):
            used_henrik_fallback = True
        else:
            try:
                url = f"https://valorantrank.chat/{region}/{in_game_name}/{in_game_tag}?mmrChange=true"
                response = requests.get(url, timeout=8)
                response.raise_for_status()
                fetched_rank, fetched_current_rr, fetched_last_game_rr = self._parse_rank_data(response.text)
                if not fetched_rank or fetched_current_rr is None:
                    used_henrik_fallback = True
                else:
                    GameSwitcher._valorantrank_down = False
            except Exception:
                used_henrik_fallback = True
                GameSwitcher._valorantrank_down = True
                GameSwitcher._valorantrank_down_since = time.time()

        if used_henrik_fallback and not is_manual_refresh:
            last_switched = self.config.get("last_switched_account")
            is_last_launched_account = (last_switched == account_name) or (last_launched_at > 0 and last_launched_at > rank_fetched_at)
            if not is_last_launched_account:
                return

        if used_henrik_fallback:
            try:
                puuid = account_config.get("puuid")
                if puuid:
                    henrik_url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/mmr/{region}/pc/{puuid}"
                else:
                    henrik_url = f"https://api.henrikdev.xyz/valorant/v3/mmr/{region}/pc/{in_game_name}/{in_game_tag}"

                try:
                    json_data = self._call_henrik_api(henrik_url)
                except Exception as rank_e:
                    if not puuid:
                        puuid = self._get_or_fetch_account_puuid(account_name, in_game_name, in_game_tag)
                    if puuid:
                        henrik_url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/mmr/{region}/pc/{puuid}"
                        json_data = self._call_henrik_api(henrik_url)
                    else:
                        raise rank_e
                
                data_obj = json_data.get("data", {}) if isinstance(json_data, dict) else {}
                current_obj = data_obj.get("current", {}) if isinstance(data_obj, dict) else {}
                tier_obj = current_obj.get("tier", {}) if isinstance(current_obj, dict) else {}

                p_puuid = data_obj.get("puuid") or current_obj.get("puuid")
                if p_puuid and not account_config.get("puuid"):
                    account_config["puuid"] = p_puuid

                res_name = data_obj.get("name") or current_obj.get("name")
                res_tag = data_obj.get("tag") or current_obj.get("tag")
                if res_name and res_tag and (res_name.lower() != in_game_name.lower() or res_tag.lower() != in_game_tag.lower()):
                    in_game_name, in_game_tag = res_name, res_tag
                    self.set_account_in_game_name_tag(account_name, res_name, res_tag)

                if isinstance(tier_obj, dict) and tier_obj.get("name"):
                    fetched_rank = tier_obj.get("name")
                    fetched_current_rr = current_obj.get("rr", 0)
                    fetched_last_game_rr = current_obj.get("last_change", 0)
                else:
                    current_data = data_obj.get("current_data", {}) if isinstance(data_obj, dict) else {}
                    if isinstance(current_data, dict) and current_data.get("currenttierpatched"):
                        fetched_rank = current_data.get("currenttierpatched")
                        fetched_current_rr = current_data.get("ranking_in_tier", current_rr)
                        fetched_last_game_rr = current_data.get("mmr_change_to_last_game", last_game_rr)

            except Exception as e:
                logging.warning(f"Henrik API fallback unavailable for {account_name}: {e}")
                return

        if fetched_rank and fetched_current_rr is not None and fetched_last_game_rr is not None:
            if str(fetched_rank).lower() in ['unrated', 'unranked']:
                fetched_rank = 'Unranked'

            self.set_account_in_game_name_tag(account_name, in_game_name, in_game_tag, fetched_current_rr, fetched_last_game_rr)
            self.set_account_rank(account_name, fetched_rank)

            account_config["rank_fetched_at"] = time.time()
            self._save_game_config(account_name, account_config)

            if on_update_callback:
                on_update_callback(account_name)

    def fetch_account_match_history(self, account_name, force_refresh=False, on_update_callback=None):
        account_data = self.get_saved_accounts().get(account_name)
        if not account_data:
            return []

        _, _, rank, in_game_name, in_game_tag, _, _ = account_data
        if not in_game_name or not in_game_tag:
            return []

        account_config = self._load_game_config(account_name)
        cached_history = account_config.get("match_history", [])
        last_launched_at = account_config.get("last_launched_at", 0.0)
        history_fetched_at = account_config.get("history_fetched_at", account_config.get("last_fetched_at", 0.0))

        if not force_refresh and cached_history and isinstance(cached_history, list) and len(cached_history) > 0:
            if history_fetched_at > 0 and (last_launched_at == 0.0 or history_fetched_at >= last_launched_at):
                return cached_history

        region = self._get_region()
        puuid = account_config.get("puuid")

        if puuid:
            url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{region}/{puuid}?size=15"
        else:
            url = f"https://api.henrikdev.xyz/valorant/v3/matches/{region}/{in_game_name}/{in_game_tag}?size=15"

        parsed_matches = []

        try:
            try:
                response_json = self._call_henrik_api(url)
            except Exception as primary_e:
                if not puuid:
                    puuid = self._get_or_fetch_account_puuid(account_name, in_game_name, in_game_tag)
                if puuid:
                    fallback_url = f"https://api.henrikdev.xyz/valorant/v3/by-puuid/matches/{region}/{puuid}?size=15"
                    response_json = self._call_henrik_api(fallback_url)
                else:
                    raise primary_e

            match_list = response_json.get("data", [])
            for match_item in match_list:
                if not isinstance(match_item, dict):
                    continue
                meta = match_item.get("metadata") or {}
                map_obj = meta.get("map")
                map_name = map_obj.get("name") if isinstance(map_obj, dict) else str(map_obj or "Unknown")
                mode_name = meta.get("mode") or "Competitive"
                game_start = meta.get("game_start") or 0

                date_formatted = ""
                if game_start:
                    try:
                        dt = datetime.fromtimestamp(game_start)
                        date_formatted = dt.strftime("%b %d, %H:%M")
                    except Exception:
                        pass

                players_dict = match_item.get("players") or {}
                all_players = players_dict.get("all_players") or []
                target_player = None
                parsed_players_list = []

                for player in all_players:
                    if isinstance(player, dict):
                        p_name = str(player.get("name") or "").strip()
                        p_tag = str(player.get("tag") or "").strip()
                        p_team = str(player.get("team") or "Red").strip()
                        p_char = str(player.get("character") or "Agent").strip()
                        p_tier = str(player.get("currenttier_patched") or "Unranked").strip()

                        p_stats = player.get("stats") or {}
                        p_kills = p_stats.get("kills", 0)
                        p_deaths = p_stats.get("deaths", 0)
                        p_assists = p_stats.get("assists", 0)
                        p_score = p_stats.get("score", 0)

                        parsed_players_list.append({
                            "name": p_name,
                            "tag": p_tag,
                            "team": p_team,
                            "character": p_char,
                            "rank": p_tier,
                            "kills": p_kills,
                            "deaths": p_deaths,
                            "assists": p_assists,
                            "score": p_score,
                            "kd": f"{(p_kills / max(1, p_deaths)):.2f}"
                        })

                        if puuid and str(player.get("puuid") or "").strip() == puuid:
                            target_player = player
                        elif p_name.lower() == in_game_name.strip().lower() and p_tag.lower() == in_game_tag.strip().lower():
                            target_player = player

                if not target_player and all_players and isinstance(all_players[0], dict):
                    target_player = all_players[0]

                agent_name = "Unknown"
                kills, deaths, assists = 0, 0, 0
                player_team = "Red"
                if isinstance(target_player, dict):
                    agent_name = target_player.get("character") or "Unknown"
                    player_team = target_player.get("team") or "Red"
                    player_stats = target_player.get("stats") or {}
                    kills = player_stats.get("kills", 0)
                    deaths = player_stats.get("deaths", 0)
                    assists = player_stats.get("assists", 0)

                    if not account_config.get("puuid") and target_player.get("puuid"):
                        account_config["puuid"] = target_player.get("puuid")

                    p_name = target_player.get("name")
                    p_tag = target_player.get("tag")
                    if p_name and p_tag and (p_name.lower() != in_game_name.lower() or p_tag.lower() != in_game_tag.lower()):
                        in_game_name, in_game_tag = p_name, p_tag
                        self.set_account_in_game_name_tag(account_name, p_name, p_tag)

                teams_data = match_item.get("teams") or {}
                red_team = teams_data.get("red") or {}
                blue_team = teams_data.get("blue") or {}
                red_won = red_team.get("has_won", False)
                red_rounds = red_team.get("rounds_won", 0)
                blue_rounds = blue_team.get("rounds_won", 0)

                if str(player_team).lower() == "red":
                    team_won = red_won
                    my_score, opp_score = red_rounds, blue_rounds
                else:
                    team_won = blue_team.get("has_won", False)
                    my_score, opp_score = blue_rounds, red_rounds

                match_result = "WIN" if team_won else ("LOSS" if my_score != opp_score else "DRAW")
                formatted_score = f"{my_score} - {opp_score}"
                formatted_kda = f"{kills} / {deaths} / {assists}"
                calculated_kd = f"{(kills / max(1, deaths)):.2f}"

                parsed_matches.append({
                    "map": map_name,
                    "mode": mode_name,
                    "agent": agent_name,
                    "result": match_result,
                    "score": formatted_score,
                    "kda": formatted_kda,
                    "kd": calculated_kd,
                    "date": date_formatted,
                    "players": parsed_players_list
                })

            if parsed_matches:
                account_config["last_match_map"] = parsed_matches[0]["map"]
                account_config["last_match_agent"] = parsed_matches[0]["agent"]
                account_config["match_history"] = parsed_matches
                account_config["history_fetched_at"] = time.time()
                self._save_game_config(account_name, account_config)
                if on_update_callback:
                    on_update_callback(account_name)

        except Exception as e:
            logging.error(f"Failed to fetch match history from Henrik API for {account_name}: {e}")
            account_config = self._load_game_config(account_name)
            parsed_matches = account_config.get("match_history", [])

        return parsed_matches

    def fetch_and_update_all_accounts(self, on_update_callback=None, is_manual_refresh=False):
        self._populate_all_last_match_info()
        ui_settings = self.get_ima_config().get("ui_settings", {})
        if ui_settings.get("auto_rank_update", True) or is_manual_refresh:
            accounts = list(self.get_saved_accounts().keys())
            last_switched = self.config.get("last_switched_account")
            if last_switched in accounts:
                accounts.remove(last_switched)
                accounts.insert(0, last_switched)

            workers = 1 if GameSwitcher._valorantrank_down else 3
            with ThreadPoolExecutor(max_workers=workers) as executor:
                for account_name in accounts:
                    executor.submit(self.fetch_and_update_rank_data, account_name, is_manual_refresh, on_update_callback)

            for account_name in accounts:
                account_config = self._load_game_config(account_name)
                last_launched_at = account_config.get("last_launched_at", 0.0)
                history_fetched_at = account_config.get("history_fetched_at", account_config.get("last_fetched_at", 0.0))
                
                is_stale = (last_launched_at > 0 and last_launched_at > history_fetched_at)
                is_active = (account_name == last_switched)

                if is_manual_refresh or is_stale or is_active:
                    try:
                        self.fetch_account_match_history(account_name, force_refresh=is_manual_refresh, on_update_callback=on_update_callback)
                    except Exception as e:
                        logging.warning(f"Error updating match history for {account_name}: {e}")

    def _run_rank_update_loop(self, on_update_callback=None):
        while True:
            ui_settings = self.get_ima_config().get("ui_settings", {})
            if ui_settings.get("auto_rank_update", True):
                accounts = list(self.get_saved_accounts().keys())
                workers = 1 if GameSwitcher._valorantrank_down else 3
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    for account_name in accounts:
                        executor.submit(self.fetch_and_update_rank_data, account_name, False, on_update_callback)
            time.sleep(3600)

    def start_rank_update_scheduler(self, on_update_callback=None):
        scheduler_thread = threading.Thread(target=self._run_rank_update_loop, args=(on_update_callback,), daemon=True)
        scheduler_thread.start()

    def _parse_version_tuple(self, version_str):
        if not version_str:
            return (0, 0, 0)
        clean_str = version_str.strip().lstrip('v').lstrip('V')
        parts = []
        for token in clean_str.split('.'):
            num = re.sub(r'\D', '', token)
            if num:
                parts.append(int(num))
        return tuple(parts)

    def check_for_update(self):
        if requests is None:
            return False, APP_VERSION, None, "Requests library unavailable.", 0

        api_url = "https://api.github.com/repos/iMAboud/iMA-Switcher/releases/latest"
        headers = {"User-Agent": "iMA-Switcher-App"}
        try:
            response = requests.get(api_url, headers=headers, timeout=6)
            if response.status_code != 200:
                return False, APP_VERSION, None, f"GitHub API error {response.status_code}", 0

            data = response.json()
            remote_tag = data.get("tag_name", "")
            release_notes = data.get("body", "") or "New version available with improvements and bug fixes."
            assets = data.get("assets", [])

            download_url = None
            file_size = 0
            for asset in assets:
                asset_name = asset.get("name", "")
                if asset_name.endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    file_size = asset.get("size", 0)
                    break

            if not download_url and assets:
                download_url = assets[0].get("browser_download_url")
                file_size = assets[0].get("size", 0)

            local_tuple = self._parse_version_tuple(APP_VERSION)
            remote_tuple = self._parse_version_tuple(remote_tag)

            has_update = remote_tuple > local_tuple
            clean_remote_version = remote_tag.lstrip('v').lstrip('V')

            return has_update, clean_remote_version, download_url, release_notes, file_size
        except Exception as e:
            logging.warning(f"Error checking for updates: {e}")
            return False, APP_VERSION, None, str(e), 0

    def download_update(self, download_url, dest_path, progress_callback=None):
        if requests is None or not download_url:
            return False
        try:
            response = requests.get(download_url, stream=True, timeout=15)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as file_handle:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        file_handle.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            return True
        except Exception as e:
            logging.error(f"Failed to download update: {e}")
            return False

    def apply_update(self, installer_path):
        target_exe = sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(sys.argv[0])
        updates_dir = Path(self.user_data_dir) / "updates"
        updates_dir.mkdir(parents=True, exist_ok=True)
        batch_script_path = updates_dir / "apply_update.bat"

        bat_content = f"""@echo off
timeout /t 2 /nobreak > NUL
taskkill /F /IM "{os.path.basename(target_exe)}" > NUL 2>&1
copy /Y "{os.path.abspath(installer_path)}" "{target_exe}"
start "" "{target_exe}"
del "{os.path.abspath(installer_path)}" > NUL 2>&1
del "%~f0" > NUL 2>&1
"""
        with open(batch_script_path, "w", encoding="utf-8") as bat_file:
            bat_file.write(bat_content)

        creation_flags = 0x08000000 if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        subprocess.Popen(["cmd.exe", "/c", str(batch_script_path)], creationflags=creation_flags)
        QApplication.instance().quit()