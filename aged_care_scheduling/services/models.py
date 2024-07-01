from django.db import models
from django.core.exceptions import ValidationError
from residents.models import Resident, VisitHistory
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.db.models import Q
from django.db import transaction
import json

class ServiceType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.DurationField(help_text="Expected duration of the service", default=timedelta(hours=1))
    is_companion_service = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Service(models.Model):
    SERVICE_STATUS = (
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('not_completed', 'Not Completed'),
        ('refused', 'Refused'),
    )

    COMPLETION_REASONS = (
        ('completed', 'Service Completed'),
        ('refused', 'Refused Service'),
        ('family_visit_no_notice', 'Family Visit (No Notice)'),
    )

    RESCHEDULE_REASONS = (
        ('hospital', 'Hospital'),
        ('illness', 'Illness'),
        ('isolation', 'Isolation'),
        ('approved_family_visit', 'Approved Family Visit'),
    )

    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE, related_name='services')
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE)
    caregiver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    scheduled_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=SERVICE_STATUS, default='scheduled')
    completion_reason = models.CharField(max_length=50, choices=COMPLETION_REASONS, blank=True, null=True)
    reschedule_reason = models.CharField(max_length=50, choices=RESCHEDULE_REASONS, blank=True, null=True)
    completion_notes = models.TextField(blank=True, null=True)
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True)
    refusal_count = models.PositiveIntegerField(default=0)
    last_refusal_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.end_time:
            self.end_time = self.scheduled_time + self.service_type.duration
        self.check_conflicts()
        super().save(*args, **kwargs)

    def check_conflicts(self):
        conflicts = Service.objects.filter(
            Q(resident=self.resident) | Q(caregiver=self.caregiver),
            scheduled_time__lt=self.end_time,
            end_time__gt=self.scheduled_time
        ).exclude(pk=self.pk)

        blocked_times = BlockedTime.objects.filter(
            Q(start_time__lt=self.end_time, end_time__gt=self.scheduled_time) |
            Q(start_time__lte=self.scheduled_time, end_time__gte=self.end_time)
        )

        if conflicts.exists():
            raise ValidationError("This service conflicts with an existing service for the resident or caregiver.")
        
        if blocked_times.exists():
            raise ValidationError("This service is scheduled during a blocked time period.")

    def mark_as_completed(self, reason='completed'):
        self.status = 'completed'
        self.completion_reason = reason
        self.save()
        VisitHistory.objects.create(resident=self.resident, service=self, visit_time=timezone.now())

    def mark_as_not_completed(self, reason):
        self.status = 'not_completed'
        self.reschedule_reason = reason
        self.save()
        return self.reschedule()

    def mark_as_refused(self):
        self.status = 'refused'
        self.completion_reason = 'refused'
        self.refusal_count += 1
        self.last_refusal_date = timezone.now().date()
        self.save()

        if self.refusal_count >= 3:
            Escalation.objects.create(
                resident=self.resident,
                service_type=self.service_type,
                escalation_type='refusal',
                reason=f"Service refused {self.refusal_count} times"
            )


    def reschedule(self):
        next_available_time = self.find_next_available_slot()
        if next_available_time:
            new_service = Service.objects.create(
                resident=self.resident,
                service_type=self.service_type,
                caregiver=self.caregiver,
                scheduled_time=next_available_time,
                status='scheduled'
            )
            
            return new_service

        return None

    def find_next_available_slot(self):
        start_date = self.scheduled_time.date() + timedelta(days=1)
        end_date = start_date + timedelta(days=7)  # Look for slots in the next 7 days
        
        resident_preference = ResidentPreference.objects.filter(
            resident=self.resident,
            service_type=self.service_type
        ).first()

        if resident_preference:
            preferred_days = json.loads(resident_preference.preferred_days)
            preferred_start = resident_preference.preferred_time_start
            preferred_end = resident_preference.preferred_time_end
        else:
            preferred_days = list(range(7))  # All days if no preference
            preferred_start = timezone.datetime.min.time()
            preferred_end = timezone.datetime.max.time()

        for day in range((end_date - start_date).days + 1):
            current_date = start_date + timedelta(days=day)
            
            if current_date.weekday() not in preferred_days:
                continue

            for hour in range(24):
                for minute in [0, 30]:  # Check every 30 minutes
                    proposed_time = timezone.make_aware(
                        timezone.datetime.combine(current_date, timezone.datetime.min.time()) 
                        + timedelta(hours=hour, minutes=minute)
                    )
                    
                    if not (preferred_start <= proposed_time.time() <= preferred_end):
                        continue

                    proposed_end_time = proposed_time + self.service_type.duration

                    # Check for conflicts with other services
                    conflicting_services = Service.objects.filter(
                        Q(resident=self.resident) | Q(caregiver=self.caregiver),
                        scheduled_time__lt=proposed_end_time,
                        end_time__gt=proposed_time
                    ).exclude(pk=self.pk)

                    if conflicting_services.exists():
                        continue

                    # Check for conflicts with blocked times
                    conflicting_blocked_times = BlockedTime.objects.filter(
                        Q(start_time__lt=proposed_end_time, end_time__gt=proposed_time) |
                        Q(start_time__lte=proposed_time, end_time__gte=proposed_end_time)
                    )

                    if conflicting_blocked_times.exists():
                        continue

                    # If we've made it here, we've found an available slot
                    return proposed_time

        # If no slot found, return None
        return None

    @classmethod
    def check_missed_services(cls):
        yesterday = timezone.now().date() - timedelta(days=1)
        missed_services = cls.objects.filter(
            Q(scheduled_time__date=yesterday) & 
            Q(status='scheduled')
        )
        
        for service in missed_services:
            Escalation.objects.create(
                resident=service.resident,
                service_type=service.service_type,
                escalation_type='missed',
                reason="Service not recorded"
            )

    def __str__(self):
        return f"{self.service_type} for {self.resident} at {self.scheduled_time}"

class Escalation(models.Model):
    ESCALATION_TYPES = (
        ('refusal', 'Service Refusal'),
        ('missed', 'Missed Service'),
    )

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    escalation_type = models.CharField(max_length=20, choices=ESCALATION_TYPES, null=True)
    reason = models.CharField(max_length=100)
    date_created = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_escalations')
    resolution_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Escalation for {self.resident} - {self.service_type} ({self.escalation_type})"

class ResidentPreference(models.Model):
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE)
    service_type = models.ForeignKey(ServiceType, on_delete=models.CASCADE)
    preferred_days = models.CharField(max_length=100)  # Store as JSON string
    preferred_time_start = models.TimeField()
    preferred_time_end = models.TimeField()

    class Meta:
        unique_together = ('resident', 'service_type')

    def __str__(self):
        return f"Preference for {self.resident} - {self.service_type}"

class BlockedTime(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    reason = models.CharField(max_length=100)

    def __str__(self):
        return f"Blocked time: {self.start_time} - {self.end_time}"