from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

from user_service.models import UserSkill


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
    DIFFICULT_CHOICES = {
        ('low', 'легко'),
        ('medium', 'средняя сложность'),
        ('high', 'сложно')
    }

    title = models.CharField('Название', max_length=100)
    slug = models.SlugField(
        'Поисковый идентификатор', max_length=100, unique=True
    )
    description = models.TextField('Описание', max_length=1000)
    skill = models.ForeignKey(UserSkill, on_delete=models.CASCADE)
    reward_experience = models.PositiveIntegerField('Опыт')
    difficult = models.CharField(
        'Сложность', max_length=6, choices=DIFFICULT_CHOICES
    )
    category = models.ManyToManyField(
        CategoryTasks, on_delete=models.CASCADE, related_name='tasks'
    )

    class Meta:
        verbose_name = 'Задание'
        verbose_name_plural = 'Задания'

    def __str__(self):
        return (
            f'{self.title[:21]}, сложность: {self.difficult}, '
            f'награда: {self.skill} - {self.reward_experience} опыта'
        )


class UsersTasks(models.Model):
    TASK_STATUSES = {
        ('started', 'начато'),
        ('completed', 'завершено'),
        ('confirmed', 'подтверждено')
    }

    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name='users'
    )
    initiator = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='tasks_initiator'
    )
    target_user = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='tasks_target_user'
    )
    target_user_name = models.CharField(
        'Имя целевого пользователя', default='Без имени', blank=True
    )
    status = models.CharField('Статус', max_length=10, choices=TASK_STATUSES)
    rating = models.PositiveSmallIntegerField(
        'Оценка целевого пользователя',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    started_at = models.DateTimeField('Дата начала', auto_now_add=True)
    completed_at = models.DateTimeField('Дата завершения', blank=True)
    confirmed_at = models.DateTimeField('Дата подтверждения', blank=True)

    class Meta:
        verbose_name = 'Задание пользователя'
        verbose_name_plural = 'Задания пользователей'

    def __str__(self):
        target_user = (
            self.target_user.username
            if self.target_user else self.target_user_name
        )
        return (
            f'Задание - {self.task.title[:21]}, от '
            f'{self.initiator.username} для {target_user}'
        )
