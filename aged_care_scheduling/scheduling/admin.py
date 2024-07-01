from django.contrib import admin
from .models import Schedule, BlockedTime

admin.site.register(Schedule)
admin.site.register(BlockedTime)