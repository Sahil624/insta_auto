from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email, password=None):
        user = self.model(
            username=username,
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_staffuser(self, email, password):
        user = self.create_user(
            email,
            password=password,
        )
        user.staff = True
        user.save(using=self._db)
        return user

    def create_superuser(self,username, email, password):
        user = self.create_user(
            username,
            email,
            password=password,
        )
        user.staff = True
        user.is_superuser = True
        user.admin = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    name = models.CharField(max_length=100, blank=True, null=True)

    objects = UserManager()
