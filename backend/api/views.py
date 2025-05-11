from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, serializers, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from .serializers import (
    SlifeUserSerializer, UserSkillsSerializer, TaskFullSerializer,
    CategoryTasksSerializer, UsersTasksListSerializer, UsersTasksDetailSerializer,
    TaskBriefSerializer
)
from user_service.models import UserSkills, Subscribe
from challenge_engine.models import (
    Task, CategoryTasks, UsersTasks,
    TASK_STATUS_STARTED, TASK_STATUS_COMPLETED,
    TASK_STATUS_CONFIRMED
)
from .permissions import IsAuthorOrAdmin
from .filters import TaskFilter

User = get_user_model()

# Константы для сообщений об ошибках
SELF_SUBSCRIBE_ERROR = {'subscribe': 'Нельзя подписаться на самого себя.'}
ALREADY_SUBSCRIBED_ERROR = 'Вы уже подписаны на "{}"'

# Константы для сообщений об ошибках заданий
TASK_ALREADY_STARTED = 'Вы уже начали выполнение этого задания'
TASK_SELF_TARGET = 'Нельзя назначить себя целевым пользователем'
TASK_USER_NOT_FOUND = 'Указанный пользователь не существует'
TASK_NOT_STARTED = 'Задание должно быть в статусе "начато"'
TASK_NOT_COMPLETED = 'Задание должно быть в статусе "завершено"'
TASK_ALREADY_CONFIRMED = 'Нельзя отменить подтвержденное задание'
TASK_INITIATOR_CONFIRM = 'Инициатор не может подтверждать свое задание'
TASK_WRONG_TARGET = 'Это задание предназначено для другого пользователя'
TASK_CONFIRMATION_REQUIRED = 'Необходимо указать confirmation_id'
TASK_NOT_FOUND = 'Задание не найдено'
TASK_INVALID_RATING = 'Рейтинг должен быть числом от 1 до 5'


def create_mutual_subscriptions(user1, user2):
    """Создает взаимные подписки между двумя пользователями"""
    Subscribe.objects.get_or_create(user=user1, subscribing=user2)
    Subscribe.objects.get_or_create(user=user2, subscribing=user1)


