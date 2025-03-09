import os
import requests
import uuid
from urllib.parse import urlparse
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
import logging
import asyncio

class TelegramPoster:
    def __init__(self, config, vk_client):
        self.config = config
        self.vk_client = vk_client
        self.bot = Bot(token=self.config.get('tg_bot_token'))
        self.files_dir = os.path.join(os.path.dirname(__file__), '..', 'files')
        self._init_files_dir()
        logging.info('Telegram bot initialized')

    def _init_files_dir(self):
        """Создаёт папку для временных файлов"""
        os.makedirs(self.files_dir, exist_ok=True)

    def _is_valid_url(self, url):
        """Проверяет валидность URL"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _download_file(self, url, file_name=None):
        """Скачивает файл во временную папку"""
        if not self._is_valid_url(url):
            raise ValueError(f"Invalid URL: {url}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Генерируем имя файла если не указано
            if not file_name:
                file_name = os.path.basename(urlparse(url).path) or f"file_{uuid.uuid4().hex}"
            
            file_path = os.path.join(self.files_dir, file_name)
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return file_path
        except Exception as e:
            logging.error(f"File download failed: {e}")
            return None

    async def process_post(self, post):
        """Основной метод обработки поста"""
        try:
            main_message = None
            repost = post.get('copy_history', [None])[0] if 'copy_history' in post else None

            # Обработка основного поста
            if post.get('text') or post.get('attachments'):
                main_message = await self._send_content(
                    text=post.get('text', ''),
                    attachments=post.get('attachments', []),
                    reply_to=None
                )

            # Обработка репоста
            if repost:
                author = self.vk_client.get_author_name(repost['owner_id'])
                repost_text = f"↘️ Repost from {author}"
                if repost.get('text'):
                    repost_text += f":\n{repost['text']}"
                
                repost_message = await self._send_content(
                    text=repost_text,
                    attachments=repost.get('attachments', []),
                    reply_to=main_message.message_id if main_message else None
                )

        except Exception as e:
            logging.exception(f"Post processing failed: {e}")

    async def _send_content(self, text, attachments, reply_to):
        """Отправка основного контента"""
        media_group = []
        message = None
        
        # Формируем медиа-группу
        for att in attachments:
            media = self._process_attachment(att)
            if media:
                media_group.append(media)

        # Отправляем текст или медиа-группу
        if len(text) > 1024 or (not media_group and text):
            message = await self._send_text(text, reply_to)
        elif media_group:
            message = await self._send_media_group(text, media_group, reply_to)

        # Отправляем специальные вложения
        await self._send_special_attachments(attachments, message)
        return message

    def _process_attachment(self, att):
        """Обработка медиа-вложений"""
        att_type = att['type']
        data = att[att_type]
        
        if att_type == 'photo':
            url = max(data['sizes'], key=lambda x: x['width'])['url']
            return InputMediaPhoto(media=url)
        elif att_type == 'video':
            return InputMediaVideo(media=data.get('player', ''))
        return None

    async def _send_text(self, text, reply_to):
        """Отправка текстового сообщения"""
        try:
            return await self.bot.send_message(
                chat_id=self.config.get('tg_channel_id'),
                text=text[:4096],
                reply_to_message_id=reply_to
            )
        except Exception as e:
            logging.exception(f"Text message failed: {e}")

    async def _send_media_group(self, text, media_group, reply_to):
        """Отправка медиа-группы"""
        try:
            if text and len(text) <= 1024:
                media_group[0].caption = text[:1024]
                media_group[0].parse_mode = 'HTML'

            messages = await self.bot.send_media_group(
                chat_id=self.config.get('tg_channel_id'),
                media=media_group[:10],
                reply_to_message_id=reply_to
            )
            return messages[0] if messages else None
        except Exception as e:
            logging.exception(f"Media group failed: {e}")

    async def _send_special_attachments(self, attachments, reply_to):
        """Отправка специальных вложений (документы, аудио, опросы)"""
        for att in attachments:
            try:
                att_type = att['type']
                data = att[att_type]

                # Получаем ID сообщения для ответа
                reply_id = reply_to.message_id if reply_to else None

                if att_type == 'doc':
                    doc_url = data.get('url')
                    if not doc_url:
                        continue
                    
                    file_ext = data.get('ext', 'bin')
                    file_name = f"{data.get('title', 'document')}.{file_ext}"
                    file_path = self._download_file(doc_url, file_name)
                    
                    if file_path:
                        with open(file_path, 'rb') as file:
                            await self.bot.send_document(
                                chat_id=self.config.get('tg_channel_id'),
                                document=file,
                                reply_to_message_id=reply_id
                            )
                        os.remove(file_path)

                elif att_type == 'audio':
                    artist = data.get('artist', 'Unknown Artist')
                    title = data.get('title', 'Unknown Track')
                    file_name = f"{artist} - {title}.mp3".replace('/', '_')
                    file_url = data.get('url')
                    
                    if not file_url:
                        continue
                    
                    file_path = self._download_file(file_url, file_name)
                    
                    if file_path:
                        with open(file_path, 'rb') as file:
                            await self.bot.send_audio(
                                chat_id=self.config.get('tg_channel_id'),
                                audio=file,
                                title=title,
                                performer=artist,
                                reply_to_message_id=reply_id
                            )
                        os.remove(file_path)

                elif att_type == 'poll':
                    await self.bot.send_poll(
                        chat_id=self.config.get('tg_channel_id'),
                        question=data['question'],
                        options=[a['text'] for a in data['answers']],
                        allows_multiple_answers=data.get('multiple', False),
                        reply_to_message_id=reply_id
                    )
            except Exception as e:
                logging.exception(f"Attachment failed: {e}")