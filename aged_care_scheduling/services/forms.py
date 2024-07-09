from django import forms
from .models import ServiceType, Service, ResidentPreference, BlockedTime, Escalation
from django.core.exceptions import ValidationError
from residents.models import Resident
from django.contrib.auth.models import User
import json
from .models import ResidentServiceFrequency, ServiceType
import calendar

class ResidentServiceFrequencyForm(forms.ModelForm):
    class Meta:
        model = ResidentServiceFrequency
        fields = ['service_type', 'period', 'start_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        resident = kwargs.pop('resident', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        
        return cleaned_data
    
class ServiceTypeForm(forms.ModelForm):
    class Meta:
        model = ServiceType
        fields = ['name', 'description', 'duration', 'is_companion_service']
        widgets = {
            'duration': forms.TextInput(attrs={'placeholder': 'HH:MM:SS'}),
        }

class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ['resident', 'service_type', 'caregiver', 'scheduled_time', 'status', 'completion_reason', 'reschedule_reason', 'completion_notes']
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'completion_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['completion_reason'].required = False
        self.fields['reschedule_reason'].required = False
        self.fields['completion_notes'].required = False
        self.fields['resident'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        completion_reason = cleaned_data.get('completion_reason')
        reschedule_reason = cleaned_data.get('reschedule_reason')

        if status == 'completed':
            if not completion_reason:
                self.add_error('completion_reason', "Please provide a completion reason for completed services.")
            if reschedule_reason:
                self.add_error('reschedule_reason', "Reschedule reason should not be provided for completed services.")
        
        elif status == 'not_completed':
            if not reschedule_reason:
                self.add_error('reschedule_reason', "Please provide a reason for not completing the service.")
            if completion_reason:
                self.add_error('completion_reason', "Completion reason should not be provided for not completed services.")
        
        elif status == 'refused':
            if completion_reason != 'refused':
                self.add_error('completion_reason', "Completion reason for refused services should be 'refused'.")
            if reschedule_reason:
                self.add_error('reschedule_reason', "Reschedule reason should not be provided for refused services.")

        return cleaned_data

    def save(self, commit=True):
        service = super().save(commit=False)
        
        if service.status == 'refused':
            service.mark_as_refused()
        elif service.status == 'not_completed':
            service.mark_as_not_completed(service.reschedule_reason)
        elif service.status == 'completed':
            service.mark_as_completed(service.completion_reason)

        if commit:
            service.save()
        return service
        
class ResidentPreferenceForm(forms.ModelForm):
    class Meta:
        model = ResidentPreference
        fields = ['resident', 'service_type', 'preferred_days', 'preferred_time_start', 'preferred_time_end']

class BlockedTimeForm(forms.ModelForm):
    class Meta:
        model = BlockedTime
        fields = ['start_time', 'end_time', 'reason']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class EscalationForm(forms.ModelForm):
    class Meta:
        model = Escalation
        fields = ['escalation_type', 'reason', 'resolved', 'resolved_by', 'resolution_notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resolved_by'].queryset = User.objects.filter(userprofile__role='manager')