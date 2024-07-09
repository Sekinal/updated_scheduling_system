from django import forms
from .models import Resident
class ResidentForm(forms.ModelForm):
    class Meta:
        model = Resident
        fields = ['first_name', 'last_name', 'date_of_birth', 'care_home', 'admission_date', 'emergency_email', 'emergency_phone']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'admission_date': forms.DateInput(attrs={'type': 'date'}),
        }