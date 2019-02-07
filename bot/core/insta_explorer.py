import json

from instaloader import instaloader


class Explorer:

    def __init__(self, bot):
        print('initializing insta explorer for user ', bot.user_instance.username, 'with login status ',
              bot.login_status)
        self.bot = bot

    def get_username_by_user_id(self, user_id):
        if self.bot.login_status:
            try:
                profile = instaloader.Profile.from_id(self.bot.instaload.context, user_id)
                username = profile.username
                return username
            except:
                print("Except on get_username_by_user_id")
                return False
        else:
            return False

    def get_userinfo_by_name(self, username):
        """ Get user info by name """

        if self.bot.login_status:
            url_info = self.bot.url_user_detail % username
            try:
                r = self.bot.session_1.get(url_info)
                print('request status code', r.status_code)
                try:
                    all_data = json.loads(r.text)
                except Exception as e:
                    print(e, 'Error in loading data\n__________________\n', r.text, '\n\n ++++++++++++++++++', url_info)
                print('all data', all_data)
                user_info = all_data["user"]
                follows = user_info["follows"]["count"]
                follower = user_info["followed_by"]["count"]
                follow_viewer = user_info["follows_viewer"]
                if follower > 3000 or follows > 1500:
                    print(
                        "   >>>This is probably Selebgram, Business or Fake account"
                    )
                if follow_viewer:
                    return None
                return user_info
            except Exception as e:
                print("Except on get_userinfo_by_name ", e)
                return False
        else:
            return False
