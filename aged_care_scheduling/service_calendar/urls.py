from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendar_view, name='service_calendar'),
    path('events/', views.get_events, name='get_events'),
    path('report/', views.generate_report, name='generate_report'),
    path('planner/', views.planner_view, name='planner_view'),
    path('get_events/', views.get_events, name='get_events'),
    path('update_service/', views.update_service, name='update_service'),
    path('update_service_status/', views.update_service_status, name='update_service_status'),
    path('get_unscheduled_services/', views.get_unscheduled_services, name='get_unscheduled_services'),  # Fixed this line
    path('create_service/', views.create_service, name='create_service'),  # Add this line
    path('save_schedule/', views.save_schedule, name='save_schedule'),
    path('unschedule_service/', views.unschedule_service, name='unschedule_service'),
]