from bot.models import Media


class LikeManager:

    def __init__(self, bot):
        self.bot = bot
        self.bot.logger.info('Initiating Like Manager')

    def remove_already_liked(self):
        self.bot.logger.info("Removing already liked medias..")
        x = 0
        while x < len(self.bot.media_by_tag):
            try:
                Media.objects.get(media_id=self.bot.media_by_tag[x]["node"]["id"])
                self.bot.media_by_tag.remove(self.bot.media_by_tag[x])

            except Media.DoesNotExist:
                x += 1
