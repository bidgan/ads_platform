# Generated by Django 5.0.4 on 2024-05-06 07:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_remove_advertisement_is_data_sent_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Dialog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user1', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dialog_user1', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь 1')),
                ('user2', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='dialog_user2', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь 2')),
            ],
            options={
                'verbose_name': 'Диалог',
                'verbose_name_plural': 'Диалоги',
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(max_length=1024, verbose_name='Текст сообщения')),
                ('dialog', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.dialog', verbose_name='Диалог')),
                ('sender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Отправитель')),
            ],
            options={
                'verbose_name': 'Сообщение',
                'verbose_name_plural': 'Сообщения',
            },
        ),
    ]
