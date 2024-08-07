# services/models.py

from django.db import models
from django.core.exceptions import ValidationError
from residents.models import Resident
from django.utils import timezone
from datetime import timedelta
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
import json
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.db import transaction
from datetime import datetime
import uuid
import calendar
from dateutil.relativedelta import relativedelta
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
        ('unscheduled', 'Unscheduled'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('not_completed', 'Not Completed'),
        ('refused', 'Refused'),
        ('missed', 'Missed'),
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
    scheduled_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SERVICE_STATUS, default='unscheduled')
    completion_reason = models.CharField(max_length=50, choices=COMPLETION_REASONS, blank=True, null=True)
    reschedule_reason = models.CharField(max_length=50, choices=RESCHEDULE_REASONS, blank=True, null=True)
    completion_notes = models.TextField(blank=True, null=True)
    refusal_count = models.PositiveIntegerField(default=0)
    last_refusal_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True)
    frequency_id = models.UUIDField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.scheduled_time and self.status == 'unscheduled':
            self.status = 'scheduled'
        if self.scheduled_time and not self.end_time:
            self.end_time = self.scheduled_time + self.service_type.duration
        self.check_conflicts()
        super().save(*args, **kwargs)

    def check_conflicts(self):
        if not self.scheduled_time:
            return  # Skip conflict check for unscheduled services

        conflicts = Service.objects.filter(
            Q(resident=self.resident) | Q(caregiver=self.caregiver),
            scheduled_time__lt=self.end_time,
            end_time__gt=self.scheduled_time,
            status='scheduled'
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
                status='scheduled',
                due_date=next_available_time.date()
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
            Q(due_date=yesterday) & 
            Q(status='unscheduled')
        )
        
        for service in missed_services:
            service.status = 'missed'
            service.save()
            Escalation.objects.create(
                resident=service.resident,
                service_type=service.service_type,
                escalation_type='missed',
                reason="Service not scheduled"
            )

    @classmethod
    def create_recurring_services(cls, resident_service_frequency):
        now = timezone.now().date()
        end_date = now + timedelta(days=30)  # Create services for the next 30 days
        
        current_date = now
        while current_date <= end_date:
            if resident_service_frequency.should_create_service(current_date):
                cls.objects.create(
                    resident=resident_service_frequency.resident,
                    service_type=resident_service_frequency.service_type,
                    status='unscheduled',
                    due_date=current_date
                )
            current_date += timedelta(days=1)

    def __str__(self):
        return f"{self.service_type} for {self.resident} due on {self.due_date}"

