from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from homes.models import CareHome
from residents.models import Resident
from .serializers import CareHomeSerializer, ResidentSerializer

class CareHomeListView(generics.ListAPIView):
    queryset = CareHome.objects.all()
    serializer_class = CareHomeSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'address']
    filterset_fields = ['is_active']

class ResidentListView(generics.ListAPIView):
    queryset = Resident.objects.all()
    serializer_class = ResidentSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['first_name', 'last_name']
    filterset_fields = ['care_home']