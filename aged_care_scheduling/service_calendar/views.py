# service_calendar/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User


from services.models import Service, ServiceType, BlockedTime
from residents.models import Resident
from homes.models import CareHome
from django.db.models import Q  # Import Q for complex queries
from django.utils import timezone  # Import timezone for date and time handling
from datetime import datetime, timedelta
from dateutil import parser

@login_required
def calendar_view(request):
    caregivers = User.objects.filter(userprofile__role__in=['staff', 'manager'])
    residents = Resident.objects.all()
    care_homes = CareHome.objects.all()
    service_types = ServiceType.objects.all()
    return render(request, 'service_calendar/calendar.html', {
        'caregivers': caregivers,
        'residents': residents,
        'care_homes': care_homes,
        'service_types': service_types,
    })

@login_required
def get_events(request):
    def parse_date(date_string):
        return parser.isoparse(date_string)

    start = parse_date(request.GET.get('start'))
    end = parse_date(request.GET.get('end'))

    caregivers = request.GET.get('caregivers', '').split(',')
    residents = request.GET.get('residents', '').split(',')
    care_homes = request.GET.get('care_homes', '').split(',')
    service_types = request.GET.get('service_types', '').split(',')

    filter_applied = request.GET.get('filter_applied') == 'true'

    services = Service.objects.filter(
        scheduled_time__range=[start, end],
        status='scheduled'
    )

    if caregivers and caregivers[0]:
        services = services.filter(caregiver__id__in=caregivers)
    if residents and residents[0]:
        services = services.filter(resident__id__in=residents)
    if care_homes and care_homes[0]:
        services = services.filter(resident__care_home__id__in=care_homes)
    if service_types and service_types[0]:
        services = services.filter(service_type__id__in=service_types)

    events = [{
        'id': service.id,
        'title': f"{service.service_type.name} - {service.resident.first_name} {service.resident.last_name}",
        'start': service.scheduled_time.isoformat(),
        'end': service.end_time.isoformat(),
        'resident': f"{service.resident.first_name} {service.resident.last_name}",
        'serviceType': service.service_type.name,
        'type': 'service',
        'caregiver': service.caregiver.username if service.caregiver else 'Not assigned',
        'status': service.get_status_display()
    } for service in services]
    
    if filter_applied:
        blocked_times = BlockedTime.objects.filter(
            Q(start_date__range=[start.date(), end.date()]) | Q(end_date__range=[start.date(), end.date()])
        )

        if caregivers and caregivers[0]:
            blocked_times = blocked_times.filter(Q(caregivers__id__in=caregivers) | Q(caregivers__isnull=True))
        if care_homes and care_homes[0]:
            blocked_times = blocked_times.filter(Q(locations__id__in=care_homes) | Q(locations__isnull=True))

        for blocked in blocked_times:
            events.append({
                'id': f"blocked_{blocked.id}",
                'title': f"Blocked: {blocked.reason}",
                'start': timezone.make_aware(datetime.combine(blocked.start_date, blocked.start_time)).isoformat(),
                'end': timezone.make_aware(datetime.combine(blocked.end_date, blocked.end_time)).isoformat(),
                'type': 'blocked',
                'allDay': True,
                'display': 'background',
                'color': '#ffcdd2',
            })

    return JsonResponse(events, safe=False)

@login_required
def get_unscheduled_services(request):
    caregivers = request.GET.get('caregivers', '').split(',')
    residents = request.GET.get('residents', '').split(',')
    care_homes = request.GET.get('care_homes', '').split(',')
    service_types = request.GET.get('service_types', '').split(',')

    services = Service.objects.filter(status='unscheduled')

    if caregivers and caregivers[0]:
        services = services.filter(caregiver__id__in=caregivers)
    if residents and residents[0]:
        services = services.filter(resident__id__in=residents)
    if care_homes and care_homes[0]:
        services = services.filter(resident__care_home__id__in=care_homes)
    if service_types and service_types[0]:
        services = services.filter(service_type__id__in=service_types)

    data = [{
        'id': service.id,
        'service_type': service.service_type.name,
        'resident': f"{service.resident.first_name} {service.resident.last_name}",
        'due_date': service.due_date.strftime('%Y-%m-%d') if service.due_date else 'Not set'
    } for service in services]

    return JsonResponse(data, safe=False)