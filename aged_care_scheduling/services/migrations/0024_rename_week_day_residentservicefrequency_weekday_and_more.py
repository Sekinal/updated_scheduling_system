# Generated by Django 5.0.6 on 2024-07-18 09:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0023_residentservicefrequency_month_day_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='residentservicefrequency',
            old_name='week_day',
            new_name='weekday',
        ),
        migrations.RemoveField(
            model_name='residentservicefrequency',
            name='month_day',
        ),
    ]
