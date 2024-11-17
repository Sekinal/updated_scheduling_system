# dashboard/views.py

from django.shortcuts import render
from django.db.models import Count, Q
from services.models import Service, ServiceType, Escalation
from residents.models import Resident
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.utils import timezone

@login_required
def dashboard_view(request):
    # Current date and time
    now = timezone.now()
    
    # Total services
    total_services = Service.objects.count()
    
    # Services by status
    services_by_status = Service.objects.values('status').annotate(count=Count('id')).order_by('-count')
    
    # Completed services
    completed_services = Service.objects.filter(status='completed').count()
    
    # Pending services (assuming 'scheduled' and 'unscheduled' are pending)
    pending_services = Service.objects.filter(status__in=['scheduled', 'unscheduled']).count()
    
    # Unscheduled services
    unscheduled_services = Service.objects.filter(status='unscheduled').count()
    
    # Refused services
    refused_services = Service.objects.filter(status='refused').count()
    
    # Missed services
    missed_services = Service.objects.filter(status='missed').count()
    
    # Services over time (e.g., last 30 days)
    thirty_days_ago = now - timedelta(days=30)
    services_last_30_days = Service.objects.filter(scheduled_time__gte=thirty_days_ago).extra({"day": "date(scheduled_time)"}).values('day').annotate(count=Count('id')).order_by('day')
    
    # Top Caregivers by number of services
    top_caregivers = Service.objects.values('caregiver__username').annotate(count=Count('id')).order_by('-count')[:10]
    
    # Escalations
    total_escalations = Escalation.objects.count()
    escalations_by_type = Escalation.objects.values('escalation_type').annotate(count=Count('id'))
    
    context = {
        'total_services': total_services,
        'services_by_status': services_by_status,
        'completed_services': completed_services,
        'pending_services': pending_services,
        'unscheduled_services': unscheduled_services,
        'refused_services': refused_services,
        'missed_services': missed_services,
        'services_last_30_days': services_last_30_days,
        'top_caregivers': top_caregivers,
        'total_escalations': total_escalations,
        'escalations_by_type': escalations_by_type,
    }
    
    return render(request, 'dashboard.html', context)