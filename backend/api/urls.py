from django.urls import include, path, re_path
from rest_framework.routers import DefaultRouter

from .views import (
    SlifeUserViewSet, UserSkillsViewSet,
    TaskViewSet, CategoryTasksViewSet, UsersTasksViewSet,
    DeviceTokenViewSet
)

router = DefaultRouter()
router.register('users', SlifeUserViewSet, basename='user')
router.register('tasks', TaskViewSet)
router.register('categories', CategoryTasksViewSet, basename='categories')
router.register('user-tasks', UsersTasksViewSet, basename='user-tasks')
router.register('user-skills', UserSkillsViewSet, basename='user-skills')

urlpatterns = [
    re_path(r'^auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
    path('user-tasks/invitation/<str:token>/', 
         UsersTasksViewSet.as_view({'post': 'accept_invitation'}),
         name='task-invitation'),
    path('device-tokens/', DeviceTokenViewSet.as_view({'get': 'list', 'post': 'create'}), name='device-tokens'),
    path('device-tokens/<int:pk>/', DeviceTokenViewSet.as_view({'delete': 'destroy'}), name='device-token-detail'),
]
