# Generated by Django 5.0.4 on 2024-05-04 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0012_review_identity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='advertisement',
            name='is_data_sent',
        ),
        migrations.AddField(
            model_name='review',
            name='is_photo_sent',
            field=models.BooleanField(default=False, verbose_name='Фото отправлено'),
        ),
        migrations.AddField(
            model_name='review',
            name='num_photos',
            field=models.IntegerField(default=0, verbose_name='Количество загруженных фото'),
        ),
    ]
