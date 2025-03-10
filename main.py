import asyncio
import logging
import sys
import os
from datetime import datetime
from modules.config_handler import ConfigHandler
from modules.vk_api_client import VKClient
from modules.telegram_bot import TelegramPoster

class VK2TG:
    def __init__(self):
        self._setup_logging()
        self.config = ConfigHandler(sys.argv[1] if len(sys.argv) > 1 else None)
        
        if not self._validate_config():
            print("Error: Invalid configuration. Please create config first:")
            print("https://daniilsavenya.github.io/Repost_bot/configurator.html")
            sys.exit(1)

        self.vk = VKClient(self.config)
        self.tg = TelegramPoster(self.config, self.vk)

    def _setup_logging(self):
        log_filename = os.path.join(os.path.dirname(__file__), 'vk2tg.log')
        logging.basicConfig(
            filename=log_filename,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(console)

    def _validate_config(self):
        required_keys = {
            'vk_access_token': "VK access token",
            'vk_user_id': "VK user ID",
            'tg_channel_id': "Telegram channel ID",
            'tg_bot_token': "Telegram bot token"
        }
        
        missing = [name for key, name in required_keys.items() if not self.config.get(key)]
        if missing:
            logging.error(f"Missing configuration parameters: {', '.join(missing)}")
            return False
            
        if self.config.get('tg_channel_id', 0) >= 0:
            logging.error("Telegram Channel ID must be negative (channel chat)")
            return False
            
        return True

    async def _process_posts(self, posts):
        last_post_date = self.config.get('last_post_date') or 0
        new_posts = [p for p in posts if p['date'] > last_post_date]
        new_posts.sort(key=lambda x: x['date'])

        if not new_posts:
            logging.info("No new posts to publish")
            return

        for i, post in enumerate(new_posts):
            try:
                await self.tg.process_post(post)
                self.config.set('last_post_date', post['date'])
                logging.info(f"Published post from {self._format_date(post['date'])}")
            except Exception as e:
                logging.exception(f"Post processing error: {str(e)}")
            if i < len(new_posts) - 1:
                await asyncio.sleep(7200)

    def _format_date(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    async def monitor(self):
        while True:
            try:
                posts = self.vk.get_new_posts()
                await self._process_posts(posts)
            except Exception as e:
                logging.exception(f"Monitoring error: {str(e)}")
            await asyncio.sleep(60)

if __name__ == '__main__':
    bot = VK2TG()
    asyncio.run(bot.monitor())