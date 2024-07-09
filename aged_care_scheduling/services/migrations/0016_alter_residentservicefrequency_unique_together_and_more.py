# Generated by Django 5.0.6 on 2024-07-09 02:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('residents', '0006_delete_residentservicefrequency'),
        ('services', '0015_remove_residentservicefrequency_start_time_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='residentservicefrequency',
            unique_together={('resident', 'service_type')},
        ),
        migrations.RemoveField(
            model_name='residentservicefrequency',
            name='day_of_week',
        ),
    ]
