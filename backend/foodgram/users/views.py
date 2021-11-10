from django.shortcuts import get_object_or_404

from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, Subscribe
from .serializer import SubscribeSerializer, UserSerializer, UserInSubscriptionsSerializer


class UserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = UserSerializer
    queryset = User.objects.all()


class SubscribeViewSet(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, user_id):
        user = request.user
        fol = User.objects.get(id=user_id)
        data = {
            'user': user.id,
            'following': fol
        }
        serializer = SubscribeSerializer(data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id):
        author = request.user
        following = get_object_or_404(User, pk=user_id)
        sub_exists = Subscribe.objects.filter(author=author, following=following).delete()
        if sub_exists[0] == 0:
            return Response('Вы не подписаны на данного пользователя', status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeListViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserInSubscriptionsSerializer

    def get_queryset(self):
        user = self.request.user
        return User.objects.filter(following__user=user)


