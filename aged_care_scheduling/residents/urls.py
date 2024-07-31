from django.urls import path
from .views import ResidentListView, ResidentDetailView, ResidentCreateView, ResidentUpdateView, ResidentDeleteView, ResidentDashboardView, ResidentServiceListView, DeleteAllServicesView, ServiceFrequencyUpdateView, ServiceFrequencyDeleteView

app_name = "residents"

urlpatterns = [
    path('', ResidentListView.as_view(), name='resident_list'),
    path('<int:pk>/', ResidentDetailView.as_view(), name='resident_detail'),
    path('new/', ResidentCreateView.as_view(), name='resident_create'),
    path('<int:pk>/edit/', ResidentUpdateView.as_view(), name='resident_update'),
    path('<int:pk>/delete/', ResidentDeleteView.as_view(), name='resident_delete'),
    path('resident/<int:pk>/dashboard/', ResidentDashboardView.as_view(), name='resident_dashboard'),
    path('resident/<int:resident_id>/services/', ResidentServiceListView.as_view(), name='resident_service_list'),
    path('resident/<int:resident_id>/delete-all-services/', DeleteAllServicesView.as_view(), name='delete_all_resident_services'),
    path('<int:pk>/dashboard/', ResidentDashboardView.as_view(), name='resident_dashboard'),
    path('service-frequency/<int:pk>/edit/', ServiceFrequencyUpdateView.as_view(), name='service_frequency_update'),
    path('service-frequency/<int:pk>/delete/', ServiceFrequencyDeleteView.as_view(), name='service_frequency_delete'),
]