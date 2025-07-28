import json
import logging
from pathlib import Path

try:
    from jsonschema import validate
    from jsonschema.exceptions import ValidationError
except ImportError:
    validate = None
    ValidationError = None
    logging.warning("jsonschema not installed. Configuration validation will be skipped.")

class ConfigManager:
    CONFIG_SCHEMA = {
        "type": "object",
        "properties": {
            "output_dir": {"type": ["string", "null"]},
            "title": {"type": "string"},
            "menu_icon_path": {"type": "string"},
            "ordered_accounts": {"type": "array", "items": {"type": "string"}},
            "riot_client_exe_path": {"type": ["string", "null"]},
            "last_graphics_settings_hash": {"type": ["string", "null"]},
            "ui_settings": {
                "type": "object",
                "properties": {
                    "show_game_icons": {"type": "boolean"},
                    "show_rank_tips": {"type": "boolean"},
                    "tip_delay": {"type": "number", "minimum": 0},
                    "use_rank_icons": {"type": "boolean"},
                    "show_rank_icon_left": {"type": "boolean"},
                    "show_name_tag": {"type": "boolean"},
                    "auto_rank_update": {"type": "boolean"},
                    "rank_check_region": {"type": "string"},
                    "grid_size": {"type": "integer", "minimum": 1},
                    "orientation": {"type": "string", "enum": ["vertical", "horizontal"]},
                }
            },
            "graphics_settings": {"type": "object"},
            "app_install_path": {"type": "string"}
        }
    }
    DEFAULT_CONFIG = {
        "output_dir": None,
        "title": "Valorant",
        "menu_icon_path": "",
        "ordered_accounts": [],
        "riot_client_exe_path": None,
        "last_graphics_settings_hash": None,
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
            "orientation": "vertical"
        }
    }

    def __init__(self, user_data_dir):
        self.config_path = Path(user_data_dir) / "config.json"
        self.config = self._load_config()

    def _load_config(self):
        config = self.DEFAULT_CONFIG.copy()
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                if validate and ValidationError:
                    try:
                        validate(instance=loaded_config, schema=self.CONFIG_SCHEMA)
                    except ValidationError as e:
                        logging.warning(f"Config validation error: {e.message}. Using default values for invalid keys.")
                
                def deep_update(target, source):
                    for k, v in source.items():
                        if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                            target[k] = deep_update(target[k], v)
                        else:
                            target[k] = v
                    return target
                
                config = deep_update(config, loaded_config)

            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logging.warning(f"config.json is corrupted or has encoding issues: {e}. Using defaults.")
        return config

    def _save_config(self):
        with self.config_path.open('w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)

    def get_config(self):
        return self.config

    def update_config(self, settings):
        self.config.update(settings)
        self._save_config()
