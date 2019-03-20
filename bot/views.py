import json

from rest_framework import status, views
from rest_framework.response import Response
from bot import models, seralizers
from handlers.redis_handler import RedisQueue
from users_profile.models import UserProfile


class BotSessionsListView(views.APIView):

    def get(self, request):
        try:
            try:
                id = request.GET['id']
                page_size = int(request.GET.get('page_size', 5))
                page_number = int(request.GET.get('page_number', 1))
                user_profile = UserProfile.objects.get(id=id, user=request.user)
                objects = models.BotSession.objects.filter(user=user_profile)
                count = objects.count()
                objects = objects[(page_number * page_size) - page_size:page_number * page_size]
                serializer_obj = seralizers.BotSessionSerializer(objects, many=True)
                return Response(data=dict(page_number=page_number, page_size=page_size, total_count=count,
                                          data=serializer_obj.data), status=status.HTTP_200_OK)

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
                profile = UserProfile.objects.get(id=id, user=request.user)

                try:
                    RedisQueue('bot_queue').put(
                        json.dumps(dict(command='START', username=profile.username, password=password)))

                    return Response(data=dict(message="Bot created"), status=status.HTTP_200_OK)

                except Exception as e:
                    print('Bot create exception', e)

            except UserProfile.DoesNotExist:
                return Response(data=dict(error="Invalid Profile"), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            try:
                id = request.data['id']
                profile = UserProfile.objects.get(id=id, user=request.user)
                password = request.data['password']

                try:
                    RedisQueue('bot_queue').put(
                        json.dumps(dict(command='STOP', username=profile.username, password=password)))

                    return Response(data=dict(message="Bot created"), status=status.HTTP_200_OK)

                except Exception as e:
                    print('Bot Stop exception', e)

            except UserProfile.DoesNotExist:
                return Response(data=dict(error="Request sent"), status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
