# services/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ServiceListView.as_view(), name='service_list'),
    path('create/', views.ServiceCreateView.as_view(), name='service_create'),
    path('<int:pk>/update/', views.ServiceUpdateView.as_view(), name='service_update'),
    path('<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),
    path('resident/<int:resident_id>/', views.ResidentServiceListView.as_view(), name='resident_service_list'),
    path('preference/create/', views.ResidentPreferenceCreateView.as_view(), name='resident_preference_create'),
    path('preference/', views.ResidentPreferenceListView.as_view(), name='resident_preference_list'),
    path('blocked-times/', views.BlockedTimeListView.as_view(), name='blocked_time_list'),
    path('blocked-times/create/', views.BlockedTimeCreateView.as_view(), name='blocked_time_create'),
    path('blocked-times/<int:pk>/update/', views.BlockedTimeUpdateView.as_view(), name='blocked_time_update'),
    path('blocked-times/<int:pk>/delete/', views.BlockedTimeDeleteView.as_view(), name='blocked_time_delete'),
    path('escalations/', views.EscalationListView.as_view(), name='escalation_list'),
    path('service-types/', views.ServiceTypeListView.as_view(), name='service_type_list'),
    path('service-types/create/', views.ServiceTypeCreateView.as_view(), name='service_type_create'),
    path('service-types/<int:pk>/update/', views.ServiceTypeUpdateView.as_view(), name='service_type_update'),
    path('service-types/<int:pk>/delete/', views.ServiceTypeDeleteView.as_view(), name='service_type_delete'),
    path('<int:pk>/update-status/', views.ServiceStatusUpdateView.as_view(), name='service_status_update'),
    path('escalations/', views.EscalationListView.as_view(), name='escalation_list'),
    path('escalations/<int:pk>/update/', views.EscalationUpdateView.as_view(), name='escalation_update'),
    path('check-missed-services/', views.check_missed_services, name='check_missed_services'),
    path('resident/<int:resident_id>/services/', views.ResidentServiceListView.as_view(), name='resident_service_list'),
    path('delete-all-services/', views.DeleteAllServicesView.as_view(), name='delete_all_services'),
    path('edit-service-frequency/<uuid:pk>/', views.edit_service_frequency, name='edit_service_frequency'),
    path('edit-service-frequency/<int:pk>/', views.edit_service_frequency, name='edit_service_frequency'),
    path('delete-service-frequency/<int:pk>/', views.delete_service_frequency, name='delete_service_frequency'),
    path('resident/<int:resident_id>/add-service-frequency/', views.add_service_frequency, name='add_service_frequency'),
]