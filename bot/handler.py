import json
import threading

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from bot.core.bot_service import InstagramBot

from handlers.redis_handler import RedisQueue


class BotHandler:
    bot_session = {}

    def read_queue(self):
        while True:
            queue = RedisQueue('bot_queue')
            size = queue.qsize()
            if size > 0:
                credentials = json.loads(queue.get(block=True))

                thread = threading.Thread(target=self.handle_credentials, args=(credentials,))
                thread.daemon = True
                thread.start()

    def handle_credentials(self, credentials):

        if credentials['command'] == "START":
            self.handle_start_bot(credentials)

        elif credentials['command'] == "STOP":
            self.handle_stop_bot(credentials)

    def handle_stop_bot(self, credentials):
        bot = self.get_or_create_bot(credentials['username'], credentials['password'])

        if bot:
            bot.stop_bot()
            del self.bot_session[credentials['username']]

    def handle_start_bot(self, credentials):
        bot = self.bot_session.get(credentials['username'], None)
        if not bot:
            bot = self.get_or_create_bot(credentials['username'], credentials['password'])

            if bot:
                self.send_to_socket(credentials['username'], "Starting bot")
                bot.run_bot()
        else:
            self.send_to_socket(credentials['username'], "Bot already running")

    def get_or_create_bot(self, username, password):
        if self.bot_session.get(username, None):
            return self.bot_session[username]

        try:
            bot = InstagramBot(username, password)
            if bot.login_status:
                self.bot_session[username] = bot

                return bot
            return None

        except Exception as e:
            print(e)

    def send_to_socket(self, username, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_' + username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })
