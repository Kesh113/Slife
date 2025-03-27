from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


User = get_user_model()


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField('Изображение', upload_to='social_service/posts/images/')
    text = models.TextField('Текст', max_length=1000)
    likes_count = models.PositiveBigIntegerField('Лайков', default=0)
    is_published = models.BooleanField('Опубликовано', default=True)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    updated = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        ordering = '-pub_date',
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return f'Пост {self.author} от {self.created_at}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField('Текст', max_length=1000)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    likes_count = models.PositiveBigIntegerField('Лайков', default=0)

    class Meta:
        ordering = '-pub_date',
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return f'Комментарий {self.author} к посту id={self.post.id}'


class Like(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='likes'
    )
    created_at = models.DateTimeField('Дата лайка', auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        verbose_name = 'Лайк'
        verbose_name_plural = 'Лайки'

    def save(self, *args, **kwargs):
        """Автоматическое обновление счётчика лайков при лайке"""
        super().save(*args, **kwargs)
        obj = self.content_object
        obj.likes_count = obj.likes.count()
        obj.save()

    def delete(self, *args, **kwargs):
        """Автоматическое обновление счётчика лайков при дизлайке"""
        obj = self.content_object
        super().delete(*args, **kwargs)
        obj.likes_count = obj.likes.count()
        obj.save()

    def __str__(self):
        return f'Лайк {self.user} для {self.content_object}'
