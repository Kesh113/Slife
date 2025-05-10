from django.db.models.signals import post_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404

from .models import SlifeUser, UserSkills, Skill


@receiver(post_save, sender=SlifeUser)
def handle_new_user(sender, instance, created, **kwargs):
    """Обработчик создания нового пользователя"""
    if created:
        # Присваиваем все существующие навыки с начальным уровнем
        skills = [
            UserSkills(
                user=instance,
                skill=skill,
                level=1,
                experience=0
            )
            for skill in Skill.objects.all()
        ]
        UserSkills.objects.bulk_create(skills)
