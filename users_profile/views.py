from rest_framework import views, status, viewsets
from rest_framework.response import Response
from rest_framework.serializers import ValidationError

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
