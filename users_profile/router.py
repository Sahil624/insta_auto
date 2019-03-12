from rest_framework import routers

from users_profile import views

router = routers.DefaultRouter()
router.register('profiles', views.UserProfileViewSet, base_name='user_profile')
router.register(r'configurations', views.ConfigurationView, base_name='configurations')
