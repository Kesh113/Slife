from django.contrib import admin

from .models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'text', 'pub_date', 'likes_count')
    list_filter = ('pub_date', 'author')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'text', 'pub_date', 'likes_count')
    list_filter = ('pub_date', 'author')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'created_at')
    list_filter = ('created_at', 'user')
