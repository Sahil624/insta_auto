from multiprocessing import Process

from django.core.management.commands.runserver import Command

from bot.handler import BotHandler


class Command(Command):
    def handle(self, *args, **options):
        print("Starting Bot Manager")
        BotHandler().read_queue()
