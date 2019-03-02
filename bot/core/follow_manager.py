import datetime
import re
import time

import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from bot.core.utils import add_time
from bot.models import InteractedUser


class FollowManager:

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        bot.logger.info("Initalizing Follow manager")

    def new_auto_mod_follow(self):
        username = None
        if time.time() < self.bot.next_iteration["Follow"]:
            return
        if (
                time.time() > self.bot.next_iteration["Follow"]
                and self.bot.configurations.follow_per_day != 0
                and len(self.bot.media_by_tag) > 0
        ):
            if self.bot.media_by_tag[0]["node"]["owner"]["id"] == self.bot.user_id:
                self.logger.warning("Keep calm - It's your own profile ;)")
                self.send_to_socket("Keep calm - It's your own profile ;)")
                return

            if self.bot.configurations.user_min_follow != 0 or self.bot.configurations.user_max_follow != 0:
                try:
                    username = self.bot.insta_explorer.get_username_by_user_id(
                        self.bot.media_by_tag[0]["node"]["owner"]["id"]
                    )
                    url = self.bot.url_user_detail % username
                    r = self.bot.session_1.get(url)
                    all_data = json.loads(
                        re.search(
                            "window._sharedData = (.*?);</script>", r.text, re.DOTALL
                        ).group(1)
                    )
                    followers = all_data["entry_data"]["ProfilePage"][0]["graphql"][
                        "user"
                    ]["edge_followed_by"]["count"]

                    if followers < self.bot.configurations.user_min_follow:
                        self.logger.warning(
                            f"Won't follow {username}: does not meet user_min_follow requirement"
                        )
                        return

                    if self.bot.configurations.user_max_follow != 0 and followers > self.bot.configurations.user_max_follow:
                        self.logger.warning(
                            f"Won't follow {username}: does not meet user_max_follow requirement"
                        )
                        self.send_to_socket(f"Won't follow {username}: does not meet user_max_follow requirement")
                        return

                except Exception:
                    pass
            if (
                    self.check_already_followed(
                        user_id=self.bot.media_by_tag[0]["node"]["owner"]["id"]
                    )
                    == 1
            ):
                self.logger.warning(
                    f"Already followed before {self.bot.media_by_tag[0]['node']['owner']['id']}"
                )
                self.send_to_socket(f"Already followed before {self.bot.media_by_tag[0]['node']['owner']['id']}")
                self.bot.next_iteration["Follow"] = time.time() + add_time(
                    self.bot.follow_delay / 2
                )
                return

            log_string = (
                f"Trying to follow: {self.bot.media_by_tag[0]['node']['owner']['id']}"
            )
            self.logger.info(log_string)
            self.send_to_socket(log_string)
            self.bot.next_iteration["Follow"] = time.time() + add_time(
                self.bot.follow_delay
            )

            if (
                    self.follow(
                        user_id=self.bot.media_by_tag[0]["node"]["owner"]["id"],
                        username=username,
                    )
                    is not False
            ):
                self.bot.bot_follow_list.append(
                    [self.bot.media_by_tag[0]["node"]["owner"]["id"], time.time()]
                )
                self.bot.next_iteration["Follow"] = time.time() + add_time(
                    self.bot.follow_delay
                )

    def check_already_followed(self, user_id):
        """ controls if user already followed before """
        try:
            self.bot.user_instance.followed_users.get(user_id=user_id)
            return 1
        except InteractedUser.DoesNotExist:
            return 0

    def follow(self, user_id, username=None):
        """ Send http request to follow """
        if self.bot.login_status:
            url_follow = self.bot.url_follow % user_id
            if username is None:
                username = self.bot.insta_explorer.get_username_by_user_id(user_id=user_id)
            try:
                follow = self.bot.session_1.post(url_follow)
                if follow.status_code == 200 and username:
                    self.bot.follow_counter += 1
                    self.bot.follow_counter += 1
                    try:
                        self.bot.bot_session.follow_counter += 1
                        self.bot.bot_session.save()
                    except Exception as e:
                        self.logger.exception('Exception in updating follow counter' + str(e))
                    log_string = f"Followed: {user_id} #{self.bot.follow_counter}."
                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                    self.add_user(user_id=user_id, username=username)
                return follow
            except Exception as e:
                self.logger.exception("Except on follow!" + str(e))
        return False

    def add_user(self, user_id, username):
        """ insert user_id to usernames """
        try:
            now = timezone.now()
            user = InteractedUser.objects.create(user_id=user_id, user_name=username, last_followed_time=now)
            self.bot.user_instance.followed_users.add(user)

        except Exception as e:
            self.logger.exception("Exception in adding interacted user" + str(e))

    def send_to_socket(self, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_' + self.bot.user_instance.username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })
