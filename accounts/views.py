from rest_framework.response import Response

from accounts import serializers

# Create your views here.
from rest_framework.views import APIView

from accounts.models import User


class Account(APIView):
    def post(self, request):
        serializer = serializers.AccountSerializer(request.data)
        # serializer.validate(request.data)
        # serializer.is_valid(raise_exception=True):
        User.objects.create_user(username=serializer.data['username'],
                                 email='test@test.com',
                                 password=serializer.data['password'])
        return Response(data=dict(message="test"))
