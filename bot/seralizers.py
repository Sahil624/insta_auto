from rest_framework import serializers

from bot import models


class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Media
        fields = '__all__'


class InteractedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InteractedUser
        fields = '__all__'


class BotSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.BotSession
        fields = '__all__'
