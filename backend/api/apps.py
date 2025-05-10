from django.apps import AppConfig
from .firebase import initialize_firebase


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'

    def ready(self):
        initialize_firebase()
