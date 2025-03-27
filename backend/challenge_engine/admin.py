from django.contrib import admin
from django.utils.html import format_html

from .models import CategoryTasks, Task, UsersTasks


@admin.register(CategoryTasks)
class CategoryTasksAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'tasks_count')
    list_filter = ('title',)
    search_fields = ('title', 'slug')
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(ordering='tasks_count', description='Заданий')
    def tasks_count(self, obj):
        return obj.tasks.count()

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title_short', 'skill', 'reward_experience', 'difficult')
    list_filter = ('skill', 'difficult')
    search_fields = ('title', 'description')
    filter_horizontal = ('category',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(ordering='title', description='Название')
    def title_short(self, obj):
        return obj.title[:30] + '...' if len(obj.title) > 30 else obj.title

@admin.register(UsersTasks)
class UsersTasksAdmin(admin.ModelAdmin):
    list_display = ('task_short', 'initiator', 'target_user', 'status', 'rating')
    list_filter = ('status', 'initiator', 'target_user')
    search_fields = ('task__title', 'initiator__username', 'target_user__username')
    raw_id_fields = ('task', 'initiator', 'target_user')
    readonly_fields = ('started_at', 'completed_at', 'confirmed_at')

    @admin.display(ordering='task__title', description='Задание')
    def task_short(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'/admin/tasks/task/{obj.task.pk}/change/',
            obj.task.title[:30] + '...' if len(obj.task.title) > 30 else obj.task.title
        )

    @admin.display(ordering='target_user', description='Целевой пользователь')
    def target_user(self, obj):
        if obj.target_user:
            return format_html(
                '<a href="{}">{}</a>',
                f'/admin/user_service/user/{obj.target_user.pk}/change/',
                obj.target_user.username
            )
        return obj.target_user_name
