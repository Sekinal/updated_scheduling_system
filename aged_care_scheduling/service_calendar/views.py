from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from services.models import Service, ServiceType
from residents.models import Resident
from homes.models import CareHome

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
    start = request.GET.get('start')
    end = request.GET.get('end')
    caregivers = request.GET.get('caregivers', '').split(',')
    residents = request.GET.get('residents', '').split(',')
    care_homes = request.GET.get('care_homes', '').split(',')
    service_types = request.GET.get('service_types', '').split(',')

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
        'serviceType': service.service_type.name
    } for service in services]
    return JsonResponse(events, safe=False)