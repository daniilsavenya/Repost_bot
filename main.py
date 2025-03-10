# main.py
import asyncio
import logging
import sys
import os
from datetime import datetime
from modules.config_handler import ConfigHandler
from modules.vk_api_client import VKClient
from modules.telegram_bot import TelegramPoster
from configurator import Configurator

class VK2TG:
    def __init__(self):
        self._setup_logging(logging.INFO)
        self.config = ConfigHandler(sys.argv[1] if len(sys.argv)>1 else None)
        
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
        # Получаем дату последней опубликованной записи (unix timestamp)
        last_post_date = self.config.get('last_post_date') or 0
        # Фильтруем записи, опубликованные после last_post_date
        new_posts = [p for p in posts if p['date'] > last_post_date]
        # Сортируем по возрастанию даты публикации
        new_posts.sort(key=lambda x: x['date'])

        if not new_posts:
            logging.info("Нет новых записей для публикации.")
            return

        # Если в очереди более одного поста, публикуем с интервалом в 2 часа (7200 секунд)
        for i, post in enumerate(new_posts):
            try:
                await self.tg.process_post(post)
                # Обновляем конфигурацию с датой публикации этого поста
                self.config.set('last_post_date', post['date'])
                logging.info(f"Успешно опубликована запись с датой: {datetime.fromtimestamp(post['date']).strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                logging.exception(f"Ошибка при обработке записи с датой {post['date']}: {e}")
            # Если есть следующие записи в очереди, ждём 2 часа перед следующей публикацией
            if i < len(new_posts) - 1:
                await asyncio.sleep(7200)

    async def monitor(self):
        while True:
            try:
                posts = self.vk.get_new_posts()
                await self.post_processing(posts)
                await asyncio.sleep(60)
            except Exception as e:
                logging.exception(f"Ошибка мониторинга: {e}")
                await asyncio.sleep(60)

if __name__ == '__main__':
    bot = VK2TG()
    asyncio.run(bot.monitor())
