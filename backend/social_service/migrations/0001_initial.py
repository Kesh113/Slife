# Generated by Django 5.1.7 on 2025-05-11 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('text', models.TextField(max_length=1000, verbose_name='Текст')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('likes_count', models.PositiveBigIntegerField(default=0, editable=False, verbose_name='Лайков')),
            ],
            options={
                'verbose_name': 'Комментарий',
                'verbose_name_plural': 'Комментарии',
                'ordering': ('-pub_date',),
                'default_related_name': 'comments',
            },
        ),
        migrations.CreateModel(
            name='CommentLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('liked_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата лайка')),
            ],
            options={
                'verbose_name': 'Лайк комментария',
                'verbose_name_plural': 'Лайки комментариев',
                'ordering': ['-liked_at'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='social_service/posts/images/', verbose_name='Изображение')),
                ('text', models.TextField(max_length=1000, verbose_name='Текст')),
                ('likes_count', models.PositiveBigIntegerField(default=0, editable=False, verbose_name='Лайков')),
                ('is_published', models.BooleanField(default=True, verbose_name='Опубликовано')),
                ('pub_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')),
                ('updated', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
            ],
            options={
                'verbose_name': 'Пост',
                'verbose_name_plural': 'Посты',
                'ordering': ('-pub_date',),
            },
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('liked_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата лайка')),
            ],
            options={
                'verbose_name': 'Лайк поста',
                'verbose_name_plural': 'Лайки постов',
                'ordering': ['-liked_at'],
                'abstract': False,
            },
        ),
    ]
