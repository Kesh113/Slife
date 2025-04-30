from django.contrib import admin

from .models import Post, Comment, PostLike, CommentLike


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'text', 'pub_date', 'likes_count')
    list_filter = ('pub_date',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'text', 'pub_date', 'likes_count')
    list_filter = ('pub_date',)


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'liked_at')
    list_filter = ('liked_at', 'user', 'post')


@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'liked_at')
    list_filter = ('liked_at', 'user', 'comment')
