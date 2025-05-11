from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.urls import reverse
import hashlib

from user_service.models import Skill

User = get_user_model()

# Константы для статусов заданий
TASK_STATUS_STARTED = 'started'
TASK_STATUS_COMPLETED = 'completed'
TASK_STATUS_CONFIRMED = 'confirmed'
TASK_STATUS_CANCELED = 'canceled'

TASK_STATUSES = (
    (TASK_STATUS_STARTED, 'начато'),
    (TASK_STATUS_COMPLETED, 'завершено'),
    (TASK_STATUS_CONFIRMED, 'подтверждено'),
    (TASK_STATUS_CANCELED, 'отменено')
)

# Константы для сложности заданий
TASK_DIFFICULTY_EASY = 'easy'
TASK_DIFFICULTY_MEDIUM = 'medium'
TASK_DIFFICULTY_HARD = 'hard'

TASK_DIFFICULTY_CHOICES = (
    (TASK_DIFFICULTY_EASY, 'легко'),
    (TASK_DIFFICULTY_MEDIUM, 'средняя сложность'),
    (TASK_DIFFICULTY_HARD, 'сложно')
)


class CategoryTasks(models.Model):
    """Модель категорий заданий"""
    title = models.CharField('Название', max_length=100)
    slug = models.SlugField(
        'Поисковый идентификатор', max_length=100, unique=True
    )

    class Meta:
        verbose_name = 'Категория задания'
        verbose_name_plural = 'Категории задания'
        ordering = ['title']

    def __str__(self):
        return self.title[:21]


class Task(models.Model):
    """Модель заданий"""
    title = models.CharField('Название', max_length=100)
    slug = models.SlugField(
        'Поисковый идентификатор', max_length=100, unique=True
    )
    description = models.TextField('Описание', max_length=1000)
    short_description = models.TextField(
        'Краткое описание',
        help_text="Краткое описание задания"
    )
    hint = models.TextField(
        'Подсказка',
        blank=True,
        help_text="Подсказка к заданию"
    )
    rewards = models.ManyToManyField(
        Skill,
        verbose_name='Награды',
        related_name='tasks',
        through='TaskRewards',
        through_fields=('task', 'reward'),
    )
    difficulty = models.CharField(
        'Сложность',
        max_length=20,
        choices=TASK_DIFFICULTY_CHOICES,
        default=TASK_DIFFICULTY_EASY
    )
    category = models.ManyToManyField(
        CategoryTasks,
        related_name='tasks',
        verbose_name='Категории'
    )
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class TaskRewards(models.Model):
    """Модель наград за выполнение заданий"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        verbose_name='Задание',
        related_name='task_rewards'
    )
    reward = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        verbose_name='Награда',
        related_name='task_rewards'
    )
    quantity = models.PositiveIntegerField('Количество')
    is_additional = models.BooleanField(
        'Дополнительная награда',
        default=False,
        help_text='Является ли эта награда дополнительной'
    )
    additional_reward_description = models.TextField(
        blank=True,
        verbose_name='Описание дополнительной награды',
        help_text="Описание дополнительной награды"
    )

    class Meta:
        verbose_name = 'Награда задания'
        verbose_name_plural = 'Награды задания'
        unique_together = ['task', 'reward']

    def __str__(self):
        return (
            f'Задание: {self.task.title[:21]}, '
            f'награда: {self.reward.title}'
        )


class UsersTasks(models.Model):
    """Модель заданий пользователей"""
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='user_tasks',
        verbose_name='Задание'
    )
    initiator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='initiated_tasks',
        verbose_name='Инициатор'
    )
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='targeted_tasks',
        verbose_name='Целевой пользователь'
    )
    target_user_name = models.CharField(
        'Имя целевого пользователя',
        max_length=150,
        default='Без имени',
        blank=True
    )
    confirmation_id = models.CharField(
        'ID подтверждения',
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='ID для подтверждения задания'
    )
    status = models.CharField(
        'Статус',
        max_length=21,
        choices=TASK_STATUSES,
        default=TASK_STATUS_STARTED
    )
    rating = models.PositiveSmallIntegerField(
        'Оценка целевого пользователя',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        blank=True,
        null=True
    )
    started_at = models.DateTimeField('Дата начала', auto_now_add=True)
    completed_at = models.DateTimeField(
        'Дата завершения',
        blank=True,
        null=True
    )
    confirmed_at = models.DateTimeField(
        'Дата подтверждения',
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'Задание пользователя'
        verbose_name_plural = 'Задания пользователей'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.initiator} - {self.task}'

    def generate_confirmation_id(self):
        """Генерирует confirmation_id как хэш от комбинации данных задания"""
        if not self.confirmation_id:
            # Создаем строку для хеширования из ID задания и инициатора
            data = f"{self.task.id}:{self.initiator.id}".encode('utf-8')
            # Генерируем хэш
            self.confirmation_id = hashlib.sha256(data).hexdigest()[:32]
            self.save()
        return self.confirmation_id

    def get_confirmation_url(self):
        """Возвращает URL для подтверждения задания"""
        return reverse('api:user-tasks-confirm', kwargs={'confirmation_id': self.confirmation_id})
