import json
import random
import re
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from instaloader import instaloader


class Explorer:

    def __init__(self, bot):
        bot.logger.info(
            'initializing insta explorer for user ' + bot.user_instance.username + 'with login status ' + str(
                bot.login_status)
        )
        self.bot = bot

    def get_username_by_user_id(self, user_id):
        if self.bot.login_status:
            try:
                profile = instaloader.Profile.from_id(self.bot.instaloader.context, user_id)
                username = profile.username
                return username
            except Exception as e:
                self.bot.logger.warning("Except on get_username_by_user_id" + user_id + str(e))
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
                    self.bot.logger.error('Error in loading data in get_userinfo_by_name' + str(e))
                    return
                user_info = all_data["user"]
                follows = user_info["follows"]["count"]
                follower = user_info["followed_by"]["count"]
                follow_viewer = user_info["follows_viewer"]
                if follower > 3000 or follows > 1500:
                    self.bot.logger.warning('This is probably Selebgram, Business or Fake account :- ' + username)
                    print(
                        "   >>>This is probably Selebgram, Business or Fake account"
                    )
                    self.send_to_socket('This is probably Selebgram, Business or Fake account :- ' + username)
                if follow_viewer:
                    return None
                return user_info
            except Exception as e:
                print("Except on get_userinfo_by_name ", e)
                self.bot.logger.error('Except on get_userinfo_by_name' + username + ' Error - ' + str(e))
                return False
        else:
            return False

    def get_user_info(self, username):
        current_user = username
        log_string = "Getting user info : %s" % current_user
        self.bot.logger.debug(log_string)
        if self.bot.login_status == 1:
            url_tag = self.bot.url_user_detail % current_user
            if self.bot.login_status == 1:
                r = self.bot.session_1.get(url_tag)
                if (
                        r.text.find(
                            "The link you followed may be broken, or the page may have been removed."
                        )
                        != -1
                ):
                    log_string = (
                            "Looks like account was deleted, skipping : %s" % current_user
                    )
                    self.bot.logger.error("Looks like account was deleted, skipping : %s" % current_user)
                    self.send_to_socket()
                    # insert_unfollow_count(self, user_id=current_id)
                    time.sleep(3)
                    return False
                all_data = json.loads(
                    re.search(
                        "window._sharedData = (.*?);</script>", r.text, re.DOTALL
                    ).group(1)
                )["entry_data"]["ProfilePage"][0]

                user_info = all_data["graphql"]["user"]
                self.bot.current_user_info = user_info
                log_string = "Checking user info.."
                self.bot.logger.info(log_string)
                self.send_to_socket(log_string)

                follows = user_info["edge_follow"]["count"]
                follower = user_info["edge_followed_by"]["count"]
                media = user_info["edge_owner_to_timeline_media"]["count"]
                follow_viewer = user_info["follows_viewer"]
                followed_by_viewer = user_info["followed_by_viewer"]
                requested_by_viewer = user_info["requested_by_viewer"]
                has_requested_viewer = user_info["has_requested_viewer"]
                log_string = "Follower : %i" % follower
                self.bot.logger.info(log_string)
                self.send_to_socket(log_string)
                log_string = "Following : %s" % follows
                self.bot.logger.info(log_string)
                self.send_to_socket(log_string)
                log_string = "Media : %i" % media
                self.bot.logger.info(log_string)
                self.send_to_socket(log_string)
                if follows == 0 or follower / follows > 2:
                    self.is_selebgram = True
                    self.is_fake_account = False
                    self.bot.logger.warning("   >>>This is probably Selebgram account")
                    self.send_to_socket("   >>>This is probably Selebgram account")
                elif follower == 0 or follows / follower > 2:
                    self.is_fake_account = True
                    self.is_selebgram = False
                    self.bot.logger.warning("   >>>This is probably Fake account")
                    self.send_to_socket("   >>>This is probably Fake account")
                else:
                    self.is_selebgram = False
                    self.is_fake_account = False
                    self.bot.logger.info("   >>>This is a normal account")
                    self.send_to_socket("   >>>This is a normal account")

                if media > 0 and follows / media < 25 and follower / media < 25:
                    self.is_active_user = True
                    self.bot.logger.info("   >>>This user is active")
                    self.send_to_socket("   >>>This user is active")
                else:
                    self.is_active_user = False
                    self.bot.logger.info("   >>>This user is passive")
                    self.send_to_socket("   >>>This user is passive")

                if follow_viewer or has_requested_viewer:
                    self.is_follower = True
                    self.send_to_socket("   >>>This account is following you")
                    self.bot.logger.info("   >>>This account is following you")
                else:
                    self.is_follower = False
                    self.bot.logger.info("   >>>This account is NOT following you")
                    self.send_to_socket("   >>>This account is NOT following you")

                if followed_by_viewer or requested_by_viewer:
                    self.is_following = True
                    self.bot.logger.info("   >>>You are following this account")
                    self.send_to_socket("   >>>You are following this account")

                else:
                    self.is_following = False
                    self.bot.logger.info("   >>>You are NOT following this account")
                    self.send_to_socket("   >>>You are NOT following this account")

            else:
                self.bot.logger.error("Except on auto_unfollow!")
                time.sleep(3)
                return False
        else:
            return 0

    def populate_user_blacklist(self):
        for user in self.bot.user_blacklist:
            user_id_url = self.bot.url_user_detail % user
            info = self.bot.session_1.get(user_id_url)
            # cevent error if 'Account of user was deleted or link is invalid
            from json import JSONDecodeError

            try:
                all_data = json.loads(
                    re.search(
                        "window._sharedData = (.*?);</script>", info.text, re.DOTALL
                    ).group(1)
                )
            except JSONDecodeError as e:
                log = (
                    f"Account of user {user} was deleted or link is " "invalid"
                )
                self.bot.logger.info(log)
                self.send_to_socket(log)

            except Exception as e:
                log = f"Failed to load user_id for {user}"
                self.bot.logger.exception(log)
                self.send_to_socket(log)

            else:
                # prevent exception if user have no media
                id_user = all_data["entry_data"]["ProfilePage"][0]["graphql"]["user"][
                    "id"
                ]
                # Update the user_name with the user_id
                self.bot.user_blacklist[user] = id_user
                log = f"Blacklisted user {user} added with ID: {id_user}"
                self.bot.logger.info(log)
                self.send_to_socket(log)
                time.sleep(5 * random.random())

    def send_to_socket(self, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_' + self.bot.user_instance.username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })
