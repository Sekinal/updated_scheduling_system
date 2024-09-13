# Generated by Django 5.0.6 on 2024-09-12 07:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homes', '0004_carehome_is_active'),
        ('residents', '0006_delete_residentservicefrequency'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='resident',
            options={'verbose_name': 'Resident', 'verbose_name_plural': 'Residents'},
        ),
        migrations.AddField(
            model_name='resident',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Designates whether this resident is currently active in the care home.', verbose_name='Active'),
        ),
        migrations.AlterField(
            model_name='resident',
            name='admission_date',
            field=models.DateField(null=True, verbose_name='Admission Date'),
        ),
        migrations.AlterField(
            model_name='resident',
            name='care_home',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='residents', to='homes.carehome', verbose_name='Care Home'),
        ),
        migrations.AlterField(
            model_name='resident',
            name='date_of_birth',
            field=models.DateField(verbose_name='Date of Birth'),
        ),
        migrations.AlterField(
            model_name='resident',
            name='first_name',
            field=models.CharField(max_length=50, verbose_name='First Name'),
        ),
        migrations.AlterField(
            model_name='resident',
            name='last_name',
            field=models.CharField(max_length=50, verbose_name='Last Name'),
        ),
    ]