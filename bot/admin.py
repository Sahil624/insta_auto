from django.contrib import admin

# Register your models here.
from bot.models import FakeUA, Media, InteractedUser, BlackListedUser, WhiteListedUser, BotSession

admin.site.register(FakeUA)
admin.site.register(Media)
admin.site.register(InteractedUser)
admin.site.register(BlackListedUser)
admin.site.register(WhiteListedUser)
admin.site.register(BotSession)
