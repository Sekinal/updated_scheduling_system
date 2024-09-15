from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='service_calendar'),
    path('events/', views.get_events, name='get_events'),
    path('get_unscheduled_services/', views.get_unscheduled_services, name='get_unscheduled_services')
]