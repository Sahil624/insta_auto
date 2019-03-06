from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from accounts import serializers
from rest_framework.serializers import ValidationError

# Create your views here.
from rest_framework.views import APIView
import logging
from accounts.models import User


class Account(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = ()

    def post(self, request):
        try:
            serializer = serializers.AccountSerializer(data=request.data)
            validated_data = serializer.validate(request.data)
            serializer.is_valid(raise_exception=True)

            User.objects.create_user(username=validated_data['username'],
                                     email=validated_data['email'],
                                     password=validated_data['password'])
            return Response(data=dict(message="User created"), status=status.HTTP_201_CREATED)

        except ValidationError as e:
            raise e

        except Exception as e:
            logging.exception(str(e))
            return Response(data=dict(message="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class Logout(APIView):

    def delete(self, request):
        try:
            request.user.auth_token.delete()
            return Response(data=dict(message="Logged out", status=status.HTTP_200_OK))

        except Exception as e:
            return Response(data=dict(message="Something went wrong"), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
