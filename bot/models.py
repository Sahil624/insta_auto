from django.db import models

# Create your models here.
from users.models import User


class FakeUA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fake_user_agent = models.CharField(max_length=200)

    def __str__(self):
        return self.fake_user_agent
