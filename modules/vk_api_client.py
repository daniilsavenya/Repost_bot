import vk_api
import logging

class VKClient:
    def __init__(self, config_handler):
        self.config = config_handler
        self._validate_config()
        self._init_session()

    def _validate_config(self):
        if not self.config.get('vk_access_token'):
            raise ValueError("Missing VK access token!")
        if not self.config.get('vk_user_id'):
            raise ValueError("Missing VK user ID!")

    def _init_session(self):
        try:
            vk_session = vk_api.VkApi(
                token=self.config.get('vk_access_token'),
                api_version="5.131"
            )
            self.vk = vk_session.get_api()
            logging.info('VK API initialized')
        except Exception as e:
            logging.exception(f"VK init error: {e}")
            raise

    def get_new_posts(self):
        try:
            response = self.vk.wall.get(
                owner_id=self.config.get('vk_user_id'),
                count=10,
                filter='owner',
                extended=1
            )
            return self._process_posts(response['items'])
        except Exception as e:
            logging.exception(f"Posts fetch error: {e}")
            return []

    def _process_posts(self, items):
        processed = []
        for item in items:
            post = item.copy()
            if 'attachments' in post:
                for att in post['attachments']:
                    if att['type'] == 'audio':
                        att['audio'] = self._get_audio_info(att['audio'])
            processed.append(post)
        return processed

    def _get_audio_info(self, audio_data):
        return {
            'artist': audio_data.get('artist', 'Unknown Artist'),
            'title': audio_data.get('title', 'Unknown Track'),
            'url': audio_data.get('url')
        }

    def get_author_name(self, owner_id):
        try:
            if owner_id > 0:
                user = self.vk.users.get(user_ids=owner_id, fields='first_name,last_name')[0]
                return f"{user['first_name']} {user['last_name']}"
            else:
                group = self.vk.groups.getById(group_ids=str(abs(owner_id)))[0]
                return group['name']
        except Exception as e:
            logging.exception(f"Author info error: {e}")
            return "Unknown Author"