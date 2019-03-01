from django.db import models

# Create your models here.
from users.models import User


class FakeUA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
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

    def __str__(self):
        return self.media_id


class InteractedUser(models.Model):
    user_id = models.IntegerField()
    user_name = models.CharField(max_length=500)
    unfollow_count = models.IntegerField(default=0)
    last_followed_time = models.DateTimeField()

    def __str__(self):
        return self.user_name


class BlackListedUser(models.Model):
    username = models.CharField(max_length=300)

    def __str__(self):
        return self.username
