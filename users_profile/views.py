from rest_framework import views, status, viewsets
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

from bot.seralizers import MediaSerializer, InteractedUserSerializer
from users_profile import models
from users_profile import serializer


class UserProfileViewSet(viewsets.ModelViewSet):
    serializer_class = serializer.UserProfileSerializer
    queryset = models.UserProfile.objects.all()

    def get_queryset(self):
        queryset = self.queryset
        query_set = queryset.filter(user=self.request.user)
        return query_set


class ConfigurationView(viewsets.ModelViewSet):
    serializer_class = serializer.ConfigurationSerializer
    queryset = models.Configuration.objects.all()


class WebSocketTokenView(views.APIView):

    def get(self, request):
        try:
            try:
                profile = models.UserProfile.objects.get(id=request.GET['id'], user=request.user)
            except models.UserProfile.DoesNotExist:
                return Response(data=dict(error="Invalid profile"), status=status.HTTP_400_BAD_REQUEST)
            obj, created = models.WebSocketToken.objects.get_or_create(user=profile)
            return Response(data=dict(token=obj.token), status=status.HTTP_201_CREATED)

        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LikedMediaListView(views.APIView):

    def get_objects(self, request):
        id = request.GET['id']
        liked_medias = models.UserProfile.objects.get(id=id, user=request.user).liked_media.all()
        return liked_medias

    def get(self, request):
        try:
            try:
                page_size = int(request.GET.get('page_size', 5))
                page_number = int(request.GET.get('page_number', 1))
                medias = self.get_objects(request)
                count = medias.count()
                medias = medias[(page_number * page_size) - page_size:page_number * page_size]
                serializer_obj = MediaSerializer(medias, many=True)
                return Response(data=dict(page_size=page_size, page_number=page_number, total_count=count,
                                          data=serializer_obj.data), status=status.HTTP_200_OK)

            except models.UserProfile.DoesNotExist:
                return Response(data=dict(error="Invalid Profile"), status=status.HTTP_400_BAD_REQUEST)

        except ValidationError as e:
            raise e

        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommentsListView(LikedMediaListView):
    def get_objects(self, request):
        id = request.GET['id']
        return models.UserProfile.objects.get(id=id, user=request.user).commented_media.all()


class FollowedUsers(views.APIView):

    def get(self, request):
        try:
            try:
                id = request.GET['id']
                page_size = int(request.GET.get('page_size', 5))
                page_number = int(request.GET.get('page_number', 1))
                objects = models.UserProfile.objects.get(id=id, user=request.user).followed_users.all()
                count = objects.count()
                objects = objects[(page_number * page_size) - page_size:page_number * page_size]
                serializer_obj = InteractedUserSerializer(objects, many=True)
                return Response(data=dict(page_number=page_number, page_size=page_size, total_count=count,
                                          data=serializer_obj.data), status=status.HTTP_200_OK)

            except models.UserProfile.DoesNotExist:
                return Response(data=dict(error="Invalid Profile"), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response(data=dict(error="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
