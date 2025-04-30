from django.urls import include, re_path, path
from rest_framework.routers import DefaultRouter

from .views import SlifeUserViewSet


router = DefaultRouter()
router.register('users', SlifeUserViewSet, basename='user')


urlpatterns = [
    # re_path(r'^auth/', include('djoser.urls')),
    re_path(r'^auth/', include('djoser.urls.jwt')),
    path('', include(router.urls)),
]
