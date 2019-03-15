import json

from django.core.management import BaseCommand

from handlers.redis_handler import RedisQueue


class Command(BaseCommand):
    help = 'Command for reading bot queue'

    def handle(self, *args, **options):
        print('Starting reading')
        while True:
            queue = RedisQueue('bot_queue')
            q = queue.qsize()
            if q > 0:
                print(json.loads(queue.get()))
