from rest_framework import serializers

from users_profile import models


class UserProfileSerializer(serializers.ModelSerializer):

    def check_username(self, attrs):
        try:
            obj = models.UserProfile.objects.get(username=attrs['username'])
            raise serializers.ValidationError('Username is already used')

        except models.UserProfile.DoesNotExist:
            pass

        return attrs

    def create(self, validated_data):
        self.check_username(validated_data)
        validated_data['user'] = self.context['request'].user
        return models.UserProfile.objects.create(**validated_data)

    class Meta:
        model = models.UserProfile

        exclude = ('user',)


class ConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Configuration
        fields = '__all__'
