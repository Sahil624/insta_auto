from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = 'Command for reading socket queue'

    def handle(self, *args, **options):
        layer = get_channel_layer()
        print('sending message')
        async_to_sync(layer.group_send)('chat_test',
                                        {
                                            'type': 'log_message',
                                            'message': 'Hello world'
                                        })
