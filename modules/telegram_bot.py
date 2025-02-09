from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo
import logging
import asyncio

class TelegramPoster:
    def __init__(self, config, vk_client):
        self.config = config
        self.vk_client = vk_client
        self.bot = Bot(token=self.config.get('tg_bot_token'))
        logging.info('Telegram bot initialized')

    async def process_post(self, post):
        try:
            main_message = None
            repost = post.get('copy_history', [None])[0] if 'copy_history' in post else None

            # Process main post
            if post.get('text') or post.get('attachments'):
                main_message = await self._send_content(
                    text=post.get('text', ''),
                    attachments=post.get('attachments', []),
                    reply_to=None
                )

            # Process repost
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
        media_group = []
        message = None
        
        # Create media group
        for att in attachments:
            media = self._process_attachment(att)
            if media:
                media_group.append(media)

        # Send text or media group
        if len(text) > 1024 or (not media_group and text):
            message = await self._send_text(text, reply_to)
        elif media_group:
            message = await self._send_media_group(text, media_group, reply_to)

        # Send other attachments
        await self._send_special_attachments(attachments, message)
        return message

    def _process_attachment(self, att):
        att_type = att['type']
        data = att[att_type]
        
        if att_type == 'photo':
            url = max(data['sizes'], key=lambda x: x['width'])['url']
            return InputMediaPhoto(media=url)
        elif att_type == 'video':
            return InputMediaVideo(media=data.get('player', ''))
        return None

    async def _send_text(self, text, reply_to):
        try:
            return await self.bot.send_message(
                chat_id=self.config.get('tg_channel_id'),
                text=text[:4096],
                reply_to_message_id=reply_to
            )
        except Exception as e:
            logging.exception(f"Text message failed: {e}")

    async def _send_media_group(self, text, media_group, reply_to):
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
        for att in attachments:
            try:
                att_type = att['type']
                data = att[att_type]

                if att_type == 'doc':
                    await self.bot.send_document(
                        chat_id=self.config.get('tg_channel_id'),
                        document=data['url'],
                        reply_to_message_id=reply_to
                    )
                elif att_type == 'poll':
                    await self.bot.send_poll(
                        chat_id=self.config.get('tg_channel_id'),
                        question=data['question'],
                        options=[a['text'] for a in data['answers']],
                        allows_multiple_answers=data.get('multiple', False),
                        reply_to_message_id=reply_to
                    )
            except Exception as e:
                logging.exception(f"Attachment failed: {e}")