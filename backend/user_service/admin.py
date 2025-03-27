from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html

from .models import UserSkill, SlifeUser, Subscribe, SELF_SUBSCRIBE_ERROR


@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('title', 'level', 'experience')
    search_fields = ('title',)
    ordering = ('title',)
    list_filter = ('level',)


@admin.register(SlifeUser)
class SlifeUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'gender', 'skills_count')
    list_filter = ('gender', 'is_active')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('confirmation_code',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональные данные', {'fields': ('phone', 'patronymic', 'avatar', 'birth_date', 'gender')}),
        ('Социальные данные', {'fields': ('skills',)}),
        ('Подтверждение', {'fields': ('confirmation_code',)}),
    )

    @admin.display(ordering='skills__count', description='Навыки')
    def skills_count(self, obj):
        return obj.skills.count()


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('user_short', 'subscribing_short', 'created_at')
    list_filter = ('user', 'subscribing')
    search_fields = ('user__username', 'subscribing__username')
    raw_id_fields = ('user', 'subscribing')
    ordering = ('-id',)
    
    @admin.display(ordering='user__username', description='Пользователь')
    def user_short(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:user_service_slifeuser_change', args=(obj.user.pk,)),
            obj.user.username[:21]
        )

    @admin.display(ordering='subscribing__username', description='Автор')
    def subscribing_short(self, obj):
        return format_html(
            '<a href="{}">{}</a>',
            reverse('admin:user_service_slifeuser_change', args=(obj.subscribing.pk,)),
            obj.subscribing.username[:21]
        )

    def save_model(self, request, obj, form, change):
        if obj.user == obj.subscribing:
            raise ValidationError(SELF_SUBSCRIBE_ERROR)
        super().save_model(request, obj, form, change)

