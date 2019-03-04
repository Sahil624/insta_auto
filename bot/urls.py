# chat/routing.py
from django.conf.urls import url
from django.urls import path, include

from bot import consumer, router

websocket_urlpatterns = [
    url(r'^ws/logs/(?P<websocket_token>[^/]+)/$', consumer.LogConsumer),
]

urlpatterns = [
    path('', include(router.router.urls)),
]
