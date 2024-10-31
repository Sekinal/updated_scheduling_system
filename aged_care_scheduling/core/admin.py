from django.contrib import admin
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only allow one instance
        if self.model.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion
        return False