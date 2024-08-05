from django.urls import path
from .views import CareHomeListView, ResidentListView
from services.views import get_service_type_duration

app_name = 'api'

urlpatterns = [
    path('care-homes/', CareHomeListView.as_view(), name='care_homes_list'),
    path('residents/', ResidentListView.as_view(), name='residents_list'),
    path('service-type/<int:service_type_id>/duration/', get_service_type_duration, name='get_service_type_duration'),

]