from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Post(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, 
        related_name='posts', verbose_name='Автор'
    )
    image = models.ImageField(
        'Изображение', upload_to='social_service/posts/images/'
    )
    text = models.TextField('Текст', max_length=1000)
    likes_count = models.PositiveBigIntegerField(
        'Лайков', default=0, editable=False
    )
    is_published = models.BooleanField('Опубликовано', default=True)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    updated = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        ordering = '-pub_date',
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return f'Пост {self.author} от {self.pub_date}'


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField('Текст', max_length=1000)
    pub_date = models.DateTimeField('Дата публикации', auto_now_add=True)
    likes_count = models.PositiveBigIntegerField(
        'Лайков', default=0, editable=False
    )

    class Meta:
        ordering = '-pub_date',
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        default_related_name = 'comments'

    def __str__(self):
        return f'Комментарий {self.author} к посту id={self.post.id}'


class Like(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name='Пользователь'
    )
    liked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-liked_at']


class PostLike(Like):
    post = models.ForeignKey(
        'Post', on_delete=models.CASCADE,
        related_name='likes', verbose_name='Пост'
    )

    class Meta(Like.Meta):
        unique_together = ('user', 'post')
        verbose_name = 'Лайк поста'
        verbose_name_plural = 'Лайки постов'

    def __str__(self):
        return f'{self.user} лайкнул пост id={self.post.id}'


class CommentLike(Like):
    comment = models.ForeignKey(
        'Comment', on_delete=models.CASCADE,
        related_name='likes', verbose_name='Комментарий'
    )

    class Meta(Like.Meta):
        unique_together = ('user', 'comment')
        verbose_name = 'Лайк комментария'
        verbose_name_plural = 'Лайки комментариев'

    def __str__(self):
        return f'{self.user} лайкнул комментарий id={self.comment.id}'
