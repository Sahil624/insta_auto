from rest_framework import viewsets, status, views
from rest_framework.response import Response
import threading
from bot.core.bot_service import InstagramBot

from bot import models, seralizers
from users_profile.models import UserProfile


class BotSessionsListView(views.APIView):

    def get(self, request):
        try:
            try:
                id = request.GET['id']
                user_profile = UserProfile.objects.get(id=id, user=request.user)
                objects = models.BotSession.objects.filter(user=user_profile)
                serializer_obj = seralizers.BotSessionSerializer(objects, many=True)
                return Response(data=dict(data=serializer_obj.data), status=status.HTTP_200_OK)

            except UserProfile.DoesNotExist:
                return Response(data=dict(error="Invalid Profile"), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Bot(views.APIView):

    def post(self, request):
        try:
            try:
                id = request.data['id']
                password = request.data['password']
                profile = UserProfile.objects.get(id=id)

                try:
                    bot = InstagramBot(profile.username, password)

                    if bot.login_status:
                        print('logged in thread')
                        thread = threading.Thread(target=bot.run_bot())
                        thread.daemon = True
                        thread.start()

                    else:
                        print('not logged')

                except Exception as e:
                    print('Bot create exception', e)

            except UserProfile.DoesNotExist:
                return Response(data=dict(error="Invalid Profile"), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
