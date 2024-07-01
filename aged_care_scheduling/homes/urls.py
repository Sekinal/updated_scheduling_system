from django.urls import path
from .views import (
    CareHomeListView, CareHomeDetailView, CareHomeCreateView, 
    CareHomeUpdateView, CareHomeDeleteView, toggle_care_home_status
)

app_name = 'care_homes'  # Add namespace

urlpatterns = [
    path('', CareHomeListView.as_view(), name='home_list'),
    path('<int:pk>/', CareHomeDetailView.as_view(), name='home_detail'),
    path('add/', CareHomeCreateView.as_view(), name='home_add'),
    path('<int:pk>/edit/', CareHomeUpdateView.as_view(), name='home_edit'),
    path('<int:pk>/delete/', CareHomeDeleteView.as_view(), name='home_delete'),
    path('<int:pk>/toggle-status/', toggle_care_home_status, name='home_toggle_status'),
]