from django.contrib import admin

# Register your models here.
from bot.models import FakeUA, Media, InteractedUser

admin.site.register(FakeUA)
admin.site.register(Media)
admin.site.register(InteractedUser)
