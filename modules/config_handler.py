import json
import os
import logging

class ConfigHandler:
    def __init__(self, config_path=None):
        if config_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.config_path = os.path.join(root_dir, 'config.json')
        else:
            self.config_path = config_path
            
        self.config = self._load_config()
        logging.info('Configuration loaded')

    def _load_config(self):
        default_config = {
            "vk_user_id": 0,
            "tg_channel_id": "",
            "tg_bot_token": "",
            "vk_access_token": "",
            "last_post_id": 0,
            "log_level": "INFO"
        }

        if not os.path.exists(self.config_path):
            logging.warning('Creating new config file')
            self.config = default_config
            self.save()
            return default_config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
        except Exception as e:
            logging.error(f'Config load error: {e}')
            return default_config

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.exception(f'Config save error: {e}')

    def get(self, key):
        return self.config.get(key)

    def set(self, key, value):
        self.config[key] = value
        self.save()