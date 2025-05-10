from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from user_service.models import Subscribe, SlifeUser, UserSkills
from challenge_engine.models import Task, CategoryTasks, UsersTasks
from user_service.models import DeviceToken


User = get_user_model()


class SlifeUserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    subscribers_count = serializers.SerializerMethodField()
    authors_count = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = (
            *DjoserUserSerializer.Meta.fields, 'username', 'is_subscribed',
            'first_name', 'patronymic', 'last_name', 'phone', 'avatar',
            'birth_date', 'gender', 'skills', 'subscribers_count', 'authors_count'
        )

    def get_is_subscribed(self, subscribing):
        request = self.context.get('request')
        return (
            request and request.user.is_authenticated
            and Subscribe.objects.filter(
                user=request.user, subscribing=subscribing
            ).exists()
        )

    def get_skills(self, obj):
        skills = UserSkills.objects.filter(user=obj)
        return UserSkillsSerializer(skills, many=True).data

    def get_subscribers_count(self, obj):
        return obj.subscribers.count()

    def get_authors_count(self, obj):
        return obj.authors.count()


class UserSkillsSerializer(serializers.ModelSerializer):
    skill_title = serializers.CharField(source='skill.title', read_only=True)

    class Meta:
        model = UserSkills
        fields = ('id', 'skill_title', 'level', 'experience')


class CategoryTasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryTasks
        fields = ('id', 'title', 'slug')


class TaskSerializer(serializers.ModelSerializer):
    category = CategoryTasksSerializer(many=True, read_only=True)
    rewards = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = (
            'id', 'title', 'slug', 'description',
            'difficult', 'category', 'rewards'
        )

    def get_rewards(self, obj):
        return [skill.title for skill in obj.rewards.all()]


class UsersTasksSerializer(serializers.ModelSerializer):
    task = TaskSerializer(read_only=True)
    initiator = SlifeUserSerializer(read_only=True)
    target_user = SlifeUserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    invitation_url = serializers.SerializerMethodField()

    class Meta:
        model = UsersTasks
        fields = (
            'id', 'task', 'initiator', 'target_user',
            'target_user_name', 'status', 'status_display', 'rating',
            'started_at', 'completed_at', 'confirmed_at', 'invitation_url'
        )
        read_only_fields = ('initiator', 'started_at', 'completed_at', 'confirmed_at')

    def get_invitation_url(self, obj):
        request = self.context.get('request')
        if request and obj.status == 'started':
            return request.build_absolute_uri(obj.get_invitation_url())
        return None


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ('token', 'device_type')
