# Generated by Django 5.0.6 on 2024-07-19 13:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0027_service_due_date_alter_service_scheduled_time_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UnscheduledService',
        ),
    ]