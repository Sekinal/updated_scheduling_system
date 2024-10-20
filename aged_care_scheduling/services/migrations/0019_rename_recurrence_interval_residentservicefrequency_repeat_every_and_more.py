# Generated by Django 5.0.6 on 2024-07-18 06:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('residents', '0006_delete_residentservicefrequency'),
        ('services', '0018_alter_residentservicefrequency_unique_together_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='residentservicefrequency',
            old_name='recurrence_interval',
            new_name='repeat_every',
        ),
        migrations.RenameField(
            model_name='residentservicefrequency',
            old_name='recurrence_days',
            new_name='repeat_on',
        ),
        migrations.AlterUniqueTogether(
            name='residentservicefrequency',
            unique_together={('resident', 'service_type', 'start_date')},
        ),
        migrations.AddField(
            model_name='residentservicefrequency',
            name='end_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='residentservicefrequency',
            name='repeat_period',
            field=models.CharField(choices=[('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')], default='day', max_length=10),
        ),
        migrations.AlterField(
            model_name='residentservicefrequency',
            name='start_date',
            field=models.DateField(),
        ),
        migrations.RemoveField(
            model_name='residentservicefrequency',
            name='recurrence_period',
        ),
    ]
