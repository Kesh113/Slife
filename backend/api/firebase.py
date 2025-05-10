import firebase_admin
from firebase_admin import credentials
from django.conf import settings

def initialize_firebase():
    """Инициализирует Firebase Admin SDK"""
    try:
        # Проверяем, не инициализирован ли уже SDK
        firebase_admin.get_app()
    except ValueError:
        # Если нет, инициализируем
        cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
        firebase_admin.initialize_app(cred) 