class SlifeUserViewSet(DjoserUserViewSet):
    """ViewSet для работы с пользователями"""
    @action(
        ['get'], 
        detail=False, 
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить список подписок пользователя"""
        subscribe_data = SlifeUserSerializer(
            self.filter_queryset(
                self.get_queryset().filter(authors__user=request.user)
            ),
            context={'request': request},
            many=True
        ).data
        return self.get_paginated_response(
            self.paginate_queryset(subscribe_data)
        )

    @action(
        ['post', 'delete'],
        detail=True,
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
    def create_delete_subscribe(self, request, id=None):
        """Создать или удалить подписку на пользователя"""
        author = self.get_object()
        
        if request.method == 'DELETE':
            get_object_or_404(
                Subscribe,
                user=request.user,
                subscribing=author
            ).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.user == author:
            raise serializers.ValidationError(SELF_SUBSCRIBE_ERROR)

        _, created = Subscribe.objects.get_or_create(
            user=request.user,
            subscribing=author
        )

        if not created:
            raise serializers.ValidationError(
                {'subscribe': ALREADY_SUBSCRIBED_ERROR.format(author)}
            )

        return Response(
            SlifeUserSerializer(
                author,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )


class UserSkillsViewSet(ListModelMixin, GenericViewSet):
    """ViewSet для работы с навыками пользователя"""
    serializer_class = UserSkillsSerializer

    def get_queryset(self):
        return UserSkills.objects.filter(user=self.request.user)


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с заданиями"""
    queryset = Task.objects.all()
    serializer_class = TaskFullSerializer
    filterset_class = TaskFilter

    def get_serializer_class(self):
        if self.action == 'list':
            return TaskBriefSerializer
        return TaskFullSerializer

    def get_queryset(self):
        queryset = Task.objects.all()
        
        started_tasks = UsersTasks.objects.filter(
            initiator=self.request.user,
            status__in=[
                TASK_STATUS_STARTED,
                TASK_STATUS_COMPLETED,
                TASK_STATUS_CONFIRMED
            ]
        ).values_list('task_id', flat=True)
        
        return queryset.exclude(id__in=started_tasks)

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Начать выполнение задания"""
        task = self.get_object()
        
        # Проверяем, не начато ли уже это задание пользователем
        if UsersTasks.objects.filter(
            task=task,
            initiator=request.user
        ).exists():
            return Response(
                {'error': TASK_ALREADY_STARTED},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Получаем данные о целевом пользователе
        target_user = request.data.get('target_user')
        target_user_name = request.data.get('target_user_name', '')

        # Проверяем, что пользователь не назначает себя целевым
        if target_user and str(target_user) == str(request.user.id):
            return Response(
                {'error': TASK_SELF_TARGET},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем существование пользователя, если указан target_user
        if target_user:
            try:
                User.objects.get(id=target_user)
            except User.DoesNotExist:
                return Response(
                    {'error': TASK_USER_NOT_FOUND},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Создаем новую запись в UsersTasks
        user_task = UsersTasks.objects.create(
            task=task,
            initiator=request.user,
            target_user_id=target_user,
            target_user_name=target_user_name,
            status=TASK_STATUS_STARTED,
            started_at=timezone.now()
        )

        # Генерируем confirmation_id
        user_task.confirmation_id = user_task.generate_confirmation_id()
        user_task.save()

        serializer = UsersTasksListSerializer(user_task)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryTasksViewSet(ListModelMixin, GenericViewSet):
    """ViewSet для работы с категориями заданий"""
    queryset = CategoryTasks.objects.all()
    serializer_class = CategoryTasksSerializer


class UsersTasksViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с заданиями пользователей"""
    permission_classes = [IsAuthorOrAdmin]
    serializer_class = UsersTasksListSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UsersTasksDetailSerializer
        return UsersTasksListSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return UsersTasks.objects.all()
        return UsersTasks.objects.filter(initiator=self.request.user)

    def perform_create(self, serializer):
        serializer.save(initiator=self.request.user)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Завершить задание"""
        task = self.get_object()
        
        if task.status != TASK_STATUS_STARTED:
            return Response(
                {'error': TASK_NOT_STARTED},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.status = TASK_STATUS_COMPLETED
        task.completed_at = timezone.now()
        task.save()
        
        serializer = self.get_serializer(task)
        response_data = serializer.data
        response_data['confirmation_id'] = task.confirmation_id
        return Response(response_data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated]
    )
    def confirm_by_id(self, request):
        """Подтвердить задание по confirmation_id"""
        confirmation_id = request.data.get('confirmation_id')
        if not confirmation_id:
            return Response(
                {'error': TASK_CONFIRMATION_REQUIRED},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Находим задание по confirmation_id
        try:
            task = UsersTasks.objects.get(confirmation_id=confirmation_id)
        except UsersTasks.DoesNotExist:
            return Response(
                {'error': TASK_NOT_FOUND},
                status=status.HTTP_404_NOT_FOUND
            )

        if task.status != TASK_STATUS_COMPLETED:
            return Response(
                {'error': TASK_NOT_COMPLETED},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Проверяем, что пользователь не является инициатором
        if task.initiator == request.user:
            return Response(
                {'error': TASK_INITIATOR_CONFIRM},
                status=status.HTTP_403_FORBIDDEN
            )

        if task.target_user and task.target_user != request.user:
            return Response(
                {'error': TASK_WRONG_TARGET},
                status=status.HTTP_403_FORBIDDEN
            )

        # Получаем рейтинг из тела ответа
        rating = request.data.get('rating')
        if rating:
            try:
                rating = int(rating)
                if not 1 <= rating <= 5:
                    raise ValueError()
            except ValueError:
                return Response(
                    {'error': TASK_INVALID_RATING},
                    status=status.HTTP_400_BAD_REQUEST
                )

        task.status = TASK_STATUS_CONFIRMED
        task.confirmed_at = timezone.now()
        if rating:
            task.rating = rating
        if not task.target_user:
            task.target_user = request.user
        task.save()

        # Создаем взаимные подписки между initiator и текущим пользователем
        create_mutual_subscriptions(request.user, task.initiator)

        serializer = UsersTasksDetailSerializer(task)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Отменить задание"""
        task = self.get_object()
        
        if task.status == TASK_STATUS_CONFIRMED:
            return Response(
                {'error': TASK_ALREADY_CONFIRMED},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
