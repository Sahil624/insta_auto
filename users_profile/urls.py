from django.urls import path, include
from users_profile.router import router
# from users_profile import views

urlpatterns = [
    path('', include(router.urls))
]
