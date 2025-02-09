import json
import logging
from modules.config_handler import ConfigHandler

class Configurator:
    def __init__(self):
        self.config = ConfigHandler()
        logging.basicConfig(level=logging.INFO)

    def setup(self):
        print("\n=== Telegram Setup ===")
        self._setup_telegram()
        print("\n=== VK Setup ===")
        self._setup_vk()
        print("\nConfiguration saved to config.json")

    def _setup_telegram(self):
        if not self.config.get('tg_bot_token'):
            self.config.set('tg_bot_token', input("Enter Telegram bot token: ").strip())
        
        if not self.config.get('tg_channel_id'):
            self.config.set('tg_channel_id', input("Enter Telegram channel ID (@username): ").strip())

    def _setup_vk(self):
        if not self.config.get('vk_access_token'):
            self.config.set('vk_access_token', input("Enter VK access token: ").strip())
        
        if not self.config.get('vk_user_id'):
            self.config.set('vk_user_id', input("Enter VK user ID: ").strip())

if __name__ == '__main__':
    Configurator().setup()