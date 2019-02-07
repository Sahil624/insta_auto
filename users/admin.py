from django.contrib import admin
from users.models import Tag, User,Configuration

# Register your models here.
admin.site.register(Tag)
admin.site.register(User)
admin.site.register(Configuration)