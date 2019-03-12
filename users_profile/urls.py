from django.urls import path, include
from users_profile import views
from users_profile import router

urlpatterns = [
    path('', include(router.router.urls))
]
