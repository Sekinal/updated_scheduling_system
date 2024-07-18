# Generated by Django 5.0.6 on 2024-07-18 07:29

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0019_rename_recurrence_interval_residentservicefrequency_repeat_every_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='residentservicefrequency',
            name='repeat_on',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.PositiveSmallIntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')]), blank=True, null=True, size=None),
        ),
    ]
