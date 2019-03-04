from rest_framework import routers

from bot.views import InteractedUsersViewSet

router = routers.DefaultRouter()

router.register('interacted_users', InteractedUsersViewSet)
