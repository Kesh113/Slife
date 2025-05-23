from django.apps import AppConfig


class SocialServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'social_service'
    verbose_name = 'Социальная сеть'

    def ready(self):
        import social_service.signals
