import datetime
import json
import random
import re
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from bot.core.utils import add_time
from bot.models import InteractedUser


class UnfollowManager:

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger

    def new_auto_mod_unfollow(self, test_run=False):
        if time.time() > self.bot.next_iteration["Unfollow"] and self.bot.configurations.unfollow_per_day != 0:
            if (time.time() - self.bot.bot_start_time) < 30 and not test_run:
                log = "let bot initialize"
                self.logger.warning(log)
                self.send_to_socket(log)
                return
            if InteractedUser.objects.all().count() < 20:
                log = (
                    f"> Waiting for database to populate before unfollowing (progress "
                    f"{str(InteractedUser.objects.all().count())} /20)"
                )
                self.logger.info(log)
                self.send_to_socket(log)

                if self.bot.configurations.unfollow_recent_feed is True:
                    log = "Will try to populate using recent feed"
                    self.logger.info(log)
                    self.send_to_socket(log)
                    self.populate_from_feed()

                self.bot.next_iteration["Unfollow"] = time.time() + (
                        add_time(self.bot.unfollow_delay) / 2
                )
                return  # DB doesn't have enough followers yet

            if self.bot.bot_mode == 0 or self.bot.bot_mode == 3:

                try:
                    if (
                            time.time() > self.bot.next_iteration["Populate"]
                            and self.bot.unfollow_recent_feed is True
                    ):
                        self.populate_from_feed()
                        self.bot.next_iteration["Populate"] = time.time() + (
                            add_time(360)
                        )
                except:
                    log = "Notice: Could not populate from recent feed right now"
                    self.logger.warning(log)
                    self.send_to_socket(log)

                log_string = f"Trying to unfollow #{self.bot.unfollow_counter + 1}:"
                self.logger.info(log_string)
                self.auto_unfollow()
                self.bot.next_iteration["Unfollow"] = time.time() + add_time(
                    self.bot.unfollow_delay
                )

    def populate_from_feed(self):
        self.get_media_id_recent_feed()

        try:
            for mediafeed_user in self.bot.media_on_feed:
                feed_username = mediafeed_user["node"]["owner"]["username"]
                feed_user_id = mediafeed_user["node"]["owner"]["id"]
                if self.check_if_userid_exists(userid=feed_user_id) is False:
                    self.bot.media_manager.add_user(self, user_id=feed_user_id, username=feed_username)
                    log = f"Inserted user {feed_username} from recent feed"
                    self.logger.info(log)
                    self.send_to_socket(log)
        except:
            log = "Notice: could not populate from recent feed"
            self.logger.warning(log)
            self.send_to_socket(log)

    def get_media_id_recent_feed(self):
        if self.bot.login_status:
            now_time = datetime.datetime.now()
            log_string = f"{self.bot.user_login} : Get media id on recent feed"
            self.logger.info(log_string)
            self.send_to_socket(log_string)
            if self.bot.login_status == 1:
                url_tag = "https://www.instagram.com/"
                try:
                    r = self.bot.session_1.get(url_tag)

                    jsondata = re.search(
                        "additionalDataLoaded\('feed',({.*})\);", r.text
                    ).group(1)
                    all_data = json.loads(jsondata.strip())

                    self.bot.media_on_feed = list(
                        all_data["user"]["edge_web_feed_timeline"]["edges"]
                    )

                    log_string = f"Media in recent feed = {len(self.bot.media_on_feed)}"
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)

                except:
                    self.logger.exception("get_media_id_recent_feed")
                    self.bot.media_on_feed = []
                    time.sleep(20)
                    return 0
            else:
                return 0

    def auto_unfollow(self):
        checking = True
        while checking:
            username_row = self.get_username_to_unfollow_random()
            if not username_row:
                log = "Looks like there is nobody to unfollow."
                self.logger.warning(log)
                self.send_to_socket(log)
                return False

            current_id = username_row.user_id
            current_user = username_row.user_name
            unfollow_count = username_row.unfollow_count

            if not current_user:
                current_user = self.bot.insta_explorer.get_username_by_user_id(user_id=current_id)
            if not current_user:
                log_string = "api limit reached from instagram. Will try later"
                self.logger.error(log_string)
                self.send_to_socket(log_string)
                return False

            for wluser in self.bot.unfollow_whitelist:
                if wluser == current_user:
                    log_string = "found whitelist user, starting search again"
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                    break

            else:
                checking = False

        if self.bot.login_status:
            log_string = f"Getting user info : {current_user}"
            self.logger.info(log_string)
            if self.bot.login_status == 1:
                url_tag = self.bot.url_user_detail % current_user
                try:
                    r = self.bot.session_1.get(url_tag)
                    if (
                            r.text.find(
                                "The link you followed may be broken, or the page may have been removed."
                            )
                            != -1
                    ):
                        log_string = (
                            f"Looks like account was deleted, skipping : {current_user}"
                        )
                        self.logger.error(log_string)
                        self.send_to_socket(log_string)
                        self.update_unfollow_count(user_id=current_id)
                        time.sleep(3)
                        return False

                    all_data = json.loads(
                        re.search(
                            "window._sharedData = (.*?);</script>", r.text, re.DOTALL
                        ).group(1)
                    )["entry_data"]["ProfilePage"][0]

                    user_info = all_data["graphql"]["user"]
                    i = 0
                    log_string = "Checking user info.."
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)

                    follows = user_info["edge_follow"]["count"]
                    follower = user_info["edge_followed_by"]["count"]
                    media = user_info["edge_owner_to_timeline_media"]["count"]
                    follow_viewer = user_info["follows_viewer"]
                    followed_by_viewer = user_info["followed_by_viewer"]
                    requested_by_viewer = user_info["requested_by_viewer"]
                    has_requested_viewer = user_info["has_requested_viewer"]

                    log_string = f"Follower : {follower}"
                    self.send_to_socket(log_string)
                    self.logger.info(log_string)

                    log_string = f"Following : {follows}"
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)

                    log_string = f"Media : {media}"
                    self.send_to_socket(log_string)
                    self.logger.info(log_string)

                    if follows == 0 or follower / follows > 2:
                        self.is_selebgram = True
                        self.is_fake_account = False
                        log = "   >>>This is probably Selebgram account"
                        self.logger.warning(log)
                        self.send_to_socket(log)

                    elif follower == 0 or follows / follower > 2:
                        self.is_fake_account = True
                        self.is_selebgram = False
                        log = "   >>>This is probably Fake account"
                        self.logger.warning(log)
                        self.send_to_socket(log)
                    else:
                        self.is_selebgram = False
                        self.is_fake_account = False
                        log = "   >>>This is a normal account"
                        self.logger.info(log)
                        self.send_to_socket(log)

                    if media > 0 and follows / media < 25 and follower / media < 25:
                        self.is_active_user = True
                        log = "   >>>This user is active"
                        self.logger.info(log)
                        self.send_to_socket(log)
                    else:
                        self.is_active_user = False
                        log = "   >>>This user is passive"
                        self.send_to_socket(log)
                        self.logger.info(log)

                    if follow_viewer or has_requested_viewer:
                        self.is_follower = True
                        log = "   >>>This account is following you"
                        self.logger.info(log)
                        self.send_to_socket(log)
                    else:
                        self.is_follower = False
                        log = "   >>>This account is NOT following you"
                        self.logger.info(log)
                        self.send_to_socket(log)

                    if followed_by_viewer or requested_by_viewer:
                        self.is_following = True
                        log = "   >>>You are following this account"
                        self.logger.info(log)
                        self.send_to_socket(log)

                    else:
                        self.is_following = False
                        log = "   >>>You are NOT following this account"
                        self.logger.info(log)
                        self.send_to_socket(log)

                except Exception as e:
                    self.logger.exception("Except on auto_unfollow!" + str(e))
                    time.sleep(3)
                    return False
            else:
                return False

            if (
                    self.is_selebgram is not False
                    or self.is_fake_account is not False
                    or self.is_active_user is not True
                    or self.is_follower is not True
            ):
                self.logger.info(current_user)
                self.unfollow(current_id)
                # don't insert unfollow count as it is done now inside unfollow()
                # insert_unfollow_count(self, user_id=current_id)
            elif self.is_following is not True:
                # we are not following this account, hence we unfollowed it, let's keep track
                self.update_unfollow_count(user_id=current_id)

    def unfollow(self, user_id):
        """ Send http request to unfollow """
        if self.bot.login_status:
            url_unfollow = self.bot.url_unfollow % user_id
            try:
                unfollow = self.bot.session_1.post(url_unfollow)
                if unfollow.status_code == 200:
                    self.bot.unfollow_counter += 1
                    log_string = f"Unfollowed: {user_id} #{self.bot.unfollow_counter}."
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                    self.update_unfollow_count(user_id=user_id)
                return unfollow
            except Exception as e:
                self.logger.exception("Exept on unfollow!" + str(e))
                self.send_to_socket("Exept on unfollow!")
        return False

    def check_if_userid_exists(self, userid):
        try:
            user_obj = InteractedUser.objects.get(user_id=userid)
            return user_obj
        except InteractedUser.DoesNotExist:
            return False

    def update_unfollow_count(self, user_id=None, user_name=None):
        if user_id:
            try:
                user_obj = InteractedUser.objects.get(user_id=user_id)
                user_obj.unfollow_count += 1
                user_obj.save()
            except InteractedUser.DoesNotExist:
                pass

        elif user_name:
            try:
                user_obj = InteractedUser.objects.get(user_name=user_name)
                user_obj += 1
                user_obj.save()
            except InteractedUser.DoesNotExist:
                pass

        else:
            return False

        return False

    def get_username_to_unfollow_random(self):
        """ Gets random username that is older than follow_time and has zero unfollow_count """
        now_time = timezone.now()
        cut_off_time = now_time - timezone.timedelta(seconds=self.bot.configurations.follow_time)
        users = InteractedUser.objects.filter(last_followed_time__lte=cut_off_time, unfollow_count=0)

        if len(users):
            return users[random.randint(0, len(users))]

        return None

    def check_already_unfollowed(self, user_id):
        try:
            obj = InteractedUser.objects.get(user_id=user_id)
            if obj.unfollow_count > 0:
                return True
            return False
        except InteractedUser.DoesNotExist:
            return False

    def send_to_socket(self, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_' + self.bot.user_instance.username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })
