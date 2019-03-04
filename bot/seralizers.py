from rest_framework import serializers

from bot import models


class InteractedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.InteractedUser
        fields = ('user_name',)
