from django.contrib import admin
from django.utils.html import format_html

from .models import CategoryTasks, Task, TaskRewards, UsersTasks


@admin.register(CategoryTasks)
class CategoryTasksAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}

    @admin.display(ordering='tasks_count', description='Заданий')
    def tasks_count(self, obj):
        return obj.tasks.count()


class TaskRewardsInline(admin.TabularInline):
    model = TaskRewards
    extra = 1


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title_short', 'slug', 'display_category',
        'display_rewards', 'difficulty'
    )
    list_filter = ('difficulty', 'category')
    search_fields = ('title', 'description')
    filter_horizontal = ('category',)
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['-created_at']
    inlines = [TaskRewardsInline]

    @admin.display(ordering='title', description='Название')
    def title_short(self, obj):
        return obj.title[:30] + '...' if len(obj.title) > 30 else obj.title

    @admin.display(ordering='rewards', description='Награды')
    def display_rewards(self, obj):
        return [
            f'{reward.reward.title} ({reward.quantity})'
            for reward in obj.task_rewards.select_related('reward').all()
        ]

    @admin.display(ordering='category', description='Категории')
    def display_category(self, obj):
        return [category.title for category in obj.category.all()]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related(
            'task_rewards__reward', 'category'
        )


@admin.register(TaskRewards)
class TaskRewardsAdmin(admin.ModelAdmin):
    list_display = ('task', 'reward', 'quantity', 'is_additional')
    list_filter = ('task', 'reward')
    search_fields = ('task__title', 'reward__title')


@admin.register(UsersTasks)
class UsersTasksAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'task_link', 'initiator_link', 'target_user_link',
        'status', 'rating'
    )
    list_display_links = (
        'id', 'task_link', 'initiator_link', 'target_user_link'
    )
    list_filter = ('status',)
    search_fields = (
        'task__title', 'initiator__username', 'target_user__username'
    )
    raw_id_fields = ('task', 'initiator', 'target_user')
    readonly_fields = ('started_at', 'completed_at', 'confirmed_at')
    ordering = ['-started_at']

    @admin.display(ordering='task__title', description='Задание')
    def task_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'/admin/challenge_engine/task/{obj.task.pk}/change/',
            (
                obj.task.title[:30] + '...'
                if len(obj.task.title) > 30
                else obj.task.title
            )
        )

    @admin.display(ordering='initiator__username', description='Инициатор')
    def initiator_link(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            f'/admin/user_service/slifeuser/{obj.initiator.pk}/change/',
            obj.initiator.email
        )

    @admin.display(
            ordering='target_user__username',
            description='Целевой пользователь'
        )
    def target_user_link(self, obj):
        if obj.target_user:
            return format_html(
                '<a href="{}">{}</a>',
                f'/admin/user_service/slifeuser/{obj.target_user.pk}/change/',
                obj.target_user.email
            )
        return obj.target_user_name
