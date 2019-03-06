from rest_framework import serializers
from accounts.models import User


class AccountSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        username = attrs.get('username', None)
        email = attrs.get('email', None)
        password = attrs.get('password', None)

        try:
            if email and username:

                user = User.objects.get(username=username)
                if user:
                    raise serializers.ValidationError('This username is already used.')

                user = User.objects.get(email=email)
                if user:
                    raise serializers.ValidationError('This email is already registered')

                return attrs
            else:
                raise serializers.ValidationError('Fill all fields')

        except User.DoesNotExist:
            return attrs

    class Meta:
        model = User
        fields = ('password', 'username', 'email')
