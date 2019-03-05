from django.contrib import admin
from users_profile.models import Tag, UserProfile, Configuration, WebSocketToken

# Register your models here.
admin.site.register(Tag)
admin.site.register(UserProfile)
admin.site.register(Configuration)
admin.site.register(WebSocketToken)
