from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from user_service.models import Subscribe


User = get_user_model()


class SlifeUserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            *DjoserUserSerializer.Meta.fields, 'username', 'is_subscribed',
            'first_name', 'patronymic', 'last_name', 'phone', 'avatar',
            'birth_date', 'gender'
        )

    def get_is_subscribed(self, subscribing):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Subscribe.objects.filter(
                user=request.user, subscribing=subscribing
            ).exists()
        )