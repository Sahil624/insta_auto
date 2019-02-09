import random

from django.core.management import BaseCommand

from bot.core.bot_service import InstagramBot


class Command(BaseCommand):
    help = 'Command for testing bot'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of test account')
        parser.add_argument('password', type=str, help='Password of test account')

    def handle(self, *args, **kwargs):
        user_name = kwargs['username']
        password = kwargs['password']

        print(user_name, password)

        bot = InstagramBot(user_name, password)
        logger = bot.user_instance.get_user_logger()
        logger.info('============ TEST BOT LOGS ===============')
        print('bot created', bot.login_status, bot.user_id)

        if bot.login_status:
            option = self.option_prompt()

            if option is 1:
                self.get_media_by_tag(bot)

            if option is 2:
                bot.this_tag_like_count = 0
                bot.max_like_for_one_tag = bot.configurations.max_like_for_one_tag
                bot.max_tag_like_count = random.randint(
                    1, bot.max_like_for_one_tag
                )
                self.get_any_user_details(bot)

            if option is 3:
                self.liker(bot)

        else:
            print('Bot failed')
        logger.info('============ TEST BOT LOGS END ===============')

    def get_media_by_tag(self, bot):
        bot.media_manager.get_media_id_by_tag('test')
        print('result', bot.media_by_tag)

    def get_any_user_details(self, bot):
        search_user = input('Enter any users name ')
        print('starting search for ', search_user)
        data = bot.insta_explorer.get_user_info(search_user)
        print(data)

    def liker(self, bot):
        bot.media_manager.get_media_id_by_tag('test')
        # new_auto_mod_like
        bot.like_manager.new_auto_mod_like()
        print('Like counter', bot.like_counter)

    def option_prompt(self):
        option = input('Enter test option avilable tests are :- \n'
                       '1) get Media by tags\n'
                       '2) get any user detail by username\n'
                       '3) test auto like \n'
                       '-1) Exit test\n')
        return int(option)
