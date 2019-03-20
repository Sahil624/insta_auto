from django.contrib.auth.models import User
from django.db import models
from users_profile.models import UserProfile


class FakeUA(models.Model):
    user = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    fake_user_agent = models.CharField(max_length=200)

    def __str__(self):
        return self.fake_user_agent


class Media(models.Model):
    media_id = models.CharField(max_length=300)
    status = models.IntegerField()
    date_time = models.DateTimeField()
    code = models.CharField(max_length=100)
    url = models.URLField(blank=True, null=True)
    media_owner = models.CharField(max_length=300, blank=True, null=True)
    comment = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        ordering = ['-date_time']

    def __str__(self):
        show_string = self.media_id
        if self.media_owner:
            show_string = self.media_owner + " | " + self.media_id[-8:]
        return show_string


class InteractedUser(models.Model):
    user_id = models.BigIntegerField()
    user_name = models.CharField(max_length=500)
    unfollow_count = models.IntegerField(default=0)
    last_followed_time = models.DateTimeField()

    class Meta:
        ordering = ['-pk']

    def __str__(self):
        return self.user_name


class BlackListedUser(models.Model):
    username = models.CharField(max_length=300)

    def __str__(self):
        return self.username


class WhiteListedUser(models.Model):
    username = models.CharField(max_length=300)

    def __str__(self):
        return self.username


class BotSession(models.Model):
    user = models.ForeignKey(UserProfile,
                             related_name='session_user',
                             related_query_name='session_user',
                             on_delete=models.CASCADE)
    bot_creation_time = models.DateTimeField(auto_now_add=True)
    unfollow_counter = models.IntegerField(default=0)
    follow_counter = models.IntegerField(default=0)
    like_counter = models.IntegerField(default=0)
    comments_counter = models.IntegerField(default=0)
    bot_start_time = models.DateTimeField(blank=True, null=True)
    bot_stop_time = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-bot_creation_time']

    def __str__(self):
        return self.user.username + " | " + str(self.bot_creation_time)
