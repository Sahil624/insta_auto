from django.urls import path, include
from users.router import router
# from users import views
from rest_framework.authtoken import views

urlpatterns = [
    path(r'login/', views.obtain_auth_token),
    path('', include(router.urls))
]
