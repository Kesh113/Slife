from django.db.models.signals import post_save, post_delete

from .models import PostLike, CommentLike


def update_likes_count(sender, instance, **kwargs):
    """
    Обновляет поле likes_count у связанного объекта (пост/комментарий)
    через полный пересчёт лайков.
    """
    if sender == PostLike:
        obj = instance.post
    elif sender == CommentLike:
        obj = instance.comment
    obj.likes_count = obj.likes.count()
    obj.save(update_fields=['likes_count'])


# Регистрируем сигналы для PostLike
post_save.connect(update_likes_count, sender=PostLike)
post_delete.connect(update_likes_count, sender=PostLike)
# Регистрируем сигналы для CommentLike
post_save.connect(update_likes_count, sender=CommentLike)
post_delete.connect(update_likes_count, sender=CommentLike)