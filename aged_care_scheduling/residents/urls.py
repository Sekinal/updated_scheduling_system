from django.urls import path
from .views import ResidentDetailView, ResidentCreateView, ResidentUpdateView, ResidentDeleteView, ResidentDashboardView

app_name = "residents"

urlpatterns = [
    path('<int:pk>/', ResidentDetailView.as_view(), name='resident_detail'),
    path('new/', ResidentCreateView.as_view(), name='resident_create'),
    path('<int:pk>/edit/', ResidentUpdateView.as_view(), name='resident_update'),
    path('<int:pk>/delete/', ResidentDeleteView.as_view(), name='resident_delete'),
    path('resident/<int:pk>/dashboard/', ResidentDashboardView.as_view(), name='resident_dashboard'),
]