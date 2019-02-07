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
        print('bot created', bot.login_status, bot.user_id)

        if bot.login_status:
            option = self.option_prompt()

            if option is 1:
                self.get_media_by_tag(bot)

            if option is 2:
                self.get_any_user_details(bot)

    def get_media_by_tag(self, bot):
        bot.media_manager.get_media_id_by_tag('test')
        print('result', bot.media_by_tag)

    def get_any_user_details(self, bot):
        search_user = input('Enter any users name ')
        print('starting search for ', search_user)
        data = bot.insta_explorer.get_userinfo_by_name(search_user)
        print(data)

    def option_prompt(self):
        option = input('Enter test option avilable tests are :- \n'
                       '1) get Media by tags\n'
                       '2) get any user detail by username\n'
                       '-1) Exit test\n')
        return int(option)
