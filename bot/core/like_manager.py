import datetime
import random
import sys
import time

from django.utils import timezone

from bot.core.utils import add_time
from bot.models import Media


class LikeManager:

    def __init__(self, bot):
        self.bot = bot
        self.bot.logger.info('Initiating Like Manager')

    def remove_already_liked(self):
        self.bot.logger.info("Removing already liked medias..")
        x = 0
        while x < len(self.bot.media_by_tag):
            try:
                Media.objects.get(media_id=self.bot.media_by_tag[x]["node"]["id"])
                self.bot.media_by_tag.remove(self.bot.media_by_tag[x])

            except Media.DoesNotExist:
                x += 1

    def new_auto_mod_like(self):
        if (
                time.time() > self.bot.next_iteration["Like"]
                and self.bot.configurations.likes_per_day != 0
                and len(self.bot.media_by_tag) > 0
        ):
            # You have media_id to like:
            if self.like_all_exist_media(media_size=1, delay=False):
                # If like go to sleep:
                self.bot.next_iteration["Like"] = time.time() + add_time(
                    self.bot.like_delay
                )
                # Count this tag likes:
                self.bot.this_tag_like_count += 1
                if self.bot.this_tag_like_count >= self.bot.max_tag_like_count:
                    self.bot.media_by_tag = [0]
        # Del first media_id
        try:
            del self.bot.media_by_tag[0]
        except:
            self.bot.logger.exception("Could not remove media")
            print("Could not remove media")

    def like_all_exist_media(self, media_size=-1, delay=True):
        """ Like all media ID that have self.media_by_tag """

        if self.bot.login_status:
            if len(self.bot.media_by_tag) != 0:
                i = 0
                for d in self.bot.media_by_tag:
                    if media_size > 0 or media_size < 0:
                        media_size -= 1
                        like_count = self.bot.media_by_tag[i]["node"]["edge_liked_by"]["count"]
                        if (
                                (
                                        like_count <= self.bot.configurations.media_max_like and like_count >= self.bot.configurations.media_min_like)
                                or (
                                self.bot.configurations.media_max_like == 0 and like_count >= self.bot.configurations.media_min_like)
                                or (
                                self.bot.configurations.media_min_like == 0 and like_count <= self.bot.configurations.media_max_like)
                                or (
                                self.bot.configurations.media_min_like == 0 and self.bot.configurations.media_max_like == 0)
                        ):
                            # TODO: Move black list user to models
                            for (
                                    blacklisted_user_name,
                                    blacklisted_user_id,
                            ) in self.bot.user_blacklist.items():
                                if self.bot.media_by_tag[i]["node"]["owner"]["id"] == blacklisted_user_id:
                                    self.bot.logger.warning(
                                        f"Not liking media owned by blacklisted user: {blacklisted_user_name}"
                                    )
                                    return False
                                if self.bot.media_by_tag[i]["node"]["owner"]["id"] == self.bot.user_id:
                                    self.bot.logger.info("Keep calm - It's your own media ;)")
                                return False

                            if self.check_already_liked(media_id=self.bot.media_by_tag[i]["node"]["id"]):
                                self.bot.logger.info("Keep calm - It's already liked ;)")
                                return False

                            try:
                                if len(self.bot.media_by_tag[i]["node"]["edge_media_to_caption"]["edges"]) > 1:
                                    caption = \
                                        self.bot.media_by_tag[i]["node"]["edge_media_to_caption"]["edges"][0]["node"][
                                            "text"].encode("ascii", errors="ignore")
                                    tag_blacklist = set(self.bot.tag_blacklist)
                                    if sys.version_info[0] == 3:
                                        tags = {
                                            str.lower((tag.decode("ASCII")).strip("#"))
                                            for tag in caption.split()
                                            if (tag.decode("ASCII")).startswith("#")
                                        }
                                    else:
                                        tags = {
                                            unicode.lower(
                                                (tag.decode("ASCII")).strip("#")
                                            )
                                            for tag in caption.split()
                                            if (tag.decode("ASCII")).startswith("#")
                                        }
                                    if tags.intersection(tag_blacklist):
                                        matching_tags = ", ".join(
                                            tags.intersection(tag_blacklist)
                                        )
                                        self.bot.logger.warning(
                                            f"Not liking media with blacklisted tag(s): {matching_tags}"
                                        )
                                        return False
                            except Exception as e:
                                self.bot.logger.error("Except on like_all_exist_media")
                                return False

                            log_string = "Trying to like media: %s" % (
                                self.bot.media_by_tag[i]["node"]["id"]
                            )
                            self.bot.logger.info(log_string)

                            like = self.like(self.bot.media_by_tag[i]["node"]["id"])
                            if like != 0:
                                if like.status_code == 200:
                                    # Like, all ok!
                                    self.bot.error_400 = 0
                                    self.bot.like_counter += 1
                                    # TODO: update log counter
                                    log_string = f"Liked: {self.bot.media_by_tag[i]['node']['id']}." \
                                        f"Like #{self.bot.like_counter}."
                                    self.add_media(media_id=self.bot.media_by_tag[i]["node"]["id"], status='200')
                                    self.bot.logger.info(log_string)

                                elif like.status_code == 400:
                                    log_string = f"Not liked: {like.status_code}"
                                    self.bot.logger.warning(log_string)
                                    self.add_media(
                                        media_id=self.bot.media_by_tag[i]["node"]["id"],
                                        status="400",
                                    )
                                    # Some error. If repeated - can be ban!
                                    # TODO: confirm this logic
                                    if self.bot.error_400 >= self.bot.error_400_to_ban:
                                        # Look like you banned!
                                        # TODO: check ban sleep time variable
                                        time.sleep(self.bot.ban_sleep_time)
                                    else:
                                        self.bot.error_400 += 1
                                else:
                                    log_string = f"Not liked: {like.status_code}"
                                    self.add_media(
                                        media_id=self.bot.media_by_tag[i]["node"]["id"],
                                        status=str(like.status_code),
                                    )
                                    self.bot.logger.warning(log_string)
                                    return False
                                    # Some error.
                                i += 1
                                if delay:
                                    time.sleep(
                                        self.bot.like_delay * 0.9
                                        + self.bot.like_delay * 0.2 * random.random()
                                    )
                                else:
                                    self.bot.logger.info("All media liked")
                                    return True
                else:
                    return False

            else:
                self.bot.logger.warning("No media to like!")

    def check_already_liked(self, media_id):
        try:
            media_obj = self.bot.user_instance.liked_media.get(media_id=media_id)
            return media_obj
        except Media.DoesNotExist:
            return False

    def add_media(self, media_id, status):
        try:
            media_obj = Media.objects.create(media_id=media_id, status=status, date_time=timezone.now())
            self.bot.user_instance.liked_media.add(media_obj)
        except Exception as e:
            self.bot.logger.error('Error in creating media object' + media_id)

    def like(self, media_id):
        """ Send http request to like media by ID """
        print("Liking media id", media_id)
        if self.bot.login_status:
            url_likes = self.bot.url_likes % media_id
            try:
                like = self.bot.session_1.post(url_likes)
                last_liked_media_id = media_id
            except:
                self.bot.logger.exception("Except on like!")
                like = 0
            return like

    def new_auto_mod_unlike(self):
        if time.time() > self.bot.next_iteration["Unlike"] and self.bot.unlike_per_day != 0:
            media = self.get_medias_to_unlike()
            if media:
                self.bot.logger.info("Trying to unlike media")
                self.auto_unlike()
                self.bot.next_iteration["Unlike"] = time.time() + add_time(
                    self.bot.unfollow_delay
                )

    def get_medias_to_unlike(self):
        """ Gets random medias that is older than unlike_time"""
        try:
            now_time = datetime.datetime.now()
            cut_off_time = now_time - datetime.timedelta(seconds=self.bot.configurations.time_till_unlike)
            medias = Media.objects.filter(date_time__lt=cut_off_time, status=200)
            if len(medias):
                return medias[0].media_id
            return False

        except Exception as e:
            self.bot.logger.exception("Error in getting media to unlike", str(e))
            return False

    def auto_unlike(self):
        checking = True
        while checking:
            media_to_unlike = self.get_medias_to_unlike()
            if media_to_unlike:
                request = self.unlike(media_to_unlike)
                if request.status_code == 200:
                    self.update_media_complete(media_to_unlike)
                else:
                    self.bot.logger.error("Couldn't unlike media, resuming.")
                    checking = False
            else:
                self.bot.logger.warning("no medias to unlike")
                checking = False

    def unlike(self, media_id):
        """ Send http request to unlike media by ID """
        if self.bot.login_status:
            url_unlike = self.bot.url_unlike % media_id
            try:
                unlike = self.bot.session_1.post(url_unlike)

            except Exception as e:
                self.bot.logger.exception("Except on unlike!", str(e))
                unlike = 0
            return unlike

    def update_media_complete(self,media_id):
        try:
            media = Media.objects.get(media_id=media_id)
            media.status = '201'
            media.save()

        except Media.DoesNotExist:
            self.bot.logger.exception("Exception in updating media with media id"
                                      + media_id+" Does not exist")
