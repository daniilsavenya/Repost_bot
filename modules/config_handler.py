import json
import os
import time
import logging

class ConfigHandler:
    def __init__(self, config_path=None):
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'config.json'
        )
        self.config = self._load_config()
        logging.info('Configuration loaded successfully')

    def _load_config(self):
        default_config = {
            "vk_user_id": 0,
            "tg_channel_id": "",
            "tg_bot_token": "",
            "vk_access_token": "",
            "last_post_date": time.time(),
            "log_level": "INFO"
        }

        if not os.path.exists(self.config_path):
            logging.warning('Creating new config file with default values')
            self.config = default_config
            self.save()
            return default_config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        except Exception as e:
            logging.error(f'Failed to load config: {str(e)}')
            return default_config

    def save(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logging.error(f'Failed to save config: {str(e)}')

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()