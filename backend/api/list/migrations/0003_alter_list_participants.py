# Generated by Django 4.0.3 on 2022-03-27 17:37

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('list', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='list',
            name='participants',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
