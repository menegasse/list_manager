# Generated by Django 4.0.4 on 2022-05-20 01:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0004_alter_list_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listitem',
            name='is_public',
        ),
        migrations.AddField(
            model_name='list',
            name='threshold',
            field=models.DecimalField(blank=True, decimal_places=2, default=None, help_text='What is the total threshold value of the list items?', max_digits=20, null=True, verbose_name='Threshold Value'),
        ),
    ]
