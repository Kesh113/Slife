from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.crypto import get_random_string
from django.urls import reverse

from user_service.models import Skill


User = get_user_model()


class CategoryTasks(models.Model):
    title = models.CharField('Название', max_length=100)
    slug = models.SlugField(
        'Поисковый идентификатор', max_length=100, unique=True
    )

    class Meta:
        verbose_name = 'Категория задания'
        verbose_name_plural = 'Категории задания'

    def __str__(self):
        return self.title[:21]


class Task(models.Model):
    DIFFICULT_CHOICES = (
        (1, 'легко'),
        (2, 'средняя сложность'),
        (3, 'сложно')
    )

    title = models.CharField('Название', max_length=100)
    slug = models.SlugField(
        'Поисковый идентификатор', max_length=100, unique=True
    )
    description = models.TextField('Описание', max_length=1000)
    rewards = models.ManyToManyField(
        Skill, verbose_name='Награды',
        related_name='tasks', through='TaskRewards'
    )
    difficult = models.IntegerField(
        'Сложность', choices=DIFFICULT_CHOICES
    )
    category = models.ManyToManyField(
        CategoryTasks, related_name='tasks'
    )

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return f'{self.title[:21]}, сложность: {self.difficult}'


class TaskRewards(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, verbose_name='Задание'
    )
    reward_skills = models.ForeignKey(
        Skill, on_delete=models.CASCADE,
        verbose_name='Награда', related_name='rewards_tasks'
    )
    quantity = models.PositiveIntegerField('Количество')

    class Meta:
        verbose_name = 'Награда задания'
        verbose_name_plural = 'Награды задания'

    def __str__(self):
        return (
            f'Задание: {self.task.title[:21]}, '
            f'награда: {self.reward_skills.title}'
        )


class UsersTasks(models.Model):
    TASK_STATUSES = {
        ('started', 'начато'),
        ('completed', 'завершено'),
        ('confirmed', 'подтверждено'),
        ('canceled', 'отменено')
    }

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE,
        related_name='user_tasks', verbose_name='Задание'
    )
    initiator = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='initiated_tasks', verbose_name='Инициатор'
    )
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='targeted_tasks', verbose_name='Целевой пользователь'
    )
    target_user_name = models.CharField(
        'Имя целевого пользователя', max_length=150,
        default='Без имени', blank=True
    )

    status = models.CharField(
        'Статус', max_length=21,
        choices=TASK_STATUSES,
        default='started'
    )
    invitation_token = models.CharField(
        'Токен приглашения', max_length=100,
        unique=True, null=True, blank=True,
        help_text='Идентификатор анонимного пользователя'
    )
    rating = models.PositiveSmallIntegerField(
        'Оценка целевого пользователя',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True, null=True
    )
    started_at = models.DateTimeField('Дата начала', auto_now_add=True)
    completed_at = models.DateTimeField(
        'Дата завершения', blank=True, null=True
    )
    confirmed_at = models.DateTimeField(
        'Дата подтверждения', blank=True, null=True
    )

    class Meta:
        verbose_name = 'Задание пользователя'
        verbose_name_plural = 'Задания пользователей'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.initiator} - {self.task}'

    def generate_invitation_token(self):
        """Генерирует уникальный токен для приглашения"""
        if not self.invitation_token:
            self.invitation_token = get_random_string(32)
            self.save()
        return self.invitation_token

    def get_invitation_url(self):
        """Возвращает URL для приглашения"""
        if not self.invitation_token:
            self.generate_invitation_token()
        return reverse('api:task-invitation', kwargs={'token': self.invitation_token})
