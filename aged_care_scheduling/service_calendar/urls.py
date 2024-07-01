from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='service_calendar'),
    path('events/', views.get_events, name='get_events'),
    path('report/', views.generate_report, name='generate_report'),
]