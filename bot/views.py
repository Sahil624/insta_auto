from rest_framework import viewsets
# Create your views here.
from bot import models
from bot.seralizers import InteractedUserSerializer


class InteractedUsersViewSet(viewsets.ModelViewSet):
    queryset = models.InteractedUser.objects.all()
    serializer_class = InteractedUserSerializer
