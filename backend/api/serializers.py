from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from user_service.models import Subscribe, UserSkills
from challenge_engine.models import Task, CategoryTasks, UsersTasks, TaskRewards


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


class TaskRewardSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='reward.title')
    quantity = serializers.IntegerField()
    is_additional = serializers.BooleanField()
    description = serializers.CharField(source='additional_reward_description')

    class Meta:
        model = TaskRewards
        fields = ('title', 'quantity', 'is_additional', 'description')


class TaskBriefSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения задания"""
    category = CategoryTasksSerializer(many=True, read_only=True)
    rewards = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'short_description', 'rewards', 'category', 'difficulty']

    def get_rewards(self, obj):
        rewards = obj.task_rewards.filter(is_additional=False)
        return [{
            'title': reward.reward.title,
            'quantity': reward.quantity
        } for reward in rewards]


class TaskFullSerializer(serializers.ModelSerializer):
    """Сериализатор для полной информации о задании"""
    category = CategoryTasksSerializer(many=True, read_only=True)
    rewards = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'rewards', 'difficulty', 'hint', 'category']

    def get_rewards(self, obj):
        rewards = obj.task_rewards.all()
        return [{
            'title': reward.reward.title,
            'quantity': reward.quantity,
            'is_additional': reward.is_additional,
            'description': reward.additional_reward_description if reward.is_additional else None
        } for reward in rewards]


class UsersTasksListSerializer(serializers.ModelSerializer):
    task = TaskBriefSerializer(read_only=True)
    rating = serializers.SerializerMethodField()
    target_user_info = serializers.SerializerMethodField()
    confirmation_id = serializers.CharField(read_only=True)

    class Meta:
        model = UsersTasks
        fields = (
            'id', 'task', 'status', 'rating',
            'started_at', 'completed_at', 'confirmed_at',
            'target_user_info', 'confirmation_id'
        )

    def get_rating(self, obj):
        if obj.status == 'confirmed':
            return obj.rating
        return None

    def get_target_user_info(self, obj):
        if obj.target_user:
            return obj.target_user.username
        return obj.target_user_name


class UsersTasksDetailSerializer(serializers.ModelSerializer):
    task = TaskFullSerializer(read_only=True)
    target_user_info = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    confirmation_id = serializers.SerializerMethodField()

    class Meta:
        model = UsersTasks
        fields = (
            'id', 'task', 'target_user_info', 'status',
            'rating', 'started_at', 'completed_at', 'confirmed_at',
            'confirmation_id'
        )

    def get_target_user_info(self, obj):
        if obj.target_user:
            return obj.target_user.username
        return obj.target_user_name

    def get_rating(self, obj):
        if obj.status == 'confirmed':
            return obj.rating
        return None

    def get_confirmation_id(self, obj):
        if obj.status == 'started':
            return obj.generate_confirmation_id()
        return None
