# core/middleware.py
from django.utils import timezone
from core.models import SiteSettings
import pytz

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            settings = SiteSettings.objects.first()
            if settings and settings.timezone in dict(pytz.all_timezones):
                timezone.activate(settings.timezone)
            else:
                timezone.deactivate()
        except Exception as e:
            # Log the exception for debugging purposes
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"TimezoneMiddleware error: {e}")
            timezone.deactivate()
        
        response = self.get_response(request)
        return response