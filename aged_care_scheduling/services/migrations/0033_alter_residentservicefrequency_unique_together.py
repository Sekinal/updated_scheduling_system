# Generated by Django 5.0.6 on 2024-07-31 14:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0032_alter_residentservicefrequency_id'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='residentservicefrequency',
            unique_together=set(),
        ),
    ]
