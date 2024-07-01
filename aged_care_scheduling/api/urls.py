from django.urls import path
from .views import CareHomeListView, ResidentListView

app_name = 'api'

urlpatterns = [
    path('care-homes/', CareHomeListView.as_view(), name='care_homes_list'),
    path('residents/', ResidentListView.as_view(), name='residents_list'),
]