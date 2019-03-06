from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from accounts import views

urlpatterns = [
    path('login/', obtain_auth_token),
    path('register/', views.Account().as_view()),
    path('logout/', views.Logout().as_view())
]
