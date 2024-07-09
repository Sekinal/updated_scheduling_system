# Generated by Django 5.0.6 on 2024-07-08 20:09

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('residents', '0006_delete_residentservicefrequency'),
        ('services', '0011_alter_service_recurrence'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='service',
            name='recurrence',
        ),
        migrations.CreateModel(
            name='ResidentServiceFrequency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], max_length=10)),
                ('resident', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_frequencies', to='residents.resident')),
                ('service_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='services.servicetype')),
            ],
            options={
                'unique_together': {('resident', 'service_type')},
            },
        ),
    ]
