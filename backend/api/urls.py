from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    SlifeUserViewSet, UserSkillsViewSet,
    TaskViewSet, CategoryTasksViewSet, UsersTasksViewSet,
)

app_name = 'api'

router = DefaultRouter()
router.register('users', SlifeUserViewSet, basename='user')
router.register('user-skills', UserSkillsViewSet, basename='user-skills')
router.register('tasks', TaskViewSet, basename='tasks')
router.register('categories', CategoryTasksViewSet, basename='categories')
router.register('user-tasks', UsersTasksViewSet, basename='user-tasks')

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]
