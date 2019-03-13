# chat/routing.py
from django.conf.urls import url
from django.urls import path, include

from bot import consumer, router, views

websocket_urlpatterns = [
    url(r'^ws/logs/(?P<websocket_token>[^/]+)/$', consumer.LogConsumer),
]

urlpatterns = [
    path('sessions/', views.BotSessionsListView.as_view()),
    path('bot/', views.Bot.as_view()),
    path('', include(router.router.urls)),
]
