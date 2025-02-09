import asyncio
import logging
import os
from modules.config_handler import ConfigHandler
from modules.vk_api_client import VKClient
from modules.telegram_bot import TelegramPoster
from configurator import Configurator

class VK2TG:
    def __init__(self):
        self._setup_logging(logging.INFO)
        self.config = ConfigHandler()
        
        log_level_str = self.config.get('log_level') or 'INFO'
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        logging.getLogger().setLevel(log_level)
        for handler in logging.getLogger().handlers:
            handler.setLevel(log_level)

        if not self.config.config or not self.config.get('vk_access_token') or not self.config.get('vk_user_id'):
            print("Configuration file missing or incomplete. Starting setup...")
            Configurator().setup()
            self.config = ConfigHandler()

        self.vk = VKClient(self.config)
        self.tg = TelegramPoster(self.config, self.vk)

    def _setup_logging(self, log_level):
        log_filename = os.path.join(os.path.dirname(__file__), 'vk2tg.log')
        if not os.path.exists(log_filename):
            open(log_filename, 'a').close()

        logging.basicConfig(
            filename=log_filename,
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            force=True
        )
        console = logging.StreamHandler()
        console.setLevel(log_level)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console.setFormatter(formatter)
        logging.getLogger('').addHandler(console)

    async def post_processing(self, posts):
        last_post_id = self.config.get('last_post_id') or 0
        new_posts = [p for p in posts if p['id'] > last_post_id]
        new_posts.sort(key=lambda x: x['id'])
        
        for post in new_posts:
            try:
                await self.tg.process_post(post)
                self.config.set('last_post_id', post['id'])
                logging.info(f'Successfully processed post ID: {post["id"]}')
            except Exception as e:
                logging.exception(f'Failed to process post {post["id"]}: {e}')
            
            if len(new_posts) > 1:
                await asyncio.sleep(9000)

    async def monitor(self):
        while True:
            try:
                posts = self.vk.get_new_posts()
                await self.post_processing(posts)
                await asyncio.sleep(60)
            except Exception as e:
                logging.exception(f'Monitoring error: {e}')
                await asyncio.sleep(60)

if __name__ == '__main__':
    bot = VK2TG()
    asyncio.run(bot.monitor())