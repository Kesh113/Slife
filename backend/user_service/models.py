import random

from django.conf import settings
from django.contrib.auth import validators
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


USERNAME_HELP_TEXT = ('Обязательное поле. Только буквы,'
                      ' цифры и @/./+/-/_.')

SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'


class Skill(models.Model):
    title = models.CharField('Название', max_length=254, unique=True)

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'

    def __str__(self):
        return self.title[:21]


class SlifeUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email должен быть указан')

        email = self.normalize_email(email)

        # Генерация уникального username
        if 'username' not in extra_fields:
            base_username = slugify(email.split('@')[0])
            unique_username = f'{base_username}{random.randint(0, 9999):04d}'

            # Добавляем случайный суффикс, если username занят
            while SlifeUser.objects.filter(username=unique_username).exists():
                unique_username = f'{base_username}{random.randint(0, 9999):04d}'

            extra_fields['username'] = unique_username

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class SlifeUser(AbstractUser):
    USER_GENDER_CHOICES = [
        ('male', 'Мужской'),
        ('female', 'Женский'),
    ]

    username = models.CharField(
        max_length=30,
        unique=True,
        help_text=USERNAME_HELP_TEXT,
        validators=(validators.UnicodeUsernameValidator(),),
        verbose_name='Никнейм',
    )
    email = models.EmailField(
        'Электронная почта', max_length=50, unique=True
    )
    phone = models.CharField(
        'Телефон', max_length=15, blank=True, null=True
    )
    patronymic = models.CharField(
        'Отчество', max_length=150, blank=True, null=True
    )
    avatar = models.ImageField(
        upload_to='user_service/avatars/', verbose_name='Аватар', blank=True,
        null=True
    )
    birth_date = models.DateField('Дата рождения', blank=True, null=True)
    gender = models.CharField(
        'Пол', max_length=10, choices=USER_GENDER_CHOICES, blank=True,
        null=True
    )
    skills = models.ManyToManyField(
        Skill,
        verbose_name='Навыки',
        through='UserSkills'
    )
    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=settings.LENGTH_CODE,
        default=settings.RESERVED_CODE,
    )

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    objects = SlifeUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.email


class UserSkills(models.Model):
    user = models.ForeignKey(
        SlifeUser, on_delete=models.CASCADE,
        verbose_name='Пользователь', related_name='user_skills'
    )
    skill = models.ForeignKey(
        Skill, on_delete=models.CASCADE,
        verbose_name='Навык', related_name='users'
    )
    level = models.PositiveIntegerField(
        'Уровень', validators=[MinValueValidator(1)]
    )
    experience = models.PositiveIntegerField('Опыт')

    class Meta:
        verbose_name = 'Навык пользователя'
        verbose_name_plural = 'Навыки пользователей'

    def __str__(self):
        return (
            f'{self.user.email} - {self.skill.title}'
            ' {self.level} lvl, {self.experience} exp.'
        )


class Subscribe(models.Model):
    user = models.ForeignKey(
        SlifeUser, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='subscribers'
    )
    subscribing = models.ForeignKey(
        SlifeUser, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='authors'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'subscribing'], name='unique_subscription'
        )]

    def __str__(self):
        return (f'{self.user.username[:21]} подписан на '
                f'{self.subscribing.username[:21]}')

    def clean(self):
        if self.user == self.subscribing:
            raise ValidationError(SELF_SUBSCRIBE_ERROR)


class DeviceToken(models.Model):
    user = models.ForeignKey(
        SlifeUser,
        on_delete=models.CASCADE,
        related_name='device_tokens'
    )
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text='FCM токен устройства'
    )
    device_type = models.CharField(
        max_length=10,
        choices=[('ios', 'iOS'), ('android', 'Android')],
        help_text='Тип устройства'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Токен устройства'
        verbose_name_plural = 'Токены устройств'

    def __str__(self):
        return f'{self.user} - {self.device_type}'
