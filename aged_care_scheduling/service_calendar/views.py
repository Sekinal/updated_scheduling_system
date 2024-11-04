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
from core.models import SiteSettings  # Adjust the import based on your app structure

@login_required
def calendar_view(request):
    caregivers = User.objects.filter(userprofile__role__in=['staff', 'manager'])
    residents = Resident.objects.all()
    care_homes = CareHome.objects.all()
    service_types = ServiceType.objects.all()

    # Get current timezone from activated timezone
    current_timezone = timezone.get_current_timezone_name()

    return render(request, 'service_calendar/calendar.html', {
        'caregivers': caregivers,
        'residents': residents,
        'care_homes': care_homes,
        'service_types': service_types,
        'current_timezone': current_timezone,  # Pass timezone to template
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

    # Handle 'unassigned' caregiver
    if caregivers and caregivers[0]:
        if 'unassigned' in caregivers:
            services = services.filter(
                Q(caregiver__id__in=[c for c in caregivers if c != 'unassigned']) | Q(caregiver__isnull=True)
            )
        else:
            services = services.filter(caregiver__id__in=caregivers)
    
    if residents and residents[0]:
        services = services.filter(resident__id__in=residents)
    if care_homes and care_homes[0]:
        services = services.filter(resident__care_home__id__in=care_homes)
    if service_types and service_types[0]:
        services = services.filter(service_type__id__in=service_types)

    current_tz = timezone.get_current_timezone()
    
    events = [{
        'id': service.id,
        'title': f"{service.service_type.name} - {service.resident.first_name} {service.resident.last_name}",
        'start': timezone.localtime(service.scheduled_time).isoformat(),
        'end': timezone.localtime(service.end_time).isoformat(),
        'resident': f"{service.resident.first_name} {service.resident.last_name}",
        'serviceType': service.service_type.name,
        'type': 'service',
        'caregiver': service.caregiver.username if service.caregiver else 'Not assigned',
        'status': service.get_status_display(),
        'frequencyId': str(service.frequency_id) if service.frequency_id else None
    } for service in services]

    if filter_applied:
        blocked_times = BlockedTime.objects.filter(
            Q(start_date__range=[start.date(), end.date()]) |
            Q(end_date__range=[start.date(), end.date()])
        )

        if caregivers and caregivers[0]:
            if 'unassigned' in caregivers:
                blocked_times = blocked_times.filter(
                    Q(caregivers__id__in=[c for c in caregivers if c != 'unassigned']) | Q(caregivers__isnull=True)
                )
            else:
                blocked_times = blocked_times.filter(caregivers__id__in=caregivers)
        if care_homes and care_homes[0]:
            blocked_times = blocked_times.filter(
                Q(locations__id__in=care_homes) | Q(locations__isnull=True)
            )

        for blocked in blocked_times:
            start_datetime = timezone.make_aware(
                datetime.combine(blocked.start_date, blocked.start_time), current_tz
            )
            end_datetime = timezone.make_aware(
                datetime.combine(blocked.end_date, blocked.end_time), current_tz
            )
            events.append({
                'id': f"blocked_{blocked.id}",
                'title': f"Blocked: {blocked.reason}",
                'start': timezone.localtime(start_datetime, current_tz).isoformat(),
                'end': timezone.localtime(end_datetime, current_tz).isoformat(),
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

    # Handle 'unassigned' caregiver
    if caregivers and caregivers[0]:
        if 'unassigned' in caregivers:
            services = services.filter(
                Q(caregiver__id__in=[c for c in caregivers if c != 'unassigned']) | Q(caregiver__isnull=True)
            )
        else:
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
        'scheduled_time': service.scheduled_time.strftime('%Y-%m-%d') if service.scheduled_time else 'Not set'
    } for service in services]

    return JsonResponse(data, safe=False)