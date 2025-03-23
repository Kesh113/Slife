from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import SlifeUser


@admin.register(SlifeUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональные данные', {
            'fields': ('email', 'phone', 'birth_date', 'gender', 'avatar')
        }),
        ('Права доступа', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'email'),
        }),
    )
