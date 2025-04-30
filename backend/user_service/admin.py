from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    Skill, SlifeUser, UserSkills, Subscribe, SELF_SUBSCRIBE_ERROR
)


admin.site.unregister(Group)


@admin.register(Skill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)
    ordering = ('title',)
    list_filter = ('title',)


@admin.register(UserSkills)
class UserSkillsAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'skill__title', 'level', 'experience')
    search_fields = ('user__username',)
    ordering = ('user__username', 'skill__title', '-level')
    list_filter = ('level',)


@admin.register(SlifeUser)
class SlifeUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'date_joined', 'last_login')
    list_filter = ('gender', 'is_active')
    search_fields = ('username', 'email', 'phone')
    readonly_fields = ('confirmation_code',)
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональные данные', {'fields': (
            'first_name', 'patronymic', 'last_name',
            'phone', 'avatar', 'birth_date', 'gender'
        )}),
        ('Роли', {'fields': ('is_superuser', 'is_staff', 'is_active')}),
        ('Подтверждение', {'fields': ('confirmation_code',)}),
    )
    add_fieldsets = (
        (None, {'fields': ('email', 'password1', 'password2')}),
    )


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_short', 'subscribing_short')
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
