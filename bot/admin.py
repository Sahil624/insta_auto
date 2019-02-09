from django.contrib import admin

# Register your models here.
from bot.models import FakeUA, Media

admin.site.register(FakeUA)
admin.site.register(Media)
