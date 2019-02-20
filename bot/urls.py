# chat/routing.py
from django.conf.urls import url

from bot import consumer

websocket_urlpatterns = [
    url(r'^ws/logs/(?P<username>[^/]+)/$', consumer.LogConsumer),
]
