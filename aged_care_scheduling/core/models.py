# core/models.py
from django.db import models
import pytz
from django.core.exceptions import ValidationError

class SiteSettings(models.Model):
    TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]
    
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC'
    )
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

    def clean(self):
        if not self.pk and SiteSettings.objects.exists():
            raise ValidationError('Only one SiteSettings instance is allowed.')

    def save(self, *args, **kwargs):
        self.clean()
        super(SiteSettings, self).save(*args, **kwargs)