class ResidentServiceFrequency(models.Model):
    RECURRENCE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    RECURRENCE_END_CHOICES = [
        ('never', 'Never'),
        ('after', 'After'),
        ('on_date', 'On Date'),
    ]

    resident = models.ForeignKey('residents.Resident', on_delete=models.CASCADE, related_name='service_frequencies')
    service_type = models.ForeignKey('ServiceType', on_delete=models.CASCADE)
    recurrence_pattern = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, null=True)
    frequency = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    preferred_days = models.CharField(max_length=100, default='[]')  # Store as JSON string
    start_time = models.TimeField(null=True)
    end_time = models.TimeField(null=True)
    start_date = models.DateField(default=timezone.now)
    recurrence_end = models.CharField(max_length=10, choices=RECURRENCE_END_CHOICES, default='never')
    occurrences = models.PositiveIntegerField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f"{self.resident} - {self.service_type}: Every {self.frequency} {self.recurrence_pattern} starting {self.start_date}"
    
    def clean(self):
        # Check for overlapping schedules
        overlapping = ResidentServiceFrequency.objects.filter(
            resident=self.resident,
            service_type=self.service_type,
            start_date=self.start_date,
        ).exclude(pk=self.pk)  # Exclude self when updating

        for schedule in overlapping:
            if (self.start_time < schedule.end_time and self.end_time > schedule.start_time):
                raise ValidationError(
                    f"This schedule overlaps with an existing schedule from {schedule.start_time} to {schedule.end_time}"
                )
                
    def save(self, *args, **kwargs):
        self.full_clean()  # This calls clean() and validates model fields
        super().save(*args, **kwargs)

    def create_services(self):
        from .models import Service  # Import here to avoid circular import
        
        current_date = self.start_date
        end_date = self.end_date
        occurrences = 0

        if self.recurrence_pattern == 'daily':
            while True:
                if self.should_create_service(current_date):
                    Service.objects.create(
                        resident=self.resident,
                        service_type=self.service_type,
                        status='unscheduled',
                        due_date=current_date,
                        scheduled_time=timezone.make_aware(datetime.combine(current_date, self.start_time)),
                        end_time=timezone.make_aware(datetime.combine(current_date, self.end_time)),
                        frequency_id=self.id
                    )
                    occurrences += 1

                # Check if we should stop creating services
                if self.recurrence_end == 'never':
                    if current_date >= timezone.now().date() + timedelta(days=365):  # Limit to 1 year in advance
                        break
                elif self.recurrence_end == 'after':
                    if occurrences >= self.occurrences:
                        break
                elif self.recurrence_end == 'on_date':
                    if current_date >= self.end_date:
                        break

                # Move to the next date based on recurrence pattern
                current_date += timedelta(days=self.frequency)

        elif self.recurrence_pattern == 'weekly':
            # Get the selected days of the week
            selected_days = json.loads(self.preferred_days)

            # Calculate the first day of the week that matches the selected days
            first_day = current_date
            while first_day.weekday() not in selected_days:
                first_day += timedelta(days=1)

            # Schedule services on the selected days of the week
            while True:
                for day in range(7):
                    current_date = first_day + timedelta(days=day)
                    if current_date.weekday() in selected_days:
                        if self.should_create_service(current_date):
                            Service.objects.create(
                                resident=self.resident,
                                service_type=self.service_type,
                                status='unscheduled',
                                due_date=current_date,
                                scheduled_time=timezone.make_aware(datetime.combine(current_date, self.start_time)),
                                end_time=timezone.make_aware(datetime.combine(current_date, self.end_time)),
                                frequency_id=self.id
                            )
                            occurrences += 1

                # Check if we should stop creating services
                if self.recurrence_end == 'never':
                    if current_date >= timezone.now().date() + timedelta(days=365):  # Limit to 1 year in advance
                        break
                elif self.recurrence_end == 'after':
                    if occurrences >= self.occurrences:
                        break
                elif self.recurrence_end == 'on_date':
                    if current_date >= self.end_date:
                        break

                # Move to the next week
                first_day += timedelta(days=7 * self.frequency)
                current_date = first_day

        elif self.recurrence_pattern == 'monthly':
            # Get the selected day of the month
            day_of_month = current_date.day

            # Schedule services on the selected day of the month
            while True:
                if self.should_create_service(current_date):
                    Service.objects.create(
                        resident=self.resident,
                        service_type=self.service_type,
                        status='unscheduled',
                        due_date=current_date,
                        scheduled_time=timezone.make_aware(datetime.combine(current_date, self.start_time)),
                        end_time=timezone.make_aware(datetime.combine(current_date, self.end_time)),
                        frequency_id=self.id
                    )
                    occurrences += 1

                # Check if we should stop creating services
                if self.recurrence_end == 'never':
                    if current_date >= timezone.now().date() + timedelta(days=365 * 5):  # Limit to 5 years in advance
                        break
                elif self.recurrence_end == 'after':
                    if occurrences >= self.occurrences:
                        break
                elif self.recurrence_end == 'on_date':
                    if current_date >= self.end_date:
                        break

                # Move to the next month
                current_date += relativedelta(months=self.frequency)
                # Set the day to the selected day of the month
                current_date = current_date.replace(day=day_of_month)
                # If the day does not exist in the month (e.g., February 30), set it to the last day of the month
                if current_date.day != day_of_month:
                    current_date = current_date + relativedelta(day=1, months=1, days=-1)

        elif self.recurrence_pattern == 'yearly':
            # Schedule services on the selected day of the year
            while True:
                if self.should_create_service(current_date):
                    Service.objects.create(
                        resident=self.resident,
                        service_type=self.service_type,
                        status='unscheduled',
                        due_date=current_date,
                        scheduled_time=timezone.make_aware(datetime.combine(current_date, self.start_time)),
                        end_time=timezone.make_aware(datetime.combine(current_date, self.end_time)),
                        frequency_id=self.id
                    )
                    occurrences += 1

                # Check if we should stop creating services
                if self.recurrence_end == 'never':
                    if current_date >= timezone.now().date() + timedelta(days=365 * 10):  # Limit to 10 years in advance
                        break
                elif self.recurrence_end == 'after':
                    if occurrences >= self.occurrences:
                        break
                elif self.recurrence_end == 'on_date':
                    if current_date >= self.end_date:
                        break

                # Move to the next year
                current_date += relativedelta(years=self.frequency)

    def should_create_service(self, date):
        preferred_days = json.loads(self.preferred_days)
        if preferred_days and date.weekday() not in preferred_days:
            return False

        if self.recurrence_pattern == 'daily':
            return (date - self.start_date).days % self.frequency == 0
        elif self.recurrence_pattern == 'weekly':
            return (date - self.start_date).days % (7 * self.frequency) == 0
        elif self.recurrence_pattern == 'monthly':
            return date.day == self.start_date.day and (date.year - self.start_date.year) * 12 + date.month - self.start_date.month % self.frequency == 0
        elif self.recurrence_pattern == 'yearly':
            return date.month == self.start_date.month and date.day == self.start_date.day and (date.year - self.start_date.year) % self.frequency == 0
        return False

    def delete(self, *args, **kwargs):
        # Delete all related services that haven't been completed
        Service.objects.filter(
            resident=self.resident,
            service_type=self.service_type,
            status__in=['unscheduled', 'scheduled'],
            frequency_id=self.id
        ).delete()
        super().delete(*args, **kwargs)

    def update_services(self):
        self.delete_services()
        self.create_services()

    def delete_services(self):
        from .models import Service  # Import here to avoid circular import
        Service.objects.filter(
            resident=self.resident,
            service_type=self.service_type,
            status='scheduled',
            due_date__gte=self.start_date,
            due_date__lte=self.end_date or timezone.now().date() + timedelta(days=365)
        ).delete()

    def get_recurrence_pattern_display(self):
        recurrence_pattern_values = {
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month',
            'yearly': 'year'
        }
        return recurrence_pattern_values[self.recurrence_pattern]

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
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    reason = models.CharField(max_length=100)

    def __str__(self):
        return f"Blocked time: {self.start_time} - {self.end_time}"