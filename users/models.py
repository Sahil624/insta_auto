import datetime
import logging
import os

from django.contrib.auth.models import User
from django.db import models


# Create your models here.


class User(User):
    tags = models.ManyToManyField("Tag", blank=True)
    configuration = models.ForeignKey("Configuration",
                                      verbose_name="config",
                                      on_delete=models.CASCADE
                                      )
    liked_media = models.ManyToManyField("bot.Media",
                                         verbose_name="liked_media",
                                         blank=True,
                                         related_name="liked_media")

    followed_users = models.ManyToManyField("bot.InteractedUser",
                                            verbose_name="followed_users",
                                            blank=True)

    commented_media = models.ManyToManyField("bot.Media",
                                             verbose_name="commented_media",
                                             blank=True,
                                             related_name="commented_media")

    blacklisted_users = models.ManyToManyField("bot.BlackListedUser",
                                               verbose_name="blacklisted_user",
                                               blank=True,
                                               related_name="blacklisted_user")

    def get_tag_list(self):
        tag_set = self.tags.all()
        tag_list = []
        for tag in tag_set:
            tag_list.append(tag.tag)
        return tag_list

    def get_user_logger(self):
        try:
            os.makedirs('logs/' + self.username)
        except FileExistsError:
            pass

        file_name = 'logs/' + self.username + '/' + self.username + '-' + str(datetime.date.today()) + '.log'

        """Function setup as many loggers as you want"""
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        handler = logging.FileHandler(filename=file_name)
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        logger = logging.getLogger(self.username + '.logs')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        return logger

    def __str__(self):
        return self.username


class Tag(models.Model):
    tag = models.CharField(max_length=100)

    def __str__(self):
        return '#' + self.tag


class Configuration(models.Model):
    name = models.CharField(max_length=50)
    likes_per_day = models.IntegerField(default=709)
    comments_per_day = models.IntegerField(default=31)
    max_like_for_one_tag = models.IntegerField(default=36)
    follow_per_day = models.IntegerField(default=360)
    follow_time = models.IntegerField(default=3600)
    unfollow_per_day = models.IntegerField(default=297)
    unfollow_break_max = models.IntegerField(default=17)
    unfollow_break_min = models.IntegerField(default=3)
    log_mod = models.IntegerField(default=0)
    unfollow_recent_feed = models.BooleanField(default=True)
    start_time = models.TimeField(blank=True, null=True)
    ends_time = models.TimeField(blank=True, null=True)
    media_max_like = models.IntegerField(default=150)
    media_min_like = models.IntegerField(default=0)
    user_max_follow = models.IntegerField(blank=True, null=True)
    unlike_per_day = models.IntegerField(blank=True, null= True, default=0)
    time_till_unlike = models.IntegerField(default=3 * 24 * 60 * 60)
    user_min_follow = models.IntegerField(blank=True, null=True)
    proxy = models.CharField(max_length=50, default="", blank=True, null=True)

    def __str__(self):
        return self.name


class Session(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_string = models.CharField(max_length=10000)


class InstaAccount(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='insta_account')
    insta_user_id = models.IntegerField(blank=True, null=True)
    last_csrf_token = models.CharField(max_length=1000, blank=True, null=True)

    def __str__(self):
        return self.user.username
