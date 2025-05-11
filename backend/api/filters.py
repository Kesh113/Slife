from django_filters import rest_framework as filters
from challenge_engine.models import Task


class TaskFilter(filters.FilterSet):
    category = filters.CharFilter(field_name='category__slug', lookup_expr='exact')

    class Meta:
        model = Task
        fields = ['category'] 