from django.urls import path, include
from users_profile import views
from users_profile import router

urlpatterns = [
    path('websocketToken/', views.WebSocketTokenView.as_view()),
    path('liked_media/', views.LikedMediaListView.as_view()),
    path('commented_media/', views.CommentsListView.as_view()),
    path('followed_users/', views.FollowedUsers.as_view()),
    path('', include(router.router.urls))
]
