from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from services.models import Service, BlockedTime
from residents.models import Resident
from homes.models import CareHome
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
import csv

@login_required
def calendar_view(request):
    caregivers = User.objects.filter(userprofile__role='staff').values('id', 'username')
    residents = Resident.objects.all()
    care_homes = CareHome.objects.all()
    return render(request, 'service_calendar/calendar.html', {
        'caregivers': caregivers,
        'residents': residents,
        'care_homes': care_homes,
    })

@login_required
def get_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    caregiver_ids = request.GET.getlist('caregivers[]')
    resident_ids = request.GET.getlist('residents[]')
    care_home_ids = request.GET.getlist('care_homes[]')

    services = Service.objects.filter(scheduled_time__range=[start, end])
    blocked_times = BlockedTime.objects.filter(start_time__range=[start, end])

    if caregiver_ids:
        services = services.filter(caregiver_id__in=caregiver_ids)
    if resident_ids:
        services = services.filter(resident_id__in=resident_ids)
    if care_home_ids:
        services = services.filter(resident__care_home_id__in=care_home_ids)

    events = []
    for service in services:
        events.append({
            'id': service.id,
            'title': f"{service.service_type.name} - {service.resident.first_name} {service.resident.last_name}",
            'start': service.scheduled_time.isoformat(),
            'end': service.end_time.isoformat(),
            'color': 'blue',
            'extendedProps': {
                'resident': f"{service.resident.first_name} {service.resident.last_name}",
                'care_home': service.resident.care_home.name,
                'service_type': service.service_type.name,
                'caregiver': service.caregiver.username if service.caregiver else 'Unassigned'
            }
        })

    for blocked_time in blocked_times:
        events.append({
            'id': f"blocked_{blocked_time.id}",
            'title': f"Blocked: {blocked_time.reason}",
            'start': blocked_time.start_time.isoformat(),
            'end': blocked_time.end_time.isoformat(),
            'color': 'red',
        })

    return JsonResponse(events, safe=False)

@login_required
def generate_report(request):
    report_type = request.GET.get('type', 'resident')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    services = Service.objects.filter(scheduled_time__range=[start_date, end_date])

    if report_type == 'resident':
        data = services.values('resident__first_name', 'resident__last_name', 'service_type__name').annotate(count=Count('id'))
    elif report_type == 'care_home':
        data = services.values('resident__care_home__name', 'service_type__name').annotate(count=Count('id'))
    else:  # group (assuming group is represented by care_home)
        data = services.values('resident__care_home__name', 'service_type__name').annotate(count=Count('id'))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_services_report.csv"'

    writer = csv.writer(response)
    if report_type == 'resident':
        writer.writerow(['Resident', 'Service Type', 'Count'])
        for item in data:
            writer.writerow([f"{item['resident__first_name']} {item['resident__last_name']}", item['service_type__name'], item['count']])
    else:
        writer.writerow(['Care Home', 'Service Type', 'Count'])
        for item in data:
            writer.writerow([item['resident__care_home__name'], item['service_type__name'], item['count']])

    return response