from rest_framework import serializers
from homes.models import CareHome
from residents.models import Resident

class CareHomeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareHome
        fields = ['id', 'name', 'address', 'capacity', 'is_active']

class ResidentSerializer(serializers.ModelSerializer):
    care_home = CareHomeSerializer(read_only=True)

    class Meta:
        model = Resident
        fields = ['id', 'first_name', 'last_name', 'date_of_birth', 'admission_date', 'care_home']