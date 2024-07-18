# Generated by Django 5.0.6 on 2024-07-18 06:42

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('residents', '0006_delete_residentservicefrequency'),
        ('services', '0017_alter_residentservicefrequency_unique_together'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='residentservicefrequency',
            unique_together={('resident', 'service_type')},
        ),
        migrations.AddField(
            model_name='residentservicefrequency',
            name='recurrence_days',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.IntegerField(), blank=True, null=True, size=None),
        ),
        migrations.AddField(
            model_name='residentservicefrequency',
            name='recurrence_interval',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='residentservicefrequency',
            name='recurrence_period',
            field=models.CharField(choices=[('day', 'Day(s)'), ('week', 'Week(s)'), ('month', 'Month(s)')], max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='residentservicefrequency',
            name='start_date',
            field=models.DateTimeField(),
        ),
        migrations.RemoveField(
            model_name='residentservicefrequency',
            name='period',
        ),
    ]