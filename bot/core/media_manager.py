import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class MediaManager:

    def __init__(self, bot):
        bot.logger.debug('Initalizing media manager for ', bot.user_instance.username, 'with login status', bot.login_status)
        self.bot = bot

    def get_media_id_by_tag(self, tag):
        """ Get media ID set, by your hashtag or location """

        if self.bot.login_status:
            if tag.startswith("l:"):
                tag = tag.replace("l:", "")
                self.bot.by_location = True
                log_string = "Get Media by location: %s" % tag
                self.bot.logger.info(log_string)
                if self.bot.login_status == 1:
                    url_location = self.bot.url_location % tag
                    try:
                        r = self.bot.session_1.get(url_location)
                        all_data = json.loads(r.text)
                        self.bot.media_by_tag = list(
                            all_data["graphql"]["location"]["edge_location_to_media"][
                                "edges"
                            ]
                        )
                    except Exception as e:
                        self.bot.media_by_tag = []
                        self.bot.logger.error("Except on get_media!" + str(e))
                else:
                    return 0

            else:
                log_string = "Get Media by tag: %s" % tag
                # self.bot.logger.info(log_string)
                self.bot.by_location = False
                if self.bot.login_status == 1:
                    url_tag = self.bot.url_tag % tag
                    try:
                        response = self.bot.session_1.get(url_tag)
                        all_data = json.loads(response.text)
                        self.bot.media_by_tag = list(
                            all_data["graphql"]["hashtag"]["edge_hashtag_to_media"][
                                "edges"
                            ]
                        )
                    except Exception as e:
                        self.bot.media_by_tag = []
                        self.bot.logger.error('Except on get_media!' + str(e))
                else:
                    return 0

    def get_instagram_url_from_media_id(self, media_id, url_flag=True, only_code=None):
        """ Get Media Code or Full Url from Media ID Thanks to Nikished """
        media_id = int(media_id)
        if url_flag is False:
            return ""
        else:
            alphabet = (
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            )
            shortened_id = ""
            while media_id > 0:
                media_id, idx = divmod(media_id, 64)
                shortened_id = alphabet[idx] + shortened_id
            if only_code:
                return shortened_id
            else:
                return f"https://www.instagram.com/p/{shortened_id}/"

    def get_username_by_media_id(self, media_id):
        """ Get username by media ID Thanks to Nikished """

        if self.bot.login_status:
            if self.bot.login_status == 1:
                media_id_url = self.get_instagram_url_from_media_id(
                    int(media_id), only_code=True
                )
                url_media = self.bot.url_media_detail % media_id_url
                try:
                    r = self.bot.session_1.get(url_media)
                    all_data = json.loads(r.text)

                    username = str(
                        all_data["graphql"]["shortcode_media"]["owner"]["username"]
                    )
                    print(
                        "media_id="
                        + media_id
                        + ", media_id_url="
                        + media_id_url
                        + ", username_by_media_id="
                        + username
                    )
                    return username
                except Exception as e:
                    self.bot.logger.error('username_by_mediaid exception' + str(e))
                    print("username_by_mediaid exception")
                    return False
            else:
                return ""

    def send_to_socket(self, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_'+ self.bot.user_instance.username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })
