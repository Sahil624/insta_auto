import itertools
import json
import random
import re
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from bot.consts import COMMENT_LIST
from bot.core.utils import add_time
from bot.models import Media


class CommentManager:

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.logger
        self.logger.info("Initializing comment manager")

    def new_auto_mod_comments(self):
        if (
                time.time() > self.bot.next_iteration["Comments"]
                and self.bot.configurations.comments_per_day != 0
                and len(self.bot.media_by_tag) > 0
                and self.check_exisiting_comment(self.bot.media_by_tag[0]["node"]["shortcode"])
                is False
        ):
            comment_text = self.generate_comment()
            log_string = f"Trying to comment: {self.bot.media_by_tag[0]['node']['id']}"
            self.logger.info(log_string)
            if (
                    self.comment(self.bot.media_by_tag[0]["node"]["id"], comment_text)
                    is not False
            ):
                self.bot.next_iteration["Comments"] = time.time() + add_time(
                    self.bot.comments_delay
                )

    def check_exisiting_comment(self, media_code):
        url_check = self.bot.url_media % media_code
        try:
            check_comment = self.bot.session_1.get(url_check)
            if check_comment.status_code == 200:

                if "dialog-404" in check_comment.text:
                    log = (
                        f"Tried to comment {media_code} but it doesn't exist (404). Resuming..."
                    )
                    self.logger.error(log)
                    self.send_to_socket(log)

                    del self.bot.media_by_tag[0]
                    return True

                all_data = json.loads(
                    re.search(
                        "window._sharedData = (.*?);", check_comment.text, re.DOTALL
                    ).group(1)
                )["entry_data"]["PostPage"][
                    0
                ]  # window._sharedData = (.*?);
                if (
                        all_data["graphql"]["shortcode_media"]["owner"]["id"]
                        == self.bot.user_id
                ):
                    log = "Keep calm - It's your own media ;)"
                    self.logger.info(log)
                    self.send_to_socket(log)
                    # Del media to don't loop on it
                    del self.bot.media_by_tag[0]
                    return True
                try:
                    comment_list = list(
                        all_data["graphql"]["shortcode_media"]["edge_media_to_comment"][
                            "edges"
                        ]
                    )
                except:
                    comment_list = list(
                        all_data["graphql"]["shortcode_media"][
                            "edge_media_to_parent_comment"
                        ]["edges"]
                    )

                for d in comment_list:
                    if d["node"]["owner"]["id"] == self.bot.user_id:
                        log = "Keep calm - Media already commented ;)"
                        self.logger.info(log)
                        self.send_to_socket(log)
                        # Del media to don't loop on it
                        del self.bot.media_by_tag[0]
                        return True
                return False
            elif check_comment.status_code == 404:
                self.bot.media_manager(
                    self,
                    self.bot.media_by_tag[0]["node"]["id"],
                    str(check_comment.status_code),
                )
                log = f"Tried to comment {media_code} but it doesn't exist (404). Resuming..."
                self.logger.warning(log)
                self.send_to_socket(log)

                del self.bot.media_by_tag[0]
                return True
            else:
                self.add_media(
                    self.bot.media_by_tag[0]["node"]["id"],
                    str(check_comment.status_code),
                )
                self.bot.media_by_tag.remove(self.bot.media_by_tag[0])
                return True
        except:
            log = "Couldn't comment post, resuming."
            self.logger.warning(log)
            self.send_to_socket(log)
            del self.bot.media_by_tag[0]
            return True

    def send_to_socket(self, message):
        layer = get_channel_layer()
        async_to_sync(layer.group_send)('log_' + self.bot.user_instance.username,
                                        {
                                            'type': 'log_message',
                                            'message': message
                                        })

    def add_media(self, media_id, status):
        try:

            try:
                url = self.bot.media_manager.get_instagram_url_from_media_id(media_id)
            except:
                url = None

            try:
                username = self.bot.media_manager.get_username_by_media_id(media_id)
            except:
                username = None

            media_obj, created = Media.objects.get_or_create(media_id=media_id, status=status, date_time=timezone.now(),
                                                             url=url, media_owner=username)
            if status is '200':
                self.bot.user_instance.commented_media.add(media_obj)
        except Exception as e:
            self.bot.logger.error('Error in creating media object' + media_id)

    def generate_comment(self):
        c_list = list(itertools.product(*COMMENT_LIST))

        repl = [("  ", " "), (" .", "."), (" !", "!")]
        res = " ".join(random.choice(c_list))
        for s, r in repl:
            res = res.replace(s, r)
        return res.capitalize()

    def comment(self, media_id, comment_text):
        """ Send http request to comment """
        if self.bot.login_status:

            comment_post = {"comment_text": comment_text}
            url_comment = self.bot.url_comment % media_id
            try:
                comment = self.bot.session_1.post(url_comment, data=comment_post)
                if comment.status_code == 200:

                    try:
                        url = self.bot.media_manager.get_instagram_url_from_media_id(media_id)
                    except:
                        url = None

                    try:
                        owner = self.bot.media_manager.get_username_by_media_id(media_id=media_id)
                    except:
                        owner = None

                    self.bot.comments_counter += 1
                    try:
                        self.bot.bot_session.comments_counter += 1
                        self.bot.bot_session.save()
                    except Exception as e:
                        self.logger.exception("Exception in updating comments counter in session " + str(e))
                    log_string = f"Write: {comment_text}. #{self.bot.comments_counter}."
                    try:

                        media_obj = Media.objects.get(media_id=media_id)
                        media_obj.comment = comment_text
                        media_obj.url = url
                        media_obj.media_owner = owner
                        media_obj.save()

                        self.bot.user_instance.commented_media.add(media_obj)

                    except Media.DoesNotExist:
                        try:
                            media_obj = Media.objects.create(media_id=media_id, status=200, date_time=timezone.now(),
                                                             comment=comment_text, url=url, media_owner=owner)
                            self.bot.user_instance.commented_media.add(media_obj)
                        except Exception as e:
                            self.logger.exception('Exception in creating media' + str(e))

                    except Exception as e:
                        self.logger.exception('Exception in adding comment to media obj', str(e))

                    self.logger.info(log_string)
                    self.send_to_socket(log_string)
                return comment
            except:
                self.logger.exception("Except on comment!")
        return False
