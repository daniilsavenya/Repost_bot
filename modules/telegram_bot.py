import requests
from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, BufferedInputFile, URLInputFile
import logging
import asyncio
from datetime import datetime
import re

class TelegramPoster:
    def __init__(self, config, vk_client):
        """Initialize Telegram bot with configuration and VK client"""
        self.config = config
        self.vk_client = vk_client
        self.bot = Bot(token=self.config.get('tg_bot_token'))
        logging.info('Telegram bot initialized')

    async def process_post(self, post):
        """Process and publish a VK post to Telegram including reposts"""
        try:
            main_message = await self._process_main_post(post)
            await self._process_reposts(post, main_message)
            self._log_success(post)
            
        except Exception as e:
            logging.exception(f"Post processing error: {str(e)}")

    async def _process_main_post(self, post):
        """Handle main post content"""
        if post.get('text') or post.get('attachments'):
            return await self._send_content(
                text=post.get('text', ''),
                attachments=post.get('attachments', []),
                reply_to=None
            )
        return None

    async def _process_reposts(self, post, main_message):
        """Handle nested reposts structure"""
        reposts = post.get('copy_history', [])
        for repost in reversed(reposts):
            if not repost.get('owner_id'):
                continue
                
            await self._send_repost_content(repost, main_message)

    async def _send_repost_content(self, repost, main_message):
        """Process and send repost content"""
        author = self.vk_client.get_author_name(repost['owner_id'])
        repost_text = f"↘️ Repost from {author}"
        
        if repost.get('text'):
            repost_text += f":\n{repost['text']}"
        
        await self._send_content(
            text=repost_text,
            attachments=repost.get('attachments', []),
            reply_to=main_message.message_id if main_message else None
        )

    async def _send_content(self, text, attachments, reply_to):
        """Manage content sending strategy based on content type"""
        media_group = []
        message = None
        
        # Process all attachments
        for att in attachments:
            media = self._process_attachment(att)
            if media:
                media_group.append(media)

        # Determine sending strategy
        if len(text) > 1024 or (not media_group and text):
            message = await self._send_text(text, reply_to)
        elif media_group:
            message = await self._send_media_group(text, media_group, reply_to)

        # Handle special attachments
        await self._send_special_attachments(attachments, message)
        return message

    def _process_attachment(self, att):
        """Create media object from VK attachment"""
        att_type = att['type']
        data = att[att_type]
        
        if att_type == 'photo':
            best_quality = max(data['sizes'], key=lambda x: x['width'])
            return InputMediaPhoto(media=best_quality['url'])
            
        elif att_type == 'video':
            return InputMediaVideo(media=URLInputFile(data.get('player', '')))
            
        return None

    async def _send_text(self, text, reply_to):
        """Send text message to Telegram channel"""
        try:
            return await self.bot.send_message(
                chat_id=self.config.get('tg_channel_id'),
                text=text[:4096],
                reply_to_message_id=reply_to
            )
        except Exception as e:
            logging.exception(f"Failed to send text: {str(e)}")

    async def _send_media_group(self, text, media_group, reply_to):
        """Send media group with optional caption"""
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
            logging.exception(f"Failed to send media group: {str(e)}")

    async def _send_special_attachments(self, attachments, reply_to):
        """Handle special attachment types separately"""
        for att in attachments:
            try:
                att_type = att['type']
                data = att[att_type]
                reply_id = reply_to.message_id if reply_to else None

                if att_type == 'doc':
                    await self._handle_document(data, reply_id)
                elif att_type == 'audio':
                    await self._handle_audio(data, reply_id)
                elif att_type == 'poll':
                    await self._handle_poll(data, reply_id)

            except Exception as e:
                logging.exception(f"Attachment error ({att_type}): {str(e)}")

    async def _handle_document(self, data, reply_id):
        """Process and send document attachment"""
        if not (url := data.get('url')):
            return

        response = requests.get(url)
        response.raise_for_status()
        
        file_name = self._sanitize_filename(
            data.get('title', 'document'),
            data.get('ext', 'bin')
        )
        
        input_file = BufferedInputFile(
            file=response.content,
            filename=file_name
        )

        await self.bot.send_document(
            chat_id=self.config.get('tg_channel_id'),
            document=input_file,
            reply_to_message_id=reply_id
        )

    async def _handle_audio(self, data, reply_id):
        """Process and send audio attachment"""
        if not (url := data.get('url')):
            return

        file_name = self._generate_audio_name(
            data.get('artist', 'Unknown Artist'),
            data.get('title', 'Unknown Track')
        )

        input_file = URLInputFile(url=url, filename=file_name)
        
        await self.bot.send_audio(
            chat_id=self.config.get('tg_channel_id'),
            audio=input_file,
            title=data.get('title', '')[:64],
            performer=data.get('artist', '')[:64],
            reply_to_message_id=reply_id
        )

    async def _handle_poll(self, data, reply_id):
        """Process and send poll attachment"""
        await self.bot.send_poll(
            chat_id=self.config.get('tg_channel_id'),
            question=data['question'],
            options=[a['text'] for a in data['answers']],
            allows_multiple_answers=data.get('multiple', False),
            reply_to_message_id=reply_id
        )

    def _sanitize_filename(self, title, ext):
        """Generate safe filename without duplicate extensions"""
        # Clean title and remove special characters
        clean_title = re.sub(r'[^\w\-_\. ]', '', title.strip())[:64]
        
        # Process extension: split from right and take last part
        clean_ext = ext.split('.')[-1].strip()[:10]
        if not clean_ext:
            clean_ext = 'bin'
            
        # Remove existing extension from title if present
        if '.' in clean_title:
            clean_title = clean_title.rsplit('.', 1)[0]
            
        return f"{clean_title}.{clean_ext}".strip('.')

    def _generate_audio_name(self, artist, title):
        """Generate filename for audio tracks"""
        clean_artist = "".join([c for c in artist if c.isalnum() or c in (' ', '_')])[:32]
        clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')])[:32]
        return f"{clean_artist} - {clean_title}.mp3"

    def _log_success(self, post):
        """Log successful post processing"""
        log_date = datetime.fromtimestamp(post['date']).strftime('%Y-%m-%d %H:%M:%S')
        logging.info(f"Successfully published post from {log_date}")