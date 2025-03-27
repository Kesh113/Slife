from django.contrib import admin

from .models import Post, Comment, Like


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'text_short', 'created_at', 'likes_count')
    list_filter = ('created_at', 'author')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'text_short', 'created_at', 'likes_count')
    list_filter = ('created_at', 'author')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_object', 'created_at')
    list_filter = ('created_at', 'user')
