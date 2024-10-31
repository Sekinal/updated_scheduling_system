from django.db import models
import pytz

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

    def save(self, *args, **kwargs):
        if not self.pk and SiteSettings.objects.exists():
            # Only allow one instance
            return
        return super(SiteSettings, self).save(*args, **kwargs)