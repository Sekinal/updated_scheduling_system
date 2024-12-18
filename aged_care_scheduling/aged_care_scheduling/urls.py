from django.contrib import admin
from django.urls import path, include
from .views import dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('homes/', include('homes.urls')),
    path('services/', include('services.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('residents/', include('residents.urls', namespace='residents')),
    path('service-calendar/', include('service_calendar.urls')),
    path('api/', include('api.urls')),
    path('', dashboard_view, name='dashboard'),
]