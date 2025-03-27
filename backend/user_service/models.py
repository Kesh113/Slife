from django.conf import settings
from django.contrib.auth import validators
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify


USERNAME_HELP_TEXT = ('Обязательное поле. Только буквы,'
                      ' цифры и @/./+/-/_.')

SELF_SUBSCRIBE_ERROR = 'Нельзя подписаться на самого себя.'


class UserSkill(models.Model):
    title = models.CharField('Название', max_length=254, unique=True)
    level = models.PositiveIntegerField(
        'Уровень', validators=[MinValueValidator(1)]
    )
    experience = models.PositiveIntegerField('Опыт')

    class Meta:
        verbose_name = 'Навык'
        verbose_name_plural = 'Навыки'

    def __str__(self):
        return self.title[:21]


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
    patronymic = models.CharField('Отчество', max_length=150, blank=True)
    avatar = models.ImageField(
        upload_to='user_service/avatars/', verbose_name='Аватар', blank=True,
        null=True
    )
    birth_date = models.DateField('Дата рождения', blank=True)
    gender = models.CharField(
        max_length=10, choices=USER_GENDER_CHOICES, blank=True
    )
    skills = models.ManyToManyField(
        UserSkill, on_delete=models.CASCADE,
        verbose_name='Навыки',
        related_name='users'
    )
    confirmation_code = models.CharField(
        'Код подтверждения',
        max_length=settings.LENGTH_CODE,
        default=settings.RESERVED_CODE,
    )

    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = slugify(self.email.split('@')[0])
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


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
