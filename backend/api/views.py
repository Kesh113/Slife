from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.generics import ListAPIView
from django.db.models import Q
from django.utils import timezone
import uuid
from django.conf import settings
from firebase_admin import messaging
from user_service.models import DeviceToken

from .serializers import (
    SlifeUserSerializer, UserSkillsSerializer, TaskSerializer,
    CategoryTasksSerializer, UsersTasksSerializer, DeviceTokenSerializer
)
from user_service.models import SlifeUser, UserSkills, Subscribe
from challenge_engine.models import Task, CategoryTasks, UsersTasks


User = get_user_model()


SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}

ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на "{}"'


def create_mutual_subscriptions(user1, user2):
    """Создает взаимные подписки между двумя пользователями"""
    Subscribe.objects.get_or_create(
        user=user1,
        subscribing=user2
    )
    Subscribe.objects.get_or_create(
        user=user2,
        subscribing=user1
    )


class SlifeUserViewSet(DjoserUserViewSet):
    def create(self, request, *args, **kwargs):
        """Переопределяем метод создания пользователя для связывания анонимных задач"""
        # Получаем anonymous_id из куки
        anonymous_id = request.COOKIES.get('anonymous_id')
        
        # Создаем пользователя
        response = super().create(request, *args, **kwargs)
        
        # После успешного создания пользователя
        if response.status_code == status.HTTP_201_CREATED and anonymous_id:
            # Получаем созданного пользователя
            user_id = response.data.get('id')
            if user_id:
                user = get_object_or_404(SlifeUser, id=user_id)
                
                # Связываем анонимные задачи
                anonymous_tasks = UsersTasks.objects.filter(
                    invitation_token__startswith=anonymous_id,
                    status='confirmed'
                )
                for task in anonymous_tasks:
                    create_mutual_subscriptions(user, task.initiator)
                    task.target_user = user
                    task.save()
        
        return response

    @action(
        ['get'], detail=False, url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
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
        permission_classes=[permissions.IsAuthenticated]
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


class UserSkillsViewSet(ListModelMixin, GenericViewSet):
    serializer_class = UserSkillsSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserSkills.objects.filter(user=self.request.user)


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Task.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category__slug=category)
        return queryset


class CategoryTasksViewSet(ListModelMixin, GenericViewSet):
    queryset = CategoryTasks.objects.all()
    serializer_class = CategoryTasksSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class UsersTasksViewSet(viewsets.ModelViewSet):
    serializer_class = UsersTasksSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UsersTasks.objects.filter(initiator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(initiator=self.request.user)

    def can_confirm_task(self, task):
        """Проверяет, может ли текущий пользователь подтвердить задание"""
        # Если есть target_user, то только он может подтвердить
        if task.target_user:
            return task.target_user == self.request.user
        # Если target_user не указан, но есть invitation_token, 
        # то любой пользователь может подтвердить по ссылке
        return bool(task.invitation_token)

    def send_confirmation_notification(self, task):
        """Отправляет push-уведомление target_user о необходимости подтверждения задачи"""
        if not task.target_user:
            return

        # Получаем все токены устройств пользователя
        device_tokens = DeviceToken.objects.filter(user=task.target_user)
        if not device_tokens:
            return

        # Формируем сообщение
        message = {
            'notification': {
                'title': 'Подтверждение задачи',
                'body': f'Пользователь {task.initiator.username} выполнил задачу "{task.task.title}". Пожалуйста, подтвердите выполнение.',
            },
            'data': {
                'type': 'task_confirmation',
                'task_id': str(task.id),
                'task_title': task.task.title,
                'initiator_username': task.initiator.username,
            },
            'tokens': [token.token for token in device_tokens],
        }

        try:
            # Отправляем уведомление
            response = messaging.send_multicast(message)
            
            # Удаляем недействительные токены
            if response.failure_count > 0:
                for idx, result in enumerate(response.responses):
                    if not result.success:
                        device_tokens[idx].delete()
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            print(f"Ошибка при отправке push-уведомления: {e}")

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        if task.status != 'started':
            return Response(
                {'error': 'Задание должно быть в статусе "начато"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()

        # Отправляем уведомление target_user
        self.send_confirmation_notification(task)
        
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        task = self.get_object()
        if not self.can_confirm_task(task):
            return Response(
                {'error': 'У вас нет прав на подтверждение этого задания'},
                status=status.HTTP_403_FORBIDDEN
            )

        if task.status != 'completed':
            return Response(
                {'error': 'Задание должно быть в статусе "завершено"'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'confirmed'
        task.confirmed_at = timezone.now()
        task.save()

        # Создаем взаимные подписки между initiator и target_user
        if task.target_user and task.initiator:
            create_mutual_subscriptions(task.target_user, task.initiator)

        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        task = self.get_object()
        if task.status in ['confirmed', 'canceled']:
            return Response(
                {'error': 'Нельзя отменить подтвержденное или отмененное задание'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = 'canceled'
        task.save()
        serializer = self.get_serializer(task)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def accept_invitation(self, request):
        """Принятие приглашения по токену"""
        token = request.data.get('token')
        if not token:
            return Response(
                {'error': 'Токен приглашения не указан'},
                status=status.HTTP_400_BAD_REQUEST
            )

        task = get_object_or_404(UsersTasks, invitation_token=token)
        if task.status == 'canceled':
            return Response(
                {'error': 'Задание уже отменено'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Если есть target_user, значит это задание для конкретного пользователя
        # и его нельзя принять по ссылке
        if task.target_user:
            return Response(
                {'error': 'Это задание предназначено для конкретного пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем или генерируем anonymous_id
        anonymous_id = request.COOKIES.get('anonymous_id')
        if not anonymous_id:
            anonymous_id = str(uuid.uuid4())
            # Устанавливаем куку
            response.set_cookie('anonymous_id', anonymous_id, max_age=365*24*60*60)  # 1 год

        # Обновляем токен с префиксом anonymous_id
        task.invitation_token = f"{anonymous_id}_{task.invitation_token}"
        task.save()
            
        serializer = self.get_serializer(task)
        return Response(serializer.data)


class DeviceTokenViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DeviceToken.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # Удаляем старый токен, если он существует
        DeviceToken.objects.filter(token=serializer.validated_data['token']).delete()
        # Создаем новый токен
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        # Удаляем только свой токен
        if instance.user == self.request.user:
            instance.delete()
