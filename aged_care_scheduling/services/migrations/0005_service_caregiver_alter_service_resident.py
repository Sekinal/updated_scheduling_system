# Generated by Django 5.0.6 on 2024-06-30 16:04

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0004_remove_blockedtime_resident'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='caregiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='caregiver_services', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='service',
            name='resident',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='resident_services', to=settings.AUTH_USER_MODEL),
        ),
    ]
