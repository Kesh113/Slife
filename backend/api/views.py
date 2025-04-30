from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .serializers import SlifeUserSerializer
from user_service.models import Subscribe


User = get_user_model()


SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на "{}"'


class SlifeUserViewSet(DjoserUserViewSet):
    @action(
        ['get'], detail=False, url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        subscribe_data = SlifeUserSerializer(
            self.filter_queryset(self.get_queryset().filter(
                authors__user=request.user
            )), context={'request': request}, many=True
        ).data
        return self.get_paginated_response(
            self.paginate_queryset(subscribe_data)
        )

    @action(
        ['post', 'delete'], detail=True, url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def create_delete_subscribe(self, request, id=None):
        author = self.get_object()
        if request.method == 'DELETE':
            get_object_or_404(
                Subscribe, user=request.user, subscribing=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if request.user == author:
            raise serializers.ValidationError(SELF_SUBSCRIBE_ERROR)
        _, created = Subscribe.objects.get_or_create(
            user=request.user, subscribing=author
        )
        if not created:
            raise serializers.ValidationError(
                {'subscribe': ALREADY_SUBSCRIBED_ERROR.format(author)}
            )
        return Response(SlifeUserSerializer(
            author, context={'request': request}
        ).data, status=status.HTTP_201_CREATED)
