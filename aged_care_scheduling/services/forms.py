# services/forms.py

from django import forms
from .models import ServiceType, Service, ResidentPreference, BlockedTime, Escalation
from django.core.exceptions import ValidationError
from residents.models import Resident
import uuid
from django.db import transaction
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.models import User
import json
from homes.models import CareHome
from .models import ResidentServiceFrequency, ServiceType
import calendar
from django.utils import timezone


class ResidentServiceFrequencyForm(forms.ModelForm):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    preferred_days = forms.MultipleChoiceField(
        choices=DAYS_OF_WEEK,
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    caregiver = forms.ModelChoiceField(
        queryset=User.objects.filter(userprofile__role='staff'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
        
    RECURRENCE_END_CHOICES = [
        ('never', 'Never'),
        ('after', 'After'),
        ('on_date', 'On Date'),
    ]

    recurrence_end = forms.ChoiceField(choices=RECURRENCE_END_CHOICES, 
                                    initial='never', 
                                    widget=forms.RadioSelect)
    occurrences = forms.IntegerField(required=False, min_value=1)

    class Meta:
        model = ResidentServiceFrequency
        fields = ['resident', 'service_type', 'recurrence_pattern', 'frequency', 'preferred_days', 'start_time', 'end_time', 'start_date', 'recurrence_end', 'occurrences', 'end_date', 'caregiver']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time', 'id': 'id_start_time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'id': 'id_end_time'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'service_type': forms.Select(attrs={'id': 'id_service_type'}),
        }

    def __init__(self, *args, **kwargs):
        self.resident = kwargs.pop('resident', None)
        super().__init__(*args, **kwargs)
        if self.resident:
            self.fields['resident'].initial = self.resident
            self.fields['resident'].widget.attrs['readonly'] = True
            self.fields['resident'].widget.attrs['style'] = 'pointer-events: none;'
        
        self.fields['preferred_days'].required = False  # Set the field as not required
        self.fields['caregiver'].queryset = User.objects.filter(userprofile__role='staff')
        # If recurrence pattern is already set to daily or monthly, hide the preferred days field
        if self.instance.recurrence_pattern in ['daily', 'monthly']:
            self.fields['preferred_days'].widget = forms.HiddenInput()

    def clean_preferred_days(self):
        preferred_days = self.cleaned_data.get('preferred_days')
        recurrence_pattern = self.cleaned_data.get('recurrence_pattern')

        if recurrence_pattern in ['daily', 'monthly', 'yearly']:
            return json.dumps([])  # Return an empty list for daily, monthly, yearly
        elif recurrence_pattern == 'weekly':
            if not preferred_days:
                raise forms.ValidationError("Please select at least one day for weekly recurrence.")
            return json.dumps([int(day) for day in preferred_days])
    
    def clean(self):
        cleaned_data = super().clean()
        recurrence_pattern = cleaned_data.get('recurrence_pattern')
        preferred_days = cleaned_data.get('preferred_days')
        
        if recurrence_pattern == 'daily' or recurrence_pattern == 'monthly' or recurrence_pattern == 'yearly':
            cleaned_data['preferred_days'] = []  # Clear any selected days when the pattern is daily
        if recurrence_pattern == 'weekly' and not preferred_days:
            raise forms.ValidationError("Please select at least one day for weekly recurrence.")
        recurrence_end = cleaned_data.get('recurrence_end')
        occurrences = cleaned_data.get('occurrences')
        end_date = cleaned_data.get('end_date')

        if recurrence_end == 'after' and not occurrences:
            self.add_error('occurrences', 'Please specify the number of occurrences.')
        elif recurrence_end == 'on_date' and not end_date:
            self.add_error('end_date', 'Please specify an end date.')

        return cleaned_data


    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.resident:
            instance.resident = self.resident
        if commit:
            instance.save()
        return instance

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
        fields = [
            'resident',
            'service_type',
            'caregiver',
            'scheduled_time',
            'end_time',
            'status',
            'completion_reason',
            'reschedule_reason',
            'completion_notes',
        ]
        widgets = {
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'completion_notes': forms.Textarea(attrs={'rows': 3}),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        completion_reason = cleaned_data.get('completion_reason')
        reschedule_reason = cleaned_data.get('reschedule_reason')

        if status == 'completed' and not completion_reason:
            self.add_error('completion_reason', "Completion reason is required when status is 'completed'.")

        if status == 'not_completed' and not reschedule_reason:
            self.add_error('reschedule_reason', "Reschedule reason is required when status is 'not_completed'.")

        if status == 'unscheduled':
            # Optionally, ensure that scheduled_time and end_time are cleared
            cleaned_data['scheduled_time'] = None
            cleaned_data['end_time'] = None

        return cleaned_data

    def save(self, commit=True):
        service = super().save(commit=False)

        if service.status == 'scheduled' and not service.scheduled_time:
            service.scheduled_time = timezone.now()
            service.end_time = service.scheduled_time + service.service_type.duration

        if service.status == 'refused':
            service.mark_as_refused()
        elif service.status == 'not_completed':
            service.mark_as_not_completed(service.reschedule_reason)
        elif service.status == 'completed':
            service.mark_as_completed(service.completion_reason)
        elif service.status == 'unscheduled':
            # Ensure scheduled_time and end_time are cleared
            service.scheduled_time = None
            service.end_time = None

        if commit:
            service.save()
        return service
        
class ResidentPreferenceForm(forms.ModelForm):
    class Meta:
        model = ResidentPreference
        fields = ['resident', 'service_type', 'preferred_days', 'preferred_time_start', 'preferred_time_end']

# services/forms.py

class BlockedTimeForm(forms.ModelForm):
    caregivers = forms.ModelMultipleChoiceField(
        queryset=User.objects.filter(userprofile__role='staff'),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )
    locations = forms.ModelMultipleChoiceField(
        queryset=CareHome.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=False
    )

    class Meta:
        model = BlockedTime
        fields = ['caregivers', 'locations', 'start_date', 'start_time', 'end_date', 'end_time', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }

class EscalationForm(forms.ModelForm):
    class Meta:
        model = Escalation
        fields = ['escalation_type', 'reason', 'resolved', 'resolved_by', 'resolution_notes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resolved_by'].queryset = User.objects.filter(userprofile__role='manager')