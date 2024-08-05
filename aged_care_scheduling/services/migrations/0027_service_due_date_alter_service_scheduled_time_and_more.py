# Generated by Django 5.0.6 on 2024-07-19 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0026_unscheduledservice'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='due_date',
            field=models.DateField(null=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='scheduled_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='service',
            name='status',
            field=models.CharField(choices=[('unscheduled', 'Unscheduled'), ('scheduled', 'Scheduled'), ('completed', 'Completed'), ('not_completed', 'Not Completed'), ('refused', 'Refused'), ('missed', 'Missed')], default='unscheduled', max_length=20),
        ),
    ]