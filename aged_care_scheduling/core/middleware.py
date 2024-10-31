from django.utils import timezone
from .models import SiteSettings

class TimezoneMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            settings = SiteSettings.objects.first()
            if settings:
                timezone.activate(settings.timezone)
            else:
                timezone.deactivate()
        except Exception:
            timezone.deactivate()
        
        return self.get_response(request)